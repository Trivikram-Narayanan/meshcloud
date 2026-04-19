import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.pool import QueuePool

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
Base = declarative_base()

class Settings(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)


def get_node_id():
    """Get or generate a persistent unique ID for this node."""
    # Check env var first
    env_id = os.getenv("NODE_ID")
    if env_id:
        return env_id
    
    # Check persistent file in storage dir
    os.makedirs(STORAGE_DIR, exist_ok=True)
    id_file = os.path.join(STORAGE_DIR, "node_id")
    
    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            return f.read().strip()
    
    # Generate new ID
    import uuid
    new_id = str(uuid.uuid4())
    with open(id_file, "w") as f:
        f.write(new_id)
    return new_id

# Per-node DB: isolate each node's data
NODE_ID = get_node_id()
_node_id_safe = NODE_ID.replace("/", "_").replace(":", "_")
_db_filename = f"meshcloud_{_node_id_safe}.db"
DB_PATH = os.path.join(STORAGE_DIR, _db_filename)

# Database URL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Configure Engine based on DB Type
# More robust engine creation
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        # For SQLite, we don't need pool_size/max_overflow and they might cause issues if too many connections
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        poolclass=QueuePool
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _create_default_admin_user():
    """Create default admin user if it doesn't exist"""
    from argon2 import PasswordHasher
    from loguru import logger
    
    admin_username = "admin"
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    # Check if admin user already exists
    with SessionLocal() as db:
        existing_admin = db.query(User).filter(User.username == admin_username).first()
        if existing_admin:
            return  # Admin user already exists
    
    # Create admin user if password is set
    if admin_password:
        ph = PasswordHasher()
        hashed_password = ph.hash(admin_password)
        create_user(
            username=admin_username,
            hashed_password=hashed_password,
            full_name="Administrator",
            email="admin@meshcloud.local"
        )
        logger.info(f"✓ Default admin user created")
    else:
        logger.warning(
            "⚠️  ADMIN_PASSWORD not set. Skipping default admin user creation. "
            "Use /register endpoint to create users."
        )


# --- Database Models ---

class File(Base):
    __tablename__ = "files"
    hash = Column(String, primary_key=True)
    original_filename = Column(String)
    created_at = Column(DateTime(timezone=True), default=func.now())
    owner = Column(String, nullable=True, index=True)


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    upload_id = Column(String, primary_key=True)
    filename = Column(String)
    total_chunks = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=func.now())


class UploadedChunk(Base):
    __tablename__ = "uploaded_chunks"
    upload_id = Column(String, primary_key=True)
    chunk_index = Column(Integer, primary_key=True)
    chunk_hash = Column(String)


class SyncQueue(Base):
    __tablename__ = "sync_queue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String)
    peer = Column(String)
    retry_count = Column(Integer, default=0)
    status = Column(String, default='pending')
    created_at = Column(DateTime(timezone=True), default=func.now())


class PeerStatus(Base):
    __tablename__ = "peer_status"
    peer = Column(String, primary_key=True)
    node_id = Column(String, nullable=True)
    online = Column(Integer, default=0)
    last_seen = Column(DateTime(timezone=True), default=func.now())


class FileChunk(Base):
    __tablename__ = "file_chunks"
    file_hash = Column(String, primary_key=True)
    chunk_index = Column(Integer, primary_key=True)
    chunk_hash = Column(String)


class FileIndex(Base):
    __tablename__ = "file_index"
    file_hash = Column(String, primary_key=True)
    node = Column(String, primary_key=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    disabled = Column(Integer, default=0)


class Chunk(Base):
    __tablename__ = "chunks"
    HASH = Column(String, primary_key=True)
    chunk_index = Column(Integer, primary_key=True)
    chunk_hash = Column(String)


# --- Operations ---


def init_db():
    # Ensure the directory for the database
    if DB_PATH:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Enable WAL mode for better concurrency in SQLite
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()

    # Migrate: add owner column to existing databases that predate this feature
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE files ADD COLUMN owner VARCHAR"))
            conn.commit()
    except Exception:
        pass  # Column already exists — normal on fresh or already-migrated DBs

    # Create default admin user if it doesn't exist
    _create_default_admin_user()


def add_sync_task(file_hash, peer):
    with SessionLocal() as db:
        task = SyncQueue(file_hash=file_hash, peer=peer)
        db.add(task)
        db.commit()


def store_file_chunks(file_hash, chunks):
    with SessionLocal() as db:
        for i, ch in enumerate(chunks):
            # Check existence first to emulate INSERT OR IGNORE logic
            exists = db.query(FileChunk).filter_by(file_hash=file_hash, chunk_index=i).first()
            if not exists:
                db.add(FileChunk(file_hash=file_hash, chunk_index=i, chunk_hash=ch))
        db.commit()


def get_file_locations(file_hash):
    with SessionLocal() as db:
        results = db.query(FileIndex.node).filter(FileIndex.file_hash == file_hash).all()
        return [r[0] for r in results]


def get_file_chunks(file_hash):
    with SessionLocal() as db:
        results = db.query(FileChunk.chunk_hash)\
            .filter(FileChunk.file_hash == file_hash)\
            .order_by(FileChunk.chunk_index)\
            .all()
        return [r[0] for r in results]


def get_filename(file_hash):
    with SessionLocal() as db:
        file_record = db.query(File).filter(File.hash == file_hash).first()
        return file_record.original_filename if file_record else None


def file_exists(file_hash):
    with SessionLocal() as db:
        return db.query(File.hash).filter(File.hash == file_hash).first() is not None


def insert_file(file_hash, filename, owner=None):
    with SessionLocal() as db:
        file_record = File(
            hash=file_hash,
            original_filename=filename,
            created_at=datetime.now(timezone.utc),
            owner=owner,
        )
        db.merge(file_record)
        db.commit()


def get_all_files(limit=100):
    """Return all files — used internally for replication and peer operations."""
    with SessionLocal() as db:
        return db.query(File).order_by(File.created_at.desc()).limit(limit).all()


def get_files_by_owner(username: str, limit: int = 100):
    """Return only files owned by a specific user — used for dashboard listings."""
    with SessionLocal() as db:
        return (
            db.query(File)
            .filter(File.owner == username)
            .order_by(File.created_at.desc())
            .limit(limit)
            .all()
        )


def get_all_peers():
    with SessionLocal() as db:
        results = db.query(PeerStatus.peer).all()
        return [r[0] for r in results]


def add_peer(peer_url, node_id=None, online=0):
    session = SessionLocal()
    try:
        peer = session.query(PeerStatus).filter(PeerStatus.peer == peer_url).first()
        if not peer:
            peer = PeerStatus(peer=peer_url, node_id=node_id, online=online)
            session.add(peer)
        else:
            if node_id:
                peer.node_id = node_id
            peer.online = 1
            peer.last_seen = func.now()
        session.commit()
    finally:
        session.close()


def update_peer_status(peer_url, online, node_id=None):
    session = SessionLocal()
    try:
        peer = session.query(PeerStatus).filter(PeerStatus.peer == peer_url).first()
        if peer:
            peer.online = 1 if online else 0
            if node_id:
                peer.node_id = node_id
            peer.last_seen = func.now()
            session.commit()
        elif online:
            # If we see a peer online but they aren't in DB, add them
            add_peer(peer_url, node_id)
    finally:
        session.close()


def is_peer_online(peer):
    with SessionLocal() as db:
        peer_record = db.query(PeerStatus).filter(PeerStatus.peer == peer).first()
        return peer_record and peer_record.online == 1


def create_upload_session(upload_id, filename, total_chunks):
    with SessionLocal() as db:
        session = UploadSession(upload_id=upload_id, filename=filename, total_chunks=total_chunks)
        db.add(session)
        db.commit()


def get_uploaded_chunk_indices(upload_id):
    with SessionLocal() as db:
        results = db.query(UploadedChunk.chunk_index).filter(UploadedChunk.upload_id == upload_id).all()
        return [r[0] for r in results]


def add_uploaded_chunk(upload_id, chunk_index, chunk_hash):
    with SessionLocal() as db:
        exists = db.query(UploadedChunk).filter_by(upload_id=upload_id, chunk_index=chunk_index).first()
        if not exists:
            db.add(UploadedChunk(upload_id=upload_id, chunk_index=chunk_index, chunk_hash=chunk_hash))
            db.commit()


def get_pending_sync_tasks(limit=10):
    with SessionLocal() as db:
        results = db.query(SyncQueue.id, SyncQueue.file_hash, SyncQueue.peer, SyncQueue.retry_count)\
            .filter(SyncQueue.status == 'pending')\
            .limit(limit)\
            .all()
        return results


def update_sync_job_status(task_id, status):
    with SessionLocal() as db:
        db.query(SyncQueue).filter(SyncQueue.id == task_id).update({"status": status})
        db.commit()


def increment_sync_retry(task_id):
    with SessionLocal() as db:
        # Use synchronization to avoid race conditions on retry count
        db.query(SyncQueue).filter(SyncQueue.id == task_id).update(
            {"retry_count": SyncQueue.retry_count + 1},
            synchronize_session=False
        )
        db.commit()


def register_file_location(file_hash, node):
    with SessionLocal() as db:
        exists = db.query(FileIndex).filter_by(file_hash=file_hash, node=node).first()
        if not exists:
            db.add(FileIndex(file_hash=file_hash, node=node))
            db.commit()


def get_user_by_username(username):
    with SessionLocal() as db:
        return db.query(User).filter(User.username == username).first()


def has_users() -> bool:
    with SessionLocal() as db:
        return db.query(User).limit(1).count() > 0


def create_user(username, hashed_password, full_name=None, email=None):
    with SessionLocal() as db:
        user = User(
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
