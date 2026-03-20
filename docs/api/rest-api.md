# 🌐 REST API Reference

This document provides a comprehensive reference for the MeshCloud REST API.

## 📋 API Overview

- **Base URL**: `https://your-node-url:8000`
- **Authentication**: JWT Bearer tokens (optional for some endpoints)
- **Content Type**: `application/json`
- **Rate Limiting**: 100 requests per minute per client

## 🔐 Authentication

Most API endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Get Authentication Token

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=yourpassword
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## 📊 Core Endpoints

### Health Check

Get the health status of the node.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Node Status

Get comprehensive node information.

```http
GET /
Authorization: Bearer <token>
```

**Response:**
```json
{
  "node": "MeshCloud",
  "status": "running",
  "version": "0.1.0",
  "peers": 3,
  "node_url": "https://node1.example.com:8000"
}
```

### File Existence Check

Check if a file exists on this node.

```http
GET /has_file/{file_hash}
```

**Parameters:**
- `file_hash` (path): SHA256 hash of the file

**Response:**
```json
{
  "exists": true
}
```

### File Location Lookup

Find which nodes have a specific file.

```http
GET /file_locations/{file_hash}
```

**Parameters:**
- `file_hash` (path): SHA256 hash of the file

**Response:**
```json
{
  "nodes": [
    "https://node1.example.com:8000",
    "https://node2.example.com:8000"
  ]
}
```

## 📤 File Upload Endpoints

### Start Upload Session

Initialize a new file upload session.

```http
POST /start_upload
Content-Type: application/json
Authorization: Bearer <token>

{
  "filename": "example.txt",
  "total_chunks": 3
}
```

**Request Body:**
```json
{
  "filename": "string",     // Required: Original filename
  "total_chunks": "integer" // Required: Total number of chunks
}
```

**Response:**
```json
{
  "upload_id": "uuid-string"
}
```

### Upload File Chunk

Upload a single chunk of the file.

```http
POST /upload_chunk
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Form Data:**
- `upload_id`: UUID from start_upload response
- `chunk_index`: Integer chunk index (0-based)
- `chunk_hash`: SHA256 hash of the chunk data
- `file`: Binary chunk data

**Response (Success):**
```json
{
  "status": "chunk stored"
}
```

**Response (Hash Mismatch):**
```json
{
  "error": "chunk hash mismatch"
}
```

### Finalize Upload

Complete the file upload and trigger replication.

```http
POST /finalize_upload
Content-Type: application/json
Authorization: Bearer <token>

{
  "upload_id": "uuid-string",
  "chunks": ["hash1", "hash2", "hash3"],
  "filename": "example.txt"
}
```

**Request Body:**
```json
{
  "upload_id": "string",   // Required: Upload session ID
  "chunks": ["string"],    // Required: Array of chunk hashes
  "filename": "string"     // Required: Original filename
}
```

**Response (New File):**
```json
{
  "status": "file finalized",
  "hash": "file_sha256_hash",
  "filename": "example.txt"
}
```

**Response (Duplicate):**
```json
{
  "status": "duplicate",
  "hash": "existing_file_hash",
  "filename": "example.txt"
}
```

### Upload Status

Check the status of an ongoing upload.

```http
GET /upload_status/{upload_id}
Authorization: Bearer <token>
```

**Parameters:**
- `upload_id` (path): Upload session UUID

**Response:**
```json
{
  "uploaded_chunks": [0, 1, 2]
}
```

## 🔄 Replication Endpoints

### Replicate Chunk

Receive a chunk from another node (internal use).

```http
POST /replicate_chunk?chunk_hash={hash}
Content-Type: application/octet-stream
X-MeshCloud-Token: <node_token>
```

**Headers:**
- `X-MeshCloud-Token`: Node authentication token

**Query Parameters:**
- `chunk_hash`: SHA256 hash of the chunk

**Request Body:** Binary chunk data

**Response:**
```json
{
  "stored": "chunk_hash"
}
```

### Legacy Upload

Direct file upload from peer nodes.

```http
POST /upload
Content-Type: multipart/form-data
X-MeshCloud-Token: <node_token>
X-MeshCloud-Node: true
```

**Headers:**
- `X-MeshCloud-Token`: Node authentication token
- `X-MeshCloud-Node`: Indicates upload from another node

**Form Data:**
- `file`: File to upload

**Response:**
```json
{
  "status": "stored",
  "hash": "file_sha256_hash",
  "filename": "uploaded_file.txt"
}
```

## 📊 Monitoring Endpoints

### Detailed Health Check

Get comprehensive health status with metrics.

```http
GET /metrics/health/detailed
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "memory_used_mb": 2048,
    "memory_available_mb": 1024,
    "disk_usage_percent": 23.5,
    "disk_free_gb": 150.5
  },
  "application": {
    "uptime_seconds": 3600,
    "total_requests": 1250,
    "total_errors": 5,
    "average_request_duration": 0.045,
    "request_rate_per_second": 0.35,
    "error_rate_per_second": 0.001,
    "file_operations": {
      "uploads": 45,
      "downloads": 23,
      "deletions": 2
    },
    "chunk_operations": {
      "stored": 180,
      "retrieved": 156
    },
    "sync_operations": {
      "success": 42,
      "failure": 3
    }
  }
}
```

### System Metrics

Get system-level metrics.

```http
GET /metrics/system
Authorization: Bearer <token>
```

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 67.8,
  "memory_used_mb": 2048,
  "memory_available_mb": 1024,
  "disk_usage_percent": 23.5,
  "disk_free_gb": 150.5
}
```

### Application Metrics

Get application-level metrics.

```http
GET /metrics/application
Authorization: Bearer <token>
```

**Response:**
```json
{
  "uptime_seconds": 3600,
  "total_requests": 1250,
  "total_errors": 5,
  "average_request_duration": 0.045,
  "request_rate_per_second": 0.35,
  "error_rate_per_second": 0.001,
  "file_operations": {
    "uploads": 45,
    "downloads": 23,
    "deletions": 2
  },
  "chunk_operations": {
    "stored": 180,
    "retrieved": 156
  },
  "sync_operations": {
    "success": 42,
    "failure": 3
  }
}
```

### Recent Requests

Get recent request history.

```http
GET /metrics/requests/recent?limit=50
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of requests to return (default: 50, max: 1000)

**Response:**
```json
{
  "requests": [
    {
      "timestamp": "2024-01-01T12:00:00.000Z",
      "method": "POST",
      "path": "/upload_chunk",
      "status_code": 200,
      "duration": 0.045
    }
  ],
  "count": 1
}
```

### Recent Errors

Get recent error history.

```http
GET /metrics/errors/recent?limit=20
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of errors to return (default: 20, max: 100)

**Response:**
```json
{
  "errors": [
    {
      "timestamp": "2024-01-01T12:00:00.000Z",
      "method": "POST",
      "path": "/upload_chunk",
      "status_code": 400,
      "duration": 0.023
    }
  ],
  "count": 1
}
```

### Prometheus Metrics

Get metrics in Prometheus format.

```http
GET /metrics/prometheus
```

**Response:**
```
# HELP meshcloud_uptime_seconds Application uptime in seconds
# TYPE meshcloud_uptime_seconds gauge
meshcloud_uptime_seconds 3600

# HELP meshcloud_requests_total Total number of HTTP requests
# TYPE meshcloud_requests_total counter
meshcloud_requests_total 1250

# HELP meshcloud_errors_total Total number of HTTP errors
# TYPE meshcloud_errors_total counter
meshcloud_errors_total 5

# HELP meshcloud_request_duration_seconds Average request duration
# TYPE meshcloud_request_duration_seconds gauge
meshcloud_request_duration_seconds 0.045

# HELP meshcloud_cpu_percent CPU usage percentage
# TYPE meshcloud_cpu_percent gauge
meshcloud_cpu_percent 45.2

# HELP meshcloud_memory_percent Memory usage percentage
# TYPE meshcloud_memory_percent gauge
meshcloud_memory_percent 67.8

# HELP meshcloud_disk_usage_percent Disk usage percentage
# TYPE meshcloud_disk_usage_percent gauge
meshcloud_disk_usage_percent 23.5
```

## 🚨 Error Responses

### Common Error Codes

- **400 Bad Request**: Invalid request data or parameters
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **413 Payload Too Large**: File size exceeds limits
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

### Error Response Format

```json
{
  "detail": "Error description",
  "error": "error_code"
}
```

### Rate Limit Error

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Try again in 60 seconds."
}
```

## 📝 Usage Examples

### Complete File Upload

```python
import requests
import hashlib
import io

# Configuration
BASE_URL = "https://your-node:8000"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Step 1: Prepare file
with open("large_file.dat", "rb") as f:
    file_data = f.read()

# Step 2: Split into chunks (4MB each)
CHUNK_SIZE = 4 * 1024 * 1024
chunks = []
for i in range(0, len(file_data), CHUNK_SIZE):
    chunk = file_data[i:i + CHUNK_SIZE]
    chunk_hash = hashlib.sha256(chunk).hexdigest()
    chunks.append((i // CHUNK_SIZE, chunk_hash, chunk))

# Step 3: Start upload session
start_response = requests.post(
    f"{BASE_URL}/start_upload",
    json={
        "filename": "large_file.dat",
        "total_chunks": len(chunks)
    },
    headers=headers
)
upload_id = start_response.json()["upload_id"]

# Step 4: Upload chunks
for chunk_index, chunk_hash, chunk_data in chunks:
    files = {
        "file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")
    }
    data = {
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "chunk_hash": chunk_hash
    }

    response = requests.post(
        f"{BASE_URL}/upload_chunk",
        files=files,
        data=data,
        headers=headers
    )
    response.raise_for_status()

# Step 5: Finalize upload
finalize_response = requests.post(
    f"{BASE_URL}/finalize_upload",
    json={
        "upload_id": upload_id,
        "chunks": [chunk_hash for _, chunk_hash, _ in chunks],
        "filename": "large_file.dat"
    },
    headers=headers
)

result = finalize_response.json()
print(f"File uploaded with hash: {result['hash']}")
```

### Monitoring Integration

```python
import requests
import time

BASE_URL = "https://your-node:8000"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Get health status
health = requests.get(f"{BASE_URL}/metrics/health/detailed", headers=headers)
print(f"Node health: {health.json()['status']}")

# Get system metrics
system = requests.get(f"{BASE_URL}/metrics/system", headers=headers)
print(f"CPU usage: {system.json()['cpu_percent']}%")

# Get recent errors
errors = requests.get(f"{BASE_URL}/metrics/errors/recent?limit=5", headers=headers)
for error in errors.json()['errors']:
    print(f"Error: {error['method']} {error['path']} -> {error['status_code']}")
```

## 🔒 Security Considerations

- Always use HTTPS in production
- Rotate JWT secrets regularly
- Implement proper firewall rules
- Monitor rate limiting and error rates
- Use strong passwords for admin accounts
- Regularly update dependencies

## 📞 Support

- **API Issues**: Check the [troubleshooting guide](../user-guide/troubleshooting.md)
- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/meshcloud/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/meshcloud/discussions)

---

<div align="center">
  <p><strong>Need help with integration?</strong></p>
  <a href="../user-guide/api-reference/" class="md-button md-button--primary">API Usage Guide</a>
  <a href="../developer-guide/api-development/" class="md-button">Developer Guide</a>
</div>