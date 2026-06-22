# Data Model: Wright Slash Commands

This document describes the design models and entities used by the `/wright` slash commands plugin module. These models facilitate command line parsing, execution state tracking, and formatting outputs for user presentation.

---

## 1. Subcommand Routing Context

Represents the parsed input from the user's slash command query.

### Attributes
- `command`: String (The active subcommand, e.g. `start`, `stop`, `status`, `catalog`, `info`, `install`, `doctor`, `open`).
- `arguments`: List of Strings (Optional arguments, e.g. `<domain>`, `<id>`, `<query>`).
- `raw_query`: String (The complete raw text typed after the slash command).

---

## 2. Process Tracker Entity (State Persistence)

Used to track whether the background FastAPI/uvicorn server is running. This is written to the local filesystem at `repo/tmp/wright-api.pid`.

### Attributes
- `pid`: Integer (The Operating System process identifier).
- `started_at`: Timestamp (ISO 8601 string of when the process was launched).
- `log_file`: Path string (Where stdout/stderr are redirected).

---

## 3. Diagnostic Report Entity (`/wright doctor`)

Represents the aggregated results of environment and workspace diagnostics.

### Attributes
- `checks`: List of `DiagnosticCheck` objects:
  - `name`: String (e.g. "Repository Path", "FastAPI Server", "SQLite Database", "Secrets Permissions").
  - `status`: Enum (`OK`, `WARNING`, `ERROR`).
  - `details`: String (Detailed description or error trace).
  - `remediation`: String (Instruction on how to fix if status is not `OK`).
- `overall_healthy`: Boolean (True if no check has an `ERROR` status).

---

## 4. Dashboard Status Entity (`/wright status`)

Represents the active connectivity state and MCP server mappings.

### Attributes
- `api_connected`: Boolean (Connection status to FastAPI server).
- `workspace_name`: String (Active workspace name).
- `workspace_path`: String (Absolute path of the workspace).
- `tools`: List of `ToolStatus` objects:
  - `id`: String (Tool ID).
  - `name`: String (Tool name).
  - `status`: Enum (`active`, `needs_credentials`, `inactive`).
  - `missing_keys`: List of Strings (Names of missing env credentials).
