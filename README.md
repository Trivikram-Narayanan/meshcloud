# MeshCloud

**Self-hosted distributed file storage for local networks.**  
Upload once — MeshCloud splits your files into encrypted chunks, spreads them across every device in your mesh, and lets any node serve them back. No cloud. No single point of failure. No monthly bill.

```
Device A ──────────────────────── Device B
  │   upload file.mp4               │
  │   → chunks encrypted (AES-GCM)  │
  │   → replicated automatically ──▶│
  │                                  │
  └────── any node serves it ────────┘
```

---

## Features

| | |
|---|---|
| **AES-GCM encryption at rest** | Every chunk is encrypted before touching disk |
| **SHA-256 content addressing** | Files are deduplicated by hash — upload the same file twice, store it once |
| **P2P replication** | Chunks automatically propagate to peer nodes in the background |
| **Gossip protocol (SWIM-like)** | Nodes discover each other, detect failures, and self-heal |
| **Chunked + streaming** | Large files are split into 4 MB chunks; downloads stream with on-the-fly decryption |
| **React dashboard** | Upload files, monitor nodes, and visualise the live network graph |
| **REST API** | Full HTTP API with JWT auth — integrate with any pipeline |
| **Python & JS clients** | SDK libraries for automation and browser use |
| **Docker / Kubernetes ready** | One-command compose, Helm chart included |

---

## Quick Start

### One command (Docker)

```bash
git clone https://github.com/Trivikram-Narayanan/meshcloud.git
cd meshcloud
docker-compose up
```

Open **http://localhost:8000** — register an account, start uploading.

### Local Python

**Prerequisites:** Python 3.11+, Node.js 18+

```bash
git clone https://github.com/Trivikram-Narayanan/meshcloud.git
cd meshcloud
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY and STORAGE_ENCRYPTION_KEY (see below)
npm --prefix frontend install && npm --prefix frontend run build
uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**, register an account, and you're in.

---

## Connecting Multiple Devices

This is the whole point of MeshCloud. Here's how to get two or more devices talking.

### Same LAN — automatic discovery

Nodes on the same Wi-Fi or subnet auto-discover each other via UDP broadcast on port `9999`. Just start MeshCloud on each device with the correct `NODE_URL` — no extra configuration needed.

**Device A** (e.g. `192.168.1.10`):
```bash
NODE_URL=http://192.168.1.10:8000 \
  uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000
```

**Device B** (e.g. `192.168.1.20`):
```bash
NODE_URL=http://192.168.1.20:8000 \
  uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000
```

Within ~5 seconds both nodes appear in each other's **Nodes** page.

### Different networks / VPN — manual bootstrap

**Option 1 — seed file** (best for permanent setups):

On Device B, create `config/peers.json` before starting:
```json
{"peers": ["http://192.168.1.10:8000"]}
```

**Option 2 — gossip API** (add peer to a running node):
```bash
curl -X POST http://device-b:8000/gossip \
  -H "Content-Type: application/json" \
  -d '{
    "peers": ["http://device-a:8000"],
    "sender": "http://device-b:8000",
    "type": "join"
  }'
```

**Option 3 — dashboard UI**:  
Open **Settings → Connect Peer**, paste the other node's URL, click **Add Peer**.

### How peer discovery works under the hood

```
Node starts
  ├─ reads config/peers.json  (seed list)
  ├─ broadcasts UDP on LAN every 5s  (auto-discovery)
  └─ gossip loop every 2s:
       ├─ pings random subset of known peers
       ├─ exchanges peer lists (so A learns about C through B)
       ├─ scores each peer (0–100) based on responsiveness
       └─ removes peers with score → 0 (dead node detection)

File uploaded on any node
  └─ replication worker propagates chunks to all healthy peers
     └─ any node can serve any file
```

### Local 3-node mesh (for testing)

```bash
bash start_mesh.sh
# Starts nodes on ports 8000, 8001, 8002 with auto-peering
```

---

## Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Generate strong keys (run twice — one for JWT, one for encryption):
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Required | Description | Default |
|---|---|---|---|
| `JWT_SECRET_KEY` | **Yes** | Secret for signing JWT tokens | _(app refuses auth)_ |
| `STORAGE_ENCRYPTION_KEY` | **Yes** | AES-GCM key for chunk encryption | _(insecure fallback)_ |
| `MESH_NODE_TOKEN` | **Yes** | Shared secret for inter-node API calls | _(none)_ |
| `NODE_URL` | **Yes** | Public URL of this node | `http://localhost:8000` |
| `NODE_NAME` | No | Human-readable name | `meshcloud-node` |
| `ADMIN_PASSWORD` | No | Initial admin password | _(none)_ |
| `DATABASE_URL` | No | SQLAlchemy connection string | `sqlite:///db/meshcloud.db` |
| `STORAGE_DIR` | No | Directory for encrypted chunks | `storage` |
| `MAX_FILE_SIZE` | No | Max upload size (bytes) | `104857600` (100 MB) |
| `PORT` | No | HTTP listen port | `8000` |
| `DISCOVERY_PORT` | No | UDP broadcast port | `9999` |
| `PEERS_FILE` | No | Seed peers JSON file | `config/peers.json` |
| `LOG_LEVEL` | No | Logging verbosity | `INFO` |

---

## Project Structure

```
meshcloud/
├── meshcloud/              # Python backend (FastAPI)
│   ├── main.py             # App entry point, WebSocket manager
│   ├── control_plane/      # Auth, metadata, network graph routes
│   ├── data_plane/         # Upload / download routes
│   ├── services/           # file_service, user_service
│   ├── storage/            # DB models, chunker, Merkle tree
│   ├── security/           # AES-GCM, JWT, auth dependencies
│   └── networking/         # Gossip protocol, UDP discovery, replication
├── frontend/               # React 19 SPA
│   └── src/
│       ├── pages/          # Dashboard, Files, Nodes, Network, Settings, Login
│       ├── components/     # Sidebar, NetworkGraph, ThroughputChart
│       ├── hooks/          # useFiles, useNodes, useNetwork
│       ├── services/       # api.js (Axios + JWT interceptors)
│       └── state/          # Zustand store
├── clients/
│   ├── python/             # Async Python SDK (meshcloud-client)
│   └── javascript/         # Browser/Node.js UMD client
├── k8s/                    # Kubernetes manifests
├── helm/                   # Helm chart
├── docker/                 # nginx, Prometheus, Grafana config
├── tests/                  # pytest test suite
├── docker-compose.yml      # Full stack incl. Postgres, Redis, Prometheus, Grafana
└── setup.sh                # One-command local install script
```

---

## Dashboard Pages

| Page | What you get |
|---|---|
| **Dashboard** | Live stat cards (files, nodes, CPU, memory), throughput chart, real-time event log |
| **Files** | Upload (drag & drop), search, download, SHA-256 hash copy, replication status bars |
| **Nodes** | This node with CPU/memory gauges; all peers with health scores |
| **Network** | Live Cytoscape mesh topology graph |
| **Settings** | Node URL, add peer, quick-start guide |

---

## API Reference

All endpoints require `Authorization: Bearer <token>` except `/health`, `/download/{hash}`, and `/gossip`.

### Auth
| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/register` | `{username, password}` | Register |
| `POST` | `/token` | `username=&password=` (form) | Get JWT |
| `GET` | `/users/me` | — | Current user |

### Files
| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Direct upload (`multipart/form-data`) |
| `POST` | `/start_upload` | Begin chunked session — returns `upload_id` |
| `POST` | `/upload_chunk` | Upload one chunk (`upload_id`, `chunk_index`, `chunk_hash`, `file`) |
| `GET` | `/upload_status/{id}` | List received chunk indices |
| `POST` | `/finalize_upload` | Assemble chunks: `{upload_id, chunks: ["hash1","hash2",...], filename}` |
| `GET` | `/download/{hash}` | Stream-download a file |

### Status & Network
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/status` | CPU, memory, peer count, uptime |
| `GET` | `/api/files` | List all stored files |
| `GET` | `/api/network/graph` | Cytoscape topology |
| `GET` | `/api/network/replication_map` | Replication status per file |
| `GET` | `/has_file/{hash}` | Boolean — does this node hold the file? |
| `GET` | `/file_locations/{hash}` | Which node URLs hold this file |
| `POST` | `/gossip` | Peer gossip handshake |
| `WS` | `/ws` | Real-time events (node_joined, chunk_uploaded, sync, …) |

---

## Python Client

```bash
pip install meshcloud-client
```

```python
import asyncio
from meshcloud_client import MeshCloudClient

async def main():
    async with MeshCloudClient("http://192.168.1.10:8000", token="your-jwt") as mc:
        result = await mc.upload_file("video.mp4")
        print("Stored:", result["hash"])

        data = await mc.download_file(result["hash"])
        open("video_copy.mp4", "wb").write(data)

asyncio.run(main())
```

## JavaScript Client

```html
<script src="clients/javascript/meshcloud-client.umd.js"></script>
<script>
  const mc = new MeshCloudClient({ baseUrl: "http://localhost:8000", token: jwt });
  const { hash } = await mc.uploadFile(input.files[0]);
  const blob = await mc.downloadFile(hash);
</script>
```

---

## Docker Compose (full stack)

```yaml
# docker-compose.yml includes:
# - MeshCloud node
# - PostgreSQL 15
# - Redis 7
# - Prometheus
# - Grafana (http://localhost:3000, admin/admin)
# - Nginx reverse proxy
```

```bash
docker-compose up -d
```

---

## Kubernetes / Helm

```bash
# Raw manifests
kubectl apply -f k8s/

# Helm
helm install meshcloud ./helm/ \
  --set env.NODE_URL=https://meshcloud.yourcluster.com \
  --set env.JWT_SECRET_KEY=<secret> \
  --set env.STORAGE_ENCRYPTION_KEY=<secret>
```

---

## Monitoring

```bash
docker-compose up -d
# Grafana:    http://localhost:3000  (admin / admin)
# Prometheus: http://localhost:9090
```

Prometheus scrapes `/metrics` on each node. Pre-built Grafana dashboards in `docker/grafana/`.

---

## Development

```bash
# Backend (hot reload)
pip install -r requirements-dev.txt
uvicorn meshcloud.main:app --reload

# Frontend (dev server, proxies /api to :8000)
cd frontend && npm install && npm start

# Run tests
pytest tests/ -v

# Lint + format
ruff check . && black . && isort .
```

Pre-commit hooks (ruff, black, isort, mypy):
```bash
pip install pre-commit && pre-commit install
```

---

## Contributing

Contributions are welcome — please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repo
2. `git checkout -b feat/my-feature`
3. Make your changes, add tests
4. Open a pull request

---

## Security

Found a vulnerability? Read [SECURITY.md](SECURITY.md) and report it privately.  
Do **not** open a public GitHub issue for security bugs.

