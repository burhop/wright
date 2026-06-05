# Research: CI/CD Quality Gates

**Branch**: `014-ci-quality-gates` | **Date**: 2026-06-05

## Technical Decisions & Rationale

### 1. Python Quality Gates (Ruff, Mypy, and Pytest)
* **Decision**: Use `ruff` for linting and formatting, `mypy` for type checking, and `pytest` for tests.
* **Rationale**:
  - `ruff` replaces both `flake8` and `black`, executing checks and auto-formatting up to 100x faster than legacy tools, keeping the feedback loop tight.
  - `mypy` is the industry standard for Python type validation. To avoid blocking pre-existing code, `mypy` will run in a lenient mode initially, reporting warnings rather than errors for legacy packages.
  - `pytest` is the established testing engine for the backend codebase, making it the natural choice for the test pipeline step.
* **Alternatives Considered**: 
  - *flake8 + black + isort*: Too slow and requires maintaining multiple independent configurations.
  - *pyright*: A strong type checker, but `mypy` has simpler integration with Python environment configurations.

### 2. Frontend Quality Gates (ESLint, Prettier, and TSC)
* **Decision**: Use `eslint` for TypeScript linting, `prettier --check` for code style formatting validation, and `tsc --noEmit` for compiler-level type safety checks.
* **Rationale**:
  - `eslint` and `prettier` are the default standards for modern React/TypeScript apps.
  - `tsc --noEmit` performs compilation checks without generating output files, ensuring absolute type correctness.
* **Alternatives Considered**: 
  - *Biome*: Fast, but lacks full plugin parity with the existing configuration of ESLint.

### 3. CI Optimization (Caching and Version Pinned Actions)
* **Decision**: Enable caching for `uv` (for Python packages) and `npm` (for Node modules) and use pinned version actions (e.g. `actions/checkout@v4`).
* **Rationale**:
  - Caching reduces CI workflow times by avoiding full package downloads on every run, keeping total execution well under the 3-minute limit.
  - Version pinning ensures security and build reproducibility, preventing supply-chain disruptions.

### 4. Git Hooks & Code Standard (Pre-commit & EditorConfig)
* **Decision**: Implement `.pre-commit-config.yaml` for optional developer pre-commit validation and a root `.editorconfig` to automatically set line endings, encoding, and indentation spacing in all major editors.
* **Rationale**:
  - Pre-commit hooks run before the code is sent to the remote branch, minimizing CI cycle noise.
  - EditorConfig automatically configures spacing (4 spaces for Python, 2 spaces for JS/TS/JSON/YAML) inside IDEs, keeping style uniform from the first keystroke.
