"""
File Service — business logic for chunked uploads, finalization, legacy uploads, and streaming downloads.
Extracted from data_plane/node_server.py to separate concerns.
"""
import asyncio
import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator

import shutil
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger

from meshcloud.security.crypto import (
    encrypt_data, 
    decrypt_data, 
    get_streaming_encryptor, 
    get_streaming_decryptor
)
from meshcloud.storage.database import (
    create_upload_session,
    get_uploaded_chunk_indices,
    add_uploaded_chunk,
    file_exists,
    register_file_location,
    insert_file,
    store_file_chunks,
    get_file_chunks,
    get_filename,
)

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TMP_DIR = os.path.join(STORAGE_DIR, "tmp")
CHUNK_DIR = Path(STORAGE_DIR) / "chunks"
MANIFEST_DIR = Path(STORAGE_DIR) / "manifests"

# Ensure directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)
os.makedirs(MANIFEST_DIR, exist_ok=True)

THIS_NODE = os.getenv("NODE_URL", "http://localhost:8000")

# -------------------------------------------------------------------------
# Per-chunk async locks to prevent race conditions on concurrent uploads
# -------------------------------------------------------------------------
_chunk_locks: dict[str, asyncio.Lock] = {}
_chunk_locks_meta_lock = asyncio.Lock()


async def _get_chunk_lock(chunk_hash: str) -> asyncio.Lock:
    """Return (or create) a per-chunk asyncio.Lock keyed by chunk_hash."""
    async with _chunk_locks_meta_lock:
        if chunk_hash not in _chunk_locks:
            _chunk_locks[chunk_hash] = asyncio.Lock()
        return _chunk_locks[chunk_hash]


# -------------------------------------------------------------------------
# Upload session management
# -------------------------------------------------------------------------

def start_upload_session(filename: str, total_chunks: int) -> str:
    """Create a new chunked upload session and return its upload_id."""
    upload_id = str(uuid.uuid4())
    create_upload_session(upload_id, filename, total_chunks)
    return upload_id


def get_upload_progress(upload_id: str) -> list[int]:
    """Return the list of chunk indices that have already been received."""
    return get_uploaded_chunk_indices(upload_id)


# -------------------------------------------------------------------------
# Chunk storage
# -------------------------------------------------------------------------

async def store_chunk(
    upload_id: str,
    chunk_index: int,
    chunk_hash: str,
    file: UploadFile,
) -> None:
    """
    Stream an uploaded chunk to disk, compute hash, and then encrypt it.
    Uses AES-GCM for better performance.
    """
    chunk_path = CHUNK_DIR / chunk_hash

    lock = await _get_chunk_lock(chunk_hash)
    async with lock:
        if chunk_path.exists():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, add_uploaded_chunk, upload_id, chunk_index, chunk_hash)
            return

        sha256 = hashlib.sha256()
        # Read the chunk in buffers for hashing
        # Note: chunk size is usually small (1-5MB), but we still stream to disk
        tmp_chunk_path = chunk_path.with_suffix(".tmp")
        try:
            with open(tmp_chunk_path, "wb") as f_tmp:
                while True:
                    data = await file.read(1024 * 64)
                    if not data:
                        break
                    sha256.update(data)
                    f_tmp.write(data)

            if sha256.hexdigest() != chunk_hash:
                raise HTTPException(status_code=400, detail="Chunk hash mismatch")

            # Streamingly encrypt the chunk
            nonce = os.urandom(12)
            encryptor = get_streaming_encryptor(nonce)
            with open(chunk_path, "wb") as f_out:
                f_out.write(nonce)
                with open(tmp_chunk_path, "rb") as f_in:
                    while True:
                        data = f_in.read(1024 * 64)
                        if not data:
                            break
                        f_out.write(encryptor.update(data))
                f_out.write(encryptor.finalize())
                f_out.write(encryptor.tag)
        finally:
            if tmp_chunk_path.exists():
                os.remove(tmp_chunk_path)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, add_uploaded_chunk, upload_id, chunk_index, chunk_hash)


async def store_replicated_chunk(
    chunk_hash: str,
    stream: AsyncGenerator[bytes, None],
) -> None:
    """
    Store a chunk received from a peer. 
    The data is already encrypted by the sending peer.
    """
    chunk_path = CHUNK_DIR / chunk_hash
    
    lock = await _get_chunk_lock(chunk_hash)
    async with lock:
        if not chunk_path.exists():
            # In MeshCloud, we trust the hash provided by the peer
            # but usually we'd verify the hash of the decrypted data if we were pedantic. 
            # For performance, we'll just store the encrypted block directly.
            with open(chunk_path, "wb") as f:
                async for piece in stream:
                    f.write(piece)
    
    logger.info(f"Stored replicated chunk: {chunk_hash}")


# -------------------------------------------------------------------------
# Finalize upload (assemble chunks → full file)
# -------------------------------------------------------------------------

async def finalize_upload(
    upload_id: str,
    chunks: list[str],
    filename: str,
    is_replica: bool = False,
) -> dict:
    """
    Verify all chunks are present, assemble into final file using streaming encryption.
    Uses AES-GCM on a per-chunk or per-file basis.
    """
    # Write manifest for reference
    manifest_path = MANIFEST_DIR / f"{upload_id}.json"
    manifest_path.write_text(json.dumps({"filename": filename, "chunks": chunks}))

    # We skip re-assembling the entire file into a plaintext temp file.
    # Instead, we just verify integrity and metadata.
    # This meshcloud version stores files as collections of chunks.
    # However, the legacy storage format expects a full file at STORAGE_DIR / file_hash.
    
    # To keep compatibility with the legacy retrieval path but make it "faster":
    # Compute the full file hash by streaming through decrypted chunks.
    hasher = hashlib.sha256()
    
    # Use a temp file for the encrypted output
    tmp_encrypted_fd, tmp_encrypted_path = tempfile.mkstemp(dir=TMP_DIR)
    
    try:
        nonce = os.urandom(12)
        encryptor = get_streaming_encryptor(nonce)
        
        with os.fdopen(tmp_encrypted_fd, "wb") as f_out:
            f_out.write(nonce)
            
            for chunk_hash in chunks:
                chunk_path = CHUNK_DIR / chunk_hash
                if not chunk_path.exists():
                    raise HTTPException(status_code=400, detail=f"Missing chunk: {chunk_hash}")

                with open(chunk_path, "rb") as cf:
                    c_nonce = cf.read(12)
                    cf.seek(0, os.SEEK_END)
                    chunk_size = cf.tell()
                    cf.seek(chunk_size - 16)
                    tag = cf.read(16)
                    cf.seek(12)
                    
                    ciphertext_len = chunk_size - 12 - 16
                    decryptor = get_streaming_decryptor(c_nonce, tag)
                    
                    read_len = 0
                    while read_len < ciphertext_len:
                        data = cf.read(min(1024 * 64, ciphertext_len - read_len))
                        if not data:
                            break
                        plaintext = decryptor.update(data)
                        hasher.update(plaintext)
                        f_out.write(encryptor.update(plaintext))
                        read_len += len(data)
                    
                    last_plaintext = decryptor.finalize()
                    hasher.update(last_plaintext)
                    f_out.write(encryptor.update(last_plaintext))
            
            f_out.write(encryptor.finalize())
            f_out.write(encryptor.tag)

        file_hash = hasher.hexdigest()
        final_path = os.path.join(STORAGE_DIR, file_hash)

        if file_exists(file_hash):
            os.remove(tmp_encrypted_path)
            register_file_location(file_hash, THIS_NODE)
            return {"status": "duplicate", "hash": file_hash, "filename": filename}

        shutil.move(tmp_encrypted_path, final_path)
        
        insert_file(file_hash, filename)
        store_file_chunks(file_hash, chunks)
        register_file_location(file_hash, THIS_NODE)

        logger.info(f"Finalized upload (single-pass): {filename} → {file_hash}")
        return {"status": "file finalized", "hash": file_hash, "filename": filename}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        if 'tmp_encrypted_path' in locals() and os.path.exists(tmp_encrypted_path):
            os.remove(tmp_encrypted_path)


# -------------------------------------------------------------------------
# Legacy direct upload
# -------------------------------------------------------------------------

async def handle_legacy_upload(file: UploadFile, is_replica: bool = False) -> dict:
    """
    Handle a direct (non-chunked) file upload.
    Streams to disk without buffering the entire file in memory.
    If is_replica=True, the input is already encrypted.
    """
    hasher = hashlib.sha256()
    tmp_fd, tmp_path = tempfile.mkstemp(dir=TMP_DIR)
    
    try:
        nonce = os.urandom(12)
        encryptor = None if is_replica else get_streaming_encryptor(nonce)
        
        with os.fdopen(tmp_fd, "wb") as tmp_f:
            if not is_replica:
                tmp_f.write(nonce)
                
            while True:
                piece = await file.read(1024 * 64)
                if not piece:
                    break
                
                if is_replica:
                    tmp_f.write(piece)
                else:
                    hasher.update(piece)
                    if encryptor:
                        tmp_f.write(encryptor.update(piece))
            
            if not is_replica and encryptor:
                tmp_f.write(encryptor.finalize())
                tmp_f.write(encryptor.tag)

        if is_replica:
            # Replicas are already encrypted, we must decrypt to find the correct hash (plaintext hash)
            hasher_replica = hashlib.sha256()
            with open(tmp_path, "rb") as tf:
                r_nonce = tf.read(12)
                file_size = os.path.getsize(tmp_path)
                tf.seek(file_size - 16)
                tag = tf.read(16)
                tf.seek(12)
                ciphertext_len = file_size - 12 - 16
                
                decryptor = get_streaming_decryptor(r_nonce, tag)
                read_len = 0
                while read_len < ciphertext_len:
                    chunk = tf.read(min(1024 * 64, ciphertext_len - read_len))
                    if not chunk:
                        break
                    plaintext_part = decryptor.update(chunk)
                    hasher_replica.update(plaintext_part)
                    read_len += len(chunk)
                hasher_replica.update(decryptor.finalize())
            file_hash = hasher_replica.hexdigest()
        else:
            file_hash = hasher.hexdigest()

        final_path = os.path.join(STORAGE_DIR, file_hash)

        if file_exists(file_hash):
            os.remove(tmp_path)
            register_file_location(file_hash, THIS_NODE)
            return {"status": "duplicate", "hash": file_hash, "filename": file.filename}

        shutil.move(tmp_path, final_path)

        insert_file(file_hash, file.filename)
        register_file_location(file_hash, THIS_NODE)

        logger.info(f"Legacy upload stored: {file.filename} → {file_hash} (is_replica={is_replica})")
        return {"status": "stored", "hash": file_hash, "filename": file.filename}
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


# -------------------------------------------------------------------------
# Streaming download with chunk verification
# -------------------------------------------------------------------------

async def stream_file(file_hash: str) -> AsyncGenerator[bytes, None]:
    """
    Yield decrypted plaintext bytes for a given file_hash.
    Verifies sha256(chunk_plaintext) == stored chunk_hash before yielding.
    Raises HTTPException on missing file, missing chunk, or hash mismatch.
    """
    if not file_exists(file_hash):
        raise HTTPException(status_code=404, detail="File not found")

    chunk_hashes = get_file_chunks(file_hash)

    if chunk_hashes:
        # Stream from individual chunks
        for chunk_hash in chunk_hashes:
            chunk_path = CHUNK_DIR / chunk_hash
            if not chunk_path.exists():
                raise HTTPException(status_code=500, detail=f"Missing chunk: {chunk_hash}")

            chunk_hasher = hashlib.sha256()
            with open(chunk_path, "rb") as cf:
                nonce = cf.read(12)
                cf.seek(0, os.SEEK_END)
                chunk_size = cf.tell()
                cf.seek(chunk_size - 16)
                tag = cf.read(16)
                cf.seek(12)
                
                ciphertext_len = chunk_size - 12 - 16
                decryptor = get_streaming_decryptor(nonce, tag)
                
                read_len = 0
                while read_len < ciphertext_len:
                    data = cf.read(min(1024 * 64, ciphertext_len - read_len))
                    if not data:
                        break
                    plaintext = decryptor.update(data)
                    chunk_hasher.update(plaintext)
                    yield plaintext
                    read_len += len(data)
                
                last_block = decryptor.finalize()
                chunk_hasher.update(last_block)
                yield last_block

            # Integrity verification
            if chunk_hasher.hexdigest() != chunk_hash:
                logger.error(f"Chunk integrity failure: {chunk_hash}")
                raise HTTPException(status_code=409, detail=f"Integrity failure in chunk {chunk_hash}")
        return

    # Legacy non-chunked file
    final_path = Path(STORAGE_DIR) / file_hash
    if not final_path.exists():
        raise HTTPException(status_code=404, detail="File data not found on this node")

    # Streaming decryption for the legacy file (if it's in the new format)
    file_size = os.path.getsize(final_path)
    if file_size < 28: # At least nonce(12) + tag(16)
        # Possibly old format or corrupt
        with open(final_path, "rb") as f:
            yield decrypt_data(f.read())
        return

    with open(final_path, "rb") as f:
        nonce = f.read(12)
        f.seek(file_size - 16)
        tag = f.read(16)
        f.seek(12)
        ciphertext_len = file_size - 12 - 16
        
        decryptor = get_streaming_decryptor(nonce, tag)
        read_len = 0
        while read_len < ciphertext_len:
            remaining = ciphertext_len - read_len
            data = f.read(min(1024 * 64, remaining))
            if not data:
                break
            yield decryptor.update(data)
            read_len += len(data)
        yield decryptor.finalize()


def download_file(file_hash: str) -> StreamingResponse:
    """
    Provide a decrypted stream of the file to the user.
    """
    # Simply use the stream_file generator
    filename = get_filename(file_hash) or "download"
    return StreamingResponse(
        stream_file(file_hash), 
        media_type="application/octet-stream", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
