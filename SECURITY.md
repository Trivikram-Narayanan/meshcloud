# Security

## Files that must never be committed

The following are already in `.gitignore` — do not force-add them.

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

All secrets must be passed via environment variables. MeshCloud will log a startup warning if any of these are missing or set to their insecure defaults.

| Variable | How to generate | Default (INSECURE) |
|---|---|---|
| `STORAGE_ENCRYPTION_KEY` | `openssl rand -hex 32` | `default-insecure-key` — warns at startup |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` | Random per-restart — all sessions lost on restart |
| `ADMIN_PASSWORD` | any strong password | `admin` — warns at startup |
| `MESH_NODE_TOKEN` | `openssl rand -hex 32` | Unset — inter-node requests are unauthenticated |

## Production checklist

- [ ] `STORAGE_ENCRYPTION_KEY` set to a strong random value
- [ ] `JWT_SECRET_KEY` set to a stable secret (tokens survive restarts)
- [ ] `ADMIN_PASSWORD` changed from default
- [ ] `MESH_NODE_TOKEN` set and the same across all nodes
- [ ] TLS enabled in front of all nodes (nginx, Caddy, or `SSL_CERT_FILE` / `SSL_KEY_FILE`)
- [ ] PostgreSQL used instead of SQLite for multi-node deployments (`DATABASE_URL=postgresql://...`)
- [ ] `CORS_ORIGINS` restricted to your actual frontend origin (not `*`)

## Reporting vulnerabilities

Please report security issues **privately** — do not open a public GitHub issue.

Email the maintainer directly or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability).
