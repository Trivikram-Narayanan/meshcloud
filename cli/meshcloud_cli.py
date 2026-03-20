import argparse
import requests
import os
import math
import hashlib
import sys
import json
from time import sleep

API_URL = os.getenv("MESHCLOUD_API", "http://localhost:8000")
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB


def calculate_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def chunk_file(file_path):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk


def upload(args):
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_chunks = math.ceil(file_size / CHUNK_SIZE)

    print(f"📦 Preparing to upload '{filename}' ({file_size / 1024 / 1024:.2f} MB)")
    print(f"   Chunks: {total_chunks}")

    try:
        # 1. Start Session
        r = requests.post(f"{API_URL}/start_upload", json={
            "filename": filename,
            "total_chunks": total_chunks
        })
        r.raise_for_status()
        upload_id = r.json()["upload_id"]

        # 2. Upload Chunks
        chunk_hashes = []
        for index, chunk in enumerate(chunk_file(file_path)):
            # Hash chunk
            sha = hashlib.sha256()
            sha.update(chunk)
            c_hash = sha.hexdigest()
            chunk_hashes.append(c_hash)

            # Upload
            files = {"file": (filename, chunk)}
            data = {"upload_id": upload_id, "chunk_index": index, "chunk_hash": c_hash}
            
            sys.stdout.write(f"\r🚀 Uploading chunk {index + 1}/{total_chunks}...")
            sys.stdout.flush()
            
            r = requests.post(f"{API_URL}/upload_chunk", files=files, data=data)
            r.raise_for_status()

        print("\n✅ All chunks uploaded.")

        # 3. Finalize
        print("🔨 Finalizing and replicating...")
        r = requests.post(f"{API_URL}/finalize_upload", json={
            "upload_id": upload_id,
            "chunks": chunk_hashes,
            "filename": filename
        })
        r.raise_for_status()
        res = r.json()
        
        print(f"🎉 Success! File CID: {res['hash']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Server says: {e.response.text}")


def download(args):
    cid = args.cid
    output = args.output
    
    url = f"{API_URL}/download/{cid}"
    print(f"📥 Requesting {cid}...")
    
    try:
        with requests.get(url, stream=True) as r:
            if r.status_code == 404:
                print("❌ File not found on this node.")
                return
            r.raise_for_status()
            
            # Determine filename
            if not output:
                content_disposition = r.headers.get("content-disposition")
                if content_disposition and "filename=" in content_disposition:
                    output = content_disposition.split("filename=")[1].strip('"')
                else:
                    output = cid
            
            with open(output, "wb") as f:
                total_len = int(r.headers.get('content-length', 0))
                dl = 0
                for chunk in r.iter_content(chunk_size=8192):
                    dl += len(chunk)
                    f.write(chunk)
                    # Basic progress bar
                    if total_len > 0:
                        percent = int(50 * dl / total_len)
                        sys.stdout.write(f"\r   [{'=' * percent}{' ' * (50 - percent)}] {dl}/{total_len} bytes")
                        sys.stdout.flush()
            
            print(f"\n✅ Download complete: {output}")

    except Exception as e:
        print(f"❌ Error: {e}")


def peers(args):
    try:
        r = requests.get(f"{API_URL}/peers")
        r.raise_for_status()
        peer_list = r.json()
        print(f"🔗 Connected Peers ({len(peer_list)}):")
        for p in peer_list:
            print(f"  - {p}")
    except Exception as e:
        print(f"❌ Could not fetch peers: {e}")


def node_status(args):
    try:
        r = requests.get(f"{API_URL}/")
        r.raise_for_status()
        data = r.json()
        print("🟢 Node Status:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


def network_stats(args):
    try:
        r = requests.get(f"{API_URL}/metrics")
        r.raise_for_status()
        print("📊 Network/Prometheus Metrics:")
        print(r.text)
    except Exception as e:
        print(f"❌ Error fetching stats: {e}")


def main():
    parser = argparse.ArgumentParser(prog="meshcloud", description="CLI for MeshCloud P2P Storage")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # upload
    up = subparsers.add_parser("upload", help="Upload a file")
    up.add_argument("file", help="Path to file")
    
    # download
    dl = subparsers.add_parser("download", help="Download a file by CID")
    dl.add_argument("cid", help="Content ID (Hash)")
    dl.add_argument("-o", "--output", help="Output filename")

    # peers
    subparsers.add_parser("peers", help="List connected peers")

    # node status
    node = subparsers.add_parser("node", help="Node operations")
    node.add_argument("action", choices=["status"], help="Action to perform")

    # network stats
    net = subparsers.add_parser("network", help="Network operations")
    net.add_argument("action", choices=["stats"], help="Action to perform")

    args = parser.parse_args()

    if args.command == "upload":
        upload(args)
    elif args.command == "download":
        download(args)
    elif args.command == "peers":
        peers(args)
    elif args.command == "node":
        if args.action == "status":
            node_status(args)
    elif args.command == "network":
        if args.action == "stats":
            network_stats(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
