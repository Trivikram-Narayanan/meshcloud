# MeshCloud Python Client

[![PyPI version](https://badge.fury.io/py/meshcloud-client.svg)](https://pypi.org/project/meshcloud-client/)
[![Python Versions](https://img.shields.io/pypi/pyversions/meshcloud-client.svg)](https://pypi.org/project/meshcloud-client/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A comprehensive Python async client library for interacting with MeshCloud distributed file storage systems.

## 🚀 Features

- ✅ **Async/Await Support** - Native async/await with asyncio
- ✅ **JWT Authentication** - Automatic token management and renewal
- ✅ **Chunked Uploads** - Efficient large file uploads with progress callbacks
- ✅ **Comprehensive Error Handling** - Detailed exceptions for all error conditions
- ✅ **Type Hints** - Full type annotations for IDE support
- ✅ **Context Manager** - Automatic resource cleanup
- ✅ **Batch Operations** - Concurrent file processing
- ✅ **Rate Limit Handling** - Automatic retry with exponential backoff

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

#### Authentication

```python
await client.authenticate(username: str, password: str) -> Dict[str, Any]
```

#### File Operations

```python
await client.upload_file(
    file_obj: Union[str, Path, BinaryIO],
    filename: str = None,
    progress_callback: callable = None
) -> Dict[str, Any]
```

```python
await client.file_exists(file_hash: str) -> bool
```

```python
await client.get_file_locations(file_hash: str) -> List[str]
```

#### System Monitoring

```python
await client.get_status() -> Dict[str, Any]
```

```python
await client.health_check() -> Dict[str, Any]
```

```python
await client.get_metrics(metric_type: str = "application") -> Dict[str, Any]
```

## 🔧 Advanced Usage

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

### Batch Operations

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
```

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=meshcloud_client --cov-report=html
```

## 📋 Requirements

- Python 3.8+
- requests
- urllib3

## 📄 License

Apache License 2.0

## 🆘 Support

- **Documentation**: https://docs.meshcloud.io/clients/python/
- **Issues**: https://github.com/yourusername/meshcloud/issues
- **Discussions**: https://github.com/yourusername/meshcloud/discussions