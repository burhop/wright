# Quickstart: Wright Slash Commands

This guide provides examples of how to use and test the `/wright` slash commands in the Hermes Wright integration plugin.

---

## 1. Developer Setup

Ensure the plugin is installed in editable mode inside your Python virtual environment:

```bash
pip install -e ./hermes-plugin-wright
```

Verify that the registration entry point still loads correctly:

```bash
python hermes-plugin-wright/verify_plugin.py
```

---

## 2. Command Reference & Examples

Once running inside Hermes, you can execute the following commands:

### Launcher Subcommands

- **Start the Application Stack**:
  ```text
  /wright start
  ```
  *Compiles frontend assets if stale, launches the FastAPI server in the background, writes the PID file, and opens the UI in your default browser.*

- **Stop the Application Stack**:
  ```text
  /wright stop
  ```
  *Gracefully terminates the background server processes and removes the PID file.*

- **Open Web Browser**:
  ```text
  /wright open
  ```
  *Opens the browser to `http://localhost:8000` if the server is healthy.*

- **Inspect Environment Health**:
  ```text
  /wright doctor
  ```
  *Diagnoses repository paths, SQLite databases, file permissions, and active credential configurations.*

### Catalog & Status Subcommands

- **Dashboard View**:
  ```text
  /wright status
  ```
  *Inspects active workspace path, connection status, and list of configured/active MCP tools.*

- **Browse Catalog**:
  ```text
  /wright catalog
  /wright catalog cad
  ```
  *Lists catalog entries or filters entries by domain tags.*

- **Search Catalog**:
  ```text
  /wright catalog search calculiX
  ```
  *Queries tool entries matching the search criteria.*

- **View Details**:
  ```text
  /wright info openfoam
  ```
  *Displays details, commands, and dependencies for a catalog tool.*

- **Install Tool**:
  ```text
  /wright install calculix
  ```
  *Registers the catalog entry directly into the active MCP tools gateway.*
