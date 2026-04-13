import os
import socket
import subprocess
import sys
import time

def get_lan_ip():
    try:
        # Connect to a public DNS server to determine the best outgoing interface
        # This doesn't actually send data, just routes it locally
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_ssl_cert():
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        print("🔐 Generating dynamic self-signed SSL certificate...")
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", "key.pem", "-out", "cert.pem",
            "-days", "365", "-nodes", "-subj", "/CN=localhost"
        ], check=True, stderr=subprocess.DEVNULL)

def main():
    print("🛑  Stopping existing MeshCloud instances...")
    # Kill process on port 8000 and 9999 (Mac/Linux specific)
    # We use Shell=True to use pipes
    subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null", shell=True)
    subprocess.run("lsof -ti:9999 | xargs kill -9 2>/dev/null", shell=True)
    
    time.sleep(1)
    
    # Wipe DB to prevent state issues (Protocol mismatch etc)
    if os.path.exists("db/meshcloud.db"):
        print("🧹  Cleaning local database cache...")
        try:
            os.remove("db/meshcloud.db")
        except OSError:
            pass

    generate_ssl_cert()

    ip = get_lan_ip()
    print(f"🚀  Starting MeshCloud on LAN IP: {ip}")
    print(f"    - Dashboard: https://{ip}:8000/dashboard/")
    print(f"    - API Docs:  https://{ip}:8000/docs")
    
    os.environ["NODE_URL"] = f"https://{ip}:8000"
    os.environ["VERIFY_SSL"] = "false"
    
    # Run Uvicorn using the current python environment
    subprocess.run([
        sys.executable, "-m", "uvicorn", "meshcloud.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload",
        "--ssl-keyfile", "key.pem",
        "--ssl-certfile", "cert.pem",
        "--reload-exclude", "storage",
        "--reload-exclude", "db",
        "--reload-exclude", "logs"
    ])

if __name__ == "__main__":
    main()