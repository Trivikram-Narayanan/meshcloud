#!/usr/bin/env bash
# =============================================================================
# MeshCloud Certificate & Key Generator
# Run this ONCE during initial setup. Never commit the generated files.
# =============================================================================
set -euo pipefail

echo "🔐 Generating MeshCloud TLS certificates and node keys..."

# --- TLS Self-Signed Certificate ---
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    echo "  ↳ Generating TLS certificate (cert.pem + key.pem)..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
        -days 365 -nodes \
        -subj "/CN=meshcloud-node/O=MeshCloud/C=US" \
        -addext "subjectAltName=IP:127.0.0.1,DNS:localhost"
    echo "  ✅ cert.pem + key.pem generated"
else
    echo "  ⚠️  cert.pem / key.pem already exist, skipping."
fi

# --- Node Signing Keypair (Ed25519) ---
if [ ! -f "node_key.pem" ] || [ ! -f "node_pub.pem" ]; then
    echo "  ↳ Generating node Ed25519 signing keypair..."
    python3 - <<'PYEOF'
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption
)

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

with open("node_key.pem", "wb") as f:
    f.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))

with open("node_pub.pem", "wb") as f:
    f.write(public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))

print("  ✅ node_key.pem + node_pub.pem generated")
PYEOF
else
    echo "  ⚠️  node_key.pem / node_pub.pem already exist, skipping."
fi

echo ""
echo "✅ Done! The following files were created (NEVER commit them):"
echo "   cert.pem  - TLS certificate"
echo "   key.pem   - TLS private key"
echo "   node_key.pem - Ed25519 node signing key"
echo "   node_pub.pem - Ed25519 node public key"
echo ""
echo "💡 Set STORAGE_ENCRYPTION_KEY in your .env file before starting nodes."
