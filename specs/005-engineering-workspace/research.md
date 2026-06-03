# Research: Engineering Workspace

This document records the research, decisions, and architectural rationales for the Engineering Workspace implementation, focusing on Git integration, file operations, remote sync, and performance.

## 1. Git CLI Integration

### Decision
Use the standard system `git` CLI invoked via Python's `subprocess` (specifically `asyncio.create_subprocess_exec` for non-blocking I/O) rather than introducing external Python Git wrappers (like `GitPython` or `pygit2`).

### Rationale
- **Zero-Dependency Policy**: Utilizing the pre-installed `git` CLI on the GB10 host (Assumption A-001) avoids importing heavy compiled packages, keeping the dependencies minimal and maintaining portability.
- **Async Execution**: `asyncio.create_subprocess_exec` prevents blocking the main FastAPI event loop during heavy operations like git clone, pull, or commit.
- **Reliability**: Direct CLI invocation uses the OS-level Git configurations, SSH keys, and credentials natively.

### Alternatives Considered
- **GitPython**: Rejected because it is a synchronous library (blocks the event loop) and has been known to leave file handles open or leak memory on large operations.
- **pygit2 / libgit2**: Rejected due to complex compilation requirements in the Docker image, violating the fast iteration and thin-code container strategy.

---

## 2. Workspace Status Calculation

### Decision
Calculate file statuses by running `git status --porcelain` inside the active workspace directory. Map porcelain status characters to a standard workspace status set:
- `M ` or ` M` -> Modified (`M`)
- `A ` or ` A` -> Added (`A`)
- `D ` or ` D` -> Deleted (`D`)
- `??` -> Untracked (`U`)
- Clean files -> (`Clean`)

Integrate these statuses directly into the hierarchical tree returned by `get_workspace_tree()`.

### Rationale
- `git status --porcelain` is specifically designed for script parsing. It has a stable, machine-readable format that does not change across Git versions or user locales.
- Combining file tree construction and status checking in a single call ensures the VS Code Explorer tree matches file state instantly.

### Alternatives Considered
- **Running `git status` text parser**: Rejected as it is highly fragile, localized, and prone to breaking changes.
- **Separate status API endpoint**: Rejected because fetching tree and status in separate HTTP requests would create layout shifting/latency in the tree rendering.

---

## 3. Diff View and Revert Logic

### Decision
- **Unified Diff**: Expose `/api/workspace/git/diff` endpoint which executes `git diff --no-color <file>` (for modified files) or `git diff --no-color /dev/null <file>` (for untracked files).
- **Reversion**: Expose `/api/workspace/git/revert` which executes `git checkout HEAD -- <file>` or deletes the file if it is untracked.
- **UI Rendering**: Render the diff in `apps/web` using standard styled lines (green for additions, red for deletions, grey for unchanged lines) modeled after VS Code.

### Rationale
- Using native git diffing keeps logic simple and leverages standard diff formatting.
- Reverting via `git checkout HEAD` is extremely fast and robust.

---

## 4. Remote Git Configuration & Security

### Decision
Add an `engineering_workspaces` table to the SQLite database.
Store:
- `workspace_id` (PRIMARY KEY)
- `session_id` (UNIQUE, INDEXED)
- `local_path`
- `git_remote_url`
- `git_username` (Null or encrypted)
- `git_token` (Encrypted or Null)

For Git authentication, use HTTP Basic authentication embedded in the remote URL (e.g., `https://<username>:<token>@github.com/...`) during operations, using credential redaction in all logging.

### Rationale
- SQLite WAL mode provides high concurrency for local sessions.
- Embedding credentials during the command execution (without saving them to `.git/config` on disk) prevents leaking credentials in the project directory.

### Alternatives Considered
- **Saving tokens in `.git/config`**: Rejected because config files are easily committed or read by other processes.
- **SSH Key management**: Rejected for simplicity in initial version, as HTTPS tokens are easier to configure on options pages for GitHub.

---

## 5. Large File Handling (Git LFS and `.gitignore`)

### Decision
- On workspace initialization, auto-create a `.gitignore` that ignores log files (`*.log`), solver temporary files (`*.solver`, `*.tmp`), and directory caches.
- Restrict tracking of files larger than 50MB by default, returning a warning to the user, and recommending the use of Git LFS if large STL/STEP files must be tracked.

### Rationale
- Prevents bloat and slow commits.
- Ensures the local Git repository remains highly performant.
