# Research: GitHub Templates & Issue Automation

**Branch**: `013-github-templates` | **Date**: 2026-06-05

## Technical Decisions & Rationale

### 1. Form-Based Issue Templates (YAML vs Markdown)
* **Decision**: Implement bug reports and feature requests as YAML-based forms (`.github/ISSUE_TEMPLATE/bug_report.yml` and `feature_request.yml`) rather than legacy markdown templates.
* **Rationale**: YAML forms allow us to enforce required fields (such as Wright version, OS, reproduction steps) using validation blocks, preventing users from submitting incomplete reports. It also allows dropdown selections (e.g., environment type, affected components), ensuring structured data.
* **Alternatives Considered**: 
  - *Markdown Templates*: Easier to write, but users often delete or ignore the placeholder sections, leading to low-quality bug reports.

### 2. General Questions & Support Redirection
* **Decision**: Redirect Q&A and general support queries to GitHub Discussions using `.github/ISSUE_TEMPLATE/config.yml`.
* **Rationale**: Keeps the issue tracker focused on actionable bugs and features. GitHub Discussions provides a threaded, searchable community space with "mark as answered" features.
* **Alternatives Considered**:
  - *Support Issue Template*: Creating issues for support requests. Discarded because support questions do not have code closure conditions and pollute project metrics.

### 3. Security Vulnerability Gating
* **Decision**: Redirect security vulnerability reports to `SECURITY.md` (or standard security reporting pipelines) in the issue chooser configuration.
* **Rationale**: Publicly disclosing zero-day security vulnerabilities in public issues places users at risk. Directing users to a private disclosure channel first is an industry-standard security best practice.

### 4. Pull Request Checklist lightweight design
* **Decision**: Keep the PR template concise, focusing on core verification checkboxes (passing tests, CONTRIBUTING.md, and constitution.md) with a clear description block.
* **Rationale**: Lightweight templates encourage community participation by reducing the friction of opening a pull request, while still ensuring project standards are met.

### 5. Dependabot Weekly Grouping Strategy
* **Decision**: Group minor and patch upgrades into a single weekly pull request per ecosystem (pip, npm, docker, github-actions) and set a concurrent PR limit of 5.
* **Rationale**: Dependabot can generate significant notification noise. Grouping minor updates ensures dependencies stay updated without overwhelming the repository owner with individual pull requests.
