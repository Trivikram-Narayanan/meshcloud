import threading
import time
import random
import requests
from loguru import logger
from meshcloud.storage.database import (
    get_all_peers,
    add_peer,
    update_peer_status,
    get_all_files,
    register_file_location
)

class GossipProtocol:
    def __init__(self, node_url, node_id):
        self.node_url = node_url
        self.node_id = node_id
        self.peers = {}  # url -> {score: int, status: str}
        self.running = False
        self.lock = threading.Lock()
        self.max_score = 100
        self.min_score = 0

    def start(self):
        self.running = True
        # Start background gossip thread
        threading.Thread(target=self.gossip_loop, daemon=True).start()
        logger.info("🕸️ Gossip Protocol (SWIM-like) started")

    def gossip_loop(self):
        while self.running:
            self.pulse()
            # Gossip interval (protocol period T')
            time.sleep(2.0)

    def pulse(self):
        try:
            # 1. Sync local peer cache with DB
            db_peers = get_all_peers()
            with self.lock:
                for p in db_peers:
                    if p not in self.peers and p != self.node_url:
                        # Initialize new peers. We don't have their node_id yet.
                        self.peers[p] = {"score": self.max_score, "status": "alive", "node_id": None}

            if not self.peers:
                return

            # 2. Select a random peer (SWIM style)
            peer_url = random.choice(list(self.peers.keys()))

            # 3. Prepare Gossip Payload
            # Share random subset of known peers (Membership Dissemination)
            peer_subset = random.sample(list(self.peers.keys()), min(len(self.peers), 5))
            
            # Share "I have these files" (File Location Discovery)
            local_files = get_all_files(limit=10)
            file_hashes = [f.hash for f in local_files]

            payload = {
                "sender": self.node_url,
                "node_id": self.node_id,
                "peers": peer_subset,
                "files": file_hashes,
                "timestamp": time.time()
            }

            # 4. Send Heartbeat/Gossip
            try:
                r = requests.post(f"{peer_url}/gossip", json=payload, timeout=1.5)
                if r.status_code == 200:
                    self.handle_ack(peer_url, r.json())
                else:
                    self.handle_failure(peer_url)
            except Exception:
                self.handle_failure(peer_url)

        except Exception as e:
            logger.error(f"Gossip pulse error: {e}")

    def handle_ack(self, peer_url, data):
        with self.lock:
            if peer_url in self.peers:
                # Increase score (Healing)
                self.peers[peer_url]["score"] = min(self.peers[peer_url]["score"] + 5, self.max_score)
                update_peer_status(peer_url, True)

            # Merge received peers
            for p in data.get("known_peers", []):
                if p != self.node_url and p not in self.peers:
                    # We don't have their node_id yet, but add_peer will handle it if we find them online
                    add_peer(p)

    def handle_failure(self, peer_url):
        with self.lock:
            if peer_url in self.peers:
                # Decrease score (Failure Detection)
                self.peers[peer_url]["score"] -= 25
                logger.debug(f"📉 Peer {peer_url} score dropped to {self.peers[peer_url]['score']}")

                # Auto Removal / Marking Offline
                if self.peers[peer_url]["score"] <= self.min_score:
                    logger.warning(f"💀 Peer {peer_url} dead. Marking offline.")
                    update_peer_status(peer_url, False)
                    del self.peers[peer_url]

    def process_incoming_gossip(self, payload):
        sender = payload.get("sender")
        node_id = payload.get("node_id")
        files = payload.get("files", [])

        # Update peer status with node_id
        if sender:
            with self.lock:
                if sender in self.peers:
                    self.peers[sender]["node_id"] = node_id
                else:
                    self.peers[sender] = {"score": self.max_score, "status": "alive", "node_id": node_id}
            update_peer_status(sender, True, node_id)

        # Update file locations
        for f_hash in files:
            register_file_location(f_hash, sender)

        # Acknowledge and send back my view of peers
        # We could also send node_ids here if we had them cached in self.peers
        return {"status": "ack", "known_peers": list(self.peers.keys())[:5]}

    def get_graph_state(self):
        """Returns current gossip state for visualization."""
        with self.lock:
            # Return a copy to ensure thread safety during serialization
            return self.peers.copy()