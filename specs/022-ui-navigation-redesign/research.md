# Research: UI Navigation and Dashboard Redesign

## 1. Structured Application Logging & Retrieval

### Decision
Implement a JSON file-based logger using a rotating file handler in `packages/core/src/core/logging.py` that outputs all structlog lines to a local file `apps/api/wright.log`. We will expose a new FastAPI router `api.routers.logs` with a `GET /api/logs` endpoint.

### Rationale
- **High Performance**: Reading from a local text log file is fast, simple, and has zero database write overhead for every log line generated.
- **Easy Parsing**: Since all log entries are structured JSON strings, the backend can easily read, parse, and filter log objects on-the-fly.
- **OTel Integration**: Structlog binds `trace_id` and `span_id` automatically from the active OpenTelemetry context, making trace-based debugging seamless.

### Alternatives Considered
- **SQLite Database Logging**: Storing every log entry in SQLite causes significant lock contention under high log volumes during concurrent agent actions.
- **Logstash/Elasticsearch/Jaeger ingestion**: Too heavy for a local-first offline appliance and violates the low-resource constraint (Constitution §3).

---

## 2. Logs Debug Agent Interaction (UX Drawer)

### Decision
Implement a sliding React drawer component that overlays on the right side of the Logs page. When log text is right-clicked and "Send to Hermes for help" is selected:
1. The text selection is captured.
2. A new or active Hermes chat session is launched/loaded inside the drawer.
3. The captured log text is automatically prepended to the chat input inside a formatted debug template.
4. The user can interact with Hermes directly within the drawer, preserving their scroll position on the main logs list.

### Rationale
- **Seamless Debugging**: Allows testing, diagnosing, and chatting with Hermes simultaneously without leaving the Logs panel.
- **Scroll Preservation**: Prevents loss of location/filters on the main logs screen.

### Alternatives Considered
- **Navigate to Workspace Chat**: Navigating away from the Logs page clears the user's focus and requires them to navigate back and re-apply filters to continue searching.

---

## 3. Workspace Settings & Prompt Injection

### Decision
Store `workspace_prompt` and `git_large_file_threshold` in the `engineering_workspaces` database table. Modify the `.hermes.md` builder in `api.services.hermes_sync` to inject the workspace prompt at compile time.

### Rationale
- **Native Alignment**: Integrates with the existing `.hermes.md` generation pipeline.
- **Customizability**: Allows user control over prompting instructions on a per-workspace level, matching the workspace adapter pattern (Constitution §2).

### Alternatives Considered
- **Store in .env/config file**: Harder to sync programmatically and more prone to corruption than database-backed variables.

---

## 4. Advanced Git Panel with Large File Warning

### Decision
Add a file size check during git status scanning in the backend workspace service. Files exceeding `git_large_file_threshold` (default 10MB) will be marked as `is_oversized` in the API payload, and the Git panel UI will display a warning badge next to them indicating they are ignored or unmanaged.

### Rationale
- **Prevents Bloat**: Warns engineers before they inadvertently commit giant STL/3D scan binary models to Git.

### Alternatives Considered
- **Rely solely on Git LFS**: Harder to guarantee LFS is installed and configured on the host machine. A warning badge is simpler and more actionable.
