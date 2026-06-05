# Data Model & Configuration Schemas: CI/CD Quality Gates

**Branch**: `014-ci-quality-gates` | **Date**: 2026-06-05

This document defines the configuration schemas, workflow setups, environment specifications, and developer command targets.

## 1. CI Workflows (GitHub Actions)

### Python Quality Gate Workflow (`python-quality.yml`)
* **Trigger Events**: Pull Requests and pushes targeting `main` and `dev`
* **Runner OS**: `ubuntu-latest`
* **Environment**:
  - Python: `3.13`
  - Package Manager: `uv` (cached)
* **Job Structure**:
  - `checkout`: Pinned code retrieval
  - `setup-python`: Configure environment
  - `setup-uv`: Install `uv`
  - `install-dependencies`: Sync with caching
  - `lint`: `ruff check --output-format=github`
  - `format`: `ruff format --check`
  - `typecheck`: `mypy apps/api/ packages/ --show-error-codes` (configured to warn on failures, not block)
  - `test`: `pytest` with JUnit XML reporter

### Frontend Quality Gate Workflow (`frontend-quality.yml`)
* **Trigger Events**: Pull Requests and pushes targeting `main` and `dev`
* **Runner OS**: `ubuntu-latest`
* **Environment**:
  - Node.js: `22` (cached)
* **Job Structure**:
  - `checkout`: Pinned code retrieval
  - `setup-node`: Configure Node.js environment
  - `install-dependencies`: `npm ci`
  - `lint`: `npm run lint` or `eslint apps/web/`
  - `format`: `prettier --check apps/web/`
  - `typecheck`: `tsc --noEmit`

---

## 2. Local Configuration Schemas

### Pre-commit Configuration (`.pre-commit-config.yaml`)
* **Hooks**:
  - `trailing-whitespace`: Trim trailing spaces
  - `end-of-file-fixer`: Verify blank line at end of file
  - `check-yaml`: Validate YAML syntax
  - `ruff`: Python lint/format check
  - `eslint`: TypeScript lint check
  - `prettier`: JS/TS/CSS/JSON auto-formatting

### EditorConfig (`.editorconfig`)
* **Root Property**: `root = true`
* **Default Settings**:
  - Indent Style: `space`
  - End of Line: `lf`
  - Insert Final Newline: `true`
  - Trim Trailing Whitespace: `true`
* **Indentation Rules**:
  - `*.py`: `indent_size = 4`
  - `*.js, *.ts, *.tsx, *.json, *.yml, *.yaml, *.css`: `indent_size = 2`

---

## 3. Developer Makefile Interface (Contract)

* **Targets**:
  - `lint`: Execute local linters (Ruff and ESLint) on development host.
  - `format`: Execute code formatters (Ruff format and Prettier) with write access.
  - `typecheck`: Run static type checking (Mypy/Pyright and TypeScript compiler).
  - `test`: Execute local test runner suites (pytest and frontend tests).
  - `check`: Run `lint` + formatting checks + `typecheck` + `test` to match CI validations.
