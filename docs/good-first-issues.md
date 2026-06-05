# Curated Good First Issues

This document lists draft issues that the repository maintainers can copy and paste to GitHub to attract new contributors. Each issue is self-contained, well-scoped, and covers different tech stacks.

---

## 1. [Frontend] Add copy-to-clipboard button to code blocks in Chat
*   **Description**: In the Agent Chat interface, code blocks (such as generated Python or OpenSCAD scripts) are formatted using markdown code blocks. To improve the developer experience, we should add a small "Copy" button to the top-right corner of these code blocks.
*   **Difficulty**: Easy
*   **Files to Modify**:
    *   `apps/web/src/components/chat/MessageContent.tsx`
*   **Expected Behavior**:
    *   When hovering over a code block, a small copy icon/button appears.
    *   Clicking the button copies the block's text to the clipboard and shows a brief "Copied!" success state.
*   **Skills Needed**: React, TypeScript, CSS

---

## 2. [Backend] Add simple system information logging on API startup
*   **Description**: To help diagnose system errors, the FastAPI server should log basic hardware info (OS type, Python version, CPU cores count) on startup.
*   **Difficulty**: Easy
*   **Files to Modify**:
    *   `apps/api/src/api/main.py`
*   **Expected Behavior**:
    *   Using the configured `structlog` logger, output a structured log `system_info` during startup (inside the lifespan context).
*   **Skills Needed**: Python, structured logging

---

## 3. [Documentation] Document environment variables configuration
*   **Description**: We need to compile a comprehensive guide of all environment variables supported by the API and agent containers.
*   **Difficulty**: Easy
*   **Files to Modify**:
    *   `docs/user-guide/env-vars.md` (Create new file)
*   **Expected Behavior**:
    *   Create a clean table documenting variables such as `WRIGHT_ENV`, `DATABASE_PATH`, `LLM_HEALTH_URL`, and their defaults.
*   **Skills Needed**: Markdown documentation

---

## 4. [Docker] Add a HEALTHCHECK command to docker-compose.minimal.yml
*   **Description**: The minimal compose file does not define healthchecks for the services. We should add a standard container health check for the core service.
*   **Difficulty**: Easy
*   **Files to Modify**:
    *   `docker-compose.minimal.yml`
*   **Expected Behavior**:
    *   Define a healthcheck block running `curl -f http://localhost:8000/api/health` every 30 seconds.
*   **Skills Needed**: Docker Compose, Bash

---

## 5. [Backend] Implement API route to download Vault files as a ZIP archive
*   **Description**: In the File Vault, users can only download files individually. We should add an endpoint `/api/vault/download-all` to download all generated artifacts as a single ZIP file.
*   **Difficulty**: Medium
*   **Files to Modify**:
    *   `apps/api/src/api/routers/workspace.py`
*   **Expected Behavior**:
    *   Create a ZIP archive of files in the workspace directory using python's `zipfile` module and return it as a FastAPI `FileResponse`.
*   **Skills Needed**: Python, FastAPI

---

## 6. [Testing] Add simple unit test for local RAG Fastener Database query
*   **Description**: Add a test that mock-queries LanceDB fasteners table and validates schema return values.
*   **Difficulty**: Easy
*   **Files to Modify**:
    *   `packages/data_vault/tests/test_fasteners.py`
*   **Expected Behavior**:
    *   Using `pytest`, assert database retrieval handles missing/empty fasteners list correctly.
*   **Skills Needed**: Python, pytest
