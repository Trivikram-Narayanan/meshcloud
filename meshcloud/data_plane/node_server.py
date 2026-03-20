"""
Data Plane — Thin API router for file storage operations.
All business logic is delegated to meshcloud.services.file_service.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, Body, BackgroundTasks, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from meshcloud.services import file_service
from meshcloud.networking.replication import propagate_to_peers

router = APIRouter()

THIS_NODE = os.getenv("NODE_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Chunked Upload Flow
# ---------------------------------------------------------------------------

class StartUploadRequest(BaseModel):
    filename: str
    total_chunks: int


@router.post("/start_upload")
def start_upload(req: StartUploadRequest):
    """Begin a new chunked upload session."""
    upload_id = file_service.start_upload_session(req.filename, req.total_chunks)
    return {"upload_id": upload_id}


@router.get("/upload_status/{upload_id}")
def upload_status(upload_id: str):
    """Return list of chunk indices already received for this session."""
    uploaded = file_service.get_upload_progress(upload_id)
    return {"uploaded_chunks": uploaded}


@router.post("/upload_chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk_hash: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Receive and store a single chunk of a chunked upload.
    Streams to disk — no full-chunk memory buffering.
    Uses per-chunk async locks to prevent race conditions.
    """
    await file_service.store_chunk(upload_id, chunk_index, chunk_hash, file)
    return {"status": "chunk stored"}


@router.post("/replicate_chunk")
async def replicate_chunk(request: Request, chunk_hash: str):
    """Receive a chunk sent during peer-to-peer replication."""
    await file_service.store_replicated_chunk(chunk_hash, request.stream())
    return {"stored": chunk_hash}


@router.post("/finalize_upload")
async def finalize_upload(
    background_tasks: BackgroundTasks,
    upload_id: str = Body(...),
    chunks: list = Body(...),
    filename: str = Body(...),
    is_replica: bool = Body(False),
):
    """Assemble all chunks into the final encrypted file."""
    result = await file_service.finalize_upload(upload_id, chunks, filename, is_replica)

    if not is_replica and result["status"] != "duplicate":
        file_hash = result["hash"]
        final_path = os.path.join(os.getenv("STORAGE_DIR", "storage"), file_hash)
        background_tasks.add_task(propagate_to_peers, final_path, filename, file_hash)

    return result


# ---------------------------------------------------------------------------
# Legacy Direct Upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_mesh_node: Optional[str] = Header(None, alias="X-MeshCloud-Node"),
    x_mesh_node_id: Optional[str] = Header(None, alias="X-MeshCloud-Node-ID"),
):
    """Legacy endpoint for direct (non-chunked) file uploads."""
    try:
        print(f"DEBUG: node_server.upload started for {file.filename} (from {x_mesh_node_id or 'client'})")
        result = await file_service.handle_legacy_upload(file, is_replica=bool(x_mesh_node or x_mesh_node_id))
        print(f"DEBUG: handle_legacy_upload returned {result.get('status')}")

        if not (x_mesh_node or x_mesh_node_id) and result["status"] != "duplicate":
            file_hash = result["hash"]
            final_path = os.path.join(os.getenv("STORAGE_DIR", "storage"), file_hash)
            print(f"DEBUG: Adding background task for {file_hash}")
            background_tasks.add_task(propagate_to_peers, final_path, file.filename, file_hash)

        return result
    except Exception as e:
        import traceback
        print(f"DEBUG: node_server.upload FAILED: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Download (new — with chunk verification)
# ---------------------------------------------------------------------------

@router.get("/download/{file_hash}")
async def download(file_hash: str):
    """
    Stream a file back to the client.
    Each chunk is decrypted and its sha256 is verified before being yielded.
    Returns 409 Conflict if any chunk fails integrity verification.
    """
    from meshcloud.storage.database import get_filename
    filename = get_filename(file_hash) or file_hash

    return StreamingResponse(
        file_service.stream_file(file_hash),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Gossip Protocol Endpoint
# ---------------------------------------------------------------------------

@router.post("/gossip")
async def receive_gossip(request: Request):
    """
    Receive an incoming gossip heartbeat from a peer node.
    Delegates processing to the module-level GossipProtocol instance in main.py.
    Returns an ACK with our known-peers list so the gossip graph can converge.
    """
    from meshcloud.main import gossip_protocol
    payload = await request.json()
    if gossip_protocol is not None:
        return gossip_protocol.process_incoming_gossip(payload)
    # Startup race: gossip not yet initialised, send a minimal ack
    return {"status": "ack", "known_peers": []}