# Contributing to Wright

Thank you for your interest in contributing to Wright! We welcome all contributions — from bug reports and documentation fixes to new features and major architectural enhancements. 

As a project focused on design and engineering agent orchestration, we maintain a highly structured, design-first development methodology to ensure robust local execution, clean architecture, and project quality.

---

## Prerequisites

To contribute to the codebase, make sure your development machine has the following tools installed:

1. **Python 3.11+**: The core backend API and tool registries are written in Python.
2. **uv**: We recommend using `uv` for ultra-fast Python package and workspace management (though `poetry` or standard virtual environments are also supported).
3. **Node.js 22+**: The frontend web application is written in TypeScript and React.
4. **Docker (Optional but recommended)**: For testing running container structures and running local OpenTelemetry tracing with Jaeger.

---

## Spec-Kit Development Workflow

Wright uses the **spec-kit** workflow to ensure all feature development is design-driven. All code modifications must follow this lifecycle before code is written:

1. **Specify** (`/speckit-specify`): Write a feature brief and generate a detailed feature specification under `specs/<feature-name>/spec.md` documenting user stories and requirements.
2. **Clarify** (`/speckit-clarify`): Identify and resolve any ambiguous requirements with the operator.
3. **Plan** (`/speckit-plan`): Build a technical plan (`specs/<feature-name>/plan.md`), defining architecture, data models, and checking compliance with the project constitution.
4. **Tasks** (`/speckit-tasks`): Generate a checklist of structured tasks in `specs/<feature-name>/tasks.md`.
5. **Implement** (`/speckit-implement`): Execute the checklist of tasks, checking them off as they are completed.

### Branch Discipline
All feature development must take place on dedicated feature branches.
* Use a sequential branch numbering scheme: `###-feature-name` (e.g., `011-repo-hygiene`).
* Switch to the branch before drafting specifications.
* **Direct commits to the `main` or `dev` branches are forbidden.**

---

## Code Style & Quality Gates

We enforce strict linting and formatting rules on all submitted code:

* **Python**: We use `ruff` for linting and formatting. Run the following checks locally before submitting code:
  ```bash
  ruff check .
  ruff format --check .
  ```
* **TypeScript / React**: We use ESLint and Prettier. Run the linting commands:
  ```bash
  npm run lint
  npm run format:check
  ```

---

## Project Constitution Compliance

Every contribution must align with the **Virtual Mechanical Engineer Constitution** (`constitution.md`). Critical mandates include:
1. **Offline-First Mandate**: The entire system must be capable of running fully air-gapped without relying on external cloud APIs for core operations.
2. **FastAPI Backend**: The API must utilize FastAPI with strict Pydantic validation. Business logic must live inside isolated packages.
3. **Embedded Databases**: No external DB servers. Relational data must use embedded **SQLite** (WAL mode) and semantic RAG must use embedded **LanceDB**.
4. **Local Auth**: JWT tokens via `OAuth2PasswordBearer` hashed locally with bcrypt in SQLite.
5. **3-Tier Testing Pyramid**: Component/story tests, mock Playwright UI integration tests, and E2E backend smoke tests.

---

## Pull Request Submission Checklist

When opening a Pull Request (PR), ensure your submission meets these requirements:

- [ ] The branch name follows the sequential format (`###-feature-name`).
- [ ] All specs and plans are located under `specs/###-feature-name/` and are fully completed.
- [ ] All unit, integration, and E2E tests pass locally.
- [ ] Code has been linted and formatted using the configured tools (`ruff`, `eslint`, `prettier`).
- [ ] The PR does not violate any rules defined in `constitution.md`.
- [ ] All interactive UI elements have a `data-testid` attribute.

---

## Finding Beginner Tasks

If you are new to the codebase and looking for a place to start, search the GitHub repository's issues page for the **"Good First Issue"** label. These issues represent self-contained tasks scoped specifically for new contributors.
