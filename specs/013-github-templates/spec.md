# Feature Specification: GitHub Templates & Issue Automation

**Feature Branch**: `013-github-templates`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "come up with a plan to implement docs/community-features/013-github-templates.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured Bug Reporting (Priority: P1)

As a user encountering an issue with the Wright toolbox, I want to submit a detailed, structured bug report so that maintainers receive all necessary debug information (reproduction steps, OS, logs, and Wright version) to resolve the issue quickly.

**Why this priority**: High-quality bug reports are critical to the project's reliability. Form-based submissions ensure that users cannot skip required diagnostic fields like Wright version or reproduction steps, preventing back-and-forth debugging comments.

**Independent Test**:
* Upload the Bug Report template to a GitHub test environment or inspect the YAML schema against GitHub's issue template syntax.
* Verify that the form displays textareas for description, reproduction, expected/actual behavior, required inputs for OS and Wright version, and dropdowns for environment details.
* Verify that issues created via this template automatically receive the `bug` and `needs-triage` labels.

**Acceptance Scenarios**:
1. **Given** a user opening a bug report, **When** they fill out the form and submit, **Then** a structured issue is created containing reproduction steps, environment details, and OS.
2. **Given** the bug report form, **When** a user attempts to submit without specifying the Wright version, **Then** the submission is blocked and the field is highlighted as required.

---

### User Story 2 - Structured Feature Suggestions (Priority: P1)

As an engineer, designer, or product manager with an idea for improving the Wright toolbox, I want to submit a feature request detailing the problem, solution, and affected components so that the community can review and scope it.

**Why this priority**: Encourages clear, use-case-driven enhancements rather than vague feature requests. It guides contributors to think through solutions and declare whether they want to implement it themselves.

**Independent Test**:
* Inspect the feature request YAML template.
* Verify it collects use cases, proposed solutions, alternatives, component dropdowns, and willingness to contribute.
* Verify that issues created via this template automatically receive the `enhancement` and `needs-triage` labels.

**Acceptance Scenarios**:
1. **Given** a feature request form, **When** submitted, **Then** the generated issue clearly highlights the target Wright component (API, Web UI, etc.) and the contributor's willingness to help.

---

### User Story 3 - Issue Redirection & Security Gating (Priority: P2)

As a community member seeking general usage help or wanting to report a security vulnerability, I want to be redirected to Discussions or the security policy instead of creating a public bug issue.

**Why this priority**: Prevents the issue tracker from being cluttered with questions, and protects the repository from public disclosure of sensitive zero-day security vulnerabilities.

**Independent Test**:
* Verify that `config.yml` disables blank issue creation.
* Verify that links are present directing general questions to the Discussions Q&A section and security reports to `SECURITY.md`.

**Acceptance Scenarios**:
1. **Given** a user navigating to the new issue page, **When** they look for help, **Then** they are presented with a button that redirects them to GitHub Discussions Q&A.
2. **Given** the issue chooser page, **When** a security vulnerability is reported, **Then** the user is directed to the project's security policy.

---

### User Story 4 - Standardized Contributions (PR Template) (Priority: P2)

As a contributor submitting code changes, I want to see a pull request checklist to ensure my contribution meets project standards, passes tests, and complies with the project constitution.

**Why this priority**: Helps maintainers review PRs faster by ensuring contributors self-validate their changes, test coverage, and constitution compliance before submitting.

**Independent Test**:
* Verify that creating a pull request automatically pre-populates the description with the PR template.
* Verify the checklist includes CONTRIBUTING.md alignment, test updates, documentation checks, and spec-kit/constitution compliance items.

**Acceptance Scenarios**:
1. **Given** a new pull request, **When** the creation page loads, **Then** the PR description field is pre-populated with the checklist and description templates.

---

### User Story 5 - Automated Dependency Updates (Dependabot) (Priority: P3)

As a project maintainer, I want dependencies across our python, npm, docker, and github actions ecosystems to be automatically checked and updated weekly without creating PR noise.

**Why this priority**: Keeps the project secure and up-to-date while protecting maintainers from notification fatigue through dependency grouping and open PR limits.

**Independent Test**:
* Verify `dependabot.yml` exists in `.github/` and configures the `pip`, `npm`, `github-actions`, and `docker` package managers.
* Verify update frequency is weekly, open PR limits are set, and minor/patch updates are grouped.

**Acceptance Scenarios**:
1. **Given** dependabot is active, **When** weekly checks run, **Then** dependabot groups minor and patch updates into single consolidated PRs for each ecosystem, keeping open PR counts within limits.

---

### Edge Cases

* **GitHub Discussions is not yet enabled on the repo**: The issue chooser configuration will point to discussions links. If discussions are not enabled, these links will result in a 404 or redirect to the discussions homepage. The repository owner must enable discussions in repository settings.
* **Non-YAML issue templates exist**: Any existing markdown bug/feature templates under `.github/ISSUE_TEMPLATE/` must be removed so they do not conflict with the new YAML forms.

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: The repository MUST include a YAML-based Bug Report issue template at `.github/ISSUE_TEMPLATE/bug_report.yml`.
* **FR-002**: The Bug Report form MUST require bug description, reproduction steps, expected behavior, operating system, and Wright version, with optional environment details and log/screenshot uploads.
* **FR-003**: The Bug Report template MUST auto-apply the `bug` and `needs-triage` labels.
* **FR-004**: The repository MUST include a YAML-based Feature Request issue template at `.github/ISSUE_TEMPLATE/feature_request.yml`.
* **FR-005**: The Feature Request form MUST require feature summary, use case/problem description, proposed solution, and willingness to contribute dropdown.
* **FR-006**: The Feature Request template MUST auto-apply the `enhancement` and `needs-triage` labels.
* **FR-007**: The repository MUST include an issue chooser config at `.github/ISSUE_TEMPLATE/config.yml` which disables blank issues, lists the templates, and redirects Q&A to Discussions and security to `SECURITY.md`.
* **FR-008**: The repository MUST include a Pull Request template at `.github/PULL_REQUEST_TEMPLATE.md` containing change descriptions, related issues, and standard checklists (testing, docs, CONTRIBUTING.md, and constitution.md).
* **FR-009**: The repository MUST include a Dependabot configuration at `.github/dependabot.yml` targeting pip, npm, docker, and github-actions on a weekly check schedule with grouped updates and an open PR limit of 5 per ecosystem.
* **FR-010**: The feature MUST document a standardized set of labels (Priority, Type, Status, Component, Contributor) with colors and descriptions for repository setup.
* **FR-011**: None of the changes made by this feature may modify application code, configuration files (other than templates/dependabot), or Docker compose configurations.

### Key Entities

* **Issue Template**: A GitHub-native configuration file (YAML) defining a structured issue submission form.
* **PR Template**: A markdown template pre-populating pull request descriptions with guidelines and checkboxes.
* **Dependabot Config**: A YAML file instructing GitHub to check for and submit package manager dependency upgrades.

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: 100% of the 5 configuration files (`bug_report.yml`, `feature_request.yml`, `config.yml`, `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`) exist in the `.github/` directory and follow valid GitHub syntax schemas.
* **SC-002**: Blank issue creation is successfully disabled in the issue chooser config.
* **SC-003**: Dependabot limits open pull requests to a maximum of 5 concurrent updates per package ecosystem.
* **SC-004**: The documentation includes a complete list of 20+ standard labels with hex colors and clear descriptions.
* **SC-005**: All existing markdown-based issue templates in the `.github/ISSUE_TEMPLATE/` directory are removed.

## Standard Label Set

To organize project issues and contributions, a standardized set of 23 labels across five categories (Priority, Type, Status, Component, and Contributor) is defined below:

### Priority Labels
* `priority: critical` (Color: `b60205`): Immediate action required; blocks releases or breaks core features.
* `priority: high` (Color: `d93f0b`): High priority; should be resolved in the next release.
* `priority: medium` (Color: `fbca04`): Normal priority; scheduled for development.
* `priority: low` (Color: `0e8a16`): Low priority; nice to have when time permits.

### Type Labels
* `type: bug` (Color: `d73a4a`): Something isn't working as expected.
* `type: feature` (Color: `a2eeef`): New feature request or enhancement.
* `type: documentation` (Color: `0075ca`): Improvements or additions to documentation.
* `type: refactor` (Color: `7057ff`): Code changes that do not modify behavior (style, cleanup).
* `type: test` (Color: `c5def5`): Adding or correcting tests.
* `type: maintenance` (Color: `d4c5f9`): General maintenance, CI/CD, dependency updates, or chore.

### Status / Triage Labels
* `needs-triage` (Color: `fbca04`): New issue requiring classification and verification.
* `status: investigation` (Color: `bfdadc`): Under investigation to identify root cause or feasibility.
* `status: backlogged` (Color: `ffffff`): Postponed; not planned for immediate work.
* `status: in-progress` (Color: `006b75`): Currently being worked on.
* `status: blocked` (Color: `e99695`): Blocked by another issue, dependency, or upstream change.

### Component Labels
* `component: api` (Color: `1d76db`): Issues or features related to the core API server.
* `component: web-ui` (Color: `fef2c0`): Issues or features related to the React/Vite web interface.
* `component: agent-adapters` (Color: `bfd4f2`): Related to agent interaction, integration, or abstraction layers.
* `component: tool-registry` (Color: `bfd4f2`): Related to deterministic tool definitions and registration.
* `component: docker` (Color: `c2e0c6`): Dockerfiles, Docker Compose, or appliance orchestration.
* `component: mcp-tools` (Color: `f9d0c4`): Model Context Protocol tools or server integrations.

### Contributor Experience Labels
* `good-first-issue` (Color: `7057ff`): Good for newcomers to the project.
* `help-wanted` (Color: `008672`): Extra attention is needed; community contributions welcome.

## Assumptions

* The repository owner will manually enable GitHub Discussions via settings and configure categories (Announcements, Q&A, Ideas, Show & Tell) as documented.
* Standard label sets will be created manually by the repository owner or using a provided script.
* Dependabot runs automatically once the `dependabot.yml` file is merged into the default branch.

