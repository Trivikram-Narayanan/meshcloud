# 🌐 MeshCloud Client Libraries

Official client libraries for interacting with MeshCloud distributed file storage systems.

## 📚 Available Libraries

### 🐍 Python Client

A comprehensive Python async client library with full API support.

**Features:**
- ✅ Async/await support
- ✅ Automatic JWT authentication
- ✅ Chunked file uploads with progress callbacks
- ✅ Comprehensive error handling
- ✅ Type hints and IDE support
- ✅ Context manager support
- ✅ Batch operations support

**Installation:**
```bash
pip install meshcloud-client
```

**Quick Start:**
```python
import asyncio
from meshcloud_client import MeshCloudClient

async def main():
    client = MeshCloudClient("https://meshcloud.example.com")
    await client.authenticate("username", "password")

    # Upload a file
    with open("file.txt", "rb") as f:
        result = await client.upload_file(f)
        print(f"Uploaded: {result['hash']}")

asyncio.run(main())
```

**[📖 Full Documentation](python-client.md) | [📝 Examples](examples/python_example.py)**

### 🌐 JavaScript Client

A modern JavaScript client library for browsers and Node.js.

**Features:**
- ✅ Browser and Node.js support
- ✅ Promise-based API
- ✅ Automatic retries and error handling
- ✅ Progress callbacks for uploads
- ✅ Web Crypto API for hashing
- ✅ ESM and CommonJS support
- ✅ Interactive HTML examples

**Installation:**
```bash
npm install meshcloud-client
# or
yarn add meshcloud-client
```

**Browser Usage:**
```html
<script src="meshcloud-client.js"></script>
<script>
const client = new MeshCloudClient('https://meshcloud.example.com');
await client.authenticate('username', 'password');

const result = await client.uploadFile(fileInput.files[0]);
console.log(`Uploaded: ${result.hash}`);
</script>
```

**Node.js Usage:**
```javascript
const { MeshCloudClient } = require('meshcloud-client');

const client = new MeshCloudClient('https://meshcloud.example.com');
await client.authenticate('username', 'password');

const result = await client.uploadFile('file.txt');
console.log(`Uploaded: ${result.hash}`);
```

**[📖 Full Documentation](javascript-client.md) | [📝 Examples](examples/javascript_example.html)**

## 🚀 API Feature Comparison

| Feature | Python Client | JavaScript Client |
|---------|---------------|-------------------|
| Authentication | ✅ JWT | ✅ JWT |
| File Upload | ✅ Chunked | ✅ Chunked |
| File Download | ❌ (Planned) | ❌ (Planned) |
| Progress Callbacks | ✅ | ✅ |
| Batch Operations | ✅ | ❌ |
| Health Checks | ✅ | ✅ |
| Metrics Access | ✅ | ✅ |
| Error Handling | ✅ Comprehensive | ✅ Comprehensive |
| Type Safety | ✅ Type Hints | ❌ |
| Async Support | ✅ Native | ✅ Promises |
| Context Manager | ✅ | ❌ |
| Browser Support | ❌ | ✅ |
| Node.js Support | ✅ | ✅ |
| Auto Retries | ✅ | ✅ |
| SSL Verification | ✅ Configurable | ✅ Configurable |

## 🛠️ Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/meshcloud.git
cd meshcloud/clients

# Python client
cd python
pip install -e ".[dev]"
pytest

# JavaScript client
cd ../javascript
npm install
npm test
```

### Testing

```bash
# Python tests
cd python
pytest --cov=meshcloud_client

# JavaScript tests (when implemented)
cd javascript
npm test
```

### Contributing

We welcome contributions to the client libraries! Please see our [contributing guide](../../CONTRIBUTING.md) for details.

**Guidelines:**
- Maintain API compatibility
- Add comprehensive tests
- Update documentation
- Follow language-specific conventions
- Test against multiple MeshCloud versions

## 📋 Requirements

### Python Client
- Python 3.8+
- requests library
- urllib3 library

### JavaScript Client
- Modern browsers with Web Crypto API support
- Node.js 14+
- Native fetch API or polyfill

## 🔒 Security

Both client libraries implement security best practices:

- **Secure Authentication**: JWT tokens with automatic renewal
- **Input Validation**: File size limits and type checking
- **Error Handling**: No sensitive information in error messages
- **SSL/TLS**: Configurable certificate verification
- **Rate Limiting**: Respect server rate limits

## 📊 Performance

### Python Client
- **Concurrent Uploads**: Multiple files simultaneously
- **Memory Efficient**: Streaming file processing
- **Configurable Chunking**: 4MB default, adjustable
- **Connection Pooling**: HTTP session reuse

### JavaScript Client
- **Browser Optimized**: Uses Web Crypto API for hashing
- **Streaming Uploads**: File.slice() for memory efficiency
- **Progress Tracking**: Real-time upload progress
- **Retry Logic**: Exponential backoff for reliability

## 🎯 Use Cases

### Data Pipeline Integration
```python
# Python: ETL pipeline integration
async def upload_dataset(client, dataset_path):
    result = await client.upload_file(dataset_path)
    return result['hash']
```

### Web Application Uploads
```javascript
// JavaScript: Web app file uploads
async function handleFileUpload(file) {
    const client = new MeshCloudClient(API_URL);
    await client.authenticate(username, password);

    const result = await client.uploadFile(file, {
        onProgress: (progress) => {
            uploadProgressBar.style.width = progress + '%';
        }
    });

    return result.hash;
}
```

### Monitoring and Health Checks
```python
# Python: Infrastructure monitoring
async def check_node_health(client):
    health = await client.health_check()
    metrics = await client.get_metrics('system')
    return health['status'] === 'ok' and metrics['cpu_percent'] < 90
```

### Batch Processing
```python
# Python: Batch file processing
async def process_directory(client, directory):
    files = Path(directory).glob('**/*')
    tasks = [client.upload_file(file) for file in files]
    results = await asyncio.gather(*tasks)
    return results
```

## 📈 Roadmap

### Planned Features

**Q1 2024:**
- File download support
- Streaming downloads
- Multipart download resumption

**Q2 2024:**
- Client-side encryption
- Compression support
- Bandwidth throttling

**Q3 2024:**
- SDK for additional languages (Go, Rust)
- Advanced retry strategies
- Connection pooling improvements

### Version Compatibility

| Client Version | MeshCloud API Version | Status |
|----------------|----------------------|--------|
| 0.1.x | 0.1.x | ✅ Current |
| 0.2.x | 0.2.x | 🚧 Planned |

## 🆘 Support

### Getting Help

- **📖 Documentation**: https://docs.meshcloud.io/clients/
- **🐛 Bug Reports**: https://github.com/yourusername/meshcloud/issues
- **💬 Discussions**: https://github.com/yourusername/meshcloud/discussions
- **📧 Security Issues**: security@meshcloud.io

### Community

- **GitHub**: https://github.com/yourusername/meshcloud
- **Discord**: https://discord.gg/meshcloud
- **Twitter**: [@meshcloud](https://twitter.com/meshcloud)

## 📄 License

All client libraries are licensed under the **Apache License 2.0**.

---

<div align="center">
  <h3>🚀 Ready to integrate MeshCloud?</h3>
  <p>Choose your preferred language and get started!</p>

  <a href="python-client/" class="md-button md-button--primary">🐍 Python Client</a>
  <a href="javascript-client/" class="md-button md-button--primary">🌐 JavaScript Client</a>
  <br><br>
  <a href="../api/rest-api/" class="md-button">📖 API Reference</a>
  <a href="../examples/" class="md-button">📝 Examples</a>
</div>