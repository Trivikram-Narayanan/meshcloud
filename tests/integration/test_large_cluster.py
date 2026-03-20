import os
import time
import json
import shutil
import hashlib
import sqlite3
import requests
import subprocess
import sys
from pathlib import Path

NUM_NODES = 11
START_PORT = 8000
REPO = Path(__file__).parent.parent.parent.absolute()
VENV_PYTHON = sys.executable
REPLICATION_FACTOR = 3

def cleanup():
    print("[TEST] Cleaning up previous runs...")
    subprocess.run(["pkill", "-f", "uvicorn meshcloud.main"], capture_output=True)
    time.sleep(2)
    
    for port in range(START_PORT, START_PORT + NUM_NODES):
        dir_path = REPO / f"storage_node{port}"
        if dir_path.exists():
            shutil.rmtree(dir_path)
            
        (REPO / "config" / f"peers_{port}.json").unlink(missing_ok=True)
        (REPO / "db" / f"meshcloud_node-{port}.db").unlink(missing_ok=True)

def setup_nodes():
    print(f"[TEST] Setting up {NUM_NODES} nodes...")
    config_dir = REPO / "config"
    config_dir.mkdir(exist_ok=True)
    (REPO / "db").mkdir(exist_ok=True)
    
    # Generate peer configs
    peers = [f"http://localhost:{p}" for p in range(START_PORT, START_PORT + NUM_NODES)]
    for port in range(START_PORT, START_PORT + NUM_NODES):
        # We'll use a ring of seeds to speed up discovery
        node_peers = [p for p in peers if p != f"http://localhost:{port}"]
        config_file = config_dir / f"peers_{port}.json"
        with open(config_file, "w") as f:
            json.dump({"peers": node_peers}, f)
            
        # Create storage directories
        storage_dir = REPO / f"storage_node{port}"
        os.makedirs(storage_dir / "tmp", exist_ok=True)
        os.makedirs(storage_dir / "chunks", exist_ok=True)
        os.makedirs(storage_dir / "manifests", exist_ok=True)

def start_nodes():
    print("[TEST] Starting nodes...")
    processes = []
    for port in range(START_PORT, START_PORT + NUM_NODES):
        env = os.environ.copy()
        env.update({
            "NODE_URL": f"http://localhost:{port}",
            "NODE_ID": f"node-{port}",
            "STORAGE_DIR": f"storage_node{port}",
            "PEERS_FILE": f"config/peers_{port}.json",
            "LOG_LEVEL": "info",
            "REPLICATION_FACTOR": str(REPLICATION_FACTOR)
        })
        
        log_file = open(f"/tmp/node{port}.log", "w")
        p = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "meshcloud.main:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=str(REPO),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        processes.append((p, log_file))
        print(f"  → Node {port} started (PID: {p.pid})")
        
    print("[TEST] Waiting for nodes to boot and discover each other (10s)...")
    time.sleep(10)
    return processes

def run_test():
    test_file = "/tmp/test_replication.bin"
    file_size = 1 * 1024 * 1024 # 1MB
    
    print(f"[TEST] Generating {file_size} bytes file...")
    with open(test_file, "wb") as f:
        f.write(os.urandom(file_size))
        
    sha256 = hashlib.sha256()
    with open(test_file, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    file_hash = sha256.hexdigest()
    
    print(f"[TEST] Uploading file to Node 8000...")
    headers = {
        "X-MeshCloud-Token": "meshcloud_secret_token"
    }
    with open(test_file, "rb") as f:
        resp = requests.post(f"http://localhost:8000/upload", files={"file": f}, headers=headers)
        
    if resp.status_code != 200:
        print(f"[FAIL] Upload failed: {resp.text}")
        return
        
    print("[TEST] Upload response:", resp.json())
    
    print(f"[TEST] Waiting for replication to {REPLICATION_FACTOR} nodes...")
    
    found_on_count = 0
    max_attempts = 20
    for attempt in range(max_attempts):
        nodes_with_file = []
        for port in range(START_PORT, START_PORT + NUM_NODES):
            try:
                # Check /has_file endpoint instead of direct FS check for realism
                r = requests.get(f"http://localhost:{port}/has_file/{file_hash}", headers=headers, timeout=2)
                if r.status_code == 200 and r.json().get("exists"):
                    nodes_with_file.append(port)
            except:
                pass
        
        found_on_count = len(nodes_with_file)
        print(f"  [Attempt {attempt+1}/{max_attempts}] Found on {found_on_count} nodes: {nodes_with_file}")
        
        if found_on_count >= REPLICATION_FACTOR:
            print(f"[PASS] Replication successful! Found on {found_on_count} nodes.")
            return True
        
        time.sleep(3)
        
    print(f"[FAIL] Replication failed! Only found on {found_on_count} nodes, expected at least {REPLICATION_FACTOR}.")
    
    # Print some logs from node 8000 if it failed
    print("\n--- NODE 8000 LOG (Last 50 lines) ---")
    os.system(f"tail -n 50 /tmp/node8000.log")
    print("---------------------\n")
    return False

def stop_nodes(processes):
    print("[TEST] Stopping nodes...")
    for p, f in processes:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
        f.close()

if __name__ == "__main__":
    cleanup()
    setup_nodes()
    processes = start_nodes()
    success = False
    try:
        success = run_test()
    finally:
        stop_nodes(processes)
        # We don't cleanup() here so we can inspect logs if needed, 
        # but cleanup() is called at the start anyway.
    
    if not success:
        exit(1)
