# Multi-stage Docker build for MeshCloud
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r meshcloud && useradd -r -g meshcloud meshcloud

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Copy application code
COPY app/ ./app/
COPY utils/ ./utils/
COPY cli/ ./cli/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p storage/chunks storage/manifests storage/tmp db logs && \
    chown -R meshcloud:meshcloud /app

# Switch to non-root user
USER meshcloud

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy all code
COPY . .

# Create necessary directories
RUN mkdir -p storage/chunks storage/manifests storage/tmp db logs && \
    chown -R meshcloud:meshcloud /app

# Switch to non-root user
USER meshcloud

# Expose port
EXPOSE 8000

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]

# Testing stage
FROM development as testing

# Copy test files
COPY tests/ ./tests/

# Run tests
RUN pytest --cov=app --cov=utils --cov=cli --cov-report=term-missing -v

# Build stage for creating distributable packages
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir build twine

# Copy Python client
COPY clients/python/ ./clients/python/

# Build Python package
RUN cd clients/python && python -m build

# Final distribution image
FROM nginx:alpine as distribution

# Copy built documentation (if available)
COPY --from=builder /build/clients/python/dist/ /usr/share/nginx/html/dist/

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]