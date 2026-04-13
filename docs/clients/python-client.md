# 🐍 Python Client Library

Complete Python client library for interacting with MeshCloud distributed file storage systems.

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install meshcloud-client
```

### From Source

```bash
git clone https://github.com/yourusername/meshcloud.git
cd meshcloud/clients/python
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## 🚀 Quick Start

```python
import asyncio
from meshcloud_client import MeshCloudClient

async def main():
    # Initialize client
    client = MeshCloudClient(
        "https://your-meshcloud-node.com",
        username="your-username",
        password="your-password"
    )

    # Upload a file
    with open("large_file.dat", "rb") as f:
        result = await client.upload_file(f, "large_file.dat")
        print(f"Uploaded: {result['hash']}")

    # Check file existence
    exists = await client.file_exists(result['hash'])
    print(f"File exists: {exists}")

asyncio.run(main())
```

## 📚 API Reference

### MeshCloudClient

Main client class for interacting with MeshCloud nodes.

#### Constructor

```python
MeshCloudClient(
    base_url: str,
    username: str = None,
    password: str = None,
    timeout: int = 30,
    max_retries: int = 3,
    verify_ssl: bool = True,
    chunk_size: int = 4194304  # 4MB
)
```

**Parameters:**
- `base_url`: Base URL of the MeshCloud node
- `username`: Username for authentication (optional)
- `password`: Password for authentication (optional)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum number of retries for failed requests
- `verify_ssl`: Whether to verify SSL certificates
- `chunk_size`: Size of chunks for file uploads in bytes

#### Authentication

```python
await client.authenticate(username: str, password: str) -> Dict[str, Any]
```

Authenticates with the MeshCloud node and returns authentication details.

#### File Operations

```python
await client.upload_file(
    file_obj: Union[str, Path, BinaryIO],
    filename: str = None,
    progress_callback: callable = None
) -> Dict[str, Any]
```

Uploads a file to MeshCloud.

**Parameters:**
- `file_obj`: File path (str/Path) or file-like object
- `filename`: Optional filename override
- `progress_callback`: Callback function for upload progress

**Returns:** Upload result with file hash and metadata

```python
await client.file_exists(file_hash: str) -> bool
```

Checks if a file exists on the node.

```python
await client.get_file_locations(file_hash: str) -> List[str]
```

Gets all nodes that have a copy of the specified file.

#### System Monitoring

```python
await client.get_status() -> Dict[str, Any]
```

Gets comprehensive node status information.

```python
await client.health_check() -> Dict[str, Any]
```

Performs a health check on the node.

```python
await client.get_metrics(metric_type: str = "application") -> Dict[str, Any]
```

Gets system or application metrics.

**Parameters:**
- `metric_type`: Type of metrics ("system", "application", or "health")

```python
await client.get_recent_requests(limit: int = 50) -> Dict[str, Any]
```

Gets recent API request history.

```python
await client.get_recent_errors(limit: int = 20) -> Dict[str, Any]
```

Gets recent API error history.

#### Upload Management

```python
await client.get_upload_status(upload_id: str) -> Dict[str, Any]
```

Gets the status of an ongoing upload.

## 🔧 Advanced Usage

### Context Manager

```python
async with MeshCloudClient(base_url, username=username, password=password) as client:
    # Client automatically handles cleanup
    result = await client.upload_file("file.txt")
```

### Progress Callbacks

```python
def upload_progress(progress, current_chunk, total_chunks):
    print(f"Upload progress: {progress:.1f}% ({current_chunk}/{total_chunks})")

result = await client.upload_file(
    "large_file.zip",
    progress_callback=upload_progress
)
```

### Error Handling

```python
from meshcloud_client import (
    MeshCloudError,
    AuthenticationError,
    UploadError,
    APIError,
    RateLimitError
)

try:
    result = await client.upload_file("file.txt")
except AuthenticationError:
    print("Authentication failed")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except UploadError as e:
    print(f"Upload failed: {e}")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

### Custom Configuration

```python
client = MeshCloudClient(
    base_url="https://meshcloud.example.com",
    timeout=60,           # 60 second timeout
    max_retries=5,        # Retry up to 5 times
    chunk_size=1024*1024, # 1MB chunks
    verify_ssl=False      # Skip SSL verification (not recommended)
)
```

## 📊 Monitoring Integration

### Prometheus Metrics

```python
import time
from prometheus_client import Gauge, Counter

# Define metrics
upload_count = Counter('meshcloud_uploads_total', 'Total file uploads')
upload_duration = Gauge('meshcloud_upload_duration_seconds', 'Upload duration')

async def monitored_upload(client, file_path):
    start_time = time.time()

    try:
        result = await client.upload_file(file_path)
        upload_count.inc()
        return result
    finally:
        upload_duration.set(time.time() - start_time)
```

### Health Checks

```python
async def health_check(client):
    try:
        health = await client.health_check()
        return health['status'] == 'ok'
    except Exception:
        return False
```

## 🔄 Batch Operations

### Multiple File Upload

```python
async def upload_batch(client, files):
    results = []
    for file_path in files:
        try:
            result = await client.upload_file(file_path)
            results.append({
                'file': file_path,
                'success': True,
                'hash': result['hash']
            })
        except Exception as e:
            results.append({
                'file': file_path,
                'success': False,
                'error': str(e)
            })
    return results

# Usage
files = ['file1.txt', 'file2.jpg', 'file3.pdf']
results = await upload_batch(client, files)
```

### Concurrent Uploads

```python
import asyncio

async def upload_concurrent(client, files):
    tasks = [client.upload_file(file) for file in files]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
files = ['file1.txt', 'file2.jpg', 'file3.pdf']
results = await upload_concurrent(client, files)
```

## 🛠️ Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=meshcloud_client --cov-report=html
```

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build docs
cd docs
make html
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📋 Requirements

- Python 3.8+
- requests
- urllib3
- typing-extensions (for Python < 3.9)

## 📄 License

Apache License 2.0

## 🆘 Support

- **Documentation**: https://docs.meshcloud.io/clients/python/
- **Issues**: https://github.com/yourusername/meshcloud/issues
- **Discussions**: https://github.com/yourusername/meshcloud/discussions

---

<div align="center">
  <p><strong>Need help?</strong></p>
  <a href="../examples/" class="md-button md-button--primary">View Examples</a>
  <a href="../api/rest-api/" class="md-button">API Reference</a>
</div>