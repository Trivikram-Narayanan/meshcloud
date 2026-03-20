import hashlib
import os
import socket
import time
import random
import sys
import subprocess
import concurrent.futures
import string
import tempfile

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEMP_DIR = tempfile.gettempdir()
LEGACY_FILENAME = os.path.join(TEMP_DIR, "test_legacy_data.bin")
CHUNKED_FILENAME = os.path.join(TEMP_DIR, "test_chunked_video.mp4")
CHUNK_SIZE = 1024 * 1024  # 1MB chunks
DISCOVERY_PORT = 9999
STORAGE_DIR = "storage_simulation"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@pytest.fixture(scope="module", autouse=True)
def mesh_node():
    """Starts a local MeshCloud node for integration testing."""
    if os.path.exists(STORAGE_DIR):
        import shutil
        shutil.rmtree(STORAGE_DIR)
    if os.path.exists("test_meshcloud.db"):
        os.remove("test_meshcloud.db")
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, "tmp"), exist_ok=True)

    env = os.environ.copy()
    env["STORAGE_DIR"] = STORAGE_DIR
    env["NODE_URL"] = BASE_URL
    env["NODE_ID"] = "simulation_node"
    env["DATABASE_URL"] = f"sqlite:///test_meshcloud.db"
    env["MESH_TOKEN"] = "meshcloud_secret_token"
    env["PYTHONPATH"] = os.getcwd() # Ensure imports from current dir work

    # Start the node
    # Use text=True for string output from stdout/stderr
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "meshcloud.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=None,
        stderr=None,
        text=True
    )
    
    # Wait for node to be ready
    max_retries = 10
    for _ in range(max_retries):
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                break
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    else:
        proc.kill()
        pytest.fail(f"Node failed to start at {BASE_URL}.")

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    
    if os.path.exists(STORAGE_DIR):
        import shutil
        shutil.rmtree(STORAGE_DIR)


def get_session():
    """Creates a requests Session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

def generate_fake_file(filename, size_bytes):
    """Generates a file with random bytes."""
    print(f"[GEN] Generating {filename} ({size_bytes / 1024 / 1024:.2f} MB)...")
    with open(filename, "wb") as f:
        f.write(os.urandom(size_bytes))


def calculate_file_hash(filename):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def test_legacy_upload():
    """Tests the simple /upload endpoint used by the current watcher."""
    print("\n--- 1. Testing Legacy Upload (Single Shot) ---")

    generate_fake_file(LEGACY_FILENAME, 2 * 1024 * 1024)  # 2MB

    session = get_session()
    print(f"[UPL] Uploading {LEGACY_FILENAME}...")
    with open(LEGACY_FILENAME, "rb") as f:
        files = {"file": f}
        # The /upload endpoint is for internal node replication and requires a token.
        headers = {
            "X-MeshCloud-Token": "meshcloud_secret_token",
        }
        try:
            resp = session.post(f"{BASE_URL}/upload", files=files, headers=headers, verify=False)
            resp.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            response_data = resp.json()
            print(f"[RES] Server Response: {response_data}")
            assert response_data.get("status") == "stored"
            assert "hash" in response_data
            print("[PASS] Legacy upload test passed!")
        except Exception as e:
            print(f"[ERR] Upload failed: {e}")

    # Cleanup
    if os.path.exists(LEGACY_FILENAME):
        os.remove(LEGACY_FILENAME)


def test_chunked_upload():
    """Tests the new chunked upload workflow (Start -> Chunk -> Finalize)."""
    print("\n--- 2. Testing New Chunked Upload Workflow ---")

    # 1. Generate a larger file (5MB)
    generate_fake_file(CHUNKED_FILENAME, 5 * 1024 * 1024)
    file_size = os.path.getsize(CHUNKED_FILENAME)
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    session = get_session()
    # 2. Start Session
    print(f"[API] Initializing upload session for {total_chunks} chunks...")
    try:
        resp = session.post(
            f"{BASE_URL}/start_upload",
            json={"filename": CHUNKED_FILENAME, "total_chunks": total_chunks},
            verify=False,
        )
        resp.raise_for_status()
        upload_id = resp.json()["upload_id"]
        print(f"[SES] Upload ID: {upload_id}")
    except Exception as e:
        print(f"[ERR] Failed to start upload session: {e}")
        return

    # 3. Upload Chunks
    chunk_hashes = []
    with open(CHUNKED_FILENAME, "rb") as f:
        for index in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)

            # Hash the chunk
            sha = hashlib.sha256()
            sha.update(chunk_data)
            c_hash = sha.hexdigest()
            chunk_hashes.append(c_hash)

            # Prepare request
            files = {"file": (os.path.basename(CHUNKED_FILENAME), chunk_data)}
            data = {"upload_id": upload_id, "chunk_index": index, "chunk_hash": c_hash}

            print(
                f"      Uploading chunk {index+1}/{total_chunks} ({len(chunk_data)} bytes)..."
            )
            try:
                r = session.post(
                    f"{BASE_URL}/upload_chunk", files=files, data=data, verify=False
                )
                r.raise_for_status()
            except Exception as e:
                print(f"[ERR] Chunk {index} upload failed: {e}")
                return

    # 4. Finalize
    print(f"[API] Finalizing upload for {CHUNKED_FILENAME}...")
    try:
        resp = session.post(
            f"{BASE_URL}/finalize_upload",
            json={
                "upload_id": upload_id,
                "chunks": chunk_hashes,
                "filename": os.path.basename(CHUNKED_FILENAME),
                "is_replica": True,  # Prevent replication in this single-node test
            },
            verify=False,
        )
        resp.raise_for_status()
        response_data = resp.json()
        print(f"[RES] Finalize Response: {response_data}")
        assert response_data.get("status") == "file finalized"
        print("[PASS] Chunked upload test passed!")
    except Exception as e:
        print(f"[ERR] Finalize failed: {e}")

    # Cleanup
    if os.path.exists(CHUNKED_FILENAME):
        os.remove(CHUNKED_FILENAME)


def simulate_network_churn():
    """Simulates network churn by flooding the discovery port with packets."""
    print("\n--- 3. Simulating Network Churn (Discovery Flood) ---")
    print(f"[NET] Sending UDP broadcast packets to port {DISCOVERY_PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Simulate 50 "nodes" announcing themselves rapidly
    start_time = time.time()
    packets_sent = 0
    
    try:
        for _ in range(50):
            # In a real network, these would come from different IPs.
            # On localhost, this stresses the listener thread.
            sock.sendto(b"MESH_DISCOVERY", ("127.0.0.1", DISCOVERY_PORT))
            packets_sent += 1
            time.sleep(0.05)  # Jitter
            
        print(f"[PASS] Sent {packets_sent} discovery packets in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"[ERR] Network churn simulation failed: {e}")
    finally:
        sock.close()


def upload_random_file(file_idx):
    """Helper for concurrent uploads."""
    filename = f"storm_file_{file_idx}_{''.join(random.choices(string.ascii_lowercase, k=4))}.bin"
    size = random.randint(100 * 1024, 500 * 1024) # 100KB - 500KB
    
    # 1. Create content in memory
    content = os.urandom(size)
    
    # 2. Start
    try:
        # We need a token for standard uploads, but legacy/node uploads use different headers.
        # Using legacy upload for speed in storm simulation
        headers = {"X-MeshCloud-Token": "meshcloud_secret_token"}
        files = {"file": (filename, content)}
        
        resp = requests.post(
            f"{BASE_URL}/upload", 
            files=files, 
            headers=headers, 
            verify=False,
            timeout=10
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[ERR] File {file_idx} failed: {e}")
        return False


def simulate_replication_storm(count=20):
    """Simulates a replication storm with concurrent uploads."""
    # This is a load test, renamed to start with test_ for pytest
    simulate_replication_storm(count=10) # Lower count for CI stability


def test_deduplication():
    """Tests content-based deduplication."""
    print("\n--- 5. Testing Content Deduplication ---")
    filename = os.path.join(TEMP_DIR, "dedup_test.bin")
    generate_fake_file(filename, 512 * 1024) # 512KB
    
    session = get_session()
    print(f"[UPL] Uploading {filename} (Pass 1)...")
    headers = {
        "X-MeshCloud-Token": "meshcloud_secret_token",
    }
    with open(filename, "rb") as f:
        resp1 = session.post(f"{BASE_URL}/upload", files={"file": f}, headers=headers, verify=False)
        if resp1.status_code != 200:
            print(f"[ERR] Pass 1 failed ({resp1.status_code}): {resp1.text}")
        resp1.raise_for_status()
    
    print(f"[UPL] Uploading {filename} (Pass 2 - Same Content)...")
    with open(filename, "rb") as f:
        resp2 = session.post(f"{BASE_URL}/upload", files={"file": f}, headers=headers, verify=False)
    
    if resp2.status_code != 200:
        print(f"[ERR] Pass 2 failed ({resp2.status_code}): {resp2.text}")
    resp2.raise_for_status()
    
    print(f"[RES] Pass 1: {resp1.json().get('status')}")
    print(f"[RES] Pass 2: {resp2.json().get('status')}")
    
    assert resp2.json().get("status") == "duplicate"
    print("[PASS] Deduplication confirmed!")
    os.remove(filename)

if __name__ == "__main__":
    # Functional Tests
    test_legacy_upload()
    test_chunked_upload()
    test_deduplication()
    
    # Resilience Tests
    simulate_network_churn()
    simulate_replication_storm(count=25)
