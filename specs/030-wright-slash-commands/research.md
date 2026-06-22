# Research: Wright Slash Commands

This document records technical research, architectural decisions, and alternatives considered for implementing the `/wright` slash commands in the Hermes Wright plugin.

---

## 1. Background Process Management (Uvicorn Launcher)

### Decision
Use Python's standard `subprocess.Popen` module with `start_new_session=True` (on Unix systems) to launch the `uvicorn` FastAPI server in a detached background session.

### Rationale
- `start_new_session=True` makes the child process a session leader, preventing it from receiving signals (like `SIGHUP` or `SIGINT`) sent to the parent Hermes process.
- Detaching the process ensures the FastAPI server remains running even if the Hermes console/client is restarted or terminated.
- Executing via `sys.executable -m uvicorn api.main:app` uses the current Python environment directly, avoiding hardcoding the `uvicorn` executable path which might vary across virtual environments.

### Alternatives Considered
- **`os.fork`**: Too complex and platform-dependent; does not integrate cleanly with Python's modern subprocess monitoring.
- **Systemd / supervisord daemonization**: Not portable to developer local machines without root privileges or custom setups.

---

## 2. Frontend Stale Build Detection

### Decision
Implement a timestamp comparison scan in python. If `apps/web/dist/` does not exist, the build is considered stale. If it exists, recursively walk `apps/web/src/` to compare modification times (`mtime`) against the newest file in `apps/web/dist/`.

### Rationale
- Prevents redundant, time-consuming frontend builds on every `/wright start` invocation.
- Keeps execution fast (< 10ms check) while ensuring the frontend is fully updated if the user pulled changes or modified frontend source code.

### Alternatives Considered
- **Building on every launch**: Takes 10-20 seconds per start, resulting in a poor user experience.
- **Hash comparison (sha256/md5 of src files)**: Provides similar accuracy but requires reading file contents, which is slower than reading directory metadata/timestamps.

---

## 3. Graceful Process Termination (`/wright stop`)

### Decision
Read the stored process ID (PID) from `repo/tmp/wright-api.pid`. Propagate `SIGTERM` to the process via `os.kill(pid, signal.SIGTERM)`. Implement a 5-second polling loop checking `os.kill(pid, 0)` (checking process existence) to ensure termination before cleaning up the PID file.

### Rationale
- `SIGTERM` allows FastAPI/uvicorn to run its shutdown handlers and release socket ports cleanly.
- Checking for process exit over a 5-second window prevents port binding conflicts if the server is restarted immediately after a stop command.

### Alternatives Considered
- **`SIGKILL` (kill -9)**: Does not allow cleanup handlers or socket release, causing immediate resource leaks.
- **Checking process name lists (psutil)**: Adds an external dependency where standard library `os.kill` is sufficient.

---

## 4. Environment Diagnostics Checks (`/wright doctor`)

### Decision
Run sequential diagnostic checks utilizing standard libraries and bridge client endpoints:
- Repository discovery: verify path via `bridge.detect_repo_dir()`.
- API Health: verify via GET `/api/health`.
- Frontend status: verify existence of `apps/web/dist/index.html`.
- Database status: verify SQLite DB file exists.
- Secrets security: verify file permission settings using `os.stat().st_mode & 0o777`.
- Credentials check: query credential status via GET `/api/mcp/servers/{id}/credentials` to count missing keys.

### Rationale
- Covers all critical configurations that could prevent the application stack from working properly.
- Protects credential values by only querying whether keys are configured/missing, without returning actual values.
