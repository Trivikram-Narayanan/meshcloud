# 📦 Installation

This guide will help you install MeshCloud on your system.

## 🐧 System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **RAM**: 512MB minimum, 2GB recommended
- **Disk**: 1GB free space for application and logs
- **Network**: Stable internet connection for peer communication

### Recommended Requirements

- **Python**: 3.11 or higher
- **RAM**: 4GB or more
- **Disk**: 10GB+ SSD storage
- **CPU**: 2+ cores
- **Network**: 100Mbps+ connection

## 🚀 Quick Install

### Using pip (Recommended)

```bash
# Install from PyPI (when available)
pip install meshcloud

# Or install from source
git clone https://github.com/yourusername/meshcloud.git
cd meshcloud
pip install -e .
```

### Using Docker

```bash
# Pull the official image
docker pull yourusername/meshcloud:latest

# Or build from source
git clone https://github.com/yourusername/meshcloud.git
cd meshcloud
docker build -t meshcloud .
```

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  meshcloud:
    image: yourusername/meshcloud:latest
    ports:
      - "8000:8000"
    environment:
      - NODE_URL=https://localhost:8000
      - JWT_SECRET_KEY=your-secret-key-here
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
```

## 📋 Detailed Installation

### Step 1: Install Python

MeshCloud requires Python 3.8 or higher. Check your Python version:

```bash
python3 --version
# or
python --version
```

If you don't have Python installed, download it from [python.org](https://python.org).

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv meshcloud-env

# Activate virtual environment
source meshcloud-env/bin/activate  # Linux/Mac
# or
meshcloud-env\Scripts\activate     # Windows
```

### Step 3: Install MeshCloud

```bash
# Install MeshCloud
pip install meshcloud

# Verify installation
meshcloud --version
```

### Step 4: Install Additional Dependencies (Optional)

For development or advanced features:

```bash
# Install development dependencies
pip install meshcloud[dev]

# Install documentation dependencies
pip install meshcloud[docs]
```

## 🔧 Post-Installation Setup

### 1. Create Configuration

Create a `.env` file in your project directory:

```bash
# Copy the example configuration
cp .env.example .env

# Edit the configuration
nano .env
```

### 2. Initialize Storage Directories

```bash
# Create necessary directories
mkdir -p storage/{chunks,manifests,tmp}
mkdir -p logs

# Set proper permissions
chmod 755 storage logs
```

### 3. Configure Firewall

Ensure the following ports are open:

- **8000**: Main API port (configurable)
- **9999**: Peer discovery port (configurable)

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8000
sudo ufw allow 9999

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9999/tcp
sudo firewall-cmd --reload
```

## 🧪 Verify Installation

### Start MeshCloud

```bash
# Start a basic node
meshcloud start --port 8000

# Or run with custom configuration
meshcloud start --config config.json
```

### Test Basic Functionality

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check status
curl http://localhost:8000/

# Should return:
# {"status": "ok"}
# {"node": "MeshCloud", "status": "running", "version": "0.1.0", "peers": 0, "node_url": "https://localhost:8000"}
```

### Test File Upload

```bash
# Create a test file
echo "Hello, MeshCloud!" > test.txt

# Start upload session
curl -X POST "http://localhost:8000/start_upload" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.txt", "total_chunks": 1}'

# Upload file chunk
curl -X POST "http://localhost:8000/upload_chunk" \
  -F "upload_id=YOUR_UPLOAD_ID" \
  -F "chunk_index=0" \
  -F "chunk_hash=YOUR_CHUNK_HASH" \
  -F "file=@test.txt"

# Finalize upload
curl -X POST "http://localhost:8000/finalize_upload" \
  -H "Content-Type: application/json" \
  -d '{"upload_id": "YOUR_UPLOAD_ID", "chunks": ["YOUR_CHUNK_HASH"], "filename": "test.txt"}'
```

## 🐳 Docker Installation

### Basic Docker Run

```bash
docker run -d \
  --name meshcloud \
  -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/logs:/app/logs \
  -e NODE_URL=https://your-domain.com:8000 \
  -e JWT_SECRET_KEY=your-secret-key \
  yourusername/meshcloud:latest
```

### Docker Compose with Monitoring

```yaml
version: '3.8'
services:
  meshcloud:
    image: yourusername/meshcloud:latest
    ports:
      - "8000:8000"
    environment:
      - NODE_URL=https://meshcloud.example.com:8000
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LOG_LEVEL=INFO
      - ENABLE_METRICS=true
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./config/peers.json:/app/config/peers.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
```

## ☁️ Cloud Installation

### AWS EC2

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups meshcloud-sg

# Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip -y

# Install MeshCloud
pip3 install meshcloud

# Configure and start
sudo systemctl enable meshcloud
sudo systemctl start meshcloud
```

### Google Cloud Platform

```bash
# Create GCE instance
gcloud compute instances create meshcloud-node \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=meshcloud

# Install dependencies
sudo apt update
sudo apt install python3 python3-pip -y

# Install and configure MeshCloud
pip3 install meshcloud
# ... configuration steps
```

### Microsoft Azure

```bash
# Create VM
az vm create \
  --resource-group meshcloud-rg \
  --name meshcloud-node \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --size Standard_B2s

# Install dependencies
sudo apt update
sudo apt install python3 python3-pip -y

# Install and configure MeshCloud
pip3 install meshcloud
# ... configuration steps
```

## 🔧 Troubleshooting

### Common Installation Issues

**1. Permission Denied Errors**

```bash
# Fix storage permissions
sudo chown -R $USER:$USER storage/
sudo chown -R $USER:$USER logs/

# Or run with sudo (not recommended for production)
sudo meshcloud start --port 8000
```

**2. Port Already in Use**

```bash
# Find process using port
lsof -i :8000

# Kill process or use different port
meshcloud start --port 8001
```

**3. Import Errors**

```bash
# Reinstall dependencies
pip uninstall meshcloud
pip install --no-cache-dir meshcloud

# Check Python path
python3 -c "import meshcloud; print(meshcloud.__file__)"
```

**4. Database Errors**

```bash
# Remove old database
rm -f db/meshcloud.db

# Reinitialize
meshcloud init-db
```

### Getting Help

- **📖 Documentation**: [docs.meshcloud.io](https://docs.meshcloud.io)
- **🐛 Issues**: [GitHub Issues](https://github.com/yourusername/meshcloud/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/yourusername/meshcloud/discussions)
- **📧 Support**: support@meshcloud.io

## 📈 Next Steps

Once installed, you can:

1. **[Configure your node](configuration.md)** - Set up authentication, networking, and storage
2. **[Start your first node](quick-start.md)** - Launch and test your MeshCloud instance
3. **[Join a mesh network](node-management.md)** - Connect with other nodes
4. **[Upload your first files](file-upload.md)** - Start using MeshCloud for file storage

---

<div align="center">
  <p><strong>Installation complete?</strong></p>
  <a href="quick-start/" class="md-button md-button--primary">Quick Start Guide</a>
  <a href="configuration/" class="md-button">Configuration</a>
</div>