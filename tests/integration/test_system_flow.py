import hashlib
import io
import os
import pytest

from meshcloud.security.crypto import decrypt_data
from meshcloud.main import STORAGE_DIR
from pathlib import Path

CHUNK_DIR = Path(STORAGE_DIR) / "chunks"

def test_health_check(client):
    """Verify the node is running and healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

def test_dashboard_access(client):
    """Verify the web dashboard is mounted and accessible."""
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert "MeshCloud | Decentralized Storage" in response.text

def test_full_upload_workflow(client):
    """
    Test the complete flow:
    1. Register User
    2. Login
    3. Start Upload
    4. Upload Chunks
    5. Finalize
    6. Verify File Listing
    """
    
    # --- 1. Register ---
    user_data = {
        "username": "flow_user",
        "password": "secure_password",
        "full_name": "Flow Tester"
    }
    reg_response = client.post("/register", json=user_data)
    assert reg_response.status_code == 200
    
    # --- 2. Login ---
    login_data = {
        "username": "flow_user",
        "password": "secure_password"
    }
    # FastAPI OAuth2PasswordRequestForm expects form data, not JSON
    login_response = client.post("/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- 3. Prepare Dummy File ---
    filename = "integration_test.txt"
    content = b"This is a test file for the full integration flow." * 100
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Simulate chunking (just 1 chunk for this small file)
    chunk_hash = hashlib.sha256(content).hexdigest()
    
    # --- 4. Start Upload Session ---
    start_payload = {
        "filename": filename,
        "total_chunks": 1
    }
    # Note: start_upload endpoint is currently public in app/main.py, but listing requires auth
    start_res = client.post("/start_upload", json=start_payload)
    assert start_res.status_code == 200
    upload_id = start_res.json()["upload_id"]
    
    # --- 5. Upload Chunk ---
    # We need to simulate the chunk directory structure for the app to find it?
    # app/main.py writes chunks to CHUNK_DIR upon upload_chunk.
    
    chunk_file = io.BytesIO(content)
    upload_chunk_data = {
        "upload_id": upload_id,
        "chunk_index": 0,
        "chunk_hash": chunk_hash
    }
    files = {"file": ("chunk", chunk_file, "application/octet-stream")}
    
    chunk_res = client.post("/upload_chunk", data=upload_chunk_data, files=files)
    assert chunk_res.status_code == 200
    
    # --- 5a. Verify chunk is encrypted on disk ---
    chunk_path = CHUNK_DIR / chunk_hash
    assert chunk_path.exists()
    with open(chunk_path, "rb") as f:
        encrypted_content = f.read()

    # Encrypted content should not be the same as original
    assert encrypted_content != content

    # It should be decryptable to the original content
    decrypted_content = decrypt_data(encrypted_content)
    assert decrypted_content == content
    
    # --- 6. Check Upload Status ---
    status_res = client.get(f"/upload_status/{upload_id}")
    assert status_res.status_code == 200
    assert status_res.json()["uploaded_chunks"] == [0]
    
    # --- 7. Finalize Upload ---
    finalize_payload = {
        "upload_id": upload_id,
        "chunks": [chunk_hash],
        "filename": filename
    }
    final_res = client.post("/finalize_upload", json=finalize_payload)
    assert final_res.status_code == 200
    assert final_res.json()["hash"] == file_hash, f"Finalize failed: {final_res.text}"

    # --- 7a. Verify finalized file is encrypted on disk ---
    final_path = os.path.join(STORAGE_DIR, file_hash)
    assert os.path.exists(final_path)
    with open(final_path, "rb") as f:
        encrypted_final_content = f.read()

    assert encrypted_final_content != content
    decrypted_final_content = decrypt_data(encrypted_final_content)
    assert decrypted_final_content == content
    
    # --- 8. Verify File in List (Authenticated) ---
    list_res = client.get("/api/files", headers=headers)
    assert list_res.status_code == 200
    files_list = list_res.json()
    
    # Find our file
    found = any(f["hash"] == file_hash and f["filename"] == filename for f in files_list)
    assert found, "Uploaded file not found in /api/files list"

def test_metrics_endpoints(client):
    """Test that metrics endpoints are operational."""
    # Public endpoint
    health_res = client.get("/metrics/health")
    assert health_res.status_code == 200
    
    # Authenticated endpoint
    # 1. Register/Login first
    client.post("/register", json={"username": "metrics_user", "password": "pw"})
    token = client.post("/token", data={"username": "metrics_user", "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    sys_res = client.get("/metrics/system", headers=headers)
    assert sys_res.status_code == 200
    data = sys_res.json()
    assert "cpu_percent" in data
    assert "memory_percent" in data

def test_unauthorized_access(client):
    """Ensure protected endpoints reject unauthenticated requests."""
    res = client.get("/api/files")
    assert res.status_code == 401