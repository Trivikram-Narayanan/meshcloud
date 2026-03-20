
import os
import requests
import time
import subprocess
import signal

def run_node(port, storage_dir, node_id=None):
    env = os.environ.copy()
    env["STORAGE_DIR"] = storage_dir
    env["PORT"] = str(port)
    env["NODE_URL"] = f"http://localhost:{port}"
    if node_id:
        env["NODE_ID"] = node_id
    
    # Run main.py as a separate process
    process = subprocess.Popen(
        ["python", "-m", "meshcloud.main"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return process

def get_node_id_from_api(port):
    try:
        resp = requests.get(f"http://localhost:{port}/api/status", timeout=2)
        data = resp.json()
        return data.get("node_id")
    except Exception as e:
        print(f"API Error on port {port}: {e}")
        return None

def main():
    storage1 = "tmp_storage_node1"
    storage2 = "tmp_storage_node2"
    
    # Clean up previous runs
    import shutil
    if os.path.exists(storage1): shutil.rmtree(storage1)
    if os.path.exists(storage2): shutil.rmtree(storage2)
    
    print("Step 1: Start node 1 and get its ID...")
    proc1 = run_node(8001, storage1)
    time.sleep(3)
    id1_attempt1 = get_node_id_from_api(8001)
    print(f"Node 1 ID (first run): {id1_attempt1}")
    
    print("Step 2: Restart node 1 and check if ID is the same...")
    proc1.terminate()
    proc1.wait()
    proc1 = run_node(8001, storage1)
    time.sleep(3)
    id1_attempt2 = get_node_id_from_api(8001)
    print(f"Node 1 ID (second run): {id1_attempt2}")
    
    if id1_attempt1 == id1_attempt2 and id1_attempt1 is not None:
        print("✅ Node identity is persistent!")
    else:
        print("❌ Node identity is NOT persistent or failed to load.")
    
    print("Step 3: Start Node 2 and check it has a DIFFERENT ID...")
    proc2 = run_node(8002, storage2)
    time.sleep(3)
    id2 = get_node_id_from_api(8002)
    print(f"Node 2 ID: {id2}")
    
    if id1_attempt1 != id2:
        print("✅ Nodes have unique identities!")
    else:
        print("❌ Nodes have conflicting IDs!")

    # Cleanup
    proc1.terminate()
    proc2.terminate()
    if os.path.exists(storage1): shutil.rmtree(storage1)
    if os.path.exists(storage2): shutil.rmtree(storage2)

if __name__ == "__main__":
    main()
