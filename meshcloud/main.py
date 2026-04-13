import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from meshcloud.control_plane.api_server import router as control_router
from meshcloud.control_plane.middleware import (
    RequestLoggingMiddleware,
    SecurityMiddleware,
    create_rate_limit_exceeded_handler,
)
from meshcloud.data_plane.node_server import router as data_router
from meshcloud.networking.discovery import (
    discovery_broadcast,
    discovery_listener,
    dns_discovery_worker,
    seed_peers_from_config,
)
from meshcloud.networking.gossip import GossipProtocol
from meshcloud.networking.replication import peer_health_worker, retry_sync_worker
from meshcloud.storage.database import NODE_ID, get_all_peers, init_db

# Ensure dirs
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
os.makedirs(os.path.join(STORAGE_DIR, "tmp"), exist_ok=True)
(Path(STORAGE_DIR) / "chunks").mkdir(parents=True, exist_ok=True)
(Path(STORAGE_DIR) / "manifests").mkdir(parents=True, exist_ok=True)

THIS_NODE = os.getenv("NODE_URL", "http://localhost:8000")
gossip_protocol = GossipProtocol(THIS_NODE, NODE_ID)
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_peers_from_config()

    threading.Thread(target=retry_sync_worker, daemon=True).start()
    threading.Thread(target=peer_health_worker, daemon=True).start()
    threading.Thread(target=discovery_broadcast, daemon=True).start()
    threading.Thread(target=discovery_listener, daemon=True).start()
    threading.Thread(target=dns_discovery_worker, daemon=True).start()

    gossip_protocol.start()
    yield


app = FastAPI(title="MeshCloud", version="0.2.0", lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestLoggingMiddleware, logger=logger)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, create_rate_limit_exceeded_handler())

from typing import List

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Mount Subsystems
app.include_router(control_router)
app.include_router(data_router)


@app.post("/gossip")
def handle_gossip(payload: dict = Body(...)):
    """Endpoint to receive gossip messages from peers."""
    return gossip_protocol.process_incoming_gossip(payload)


@app.get("/api/status")
@limiter.limit("100/minute")
def node_status(request: Request):
    """Moved from / to /api/status so / can serve the SPA."""
    peers = get_all_peers()

    # Get system metrics
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    return {
        "node": "MeshCloud",
        "status": "running",
        "peers": len(peers),
        "node_url": os.getenv("NODE_URL", "http://localhost:8000"),
        "node_id": NODE_ID,
        "metrics": {
            "cpu_usage": cpu_usage,
            "memory_usage": memory.percent,
            "memory_used_mb": round(memory.used / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "uptime": round(time.time() - START_TIME, 2),
        },
    }


# Mount Dashboard SPA (Catch-All)
from fastapi.responses import FileResponse

root_dir = os.path.dirname(os.path.dirname(__file__))
# Try multiple possible static paths, prioritizing test/dev locations
possible_static_dirs = [
    os.path.join(root_dir, "app/static"),
    os.path.join(root_dir, "frontend/build"),
    os.path.join(root_dir, "meshcloud/control_plane/static"),
]

static_path = None
for s_path in possible_static_dirs:
    # Check if directory exists AND has index.html
    if os.path.exists(s_path) and os.path.isfile(os.path.join(s_path, "index.html")):
        static_path = s_path
        break

if static_path is not None:
    # Mount static assets
    if os.path.exists(os.path.join(static_path, "static")):
        app.mount(
            "/static",
            StaticFiles(directory=os.path.join(static_path, "static")),
            name="static",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    @limiter.limit("100/minute")
    async def serve_frontend(request: Request, full_path: str):
        # Fast fail for API paths
        if full_path.startswith("api/"):
            # We let existing API routes handle /api/
            pass

        # Serve exact file if it exists (e.g., manifest.json, favicon.ico)
        assert static_path is not None
        file_path = os.path.join(static_path, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for SPA routing
        index_path = os.path.join(static_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not built"}
