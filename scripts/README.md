# Wright Developer & Utility Scripts

This directory contains helper scripts to automate local development, manage Docker container environments, perform database cleanups, patch submodules, and run developer diagnostics.

## Script Index

| Script | Language | Purpose | Key Dependencies |
| :--- | :--- | :--- | :--- |
| [`backup-volumes.sh`](#backup-volumessh) | Bash | Backs up Wright Docker volumes to local disk | Docker |
| [`restore-volume.sh`](#restore-volumesh) | Bash | Restores a Docker volume from a saved backup | Docker |
| [`alpha-release-check.sh`](#alpha-release-checksh-and-alpha-release-checkps1) / [`alpha-release-check.ps1`](#alpha-release-checksh-and-alpha-release-checkps1) | Bash / PowerShell | Runs the full local alpha release gate | Python 3, uv, npm, Docker |
| [`check-dev-merge.sh`](#check-dev-mergesh) | Bash | Runs the CI-equivalent gate before merging a feature branch to `dev` | Python 3, uv, npm, Playwright |
| [`check-prod-merge.sh`](#check-prod-mergesh) | Bash | Runs the release gate before merging `dev` to `main` | Python 3, uv, npm, Docker, Hermes |
| [`cleanup-workspaces.py`](#cleanup-workspacespy) | Python | Truncates database tables and cleans workspace directories | Python 3, SQLite |
| [`check-public-alpha-leaks.py`](#check-public-alpha-leakspy) | Python | Scans tracked text files for obvious public-alpha secret leaks | Python 3, Git |
| [`security-scan.sh`](#security-scansh-and-security-scanps1) / [`security-scan.ps1`](#security-scansh-and-security-scanps1) | Bash / PowerShell | Runs public-alpha, Gitleaks, and TruffleHog secret scans | Python 3, Docker |
| [`docker-smoke-test.sh`](#docker-smoke-testsh) | Bash | Validates Docker build, permissions, and self-healing behaviors | Docker |
| [`test-hermes-plugin-install.sh`](#hermes-plugin-lifecycle-scripts) / [`test-hermes-plugin-uninstall.sh`](#hermes-plugin-lifecycle-scripts) / [`test-hermes-plugin-update.sh`](#hermes-plugin-lifecycle-scripts) | Bash | Validates Hermes plugin install, uninstall, and update paths in Docker | Docker |
| [`production-update.sh`](#production-updatesh) | Bash | Guards operator-run production updates against stale, dirty, or unverified commits | Git, Docker, optional `gh` CLI |
| [`fetch_ci_failures.py`](#fetch_ci_failurespy) | Python | Retrieves logs of failed GitHub Action runs to a local markdown file | Python 3, `gh` CLI |
| [`openscad-headless.sh`](#openscad-headlesssh) | Bash | Runs OpenSCAD headlessly inside containerized environments | `xvfb-run`, OpenSCAD |
| [`patch-submodule.sh`](#patch-submodulesh) | Bash | Applies localized patches to the FreeCAD MCP submodule | Git |
| [`setup-wright-profile.sh`](#setup-wright-profilesh) | Bash | Provisions and configures a Hermes profile for native Wright development | `hermes` CLI |

---


### `check-dev-merge.sh`

Runs the heavyweight local gate before merging a feature branch to `dev`. It is
intended to mirror the checks that have previously caught branch integration
drift in CI:

1. `git diff --check`
2. Ruff lint and format checks for Wright-owned Python workspaces
3. ESLint, Prettier, TypeScript, Vitest, and frontend build checks
4. mypy in the same warning mode used by CI
5. Python package metadata dry-run validation
6. Backend pytest and Hermes plugin pytest
7. Strict docs build
8. Playwright with `PLAYWRIGHT_INCLUDE_LIVE=1` against a temporary local API database

* **Usage**:
  ```bash
  scripts/check-dev-merge.sh
  make check-dev-merge
  ```

Set `SKIP_PLAYWRIGHT=1` only for a documented local browser/runtime limitation.

---

### `check-prod-merge.sh`

Runs the release-oriented gate before merging `dev` to `main`. It includes the
dev merge gate, public-alpha secret scans, alpha release checks, Docker smoke
coverage, Hermes plugin mirror validation, and Hermes plugin root lifecycle
validation.

* **Usage**:
  ```bash
  scripts/check-prod-merge.sh
  make check-prod-merge
  ```

Set `SKIP_HERMES_PLUGIN_LIFECYCLE=1` only for a documented local Docker/Hermes
limitation. Do not use skip switches to bypass real failures.

---

### `alpha-release-check.sh` and `alpha-release-check.ps1`

Runs the full local alpha release gate:

1. `git diff --check`
2. `uv run pytest`
3. `npm run test --workspace=apps/web`
4. `npm run build --workspace=apps/web`
5. `uv run --with mkdocs-material mkdocs build --strict`
6. `scripts/security-scan.* --include-untracked`
7. `scripts/docker-smoke-test.sh`

* **Bash usage**:
  ```bash
  scripts/alpha-release-check.sh
  ```
* **PowerShell usage**:
  ```powershell
  scripts/alpha-release-check.ps1
  ```

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
`sk-your-key-here`, `${{ secrets.NAME }}`, and `wright-local-dev-key-000000000000000000000000` are ignored.

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

### `security-scan.sh` and `security-scan.ps1`

Runs the full local public-alpha secret scanning gate:

1. `python scripts/check-public-alpha-leaks.py`
2. Gitleaks history scan with `ghcr.io/gitleaks/gitleaks:v8.30.1`
3. TruffleHog history scan with `ghcr.io/trufflesecurity/trufflehog:3.95.7`

The wrappers use Docker images, so Gitleaks and TruffleHog do not need to be
installed globally.

* **Bash usage**:
  ```bash
  scripts/security-scan.sh --include-untracked
  ```
* **PowerShell usage**:
  ```powershell
  scripts/security-scan.ps1 -IncludeUntracked
  ```

---

### `docker-smoke-test.sh`

Runs a local verification suite against a production Docker build to ensure environment configuration compliance, secure file permissions, and self-healing.

* **Key Checks**:
  1. Builds the Docker image locally as `wright-agent:test`.
  2. Asserts that the container user runs as the non-root `agent` user by default.
  3. Verifies that the `/container-manifest.md` is present and has read-only `444` permissions.
  4. Verifies that `/entrypoint.sh` is present and executable.
  5. Validates setup-pending behavior (warns and continues if `LLM_API_URL` is missing, succeeds when provided).
  6. Validates container recovery paths (ephemeral write checks and entrypoint shell bypasses).
* **Usage**:
  ```bash
  ./scripts/docker-smoke-test.sh
  ```
* **Smoke an existing image without rebuilding**:
  ```bash
  WRIGHT_DOCKER_IMAGE=wright-agent:latest WRIGHT_DOCKER_SKIP_BUILD=1 ./scripts/docker-smoke-test.sh
  ```

---

### Hermes Plugin Lifecycle Scripts

Validates the standard Hermes user-plugin lifecycle in a disposable Docker container with an isolated `HERMES_HOME`. These scripts exercise Hermes Git-managed plugin path under `~/.hermes/plugins`, not the plugin that is baked into the Wright Docker appliance with `uv pip install`.

* **Install path**:
  ```bash
  scripts/test-hermes-plugin-install.sh
  ```
* **Uninstall path**:
  ```bash
  scripts/test-hermes-plugin-uninstall.sh
  ```
* **Update path**:
  ```bash
  scripts/test-hermes-plugin-update.sh
  ```
* **Run all three**:
  ```bash
  make hermes-plugin-lifecycle-test
  ```

By default, the scripts use `WRIGHT_DOCKER_IMAGE=wright-agent:test` and install from the public Wright Git repository on the `dev` branch: `https://github.com/burhop/wright/tree/dev/hermes-plugin-wright`. Use `--ref main` or `WRIGHT_PLUGIN_REF=main` to test the main-branch customer path; the default is `dev`.

`test-hermes-plugin-update.sh` intentionally uses Hermes standard `plugins update`, which requires the installed plugin directory to be a Git checkout. This is why the script installs from GitHub instead of the local checkout. If Hermes still drops `.git` metadata for the `hermes-plugin-wright` subdirectory install, the script fails with that diagnosis so we can fix the distribution shape before users hit it.

Useful overrides:

```bash
WRIGHT_DOCKER_BUILD=1 scripts/test-hermes-plugin-install.sh
WRIGHT_DOCKER_IMAGE=wright-agent:latest WRIGHT_DOCKER_SKIP_BUILD=1 make hermes-plugin-lifecycle-test
scripts/test-hermes-plugin-update.sh --ref main
scripts/test-hermes-plugin-install.sh --identifier file:///wright-src#hermes-plugin-wright
WRIGHT_KEEP_TEST_HOME=1 scripts/test-hermes-plugin-uninstall.sh
```

---

### `production-update.sh`

Runs a guarded production update from a checked-out repository. It fetches
fresh refs, rejects dirty working trees by default, refuses to deploy stale
`origin/main`, verifies the checked-out commit matches the selected branch or
release tag, and checks required GitHub Actions when authenticated `gh` CLI
access is available.

* **Update from `origin/main`**:
  ```bash
  scripts/production-update.sh --pull
  ```
* **Deploy a release tag**:
  ```bash
  git checkout v0.1.0-alpha.1
  scripts/production-update.sh --ref v0.1.0-alpha.1
  ```

The script then runs `docker compose pull` and `docker compose up -d --build`
for `docker-compose.minimal.yml` unless another file is passed with
`--compose-file`.

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
  - `API_SERVER_KEY=wright-local-dev-key-000000000000000000000000`
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

### Hermes Plugin Mirror and Package Release Scripts

These helpers support the thin `hermes-plugin-wright` mirror and the PyPI/TestPyPI package publication path used by the Wright Hermes plugin.

| Script | Language | Purpose | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `build-python-distributions.sh` | Bash | Validates `wright-core` and `wright-tool-registry` package metadata, builds source/wheel artifacts, and optionally performs clean install/import checks | Python 3, `build`, pip |
| `sync-hermes-plugin-mirror.sh` | Bash | Exports only allowlisted plugin files from `hermes-plugin-wright/` into a root-level mirror directory and writes provenance | Git, Python 3 |
| `validate-hermes-plugin-mirror.sh` | Bash | Validates mirror required files, prohibited paths, README links, provenance, and dependency policy | Bash, Python 3 |

* Validate package metadata without building artifacts:
  ```bash
  scripts/build-python-distributions.sh --dry-run packages/core packages/tool_registry
  ```

* Preview mirror contents:
  ```bash
  scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --dry-run
  ```

* Generate and validate a local development mirror:
  ```bash
  tmp_dir=$(mktemp -d)
  scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --channel development --output-dir "$tmp_dir"
  scripts/validate-hermes-plugin-mirror.sh --mirror-dir "$tmp_dir" --channel development
  ```

* Test the standard Hermes lifecycle against the root mirror repository:
  ```bash
  scripts/test-hermes-plugin-install.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
  scripts/test-hermes-plugin-update.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
  scripts/test-hermes-plugin-uninstall.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
  ```

The root mirror identifier is `https://github.com/burhop/hermes-plugin-wright/tree/dev` for development testing and `https://github.com/burhop/hermes-plugin-wright/tree/main` for stable customer testing. Use `--mirror-root` when validating the mirror repository itself; use the default subdirectory mode only when intentionally testing the legacy monorepo path.
