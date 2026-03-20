"""
Control Plane — Thin API router for management, auth, and monitoring endpoints.
Business logic is delegated to meshcloud.services and meshcloud.storage.database.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from meshcloud.security.auth import Token, User as UserSchema
from meshcloud.security.dependencies import get_current_user_db
from meshcloud.services import user_service
from meshcloud.storage.database import (
    get_all_files,
    get_all_peers,
    get_file_locations,
    file_exists,
    get_user_by_username,
)
from meshcloud.control_plane.metrics import router as metrics_router

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None


@router.post("/register", response_model=UserSchema)
def register_user(user: UserCreate):
    """Register a new user account."""
    db_user = user_service.register(
        username=user.username,
        password=user.password,
        full_name=user.full_name,
        email=user.email,
    )
    return UserSchema(
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        disabled=bool(db_user.disabled),
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate with username/password and receive a JWT bearer token."""
    return user_service.login(form_data.username, form_data.password)


@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user=Depends(get_current_user_db)):
    """Return the currently authenticated user's profile."""
    return UserSchema(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        disabled=bool(current_user.disabled),
    )


# ---------------------------------------------------------------------------
# File & Network Info
# ---------------------------------------------------------------------------

@router.get("/api/files", response_model=list[dict])
def list_files(limit: int = 50, current_user=Depends(get_current_user_db)):
    """List files stored on this node."""
    files = get_all_files(limit)
    return [
        {
            "hash": f.hash,
            "filename": f.original_filename,
            "created_at": f.created_at,
        }
        for f in files
    ]


@router.get("/health")
def health():
    """Basic liveness probe."""
    from meshcloud.storage.database import NODE_ID
    return {
        "status": "ok",
        "node_id": NODE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/has_file/{file_hash}")
def has_file(file_hash: str):
    """Used by peer nodes to check before sending replication data."""
    return {"exists": file_exists(file_hash)}


@router.get("/file_locations/{file_hash}")
def file_locations(file_hash: str):
    """Return the list of node URLs known to hold a given file."""
    nodes = get_file_locations(file_hash)
    return {"nodes": nodes}


@router.get("/replication_status/{file_hash}")
def replication_status_endpoint(file_hash: str, current_user=Depends(get_current_user_db)):
    """Return the replication health for a specific file."""
    from meshcloud.networking.replication import get_replication_status
    return get_replication_status(file_hash)


@router.get("/api/network/replication_map")
def replication_map(current_user=Depends(get_current_user_db)):
    """Return replication status for all files — used by the dashboard."""
    from meshcloud.networking.replication import get_replication_status
    files = get_all_files(limit=500)
    return [get_replication_status(f.hash) for f in files]


@router.get("/api/network/graph")
def network_graph():
    """
    Return the network topology as a graph for cytoscape.js visualization.
    Includes nodes with metadata and peer edges with gossip scores.
    """
    from meshcloud.main import gossip_protocol
    import os

    peers_state = gossip_protocol.get_graph_state() if gossip_protocol else {}
    this_node_url = os.getenv("NODE_URL", "http://localhost:8000")

    # Build cytoscape-compatible elements
    elements = []

    # This node
    files = get_all_files(limit=500)
    elements.append({
        "data": {
            "id": this_node_url,
            "label": this_node_url.replace("http://", ""),
            "file_count": len(files),
            "status": "alive",
            "type": "self",
        }
    })

    # Peer nodes + edges
    for peer_url, peer_info in peers_state.items():
        elements.append({
            "data": {
                "id": peer_url,
                "label": peer_url.replace("http://", ""),
                "file_count": 0,
                "status": peer_info.get("status", "unknown"),
                "score": peer_info.get("score", 0),
                "type": "peer",
            }
        })
        elements.append({
            "data": {
                "id": f"{this_node_url}->{peer_url}",
                "source": this_node_url,
                "target": peer_url,
                "weight": peer_info.get("score", 0),
            }
        })

    return {"elements": elements}


@router.get("/status")
def node_status():
    """
    Full node status: version, peer count, file count, disk info.
    Used by gossip protocol and dashboard.
    """
    import psutil, os
    from meshcloud.storage.database import NODE_ID
    peers = get_all_peers()
    files = get_all_files(limit=500)
    disk = psutil.disk_usage("/")
    return {
        "node_url": os.getenv("NODE_URL", "http://localhost:8000"),
        "node_id": NODE_ID,
        "version": "1.0.0",
        "peers": len(peers),
        "peer_urls": peers,
        "file_count": len(files),
        "disk_total_gb": round(disk.total / 1e9, 2),
        "disk_used_gb": round(disk.used / 1e9, 2),
        "disk_free_gb": round(disk.free / 1e9, 2),
        "disk_usage_percent": disk.percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include metrics sub-router
router.include_router(metrics_router)