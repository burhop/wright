# Wright: Standalone Engineering AI-in-a-Box

Wright is a modular, local-first agent orchestration platform designed for product designers and mechanical analysts. It allows deploying task-specific AI agents (like Hermes, OpenClaw, and Pi) to manage end-to-end design lifecycles, CAD geometry generation, Finite Element Analysis (FEA), and CAM print slicing fully offline in air-gapped environments.

---

## Quick Start (Docker Compose)

The easiest way to launch Wright is using Docker Compose. Create a `.env` file at the root:

```env
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-api-key-here
LLM_API_MODEL=gemini-3.5-flash
```

Launch the stack:
```bash
docker compose up -d
```
The frontend dashboard is accessible at `http://localhost:8080/`.

---

## Environment Configuration

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_URL` | **Yes** | None | Base endpoint for chat completions (e.g. Gemini, OpenAI, or local Ollama). |
| `LLM_API_KEY` | No | None | Authentication key for the provider. |
| `LLM_API_MODEL` | No | `gemini-3.5-flash` | Target LLM model name. |

---

## Volumes Reference

| Volume Name | Target Path | Purpose |
| :--- | :--- | :--- |
| `wright_home` | `/home/` | Agent user workspaces, code history, and caches. |
| `wright_local` | `/usr/local/` | Programmatic installations and bin configurations. |
| `wright_opt` | `/opt/` | Scientific packages, Conda/Micromamba runtimes. |
| `wright_varlib` | `/var/lib/` | System registries and package databases. |
| `wright_varcache` | `/var/cache/` | Package file cache and downloads. |
| `wright_etc` | `/etc/` | Critical system configurations. |
| `wright_logs` | `/var/log/` | System and agent execution logs. |

---

## Exposed Ports

*   `8080` (Host) -> mapped to `8000` (Container): Wright FastAPI gateway and Web SPA dashboard.
*   `8788` (Internal): Hermes agent service console interface.

---

For full documentation and monorepo source files, check out [GitHub Repository](https://github.com/burhop/wright).
