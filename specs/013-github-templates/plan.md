# Implementation Plan: GitHub Templates & Issue Automation

**Branch**: `013-github-templates` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-github-templates/spec.md`

## Summary

Standardize community engagement and repository hygiene on GitHub by implementing form-based Issue Templates (YAML), a structured Pull Request template (Markdown), a grouped weekly Dependabot updater, and documented GitHub Discussion categories and standard label schemas. This will involve creating 5 configuration files under the `.github/` directory.

## Technical Context

**Language/Version**: GitHub YAML form schema v2, Markdown, YAML (Dependabot v2)

**Primary Dependencies**: None (GitHub-native automation features)

**Storage**: N/A

**Testing**: Local YAML syntax validator script (using Python `yaml` package)

**Target Platform**: GitHub Repo Landing Page & Action Automation

**Project Type**: Documentation and Repository Health Configuration

**Performance Goals**: N/A

**Constraints**: Do not modify any application code, Docker files, or existing CI/CD workflows. Issue templates must use YAML forms, not markdown.

**Scale/Scope**: 5 configuration files, 20+ standard labels, 4 discussion categories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Framework (FastAPI): N/A (Compliant)
- Architecture (Modular Monorepo): N/A (Compliant)
- Offline-First Mandate: Compliant. These configurations are for remote repository interaction and do not affect local runtimes.
- Container Strategy: N/A (Compliant)
- Agent Abstraction: N/A (Compliant)
- Databases (Zero-Server): N/A (Compliant)
- State & Memory: N/A (Compliant)
- Vector RAG: N/A (Compliant)
- File Vault: N/A (Compliant)
- Security & Identity: N/A (Compliant)
- Engineering Tooling Protocol: N/A (Compliant)
- UI & Testing (3-Tier Pyramid): N/A (Compliant)
- Observability & Tracing: N/A (Compliant)
- Autonomous Agent Workflow Rules: Compliant. The plan is created on feature branch `013-github-templates` and is submitted to the operator before implementation code is generated.

## Project Structure

### Documentation (this feature)

```text
specs/013-github-templates/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Technical research notes
├── data-model.md        # Form schemas and dependabot config parameters
├── quickstart.md        # Testing and validation steps
└── tasks.md             # Actionable task list
```

### Source Code & Configuration Files

```text
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml       # [NEW] YAML issue form for bugs
│   ├── feature_request.yml  # [NEW] YAML issue form for features
│   └── config.yml           # [NEW] Redirect Q&A and security reports
├── PULL_REQUEST_TEMPLATE.md  # [NEW] Pull Request checklist markdown
└── dependabot.yml           # [NEW] Automated dependency manager configuration
```

**Structure Decision**: All GitHub-native templates must live in the standard `.github/` folder in the root of the repository to be recognized by GitHub's systems.

## Complexity Tracking

> *No violations of the Constitution Check.*

## Proposed Changes

### Configuration Files

#### [NEW] [bug_report.yml](file:///home/burhop/repos/wright/.github/ISSUE_TEMPLATE/bug_report.yml)
Define structured form fields for bug reports (description, OS, environment, Wright version).

#### [NEW] [feature_request.yml](file:///home/burhop/repos/wright/.github/ISSUE_TEMPLATE/feature_request.yml)
Define structured form fields for feature requests (summary, component, contribution willingness).

#### [NEW] [config.yml](file:///home/burhop/repos/wright/.github/ISSUE_TEMPLATE/config.yml)
Configure redirect links for general support questions (to GitHub Discussions) and security reports (to SECURITY.md).

#### [NEW] [PULL_REQUEST_TEMPLATE.md](file:///home/burhop/repos/wright/.github/PULL_REQUEST_TEMPLATE.md)
Provide markdown pull request template with self-review checklist items (docs, tests, CONTRIBUTING.md, and constitution.md).

#### [NEW] [dependabot.yml](file:///home/burhop/repos/wright/.github/dependabot.yml)
Configure weekly automated updates for Python, npm, Docker, and GitHub Actions dependencies with grouped PRs.

## Verification Plan

### Automated Tests
- Parse all YAML files locally using a Python verification script:
  ```bash
  python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml', recursive=True)]"
  ```

### Manual Verification
- Review YAML schemas against GitHub's official schema specifications.
- Verify Pull Request template markdown renders cleanly.
