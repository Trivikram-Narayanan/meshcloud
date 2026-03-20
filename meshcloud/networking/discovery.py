"""
Peer discovery for MeshCloud nodes.
  - seed_peers_from_config  : reads peers.json (or PEERS_FILE env) at startup
  - discovery_broadcast     : LAN mDNS-style UDP broadcast
  - discovery_listener      : receives broadcasts from other nodes
  - dns_discovery_worker    : for Kubernetes / Docker headless-service DNS
"""
import socket
import time
import json
import os
from urllib.parse import urlparse
from loguru import logger
from meshcloud.storage.database import add_peer, NODE_ID

DISCOVERY_PORT = 9999
DISCOVERY_MESSAGE = "MESH_DISCOVERY"
DNS_DISCOVERY_SERVICE = os.getenv("DNS_DISCOVERY_SERVICE")
THIS_NODE = os.getenv("NODE_URL", "http://localhost:8000")


def seed_peers_from_config():
    """Load initial peers from a JSON file. Supports per-node PEERS_FILE env var."""
    peers_file = os.getenv("PEERS_FILE", "config/peers.json")
    try:
        with open(peers_file) as f:
            data = json.load(f)
            peers = data.get("peers", [])
            for peer in peers:
                if peer and peer != THIS_NODE:
                    add_peer(peer)
                    logger.info(f"🌱 Seeded peer from config: {peer}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Peer seed skipped ({peers_file}): {e}")


def discovery_broadcast():
    """Periodically broadcast UDP presence on the LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Include THIS_NODE and NODE_ID in the broadcast so peers know exactly who we are
    message = f"{DISCOVERY_MESSAGE}|{THIS_NODE}|{NODE_ID}".encode()
    while True:
        try:
            s.sendto(message, ("<broadcast>", DISCOVERY_PORT))
        except OSError:
            pass  # Network unreachable or similar — safe to ignore
        time.sleep(10)


def discovery_listener():
    """Listen for UDP broadcasts from other nodes on the same LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    try:
        s.bind(("", DISCOVERY_PORT))
    except OSError as e:
        logger.warning(f"Discovery listener could not bind port {DISCOVERY_PORT}: {e}")
        return

    while True:
        try:
            data, addr = s.recvfrom(1024)
            msg = data.decode()
            if msg.startswith(DISCOVERY_MESSAGE):
                parts = msg.split("|")
                peer = None
                node_id = None
                
                if len(parts) > 2:
                    peer = parts[1]
                    node_id = parts[2]
                elif len(parts) > 1:
                    peer = parts[1]
                else:
                    # Backward compatibility / Fallback
                    peer_ip = addr[0]
                    peer = f"http://{peer_ip}:8000"
                
                if peer and peer != THIS_NODE:
                    add_peer(peer, node_id=node_id)
                    logger.debug(f"Discovered peer via UDP: {peer} (ID: {node_id})")
        except Exception as e:
            logger.debug(f"Discovery listener error: {e}")


def dns_discovery_worker():
    """For Kubernetes headless services — resolves DNS to find peer IPs."""
    if not DNS_DISCOVERY_SERVICE:
        return

    logger.info(f"DNS discovery started for: {DNS_DISCOVERY_SERVICE}")
    parsed = urlparse(THIS_NODE)
    scheme = parsed.scheme or "http"
    port = parsed.port or 8000

    while True:
        try:
            addr_infos = socket.getaddrinfo(DNS_DISCOVERY_SERVICE, port, proto=socket.IPPROTO_TCP)
            for info in addr_infos:
                ip = info[4][0]
                peer_url = f"{scheme}://{ip}:{port}"
                if peer_url != THIS_NODE:
                    add_peer(peer_url)
        except Exception as e:
            logger.debug(f"DNS discovery cycle failed: {e}")
        time.sleep(30)