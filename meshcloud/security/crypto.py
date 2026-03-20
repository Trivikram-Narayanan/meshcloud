import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Default salt for KDF
SALT = b'meshcloud_static_salt'

# Cache for derived key
_CACHED_KEY = None
_CACHED_SEED = None

def get_key():
    """Derive a 32-byte key using PBKDF2 with SHA256 and cache it."""
    global _CACHED_KEY, _CACHED_SEED
    
    seed = os.environ.get("STORAGE_ENCRYPTION_KEY", "default-insecure-key")
    
    if _CACHED_KEY and seed == _CACHED_SEED:
        return _CACHED_KEY
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000
    )
    key = kdf.derive(seed.encode())
    
    _CACHED_KEY = key
    _CACHED_SEED = seed
    
    return _CACHED_KEY

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data using AES-GCM. Returns nonce + ciphertext + tag."""
    aesgcm = AESGCM(get_key())
    nonce = os.urandom(12)
    # Returns nonce (12) + ciphertext + tag (16)
    return nonce + aesgcm.encrypt(nonce, data, None)

def decrypt_data(data: bytes) -> bytes:
    """Decrypt data using AES-GCM. Expects nonce + ciphertext + tag."""
    if len(data) < 28:  # 12 (nonce) + 16 (tag)
        raise ValueError("Data too short for decryption")
    
    aesgcm = AESGCM(get_key())
    nonce = data[:12]
    ciphertext = data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)

def get_streaming_encryptor(nonce: bytes):
    """Return a hazmat ciphers encryptor for AES-GCM."""
    cipher = Cipher(algorithms.AES(get_key()), modes.GCM(nonce), backend=default_backend())
    return cipher.encryptor()

def get_streaming_decryptor(nonce: bytes, tag: bytes):
    """Return a hazmat ciphers decryptor for AES-GCM."""
    cipher = Cipher(algorithms.AES(get_key()), modes.GCM(nonce, tag), backend=default_backend())
    return cipher.decryptor()