# Data Model: Agent Docker Container Setup

**Date**: 2026-06-04 | **Feature**: 010-agent-docker-setup

## Entities

### Docker Image (`wright-agent`)

| Attribute | Description |
|-----------|-------------|
| Base OS | Ubuntu 24.04 LTS |
| Python | 3.13 via system + uv |
| Node.js | 22 LTS (for frontend build) |
| CLI Tools | git, curl, wget, vim, nano, htop, jq, sudo, pipx, ca-certificates |
| Micromamba | Installed to `/usr/local/bin/micromamba` for conda-compatible packages |
| Agent User | `agent` with passwordless sudo and home at `/home/agent` |
| Manifest | `/container-manifest.md` (444 permissions, read-only) |
| Entrypoint | `/entrypoint.sh` (executable, exports manifest, logs startup) |
| Frontend | Pre-built Vite static files served by FastAPI `StaticFiles` |
| API Server | uvicorn running `api.main:app` on port 8000 |

### Named Volumes (7 total)

| Volume Name | Mount Path | Persistence | What It Preserves |
|-------------|-----------|-------------|-------------------|
| `wright_home` | `/home/` | ✅ Survives restart | Agent workspaces, user configs, `.local`, databases, backups |
| `wright_local` | `/usr/local/` | ✅ Survives restart | pip/pipx installs, compiled tools, local binaries, micromamba |
| `wright_opt` | `/opt/` | ✅ Survives restart | conda environments, self-contained app installs |
| `wright_varlib` | `/var/lib/` | ✅ Survives restart | apt package database, application state |
| `wright_varcache` | `/var/cache/` | ✅ Survives restart | apt package cache, downloaded archives |
| `wright_etc` | `/etc/` | ✅ Survives restart | System-wide config (⚠️ high-risk, backup first) |
| `wright_logs` | `/var/log/` | ✅ Survives restart | Persistent logs, change records, corruption reports |

### Ephemeral Paths (image layer, reset on restart)

| Path | Behavior |
|------|----------|
| `/bin`, `/sbin` | Reset to clean image state |
| `/usr/bin`, `/usr/sbin` | Reset to clean image state |
| `/usr/lib`, `/lib`, `/lib64` | Reset to clean image state |
| `/tmp`, `/run` | Reset to clean image state |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_URL` | Yes | LLM API endpoint URL |
| `LLM_API_KEY` | No | LLM API authentication key |
| `LLM_API_MODEL` | No | Default LLM model identifier |
| `WRIGHT_ENV` | No | Environment name (default: `production`) |
| `CONTAINER_MANIFEST` | Auto | Exported by entrypoint from `/container-manifest.md` |

### Backup Archives

| Attribute | Description |
|-----------|-------------|
| Location | `/backups/wright-volumes/<YYYY-MM-DD-HH-MM>/` on host |
| Format | `.tar.gz` per volume |
| Retention | 7 days (older auto-pruned) |
| Trigger | Nightly cron at 3:00 AM host time |

## State Transitions

### Container Lifecycle

```
[Image Built] → docker compose up → [Starting]
                                        ↓
                                   [entrypoint.sh]
                                   - Export CONTAINER_MANIFEST
                                   - Create /home/agent/.backups/etc
                                   - Log startup to /var/log/agent-startup.log
                                        ↓
                                   [Running / Healthy]
                                        ↓
                            docker compose restart → [Starting] (volumes persist)
                            docker compose down    → [Stopped]  (volumes persist)
                            docker volume rm       → [Data Lost] (volume deleted)
```

### Recovery Scenarios

```
Ephemeral Corruption  → docker compose restart        → Self-healing (< 1 min)
Broken /etc           → docker compose run --entrypoint bash → Manual fix (< 15 min)
Won't Start           → Rescue container with volumes attached → Inspect and repair
Cascading Corruption  → Selective volume restore from backup   → Targeted recovery
Deleted Work          → File restore from nightly backup       → Partial recovery
```
