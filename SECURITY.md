# Security

## Files that must never be committed

The following are already in `.gitignore` and must not be force-added.

| File | Contents |
|---|---|
| `cert.pem` / `key.pem` | TLS certificate and private key |
| `node_key.pem` / `node_pub.pem` | Ed25519 node signing keys |
| `*.db` / `*.sqlite` / `*.db-shm` / `*.db-wal` | Local database files |
| `.env` | Runtime secrets |

Run `generate_certs.sh` to create TLS certs locally:

```bash
chmod +x generate_certs.sh && ./generate_certs.sh
```

## Required environment variables

All secrets must be passed via environment variables. MeshCloud logs a startup warning if any of these are missing or set to insecure defaults.

| Variable | How to generate | Default (INSECURE) |
|---|---|---|
| `STORAGE_ENCRYPTION_KEY` | `openssl rand -hex 32` | `default-insecure-key` |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` | Random per restart; all sessions are invalidated on restart |
| `ADMIN_PASSWORD` | any strong password | `admin` |
| `MESH_NODE_TOKEN` | `openssl rand -hex 32` | Unset; inter-node requests are unauthenticated |

## Production checklist

- [ ] `STORAGE_ENCRYPTION_KEY` set to a strong random value
- [ ] `JWT_SECRET_KEY` set to a stable secret
- [ ] `ADMIN_PASSWORD` changed from the default
- [ ] `MESH_NODE_TOKEN` set and shared across all nodes
- [ ] TLS enabled in front of all nodes
- [ ] PostgreSQL used instead of SQLite for multi-node deployments
- [ ] `CORS_ORIGINS` restricted to the actual frontend origin

## Reporting vulnerabilities

Report security issues privately. Do not open a public GitHub issue.

Contact the maintainer directly or use GitHub's private vulnerability reporting:
https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability
