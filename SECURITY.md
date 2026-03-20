# Security Guidelines

## ⚠️ Never Commit These Files

The following files must **never** be committed to git. They are already in `.gitignore`.

| File | Contents |
|------|----------|
| `cert.pem` | TLS certificate |
| `key.pem` | TLS private key |
| `node_key.pem` | Ed25519 node signing private key |
| `node_pub.pem` | Ed25519 node signing public key |
| `*.db`, `*.sqlite` | Local database files |

Run `generate_certs.sh` to generate them locally:

```bash
chmod +x generate_certs.sh && ./generate_certs.sh
```

## Environment Variables

All secrets must be passed via environment variables:

| Variable | Description | Default (INSECURE) |
|----------|-------------|-------------------|
| `STORAGE_ENCRYPTION_KEY` | Fernet key for at-rest encryption | `meshcloud_insecure_dev_key` |
| `JWT_SECRET_KEY` | JWT signing secret | Random (ephemeral) |
| `NODE_TOKEN` | Inter-node auth token | `meshcloud_secret_token` |
| `DATABASE_URL` | SQLAlchemy database URL | SQLite default |

## Production Checklist

- [ ] Set `STORAGE_ENCRYPTION_KEY` to a strong random value (`python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- [ ] Set `JWT_SECRET_KEY` to a random 256-bit value
- [ ] Set `NODE_TOKEN` to a strong random token shared across nodes
- [ ] Use `VERIFY_SSL=true` with valid TLS certs in production
- [ ] Replace SQLite with PostgreSQL (`DATABASE_URL=postgresql://...`) for multi-node deployments
- [ ] Use `REPLICATION_FACTOR=3` for production durability

## Reporting Vulnerabilities

Please report security issues privately via email to the project maintainer. Do not open public issues for vulnerabilities.
