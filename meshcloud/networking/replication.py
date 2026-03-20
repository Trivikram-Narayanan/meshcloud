import os
import time
import uuid
import random
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

from meshcloud.storage.database import (
    get_file_chunks, is_peer_online, add_sync_task, get_all_peers,
    get_pending_sync_tasks, get_filename, update_sync_job_status,
    increment_sync_retry, update_peer_status, get_all_files, get_file_locations,
    register_file_location, NODE_ID
)


NODE_TOKEN = os.getenv("NODE_TOKEN", "meshcloud_secret_token")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
CHUNK_DIR = Path(STORAGE_DIR) / "chunks"
REPLICATION_FACTOR = int(os.getenv("REPLICATION_FACTOR", "3"))
THIS_NODE = os.getenv("NODE_URL", "http://localhost:8000")
THIS_NODE_ID = NODE_ID

sync_executor = ThreadPoolExecutor(max_workers=3)


# -------------------------------------------------------------------------
# Replication status & monitoring
# -------------------------------------------------------------------------

def get_replication_status(file_hash: str) -> dict:
    """
    Return the replication health for a single file.
    Compares the number of known holder nodes against REPLICATION_FACTOR.
    """
    nodes = get_file_locations(file_hash)
    current = len(nodes)
    return {
        "file_hash": file_hash,
        "filename": get_filename(file_hash),
        "target": REPLICATION_FACTOR,
        "current": current,
        "nodes": nodes,
        "under_replicated": current < REPLICATION_FACTOR,
    }


def replication_monitor_worker():
    """
    Background worker: every 60 seconds scan all files for
    under-replication and trigger propagation for any that need more copies.
    """
    while True:
        try:
            files = get_all_files(limit=1000)
            under = [f for f in files if len(get_file_locations(f.hash)) < REPLICATION_FACTOR]
            if under:
                logger.warning(
                    f"🔴 Under-replicated files detected: {len(under)} / {len(files)}"
                )
            for f in under:
                file_path = Path(STORAGE_DIR) / f.hash
                logger.info(f"  ↳ Re-triggering replication for {f.hash}")
                propagate_to_peers(str(file_path), f.original_filename, f.hash)
        except Exception as e:
            logger.error(f"Replication monitor error: {e}")
        time.sleep(10) # Faster monitor for tests/dev

def sync_with_peer(peer, file_path, filename, file_hash):
    headers = {
        "X-MeshCloud-Token": NODE_TOKEN,
        "X-MeshCloud-Node": THIS_NODE,
        "X-MeshCloud-Node-ID": THIS_NODE_ID
    }

    # Check existence
    try:
        check = requests.get(f"{peer}/has_file/{file_hash}", headers=headers, timeout=5, verify=VERIFY_SSL)
        if check.status_code == 200 and check.json().get("exists"):
            logger.info(f"{peer} already has file {file_hash}")
            return
    except requests.RequestException:
        return

    chunks = get_file_chunks(file_hash)

    if chunks:
        logger.info(f"Replicating {file_hash} to {peer} (Chunked)")

        def replicate_single_chunk(chunk_hash):
            chunk_path = CHUNK_DIR / chunk_hash
            if not chunk_path.exists():
                raise Exception(f"Chunk {chunk_hash} missing locally.")
            
            with open(chunk_path, "rb") as cf:
                requests.post(
                    f"{peer}/replicate_chunk",
                    params={"chunk_hash": chunk_hash},
                    data=cf,
                    headers={
                        "Content-Type": "application/octet-stream",
                        **headers
                    },
                    timeout=30,
                    verify=VERIFY_SSL,
                ).raise_for_status()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(replicate_single_chunk, chunk) for chunk in chunks]
            for future in futures:
                future.result()

        dummy_upload_id = f"repl_{uuid.uuid4()}"
        requests.post(
            f"{peer}/finalize_upload",
            json={
                "upload_id": dummy_upload_id, 
                "chunks": chunks, 
                "filename": filename,
                "is_replica": True
            },
            headers=headers,
            verify=VERIFY_SSL,
        ).raise_for_status()
        
        # Immediate local registration
        register_file_location(file_hash, peer)
        logger.info(f"Successfully replicated {file_hash} to {peer}")
    else:
        # Fallback: file was stored via legacy /upload (no chunk records).
        # Stream the raw file directly to the peer's /upload endpoint.
        file_p = Path(file_path)
        if not file_p.exists():
            logger.warning(f"No chunks and no local file for {file_hash}, cannot replicate")
            return
        logger.info(f"Replicating {file_hash} to {peer} (legacy file-level copy)")
        with open(file_p, "rb") as fh:
            requests.post(
                f"{peer}/upload",
                files={"file": (filename or file_hash, fh, "application/octet-stream")},
                headers={
                    "X-MeshCloud-Token": NODE_TOKEN,
                    "X-MeshCloud-Node": THIS_NODE,
                    "X-MeshCloud-Node-ID": THIS_NODE_ID
                },
                timeout=60,
                verify=VERIFY_SSL,
            ).raise_for_status()
            
            # Local registration
            register_file_location(file_hash, peer)
            logger.info(f"Successfully replicated {file_hash} to {peer} (legacy)")

def propagate_to_peer(peer, file_path, filename, file_hash):
    if not is_peer_online(peer):
        add_sync_task(file_hash, peer)
        return

    try:
        sync_with_peer(peer, file_path, filename, file_hash)
    except Exception as e:
        logger.error(f"Failed syncing with {peer}: {e}")
        add_sync_task(file_hash, peer)

def propagate_to_peers(file_path, filename, file_hash):
    """
    Ensure the file is replicated to enough nodes to satisfy REPLICATION_FACTOR.
    """
    current_locations = get_file_locations(file_hash)
    # Filter out this node to count remote copies correctly
    remote_locations = [loc for loc in current_locations if loc != THIS_NODE]
    
    needed = REPLICATION_FACTOR - len(current_locations)
    if needed <= 0:
        logger.debug(f"Replication target met for {file_hash} ({len(current_locations)} copies)")
        return

    peers = get_all_peers()
    # Filter out peers that already have it (from our current knowledge)
    potential_peers = [p for p in peers if p not in remote_locations and p != THIS_NODE]
    
    if not potential_peers:
        logger.warning(f"No potential peers found to replicate {file_hash}. Needed: {needed}")
        return

    # Randomize to avoid hot nodes
    random.shuffle(potential_peers)
    
    # Try more peers than strictly needed to account for intermittent failures
    # or discovery delays, but limit to a reasonable number.
    to_attempt = potential_peers[:needed]
    
    logger.info(f"Replicating {file_hash} to {len(to_attempt)} new peers. Current copies: {len(current_locations)}, Target: {REPLICATION_FACTOR}")
    
    for peer in to_attempt:
        sync_executor.submit(propagate_to_peer, peer, file_path, filename, file_hash)

def retry_sync_worker():
    while True:
        tasks = get_pending_sync_tasks(limit=10)
        for task in tasks:
            task_id, file_hash, peer, retry_count = task
            try:
                file_path = Path(STORAGE_DIR) / file_hash
                filename = get_filename(file_hash)
                # Sync even if filename is missing (using hash as fallback)
                sync_with_peer(peer, file_path, filename, file_hash)
                update_sync_job_status(task_id, 'done')
            except Exception:
                increment_sync_retry(task_id)
        time.sleep(5)  # Faster retry for tests/dev

def peer_health_worker():
    while True:
        peers = get_all_peers()
        for peer in peers:
            try:
                r = requests.get(peer + "/health", timeout=3, verify=VERIFY_SSL)
                if r.status_code == 200:
                    data = r.json()
                    peer_node_id = data.get("node_id")
                    update_peer_status(peer, True, node_id=peer_node_id)
                else:
                    update_peer_status(peer, False)
            except Exception:
                update_peer_status(peer, False)
        time.sleep(5)  # Faster health check for tests/dev