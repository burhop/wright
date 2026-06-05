# Feature Brief: Repo Hygiene & Legal Foundation

Add all missing community health files and clean up the repository root directory so the Wright project meets the minimum standard expected by open-source contributors and GitHub's Community Profile checklist.

## What to build

### Legal & Governance Files

Create the following files in the repository root:

1. **LICENSE** — MIT license (consistent with how OpenHands, CrewAI, and other popular agentic frameworks are licensed). The MIT license maximizes adoption by allowing commercial use, modification, and distribution with minimal restrictions. Include the correct copyright holder name and year.

2. **CODE_OF_CONDUCT.md** — Adopt the Contributor Covenant v2.1, the industry standard used by most major open-source projects. Include contact information for reporting violations.

3. **SECURITY.md** — A security disclosure policy that tells security researchers how to privately report vulnerabilities. Must include: a contact email for security reports, expected response timeframe (e.g., 48 hours acknowledgment, 7 days initial assessment), which versions are supported, and an explicit instruction NOT to file security issues as public GitHub Issues.

4. **SUPPORT.md** — A guide for users seeking help. Point to: GitHub Discussions for Q&A, the docs directory for technical documentation, and existing GitHub Issues for known bugs. Note that Wright is in active development and community support is best-effort.

### Contributing Guide

5. **CONTRIBUTING.md** — A comprehensive contribution guide covering:
   - How to set up the development environment (prerequisites: Python 3.11+, uv, Node.js 22+, Docker optional)
   - The spec-kit development workflow: contributors should understand that Wright uses speckit for feature development (specify → plan → tasks → implement)
   - Branch naming conventions (sequential numbered feature branches like `011-feature-name`)
   - Code style enforcement (ruff for Python, eslint/prettier for TypeScript)
   - How to submit pull requests (PR template checklist, what reviewers look for)
   - The constitution.md governance model — all PRs must comply with project principles
   - "Good First Issue" guidance — where to find beginner-friendly tasks

### Code Ownership

6. **.github/CODEOWNERS** — Auto-assign code reviewers based on file paths. Map: `apps/api/` and `packages/` to backend reviewers, `apps/web/` to frontend reviewers, `docker/` and `.github/workflows/` to infrastructure reviewers, `specs/` and `.specify/` to spec reviewers.

### Repository Cleanup

7. **Root directory cleanup** — The repo root currently contains files that should not be in version control:
   - Add to `.gitignore`: `phase*.log`, `ps_debug.log`, `tests_output*.txt`, `test-*-output.log`, `test-live-*.log`, `screenshot_*.png`, `state.db`, `tests_output/`
   - Move any existing screenshots that are referenced by the README into `docs/images/`
   - Remove or gitignore the stale log and output files

### GitHub Repo Metadata

8. **GitHub "About" section** — Configure the repository with:
   - Description: "🔧 Local-first AI mechanical engineer — CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs"
   - Topics (all 20 slots): ai-agent, mechanical-engineering, cad, fea, local-first, multi-agent, docker, fastapi, llm, offline-first, manufacturing, openscad, python, typescript, nvidia-dgx, engineering-tools, mcp, parametric-design, digital-twin, autonomous-agent
   - Note: These are GitHub settings, not files — document the recommended values and include instructions for the repo owner to apply them

## Constraints

- Do not modify any existing source code (Python, TypeScript, or application logic)
- Do not modify README.md in this feature (that is a separate feature)
- Do not modify any Docker files or CI/CD workflows
- The `.gitignore` changes must not break any existing workflows
- All community health files must pass GitHub's Community Profile checker
