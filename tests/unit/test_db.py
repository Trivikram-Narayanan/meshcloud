import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from meshcloud.storage import database as db
from meshcloud.storage.database import Base

# Use in-memory SQLite for speed and isolation
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db_session():
    """
    Creates a fresh in-memory database for each test function.
    Monkeypatches meshcloud.storage.database.SessionLocal to use this test database.
    """
    # Create engine and session for testing
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables defined in Base
    Base.metadata.create_all(bind=engine)
    
    # Save original SessionLocal to restore later
    original_session_local = db.SessionLocal
    
    # Patch the SessionLocal in the database module
    db.SessionLocal = TestingSessionLocal
    
    yield
    
    # Teardown: Drop tables and restore original session factory
    Base.metadata.drop_all(bind=engine)
    db.SessionLocal = original_session_local

def test_user_operations(test_db_session):
    """Test creating and retrieving users."""
    # 1. Create User
    user = db.create_user("testuser", "hashed_secret", "Test User", "test@example.com")
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    
    # 2. Retrieve User
    fetched = db.get_user_by_username("testuser")
    assert fetched is not None
    assert fetched.username == "testuser"
    
    # 3. Retrieve Non-existent User
    assert db.get_user_by_username("nobody") is None

def test_peer_operations(test_db_session):
    """Test peer discovery and status tracking."""
    peer_url = "http://localhost:8001"
    
    # 1. Add Peer
    db.add_peer(peer_url)
    peers = db.get_all_peers()
    assert len(peers) == 1
    assert peers[0] == peer_url
    
    # 2. Check Initial Status (Offline by default)
    assert db.is_peer_online(peer_url) is False
    
    # 3. Update Status to Online
    db.update_peer_status(peer_url, True)
    assert db.is_peer_online(peer_url) is True
    
    # 4. Update Status to Offline
    db.update_peer_status(peer_url, False)
    assert db.is_peer_online(peer_url) is False

def test_file_metadata_operations(test_db_session):
    """Test file insertion and location tracking."""
    file_hash = "abc123hash"
    filename = "test.txt"
    
    # 1. Insert File
    db.insert_file(file_hash, filename)
    
    # 2. Check Existence
    assert db.file_exists(file_hash) is True
    assert db.file_exists("nonexistent") is False
    
    # 3. Get Filename
    assert db.get_filename(file_hash) == filename
    
    # 4. Register and Get Locations
    node_url = "http://node2:8000"
    db.register_file_location(file_hash, node_url)
    nodes = db.get_file_locations(file_hash)
    assert node_url in nodes

def test_upload_session_operations(test_db_session):
    """Test upload session and chunk tracking."""
    upload_id = "upload_123"
    
    # 1. Create Session
    db.create_upload_session(upload_id, "video.mp4", 10)
    
    # 2. Add Uploaded Chunks
    db.add_uploaded_chunk(upload_id, 0, "chunkhash0")
    db.add_uploaded_chunk(upload_id, 1, "chunkhash1")
    
    # 3. Verify Indices
    indices = db.get_uploaded_chunk_indices(upload_id)
    assert len(indices) == 2
    assert 0 in indices
    assert 1 in indices
    
    # 4. Test Idempotency (adding same chunk shouldn't crash)
    db.add_uploaded_chunk(upload_id, 0, "chunkhash0")
    indices_after = db.get_uploaded_chunk_indices(upload_id)
    assert len(indices_after) == 2