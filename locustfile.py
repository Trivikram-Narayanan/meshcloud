import hashlib
import os
import random
import string
from locust import HttpUser, task, between, constant, events

# Disable SSL warnings for load testing against localhost
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseMeshUser(HttpUser):
    """Base user class that handles registration and login."""
    abstract = True
    
    def on_start(self):
        """Register and login a unique user for this session."""
        self.username = f"user_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        self.password = "password123"
        
        # 1. Register
        with self.client.post("/register", json={
            "username": self.username,
            "password": self.password,
            "full_name": "Load Tester"
        }, verify=False, catch_response=True) as response:
            if response.status_code == 400 and "already registered" in response.text:
                response.success()

        # 2. Login
        response = self.client.post("/token", data={
            "username": self.username,
            "password": self.password
        }, verify=False)
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.auth_header = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.auth_header = {}

class DashboardUser(BaseMeshUser):
    """Simulates an admin or monitoring tool polling the dashboard."""
    wait_time = constant(2) # Every 2 seconds exactly

    @task
    def refresh_dashboard(self):
        if not self.token: return
        # Dashboard fetches these 3 endpoints
        self.client.get("/metrics/system", headers=self.auth_header, verify=False, name="/metrics/system")
        self.client.get("/api/dashboard/network", headers=self.auth_header, verify=False, name="/api/dashboard/network")
        self.client.get("/api/dashboard/files", headers=self.auth_header, verify=False, name="/api/dashboard/files")

class RegularUser(BaseMeshUser):
    """Simulates a standard user browsing and occasionally uploading."""
    wait_time = between(2, 10)

    @task(3)
    def list_files(self):
        if not self.token: return
        self.client.get("/api/files", headers=self.auth_header, verify=False, name="/api/files")

    @task(1)
    def check_node_status(self):
        self.client.get("/", verify=False, name="/ (Status)")

class ReplicationStormUser(BaseMeshUser):
    """Simulates heavy load: rapid file uploads to trigger replication."""
    wait_time = between(0.5, 2)

    @task(1)
    def rapid_upload(self):
        if not self.token: return
        
        filename = f"storm_{''.join(random.choices(string.ascii_lowercase, k=8))}.bin"
        content = os.urandom(1024 * 100) # 100KB file
        
        # 1. Start Upload
        res = self.client.post("/start_upload", json={
            "filename": filename,
            "total_chunks": 1
        }, headers=self.auth_header, verify=False, name="/start_upload")
        
        if res.status_code != 200: return
        upload_id = res.json()["upload_id"]
        
        # 2. Upload Chunk
        chunk_hash = hashlib.sha256(content).hexdigest()
        files = {"file": ("chunk", content, "application/octet-stream")}
        data = {
            "upload_id": upload_id,
            "chunk_index": 0,
            "chunk_hash": chunk_hash
        }
        
        self.client.post("/upload_chunk", files=files, data=data, 
                        headers=self.auth_header, verify=False, name="/upload_chunk")
        
        # 3. Finalize
        self.client.post("/finalize_upload", json={
            "upload_id": upload_id,
            "chunks": [chunk_hash],
            "filename": filename
        }, headers=self.auth_header, verify=False, name="/finalize_upload")