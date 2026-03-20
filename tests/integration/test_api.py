"""Integration tests for MeshCloud API endpoints."""
import pytest


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_status_endpoint(client):
    """Test status endpoint."""
    # 1. Register User
    user_data = {
        "username": "status_user_api",
        "password": "password",
        "full_name": "Status User",
        "email": "status_api@example.com",
    }
    reg_res = client.post("/register", json=user_data)
    assert reg_res.status_code == 200, f"Register failed: {reg_res.text}"

    # 2. Login
    token_res = client.post("/token", data={"username": user_data["username"], "password": user_data["password"]})
    assert token_res.status_code == 200, f"Login failed: {token_res.text}"
    token = token_res.json()["access_token"]
    
    # 3. Access Status Endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["node"] == "MeshCloud"
    assert data["status"] == "running"


def test_has_file_endpoint(client):
    """Test file existence check endpoint."""
    # Test with non-existent file
    response = client.get("/has_file/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"exists": False}


def test_file_locations_endpoint(client):
    """Test file location lookup endpoint."""
    # Test with non-existent file
    response = client.get("/file_locations/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"nodes": []}


def test_start_upload_endpoint(client):
    """Test upload session initialization."""
    payload = {"filename": "test.txt", "total_chunks": 3}
    response = client.post("/start_upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert isinstance(data["upload_id"], str)


def test_upload_status_endpoint(client):
    """Test upload status checking."""
    # First start an upload
    start_response = client.post("/start_upload", json={"filename": "test.txt", "total_chunks": 2})
    upload_id = start_response.json()["upload_id"]

    # Check status
    status_response = client.get(f"/upload_status/{upload_id}")
    assert status_response.status_code == 200
    assert status_response.json() == {"uploaded_chunks": []}


def test_upload_status_invalid_id(client):
    """Test upload status with invalid ID."""
    response = client.get("/upload_status/invalid-id")
    assert response.status_code == 200
    assert response.json() == {"uploaded_chunks": []}


def test_chunk_upload_workflow(client):
    """Test complete chunk upload workflow."""
    import hashlib
    import io

    # Step 1: Start upload
    start_response = client.post("/start_upload", json={"filename": "test.txt", "total_chunks": 1})
    upload_id = start_response.json()["upload_id"]

    # Step 2: Prepare chunk data
    chunk_data = b"Hello, World! This is test data."
    chunk_hash = hashlib.sha256(chunk_data).hexdigest()

    # Step 3: Upload chunk
    files = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
    data = {"upload_id": upload_id, "chunk_index": 0, "chunk_hash": chunk_hash}

    upload_response = client.post("/upload_chunk", files=files, data=data)
    assert upload_response.status_code == 200
    assert upload_response.json() == {"status": "chunk stored"}

    # Step 4: Check upload status
    status_response = client.get(f"/upload_status/{upload_id}")
    assert status_response.status_code == 200
    assert status_response.json() == {"uploaded_chunks": [0]}


def test_finalize_upload_workflow(client):
    """Test complete upload finalization workflow."""
    import hashlib
    import io
    import uuid

    # Step 1: Start upload
    start_response = client.post("/start_upload", json={"filename": "finalize_test.txt", "total_chunks": 1})
    upload_id = start_response.json()["upload_id"]

    # Step 2: Upload chunk with unique content
    unique_content = f"Finalize upload test data - {uuid.uuid4()}"
    chunk_data = unique_content.encode()
    chunk_hash = hashlib.sha256(chunk_data).hexdigest()

    files = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
    data = {"upload_id": upload_id, "chunk_index": 0, "chunk_hash": chunk_hash}

    client.post("/upload_chunk", files=files, data=data)

    # Step 3: Finalize upload
    finalize_payload = {
        "upload_id": upload_id,
        "chunks": [chunk_hash],
        "filename": "finalize_test.txt",
    }

    finalize_response = client.post("/finalize_upload", json=finalize_payload)
    assert finalize_response.status_code == 200
    data = finalize_response.json()
    assert data["status"] == "file finalized"
    assert "hash" in data
    assert data["filename"] == "finalize_test.txt"

    # Step 4: Verify file exists
    file_hash = data["hash"]
    exists_response = client.get(f"/has_file/{file_hash}")
    assert exists_response.status_code == 200
    assert exists_response.json() == {"exists": True}


def test_duplicate_upload(client):
    """Test uploading the same file twice (deduplication)."""
    import hashlib
    import io

    # First upload
    start_response1 = client.post("/start_upload", json={"filename": "duplicate.txt", "total_chunks": 1})
    upload_id1 = start_response1.json()["upload_id"]

    chunk_data = b"This is duplicate content."
    chunk_hash = hashlib.sha256(chunk_data).hexdigest()

    files = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
    data = {"upload_id": upload_id1, "chunk_index": 0, "chunk_hash": chunk_hash}

    client.post("/upload_chunk", files=files, data=data)

    finalize_payload = {
        "upload_id": upload_id1,
        "chunks": [chunk_hash],
        "filename": "duplicate.txt",
    }

    finalize_response1 = client.post("/finalize_upload", json=finalize_payload)
    assert finalize_response1.status_code == 200
    first_hash = finalize_response1.json()["hash"]

    # Verify existence before duplicate attempt
    exists_check = client.get(f"/has_file/{first_hash}")
    assert exists_check.json()["exists"] is True, "First file upload failed to persist"

    # Second upload (same content)
    start_response2 = client.post("/start_upload", json={"filename": "duplicate2.txt", "total_chunks": 1})
    upload_id2 = start_response2.json()["upload_id"]

    files2 = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
    data2 = {"upload_id": upload_id2, "chunk_index": 0, "chunk_hash": chunk_hash}

    client.post("/upload_chunk", files=files2, data=data2)

    finalize_payload2 = {
        "upload_id": upload_id2,
        "chunks": [chunk_hash],
        "filename": "duplicate2.txt",
    }

    finalize_response2 = client.post("/finalize_upload", json=finalize_payload2)
    second_result = finalize_response2.json()

    # Should be marked as duplicate
    assert second_result["status"] == "duplicate"
    assert second_result["hash"] == first_hash


def test_invalid_chunk_hash(client):
    """Test uploading chunk with invalid hash."""
    import io

    # Start upload
    start_response = client.post("/start_upload", json={"filename": "test.txt", "total_chunks": 1})
    upload_id = start_response.json()["upload_id"]

    # Upload chunk with wrong hash
    chunk_data = b"test data"
    wrong_hash = "invalid_hash"

    files = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
    data = {"upload_id": upload_id, "chunk_index": 0, "chunk_hash": wrong_hash}

    upload_response = client.post("/upload_chunk", files=files, data=data)
    assert upload_response.status_code == 400
    assert upload_response.json()["detail"] == "Chunk hash mismatch"
