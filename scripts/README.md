# Wright Developer & Utility Scripts

This directory contains helper scripts to automate local development, manage Docker container environments, perform database cleanups, patch submodules, and run developer diagnostics.

## Script Index

| Script | Language | Purpose | Key Dependencies |
| :--- | :--- | :--- | :--- |
| [`backup-volumes.sh`](#backup-volumessh) | Bash | Backs up Wright Docker volumes to local disk | Docker |
| [`restore-volume.sh`](#restore-volumesh) | Bash | Restores a Docker volume from a saved backup | Docker |
| [`cleanup-workspaces.py`](#cleanup-workspacespy) | Python | Truncates database tables and cleans workspace directories | Python 3, SQLite |
| [`check-public-alpha-leaks.py`](#check-public-alpha-leakspy) | Python | Scans tracked text files for obvious public-alpha secret leaks | Python 3, Git |
| [`docker-smoke-test.sh`](#docker-smoke-testsh) | Bash | Validates Docker build, permissions, and self-healing behaviors | Docker |
| [`fetch_ci_failures.py`](#fetch_ci_failurespy) | Python | Retrieves logs of failed GitHub Action runs to a local markdown file | Python 3, `gh` CLI |
| [`openscad-headless.sh`](#openscad-headlesssh) | Bash | Runs OpenSCAD headlessly inside containerized environments | `xvfb-run`, OpenSCAD |
| [`patch-submodule.sh`](#patch-submodulesh) | Bash | Applies localized patches to the FreeCAD MCP submodule | Git |
| [`setup-wright-profile.sh`](#setup-wright-profilesh) | Bash | Provisions and configures a Hermes profile for native Wright development | `hermes` CLI |

---

### `backup-volumes.sh`

Backs up the stateful data stored inside Wright's Docker volumes to prevent data loss.

* **Target Volumes**: `wright_home`, `wright_local`, `wright_opt`, `wright_varlib`, `wright_varcache`, `wright_etc`, `wright_logs`
* **Backup Destination**: `/backups/wright-volumes/<timestamp>/` (falls back to `<repo_root>/backups/wright-volumes/` if the root `/backups` directory is not writable on the host).
* **Retention Policy**: Retains the last 7 days of backups and automatically prunes directories older than 7 days.
* **Usage**:
  ```bash
  ./scripts/backup-volumes.sh
  ```

---

### `restore-volume.sh`

Restores a specific Wright Docker volume from a previously generated backup.

> [!WARNING]
> This script will automatically stop the running Docker Compose stack (detecting either production or test environments) to avoid database corruption or file lock conflicts during the restore process. It restarts the containers once complete.

* **Arguments**: `<volume_name> <backup_timestamp_or_date>`
* **Usage**:
  ```bash
  # Example: Restore the home volume from a backup on June 24th, 2026
  ./scripts/restore-volume.sh wright_home 2026-06-24-18-00
  ```

---

### `cleanup-workspaces.py`

Resets the active developer environment by purging generated engineering workspaces and database tables.

* **Database Actions**: Truncates the `engineering_workspaces`, `agent_contexts`, and `chat_messages` tables from `state.db` (or from the database configured in the `DATABASE_PATH` environment variable).
* **Disk Actions**:
  - Deletes all workspace directories pointed to by the truncated database records.
  - Recursively cleans all subdirectories under `~/workspace` and `~/wright` (excluding hidden directories).
* **Usage**:
  ```bash
  uv run python scripts/cleanup-workspaces.py
  ```

---

### `check-public-alpha-leaks.py`

Scans tracked repository text files for obvious public-alpha leaks such as
private key headers, OpenAI-style keys, GitHub tokens, and generic
secret/token/password assignments. Documented placeholders such as
`sk-your-key-here`, `${{ secrets.NAME }}`, and `wright-dev-key` are ignored.

* **CI usage**:
  ```bash
  python scripts/check-public-alpha-leaks.py
  ```
* **Local pre-launch usage**:
  ```bash
  python scripts/check-public-alpha-leaks.py --include-untracked
  ```

This is a fast guardrail, not a substitute for a full history scan with a
dedicated tool such as `gitleaks` or `trufflehog`.

---

### `docker-smoke-test.sh`

Runs a local verification suite against a production Docker build to ensure environment configuration compliance, secure file permissions, and self-healing.

* **Key Checks**:
  1. Builds the Docker image locally as `wright-agent:test`.
  2. Asserts that the container user runs as the non-root `agent` user by default.
  3. Verifies that the `/container-manifest.md` is present and has read-only `444` permissions.
  4. Verifies that `/entrypoint.sh` is present and executable.
  5. Validates fail-fast rules (fails if `LLM_API_URL` is missing, succeeds if provided).
  6. Validates container recovery paths (ephemeral write checks and entrypoint shell bypasses).
* **Usage**:
  ```bash
  ./scripts/docker-smoke-test.sh
  ```

---

### `fetch_ci_failures.py`

Fetches GitHub Actions workflow failure details and aggregates the logs locally into a Markdown report (`ci_failures.md`). This allows for quick, local troubleshooting without manually digging through the GitHub UI.

* **Requirements**: Must have the GitHub CLI (`gh`) installed and configured (it will attempt to auto-discover your GitHub token using `git credential fill`).
* **Arguments**:
  - `--branch <name>`: Restrict logs to a specific branch (defaults to the currently checked-out Git branch).
  - `--all`: Fetch failed runs from all branches.
  - `--limit <number>`: Maximum number of failed runs to fetch (default is 5).
  - `--output <path>`: Output filepath (default is `ci_failures.md`).
* **Usage**:
  ```bash
  # Fetch failures for the current branch
  uv run python scripts/fetch_ci_failures.py
  
  # Fetch failures across all branches and save to a custom file
  uv run python scripts/fetch_ci_failures.py --all --limit 3 --output build_errors.md
  ```

---

### `openscad-headless.sh`

A lightweight wrapper script that launches OpenSCAD headlessly inside containerized and remote Linux environments. It leverages `xvfb-run` to spin up a temporary X virtual framebuffer, satisfying OpenSCAD's requirement for a windowing display.

* **Usage**:
  ```bash
  ./scripts/openscad-headless.sh -o output.png input.scad
  ```

---

### `patch-submodule.sh`

Applies localized fixes to the `packages/freecad_mcp` submodule. It ensures the submodule is in a clean state (no local changes) before attempting to apply `scripts/freecad_mcp.patch`.

* **Usage**:
  ```bash
  ./scripts/patch-submodule.sh
  ```

---

### `setup-wright-profile.sh`

Provisions a custom, dedicated configuration profile named `wright` inside the local Hermes client and spins up its API gateway.

* **Configuration Set**:
  - `API_SERVER_ENABLED=true`
  - `API_SERVER_KEY=wright-dev-key`
  - `API_SERVER_PORT=8642`
* **Workflow**:
  1. Verifies the `hermes` CLI is installed.
  2. Clones the default Hermes profile into a new `wright` profile if it does not already exist.
  3. Set profile configuration keys.
  4. Starts the Hermes profile gateway and polls the health endpoint (`http://127.0.0.1:8642/health`) to ensure it boots successfully.
* **Usage**:
  ```bash
  ./scripts/setup-wright-profile.sh
  ```
