# Data Model: Repo Hygiene & Legal Foundation

While this feature does not introduce database tables or persistent software schemas, it establishes structured file formats and metadata configurations that function as the project's repository hygiene model.

## Community Health File Model

Every community health file added to the repository must conform to the following schema structure:

| File Path | Entity Type | Structure / Format | Mandatory Fields / Keys | Validation Rules |
|---|---|---|---|---|
| `LICENSE` | Legal License | Plain Text (MIT License) | Copyright holder (`burhop`), Copyright year (`2026`) | Must contain verbatim MIT License text. |
| `CODE_OF_CONDUCT.md` | Community Guidelines | Markdown (Contributor Covenant v2.1) | Enforcement contact email (`burhop@gmail.com`) | Must follow the standard Contributor Covenant v2.1 text. |
| `SECURITY.md` | Security Policy | Markdown (Custom Policy) | Reporting contact email (`burhop@gmail.com`), Supported Versions table | Must explicitly forbid public issues for vulnerabilities. |
| `SUPPORT.md` | Support Index | Markdown (Custom Index) | GitHub Discussions link, Issues link, Docs link | Must map usage questions to Discussions. |
| `CONTRIBUTING.md` | Developer Guidelines | Markdown (Custom Guide) | Dev setup prerequisites, Spec-kit workflow, PR checklist | Must document the speckit slash commands. |
| `.github/CODEOWNERS` | Automated Review Assignment | GitHub Ruleset Format | File patterns, GitHub usernames (`@burhop`) | Syntax must follow GitHub CODEOWNERS rules. |
| `.gitignore` | Git Exclusions | Plain Text (Git Ruleset) | Log exclusions, Database exclusions, Test artifact exclusions | Must exclude `state.db` and `*.log` without affecting source files. |

## CODEOWNERS Rule Mapping

The `.github/CODEOWNERS` mappings are defined as follows:

| Path Pattern | Owner Username | Target Component |
|---|---|---|
| `apps/api/` | `@burhop` | Backend Code & API |
| `packages/` | `@burhop` | Shared packages & code utilities |
| `apps/web/` | `@burhop` | Frontend application |
| `docker/` | `@burhop` | Infrastructure & Containerization |
| `.github/workflows/` | `@burhop` | CI/CD automation pipelines |
| `specs/` | `@burhop` | Feature Specifications |
| `.specify/` | `@burhop` | Spec-kit Tooling |
