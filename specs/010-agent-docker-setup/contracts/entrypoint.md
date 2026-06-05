# Contract: Container Entrypoint

**Date**: 2026-06-04 | **Feature**: 010-agent-docker-setup

## Script: `/entrypoint.sh`

### Preconditions

- Container has started from the `wright-agent` image
- `/container-manifest.md` exists with 444 permissions
- Environment variables `LLM_API_URL` (required), `LLM_API_KEY`, `LLM_API_MODEL` are set via `.env`

### Execution Steps

```
1. Print startup banner with LLM_API_URL and timestamp
2. Validate LLM_API_URL is set (fail fast with error if missing)
3. Export CONTAINER_MANIFEST=$(cat /container-manifest.md)
4. Create /home/agent/.backups/etc (mkdir -p, idempotent)
5. Log startup event to /var/log/agent-startup.log
6. exec "$@" (default: uvicorn api.main:app --host 0.0.0.0 --port 8000)
```

### Postconditions

- `$CONTAINER_MANIFEST` environment variable is set and non-empty
- `/home/agent/.backups/etc` directory exists
- `/var/log/agent-startup.log` contains a new timestamped entry
- Main process (uvicorn) is running as PID 1 (via exec)

### Error Behavior

| Condition | Behavior |
|-----------|----------|
| `LLM_API_URL` not set | Print error to stderr, exit 1 |
| `/container-manifest.md` missing | Print warning, continue (CONTAINER_MANIFEST will be empty) |
| `/var/log` not writable | Print warning to stderr, continue |

### Health Check

```yaml
healthcheck:
  test: ["CMD", "test", "-f", "/var/log/agent-startup.log"]
  interval: 60s
  timeout: 10s
  retries: 3
  start_period: 30s
```
