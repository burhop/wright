# Feature Brief: CI/CD Quality Gates

Add comprehensive continuous integration workflows that run linting, formatting, type checking, and tests on every pull request. This ensures code quality stays consistent as contributors join, prevents regressions, and enables branch protection rules that require CI checks to pass before merging.

## What to build

### Python Quality Gate Workflow

1. **Python lint/format CI** (`.github/workflows/python-quality.yml`) — A GitHub Actions workflow triggered on every PR and push to `main`/`dev` that:
   - Runs `ruff check` for linting across all Python code in `apps/api/` and `packages/`
   - Runs `ruff format --check` to verify formatting consistency
   - Uses the project's existing `pyproject.toml` for ruff configuration
   - Runs on Python 3.13 (matching the project's target version)
   - Uses `uv` for dependency installation (matching the project's package manager)
   - Fails the PR if any lint errors or formatting inconsistencies are found
   - Provides clear error messages showing exactly which files/lines need fixing

2. **Python type checking** — Add `mypy` or `pyright` to the Python quality workflow:
   - Type-check `apps/api/` and `packages/` directories
   - Use a reasonable strictness level to start (not `--strict`) to avoid blocking existing code
   - Report type errors as CI warnings initially, with a plan to promote to errors

3. **Python tests** — Add a test step that:
   - Runs `pytest` for any existing unit and integration tests
   - Reports test results with pass/fail counts
   - Fails the PR if any tests fail

### TypeScript/Frontend Quality Gate Workflow

4. **Frontend lint/format CI** (`.github/workflows/frontend-quality.yml`) — A workflow that:
   - Runs `eslint` on all TypeScript code in `apps/web/`
   - Runs `prettier --check` for formatting verification
   - Runs `tsc --noEmit` for type checking
   - Uses Node.js 22 (matching the project's target version)
   - Fails the PR if any lint, format, or type errors are found

### Pre-commit Hooks

5. **Pre-commit hook configuration** (`.pre-commit-config.yaml`) — Local developer hooks that run the same checks before committing:
   - `ruff check --fix` (Python lint with auto-fix)
   - `ruff format` (Python auto-format)
   - `prettier --write` (TypeScript/CSS/JSON auto-format)
   - `eslint --fix` (TypeScript lint with auto-fix)
   - Trailing whitespace and end-of-file fixers
   - Document in CONTRIBUTING.md how to install: `pip install pre-commit && pre-commit install`

### Editor Configuration

6. **EditorConfig** (`.editorconfig`) — Standardize editor settings across all contributors:
   - UTF-8 encoding
   - LF line endings
   - 4-space indentation for Python
   - 2-space indentation for TypeScript, JavaScript, JSON, YAML, CSS
   - Trim trailing whitespace
   - Insert final newline

### Makefile Dev Targets

7. **Developer convenience targets** — Add non-Docker targets to the existing Makefile:
   - `make lint` — Run all linters (ruff + eslint)
   - `make format` — Auto-format all code (ruff format + prettier)
   - `make typecheck` — Run type checkers (mypy/pyright + tsc)
   - `make test` — Run all tests (pytest + any frontend tests)
   - `make check` — Run all quality checks (lint + format-check + typecheck + test) — same as CI
   - These targets should work independently of Docker

### Branch Protection Documentation

8. **Branch protection rules** — Document the recommended GitHub branch protection settings for the repo owner to configure:
   - Require pull request reviews before merging (at least 1 reviewer)
   - Require status checks to pass (python-quality, frontend-quality, docker-build)
   - Require branches to be up to date before merging
   - Do not allow force pushes to `main`
   - Do not allow deletion of `main`
   - Include instructions for configuring these in GitHub Settings → Branches

## Constraints

- Do not modify any existing application source code (Python or TypeScript business logic)
- CI workflows must not duplicate the existing `docker-build.yml` workflow — they complement it
- Pre-commit hooks must be opt-in (documented, not forced) since some developers may prefer CI-only checking
- Quality checks should initially be lenient enough to pass on the current codebase — if the existing code has lint issues, create a baseline/exclusion and note it for follow-up cleanup
- All workflows must use pinned action versions (e.g., `actions/checkout@v4`) for security
- Workflows should use caching (pip cache, npm cache) to keep CI times under 3 minutes
