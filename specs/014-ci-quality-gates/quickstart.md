# Quick Start: CI/CD Quality Gates

**Branch**: `014-ci-quality-gates` | **Date**: 2026-06-05

This document details how to run the quality gate checks locally, set up pre-commit hooks, and configure GitHub branch protection rules.

## 1. Local Validation with Makefile

You can run quality checks on your local machine using the newly added Makefile targets:

```bash
# Run all code quality checks (linting, formatting verification, type checking, and tests)
make check

# Format all files automatically
make format

# Run only linters (Ruff + ESLint)
make lint

# Run type checks (Mypy + TSC)
make typecheck

# Run test suites (Pytest)
make test
```

## 2. Setting Up Pre-commit Hooks

Pre-commit hooks are optional and validate code styling before commits are finalized:

```bash
# 1. Install pre-commit utility using your Python package manager
pip install pre-commit

# 2. Register the hooks with Git in the repository root
pre-commit install

# 3. (Optional) Run hooks manually on all files to verify baseline compliance
pre-commit run --all-files
```

## 3. GitHub Branch Protection Policy Setup

To enforce quality gates on GitHub, the repository owner should configure the following settings under **Settings** -> **Branches** on GitHub:

1. Click **Add branch protection rule** for the default branch (e.g. `main` or `dev`).
2. Enable **Require a pull request before merging** and check **Require approvals** (minimum `1` reviewer).
3. Enable **Require status checks to pass before merging**:
   - Check **Require branches to be up to date before merging**.
   - Search for and check these status checks:
     - `python-quality`
     - `frontend-quality`
     - `docker-build` (the existing container verification workflow)
4. Enable **Do not allow force pushes** and **Do not allow deletions**.
5. Save changes.
