# Data Model: UI Navigation and Dashboard Redesign

This document describes the schema changes and new data structures introduced for global settings, workspace settings, and application logging.

## 1. Relational Database Updates (SQLite)

### Table: `engineering_workspaces`
Two new columns will be added to configure workspace-specific settings:

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `workspace_prompt` | TEXT | NULL | Custom system instructions injected into the LLM context for this workspace. |
| `git_large_file_threshold` | INTEGER | NOT NULL DEFAULT 10485760 | File size warning threshold in bytes (defaults to 10MB). |

### Table: `system_settings`
Used for global (system-wide) configurations:

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `key` | TEXT | PRIMARY KEY | Configuration key (e.g. `llm_provider`, `theme`, `api_keys`). |
| `value` | TEXT | NOT NULL | JSON serialized configuration value. |

---

## 2. In-Memory / Structured Log Types

### Entity: `LogEntry`
Represents a single log line parsed from the application logs:

- `timestamp`: String (ISO 8601 format, e.g. `"2026-06-09T11:47:33Z"`)
- `level`: String (one of `"info"`, `"warning"`, `"error"`)
- `message`: String (the main log event description)
- `logger`: String (the logger module name, e.g. `"api.routers.workspace"`)
- `workspace_id`: String (Optional - workspace association parsed from context if bound)
- `trace_id`: String (UUID trace ID, defaults to `"no-active-span"`)
- `span_id`: String (Optional span ID)
- `extra`: Object (Optional dictionary of extra bound metadata)
