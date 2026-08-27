# Wright Developer & Utility Scripts

This directory contains helper scripts to automate local development, manage Docker container environments, perform database cleanups, patch submodules, and run developer diagnostics.

## Quiet Windows workstation startup

`scripts/windows/start-wright.ps1` starts Docker Desktop minimized and launches
the Wright API and Vite development UI with hidden process windows. It is
idempotent, writes lifecycle logs under
`%LOCALAPPDATA%\wright\startup\logs`, and deliberately leaves Rivet, BREP, and
other managed tools stopped until a Wright surface or MCP call requests them.

For a login startup entry, invoke this script from a hidden `wscript.exe`
launcher in the user's Startup folder. The workstation setup uses
`http://127.0.0.1:5173/` for the development UI and
`http://127.0.0.1:8000/api/health` for the API health check.

## Script Index

| Script | Language | Purpose | Key Dependencies |
| :--- | :--- | :--- | :--- |
| [`backup-volumes.sh`](#backup-volumessh) | Bash | Backs up Wright Docker volumes to local disk | Docker |
| [`restore-volume.sh`](#restore-volumesh) | Bash | Restores a Docker volume from a saved backup | Docker |
| [`alpha-release-check.sh`](#alpha-release-checksh-and-alpha-release-checkps1) / [`alpha-release-check.ps1`](#alpha-release-checksh-and-alpha-release-checkps1) | Bash / PowerShell | Runs the full local alpha release gate | Python 3, uv, npm, Docker |
| [`check-dev-push.sh`](#check-dev-pushsh-and-check-dev-pushps1) / [`check-dev-push.ps1`](#check-dev-pushsh-and-check-dev-pushps1) | Bash / PowerShell | Runs the fast diff-aware gate before pushing a PR that targets `dev` | Git, Python 3, uv, npm, Playwright |
| [`check-dev-merge.sh`](#check-dev-mergesh) | Bash | Runs the CI-equivalent gate before merging a feature branch to `dev` | Python 3, uv, npm, Playwright |
| [`check-prod-merge.sh`](#check-prod-mergesh) | Bash | Runs the release gate before merging `dev` to `main` | Python 3, uv, npm, Docker, Hermes |
| [`cleanup-workspaces.py`](#cleanup-workspacespy) | Python | Truncates database tables and cleans workspace directories | Python 3, SQLite |
| [`validate-engineering-process-program.py`](#validate-engineering-process-program) | Python | Validates an exact committed engineering-process program subject and generates a local candidate dashboard | Python 3.11+, Git 2.39+, existing `jsonschema` runtime |
| [`check-public-alpha-leaks.py`](#check-public-alpha-leakspy) | Python | Scans tracked text files for obvious public-alpha secret leaks | Python 3, Git |
| [`security-scan.sh`](#security-scansh-and-security-scanps1) / [`security-scan.ps1`](#security-scansh-and-security-scanps1) | Bash / PowerShell | Runs public-alpha, Gitleaks, and TruffleHog secret scans | Python 3, Docker |
| [`docker-smoke-test.sh`](#docker-smoke-testsh) | Bash | Validates Docker build, Hermes dependencies, permissions, and self-healing behaviors | Docker, Python 3 |
| `reconcile_hermes_pip_check.py` | Python | Accepts only the two reviewed Hermes 0.19 security-version conflicts from raw `uv pip check` output | Python 3 |
| [`test-hermes-plugin-install.sh`](#hermes-plugin-lifecycle-scripts) / [`test-hermes-plugin-uninstall.sh`](#hermes-plugin-lifecycle-scripts) / [`test-hermes-plugin-update.sh`](#hermes-plugin-lifecycle-scripts) | Bash | Validates Hermes plugin install, uninstall, and update paths in Docker | Docker |
| [`production-update.sh`](#production-updatesh) | Bash | Guards operator-run production updates against stale, dirty, or unverified commits | Git, Docker, optional `gh` CLI |
| [`fetch_ci_failures.py`](#fetch_ci_failurespy) | Python | Retrieves logs of failed GitHub Action runs to a local markdown file | Python 3, `gh` CLI |
| [`openscad-headless.sh`](#openscad-headlesssh) | Bash | Runs OpenSCAD headlessly inside containerized environments | `xvfb-run`, OpenSCAD |
| [`patch-submodule.sh`](#patch-submodulesh) | Bash | Applies localized patches to the FreeCAD MCP submodule | Git |
| [`setup-wright-profile.sh`](#setup-wright-profilesh) | Bash | Provisions and configures a Hermes profile for native Wright development | `hermes` CLI |

---

### Validate engineering process program

This validator is deliberately repo-local and adds no dependency. It requires Python 3.11 or newer, Git 2.39 or newer, and the `jsonschema` package already present in Wright's runtime/test environment. It reads committed Git objects through argument-array, read-only commands; it does not treat checkout line endings as artifact identity.

Run the focused suite without pytest cache writes:

```powershell
python -m pytest -p no:cacheprovider tests/program_control_plane -q
```

Validate the current committed program subject:

```powershell
python scripts/validate-engineering-process-program.py validate --source HEAD --format text
```

Validate an explicit source `S` with a dashboard-only successor `C` and an
explicit delivery-evidence successor `D`:

```powershell
python scripts/validate-engineering-process-program.py validate --source <S> --container <C> --delivery <D> --format json
```

`--container` is optional; without it, only `HEAD` may be inferred and only
when its first parent is `S` and the diff is exactly `dashboard.json`.
`--delivery` is always explicit, requires a resolved `C`, and never searches
descendants. Exit `0` means the validator contract passed even when readiness
areas are honestly blocked/not-started; `2` is usage/subject resolution, `3`
schema/raw JSON, `4` semantic authority, `5` dashboard delivery, `6`
compatibility, and `70` contained internal failure. Inspect the JSON finding's
repository-relative artifact, invariant, bounded evidence, and recovery. A
valid report never makes non-passing readiness green and never grants an action
that `program-state.json` and policy do not prove.

Both commands are offline. A validator failure authorizes no repair, integration, benchmark execution, or release action; inspect the repository-relative finding and follow the program state's sole eligible action.

Generate the schema-valid local candidate snapshot only at its declared path:

```powershell
python scripts/validate-engineering-process-program.py generate-dashboard --source HEAD --program-root docs/programs/engineering-process-platform --output docs/programs/engineering-process-platform/dashboard.json --format text
```

The snapshot always remains `candidate_not_evidence`. Current empty benchmark evidence is rendered honestly as `0/100` counted, `100` not tested, and independent coverage/oracle/artifact/partition/freshness deficits. `COMMITTED_IDENTITY_MISMATCH` and `TRANSITION_INPUT_ORIGIN_MISMATCH` are resolved only by their exact approved `37/37` and `1/1` profiles; any profile, authority, target, Git-object, or source/container mismatch fails closed with a bounded recovery direction.

---


### `check-dev-push.sh` and `check-dev-push.ps1`

Read [`docs/contributing/dev-push-runbook.md`](../docs/contributing/dev-push-runbook.md)
before every push to a pull request targeting `dev`. The fast gate selects the
Python, frontend/browser, and documentation slices affected since the branch's
last pushed tip, including staged, unstaged, and untracked files. A new branch
falls back to `origin/dev`. Gate-infrastructure changes select all slices. The PowerShell
entry point deliberately uses Git for Windows Bash instead of WSL, so the
Windows `uv`, Node, and browser installations remain available.
Python dependencies are cached in `.venv-dev-gate`, separate from a running
Wright development environment.

```powershell
scripts/check-dev-push.ps1
```

```bash
scripts/check-dev-push.sh
```

The mocked Playwright slice uses port `15174` by default and does not disturb a
developer's Wright UI on 5173.

---

### `check-dev-merge.sh`

Runs the heavyweight local gate before merging a feature branch to `dev`. It is
intended to mirror the checks that have previously caught branch integration
drift in CI:

Before its test stages, the gate refreshes `wright-engineering` so the Rivet editor and runner bundles force-included from `integrations/rivet/` cannot remain stale in an editable environment.

The frontend is built once from the developer's installed lockfile dependencies
and that fresh output is reused by native packaging. The merge gate does not run
`npm ci` against a shared `node_modules` that may be serving a live Wright UI.

The full gate verifies that its configurable API and UI ports can be bound
before starting the long test matrix. Port conflicts therefore fail immediately
with the override to use instead of appearing at the browser stage.

1. `git diff --check`
2. Ruff lint and format checks for Wright-owned Python workspaces
3. ESLint, Prettier, TypeScript, Vitest, and frontend build checks
4. mypy in the same warning mode used by CI
5. Python package metadata dry-run validation
6. Backend pytest and Hermes plugin pytest
7. Strict docs build
8. Playwright with `PLAYWRIGHT_INCLUDE_LIVE=1` against a temporary local API database

* **Usage**:
  ```powershell
  scripts/check-dev-merge.ps1
  ```

  ```bash
  scripts/check-dev-merge.sh
  make check-dev-merge
  ```

The live Playwright portion uses isolated ports `18000` and `15173` by default.
Override them with `WRIGHT_GATE_API_PORT` and `WRIGHT_GATE_UI_PORT` when needed.
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
installed globally. When invoked from Git for Windows, the Bash wrapper passes
Docker Desktop an explicit Windows bind source and disables MSYS argument
conversion so both the host mount and literal in-container `/repo` paths remain
correct.

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
  1. Builds the Docker image locally as `wright:test`.
  2. Asserts that the container user runs as the non-root `agent` user by default.
  3. Runs raw `uv pip check`; only the exact Hermes 0.19 cryptography/Pillow
     security overrides are reconciled, and every other conflict fails.
  4. Verifies that the `/container-manifest.md` is present and has read-only `444` permissions.
  5. Verifies that `/entrypoint.sh` is present and executable.
  6. Validates setup-pending behavior (warns and continues if no LLM provider is configured, succeeds when one is provided).
  7. Validates container recovery paths (ephemeral write checks and entrypoint shell bypasses).

Host-side JSON and dependency assertions honor an explicit `PYTHON`
interpreter, then fall back to `python3`, `python`, or `py -3`. This keeps the
production gate on the same validated interpreter in Git Bash and CI. The
script also keeps every absolute Docker argument as a literal in-container path
when run through Git for Windows.

* **Usage**:
  ```bash
  ./scripts/docker-smoke-test.sh
  ```
* **Smoke an existing image without rebuilding**:
  ```bash
  WRIGHT_DOCKER_IMAGE=wright:latest WRIGHT_DOCKER_SKIP_BUILD=1 ./scripts/docker-smoke-test.sh
  ```

---

### `docker-mcp-smoke-test.sh`

Builds the standard Wright image as `wright:test`, derives the MCP appliance
image as `wright:mcp-test`, validates the MCP bundle, starts the container with
fresh runtime state, and checks Wright API health, Hermes gateway supervision,
generated MCP config, generated compliance artifacts, and local tool/wrapper
presence for OpenSCAD, FreeCAD, BREP, SolidEdgeMCP, and Playwright.
The default Docker platform is `linux/amd64`; set
`WRIGHT_MCP_DOCKER_PLATFORM=linux/arm64` to smoke the arm64 bundle on GB10-class
hosts.

* **Usage**:
  ```bash
  ./scripts/docker-mcp-smoke-test.sh
  ```
* **Smoke an existing MCP image without rebuilding**:
  ```bash
  WRIGHT_MCP_DOCKER_IMAGE=wright:mcp-test WRIGHT_MCP_SKIP_BUILD=1 ./scripts/docker-mcp-smoke-test.sh
  ```

Bundle-only validation:

```bash
python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml
python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated
```

---

### `docker-image-family-build.sh` / `docker-image-family-build.ps1`

Builds managed Wright image profiles from `docker/image-family.yaml`.

* **Linux/GB10 arm64**:
  ```bash
  ./scripts/docker-image-family-build.sh linux-arm64
  ```
* **Linux amd64**:
  ```bash
  ./scripts/docker-image-family-build.sh linux-amd64
  ```
* **Windows host**:
  ```powershell
  pwsh -File scripts/docker-image-family-build.ps1 -Profile windows-amd64
  ```

The Windows profile must be built from Docker Desktop in Windows container
mode. It honors `WRIGHT_SOLIDEDGE_MCP_GIT_URL`, exact
`WRIGHT_SOLIDEDGE_MCP_GIT_REF`, and optional
`WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL` for nonstandard archive sources. Private
GitHub MCP sources require `GITHUB_TOKEN` or a valid `gh auth login`; Linux MCP
builds pass that token as a BuildKit `github_token` secret. Linux profiles
should be built from Linux container mode.

---

### `docker-mcp-run.sh` / `docker-mcp-run-windows.ps1`

Runs a built MCP image with platform-specific named volumes so Wright data,
workspaces, config, Hermes profile data, and logs survive container recreation.

* **Linux arm64**:
  ```bash
  WRIGHT_API_TOKEN=change-this ./scripts/docker-mcp-run.sh linux-arm64
  ```
* **Linux amd64**:
  ```bash
  WRIGHT_API_TOKEN=change-this ./scripts/docker-mcp-run.sh linux-amd64
  ```
* **Remote browser access on a trusted LAN**:
  ```bash
  WRIGHT_MCP_BIND=0.0.0.0 \
  WRIGHT_MCP_PUBLIC_HOST=<host-lan-ip> \
  WRIGHT_API_TOKEN=change-this \
  ./scripts/docker-mcp-run.sh linux-arm64
  ```
  `WRIGHT_MCP_PUBLIC_HOST` is added to `WRIGHT_ALLOWED_ORIGINS` so browser
  requests for CSS, JavaScript, API calls, and WebSocket connections are not
  rejected by the origin guard.
* **Windows MCP runtime**:
  ```powershell
  pwsh -File scripts/docker-mcp-run-windows.ps1
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

By default, the scripts use `WRIGHT_DOCKER_IMAGE=wright:test` and install from the public Wright Git repository on the `dev` branch: `https://github.com/burhop/wright/tree/dev/hermes-plugin-wright`. Use `--ref main` or `WRIGHT_PLUGIN_REF=main` to test the main-branch customer path; the default is `dev`.

`test-hermes-plugin-update.sh` intentionally uses Hermes standard `plugins update`, which requires the installed plugin directory to be a Git checkout. This is why the script installs from GitHub instead of the local checkout. If Hermes still drops `.git` metadata for the `hermes-plugin-wright` subdirectory install, the script fails with that diagnosis so we can fix the distribution shape before users hit it.

Useful overrides:

```bash
WRIGHT_DOCKER_BUILD=1 scripts/test-hermes-plugin-install.sh
WRIGHT_DOCKER_IMAGE=wright:latest WRIGHT_DOCKER_SKIP_BUILD=1 make hermes-plugin-lifecycle-test
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
  - `API_SERVER_KEY` from the required `HERMES_API_KEY` environment variable
  - `API_SERVER_PORT=8642`
* **Workflow**:
  1. Verifies the `hermes` CLI is installed.
  2. Clones the default Hermes profile into a new `wright` profile if it does not already exist.
  3. Set profile configuration keys.
  4. Starts the Hermes profile gateway and polls the health endpoint (`http://127.0.0.1:8642/health`) to ensure it boots successfully.
* **Usage**:
  ```bash
  export HERMES_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  ./scripts/setup-wright-profile.sh
  ```

### Hermes Plugin Mirror and Package Release Scripts

These helpers support the thin `hermes-plugin-wright` mirror and the PyPI/TestPyPI package publication path used by the Wright Hermes plugin.

| Script | Language | Purpose | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `build-python-distributions.sh` | Bash | Validates `wright-core` and `wright-tool-registry` package metadata, builds source/wheel artifacts, and optionally performs clean install/import checks | Python 3, `build`, pip |
| `sync-hermes-plugin-mirror.sh` | Bash | Exports only allowlisted plugin files from `hermes-plugin-wright/` into a root-level mirror directory and writes provenance | Git, Python 3 |
| `validate-hermes-plugin-mirror.sh` | Bash | Validates mirror required files, prohibited paths, README links, provenance, and dependency policy | Bash, Python 3 |

Both mirror scripts honor an explicit `PYTHON` interpreter and otherwise select
a working `python3`, `python`, or `py -3` command. This prevents Git for Windows
from accepting the non-functional Microsoft Store `python3` alias during the
production merge gate. The Make target also stops immediately if mirror
generation fails, so validation cannot continue against a partial export.

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

On Git for Windows, the shared lifecycle helper converts only the host-side
bind-mount sources to Windows paths and disables further MSYS argument
rewriting. Container paths such as `/bin/bash`, `/tmp/hermes-home`, and
`/wright-src` therefore reach Docker unchanged.
