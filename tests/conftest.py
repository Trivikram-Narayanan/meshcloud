import os
import sys
import pytest
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import shutil
from unittest.mock import patch
from cryptography.fernet import Fernet

# Add project root to sys.path to allow for absolute imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 0. Define Test DB URL
TEST_DB_URL = "sqlite:///./test_meshcloud.db"

# 1. Set Critical Env Vars BEFORE importing app
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-that-is-at-least-32-characters-long"
os.environ["NODE_TOKEN"] = "test-node-token"
os.environ["VERIFY_SSL"] = "false"
os.environ["STORAGE_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["DATABASE_URL"] = TEST_DB_URL

# 3. Import App and DB
from meshcloud.main import app # noqa: E402
from meshcloud.storage.database import Base, engine as app_engine # noqa: E402

@pytest.fixture(scope="function")
def client():
    """Return a TestClient that uses the overridden DB."""
    # Create tables before each test using the app's configured engine
    Base.metadata.create_all(bind=app_engine)
    
    # Override lifespan to prevent background threads from starting
    # This avoids patching threading.Thread which breaks ThreadPoolExecutor
    @asynccontextmanager
    async def test_lifespan(app):
        # Perform necessary startup tasks (e.g. DB init)
        from meshcloud.storage.database import init_db
        init_db()
        os.makedirs("app/static", exist_ok=True)
        yield
    
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan
    
    # Patch BackgroundTasks to prevent post-request tasks
    with patch("starlette.background.BackgroundTasks.add_task"):
        with TestClient(app) as c:
            yield c
            
    # Restore original lifespan
    app.router.lifespan_context = original_lifespan

    # Drop tables after each test
    Base.metadata.drop_all(bind=app_engine)

@pytest.fixture(scope="function", autouse=True)
def cleanup_test_files():
    """Cleanup any file artifacts after testing."""
    # CRITICAL: Dispose engine to close open connections before deleting the DB file
    app_engine.dispose()

    # Clean up storage from previous runs to ensure clean state for encryption tests
    if os.path.exists("storage"):
        shutil.rmtree("storage")
    
    # Re-create directories required by app (since app imports happen before this)
    os.makedirs("storage/chunks", exist_ok=True)
    os.makedirs("storage/manifests", exist_ok=True)
    os.makedirs("storage/tmp", exist_ok=True)
    os.makedirs("app/static", exist_ok=True)
    
    with open("app/static/index.html", "w") as f:
        f.write("<html><body>MeshCloud | Decentralized Storage</body></html>")

    yield
    
    # Cleanup after test execution
    app_engine.dispose()
    if os.path.exists("./test_meshcloud.db"):
        os.remove("./test_meshcloud.db")
    
    if os.path.exists("storage"):
        shutil.rmtree("storage")