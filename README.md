# MeshCloud

A self-hosted, distributed file storage system for local networks and NAS devices.

Upload files once — MeshCloud splits them into encrypted chunks, spreads them across every node in your mesh, and lets any node serve them back. No cloud required, no single point of failure.

---

## What it does

- **Chunked uploads** — files are split into pieces, each hashed and verified
- **AES-GCM encryption at rest** — every chunk is encrypted before touching disk
- **P2P replication** — chunks automatically propagate to peer nodes
- **Gossip protocol (SWIM-like)** — nodes discover each other, detect failures, and self-heal
- **Content-addressable storage** — files are deduplicated by SHA-256 hash
- **Streaming downloads** — chunks are decrypted and integrity-verified on the fly
- **React dashboard** — upload files, browse the file list, and visualise the network graph
- **REST API + Python & JS clients** — integrate with any pipeline

---

## Architecture

```
┌──────────────────────────────────────────┐
│              React Dashboard             │
└───────────────────┬──────────────────────┘
                    │ HTTP / WebSocket
┌───────────────────▼──────────────────────┐
│              FastAPI Node                │
│  ┌─────────────┐  ┌────────────────────┐ │
│  │ Control     │  │ Data Plane         │ │
│  │ Plane       │  │ (upload/download)  │ │
│  │ (auth/meta) │  │                    │ │
│  └─────────────┘  └────────────────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │ Networking: Gossip · Replication     │ │
│  │ Discovery (UDP broadcast / DNS)      │ │
│  └──────────────────────────────────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │ Storage: AES-GCM · SQLite/Postgres   │ │
│  └──────────────────────────────────────┘ │
└───────────────┬──────────────────────────┘
                │ HTTP gossip + replication
        ┌───────┴────────┐
        │  Peer Node(s)  │
        └────────────────┘
```

---

## Quick start

### Docker Compose (recommended)

```bash
git clone https://github.com/Trivikram-Narayanan/meshcloud.git
cd meshcloud
cp .env.example .env          # edit the values
docker-compose up
```

Open [http://localhost:8000](http://localhost:8000) to access the dashboard.

### Local (Python)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Minimum required env vars
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export STORAGE_ENCRYPTION_KEY=$(openssl rand -hex 32)
export ADMIN_PASSWORD=changeme

uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000
```

### Multi-node mesh

Run one node per port, each pointing at its neighbours via `config/peers_<port>.json`:

```bash
./start_mesh.sh       # starts nodes on ports 8000–8002 by default
```

Or use the Kubernetes manifests in [k8s/](k8s/) / Helm chart in [helm/](helm/).

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` to get started.

| Variable | Required | Description |
|---|---|---|
| `STORAGE_ENCRYPTION_KEY` | **Yes** | Key used to derive the AES-GCM encryption key |
| `JWT_SECRET_KEY` | **Yes** | Secret for signing JWT tokens |
| `ADMIN_PASSWORD` | **Yes** | Password for the built-in admin account |
| `MESH_NODE_TOKEN` | Yes (multi-node) | Shared secret for node-to-node auth |
| `NODE_URL` | Yes (multi-node) | Public URL of this node, e.g. `http://192.168.1.10:8000` |
| `DATABASE_URL` | No | SQLAlchemy URL — defaults to per-node SQLite |
| `STORAGE_DIR` | No | Directory to store chunks (default: `storage`) |
| `NODE_ID` | No | Fixed node identity — auto-generated if unset |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Create a new user account |
| `POST` | `/token` | Get a JWT bearer token |
| `POST` | `/start_upload` | Begin a chunked upload session |
| `POST` | `/upload_chunk` | Upload a single chunk |
| `POST` | `/finalize_upload` | Assemble chunks into the final file |
| `GET` | `/download/{hash}` | Stream a file (decrypted) |
| `GET` | `/api/files` | List files on this node |
| `GET` | `/api/network/graph` | Network topology for dashboard |
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/status` | Node metrics (CPU, memory, uptime) |

Full reference: [docs/api/rest-api.md](docs/api/rest-api.md)

---

## Clients

**Python** (async):

```python
from meshcloud_client import MeshCloudClient
import asyncio

async def main():
    async with MeshCloudClient("http://localhost:8000") as c:
        await c.authenticate("admin", "changeme")
        result = await c.upload_file("photo.jpg")
        print(result["hash"])

asyncio.run(main())
```

**JavaScript** (browser / Node.js):

```javascript
const client = new MeshCloudClient('http://localhost:8000');
await client.authenticate('admin', 'changeme');
const result = await client.uploadFile(file);
console.log(result.hash);
```

---

## Development

```bash
# Install dev deps
pip install -r requirements-dev.txt

# Run tests
pytest

# Run a single node with hot-reload
uvicorn meshcloud.main:app --reload

# Build the React dashboard
cd frontend && npm install && npm run build
```

Pre-commit hooks are configured in [.pre-commit-config.yaml](.pre-commit-config.yaml).

---

## Project structure

```
meshcloud/
├── control_plane/   API routes for auth, metadata, metrics
├── data_plane/      Upload / download API routes
├── services/        Business logic (file_service, user_service)
├── storage/         Database models, chunker, hasher, Merkle tree
├── security/        AES-GCM crypto, JWT auth
└── networking/      Gossip protocol, peer replication, UDP discovery

frontend/            React + Tailwind dashboard (source)
clients/             Python and JavaScript client libraries
docs/                MkDocs documentation source
k8s/                 Kubernetes manifests
helm/                Helm chart
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repo and create a feature branch
2. Make your changes with tests
3. Open a pull request

See [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
