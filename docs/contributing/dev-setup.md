# Developer Workspace Setup

To configure a local developer environment for committing code and verifying changes on Wright, follow this guide.

---

## 1. Environment Preparation

### Python Environment Setup
Wright utilizes `uv` to handle dependencies, python versions, and virtual environments.

```bash
# Verify python installation (>3.11)
python3 --version

# Synchronize virtual env packages
uv sync
```

### Frontend Environment Setup
Ensure Node.js v20+ is active.

```bash
# Install NPM dependencies
npm install
```

---

## 2. API Credentials Setup

Create a `.env` configuration file at the project root matching the schema in the [Environment Variables Guide](../user-guide/env-vars.md).

```env
LLM_API_URL=https://your-llm-endpoint/v1
LLM_API_KEY=sk-your-secret-key
```

---

## 3. Working with Git Branches

When contributing features or fixes:
1.  Always branch off `dev` or `main` depending on release rules.
2.  Use feature branches (e.g. `016-docs-site` or `feat/some-tool`).
3.  Ensure git workspaces are clean before opening Pull Requests.
