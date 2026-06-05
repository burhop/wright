# Feature Specification: Repo Hygiene & Legal Foundation

**Feature Branch**: `011-repo-hygiene`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Implement the feature described in docs/community-features/011-repo-hygiene.md — Add all missing community health files (LICENSE, CODE_OF_CONDUCT, SECURITY, CONTRIBUTING, CODEOWNERS, SUPPORT) and clean up the repository root directory so the Wright project meets the minimum standard expected by open-source contributors and GitHub's Community Profile checklist."

## User Scenarios & Testing

### User Story 1 — License and Legal Clarity (Priority: P1)

A potential contributor or user visits the Wright GitHub repository to evaluate whether they can use the project in their own work or contribute code. They look for a LICENSE file in the repository root. Finding a clear, permissive license (MIT), they understand they can freely use, modify, and distribute the software, including in commercial products, with minimal restrictions.

**Why this priority**: Without a license, no external developer can legally use, fork, or contribute to Wright. This is the single most critical blocker for community adoption and is a prerequisite for every other community engagement activity.

**Independent Test**: Visit the GitHub repository page and verify that the license badge is displayed automatically by GitHub in the repository sidebar, and that the LICENSE file is present and contains a valid MIT license text.

**Acceptance Scenarios**:

1. **Given** the Wright repository, **When** a visitor views the repository on GitHub, **Then** the sidebar displays "MIT License" with a link to the LICENSE file.
2. **Given** a LICENSE file in the repository root, **When** its content is read, **Then** it contains the full MIT license text with the correct copyright holder name and current year.
3. **Given** a downstream project that depends on Wright, **When** they include Wright's license notice, **Then** they satisfy all legal obligations with a single copyright line and the MIT license text.

---

### User Story 2 — Contributor Onboarding Guide (Priority: P1)

A developer interested in contributing to Wright looks for a CONTRIBUTING.md file to understand how to set up their development environment, follow the project's coding standards, and submit pull requests. They find a comprehensive guide that walks them through the entire workflow — from prerequisites and installation, through the spec-kit development methodology, to the PR submission process.

**Why this priority**: The contributing guide is the primary onboarding path for external contributors. Without it, only people with direct access to maintainers can effectively contribute, which limits community growth.

**Independent Test**: A new developer follows the CONTRIBUTING.md instructions from start to finish and is able to set up their local environment, create a feature branch, and understand the PR checklist requirements without needing additional guidance.

**Acceptance Scenarios**:

1. **Given** the CONTRIBUTING.md file, **When** a new developer reads it, **Then** they can identify all prerequisites (runtime versions, package managers, optional tools) needed to set up the development environment.
2. **Given** a contributor who has never used spec-kit, **When** they read the development workflow section, **Then** they understand the specify → plan → tasks → implement lifecycle and know which commands to run.
3. **Given** a contributor ready to submit code, **When** they read the PR submission section, **Then** they find a clear checklist of what reviewers expect (tests pass, docs updated, constitution compliance, branch naming).
4. **Given** a new contributor looking for starter tasks, **When** they read the "Good First Issue" section, **Then** they know where to find beginner-friendly tasks and how to claim them.

---

### User Story 3 — Community Standards and Safety (Priority: P2)

A community member or potential contributor evaluates whether the Wright project is a safe and welcoming place to participate. They find a CODE_OF_CONDUCT.md that sets clear behavioral expectations, and a SECURITY.md that provides a responsible disclosure pathway for reporting vulnerabilities.

**Why this priority**: Community standards and security policies are table-stakes for any serious open-source project. GitHub's Community Profile checker flags repositories that lack these files, and experienced open-source contributors use their presence as a signal of project maturity.

**Independent Test**: Navigate to the repository's "Community" tab on GitHub and verify that both the Code of Conduct and Security Policy show green checkmarks in the Community Profile.

**Acceptance Scenarios**:

1. **Given** the CODE_OF_CONDUCT.md file, **When** its content is read, **Then** it contains the Contributor Covenant v2.1 standard text with project-specific contact information for reporting violations.
2. **Given** a security researcher who discovers a vulnerability, **When** they read SECURITY.md, **Then** they find a private contact channel (email), an expected response timeframe, and an explicit instruction not to use public GitHub Issues.
3. **Given** GitHub's Community Profile checker, **When** it evaluates the Wright repository, **Then** it shows green checkmarks for both Code of Conduct and Security Policy.

---

### User Story 4 — Support Channel Guidance (Priority: P2)

A user encountering an issue with Wright needs to know where to get help. They find a SUPPORT.md file that directs them to the appropriate channel — GitHub Discussions for questions, the documentation for self-service answers, and GitHub Issues for confirmed bugs.

**Why this priority**: Clear support guidance reduces noise in the issue tracker (preventing "how do I...?" questions from cluttering bug reports) and helps users find answers faster.

**Independent Test**: A user looking for help finds SUPPORT.md and is directed to the correct channel for their type of question (Q&A, bug report, or documentation).

**Acceptance Scenarios**:

1. **Given** a user with a usage question, **When** they read SUPPORT.md, **Then** they are directed to GitHub Discussions Q&A rather than opening an issue.
2. **Given** a user who found a bug, **When** they read SUPPORT.md, **Then** they are directed to GitHub Issues with guidance on providing reproduction steps.
3. **Given** SUPPORT.md, **When** GitHub's Community Profile checker evaluates the repository, **Then** it shows a green checkmark for the Support resource.

---

### User Story 5 — Code Ownership and Review Assignment (Priority: P2)

A contributor submits a pull request that modifies files in the API backend. GitHub automatically assigns the appropriate code owner as a reviewer based on the CODEOWNERS file, ensuring that changes to critical areas are reviewed by domain experts.

**Why this priority**: Automated reviewer assignment reduces maintainer burden and ensures that changes to specialized areas (Docker, API, frontend, specs) are reviewed by the right people.

**Independent Test**: Submit a test PR that modifies a file in `apps/api/` and verify that the CODEOWNERS-designated reviewer is automatically requested.

**Acceptance Scenarios**:

1. **Given** a CODEOWNERS file in `.github/CODEOWNERS`, **When** a PR modifies files in `apps/api/` or `packages/`, **Then** the designated backend reviewer is automatically requested.
2. **Given** a PR that modifies files in `apps/web/`, **When** it is opened, **Then** the designated frontend reviewer is automatically requested.
3. **Given** a PR that modifies files in `docker/` or `.github/workflows/`, **When** it is opened, **Then** the designated infrastructure reviewer is automatically requested.

---

### User Story 6 — Repository Cleanup and Professional Appearance (Priority: P3)

A visitor browsing the Wright repository on GitHub sees a clean, organized root directory without stale log files, debug output, or misplaced screenshots. The `.gitignore` file properly excludes temporary and generated files from version control, presenting a professional project image.

**Why this priority**: A cluttered repository root with log files and debug output signals an unmaintained or amateur project. While this doesn't affect functionality, it directly impacts first impressions and community trust.

**Independent Test**: List the files in the repository root and verify that no log files, debug output files, or stale screenshots appear in version control.

**Acceptance Scenarios**:

1. **Given** the updated `.gitignore`, **When** `git status` is run, **Then** files matching `phase*.log`, `ps_debug.log`, `tests_output*.txt`, `test-*-output.log`, `screenshot_*.png`, and `state.db` are not tracked.
2. **Given** screenshots referenced by documentation, **When** they are needed, **Then** they are located in `docs/images/` rather than the repository root.
3. **Given** a fresh clone of the repository, **When** the root directory is listed, **Then** only project-relevant files and directories appear (no temporary or debug artifacts).

---

### User Story 7 — Repository Discoverability via Metadata (Priority: P3)

A developer searching GitHub for "local AI mechanical engineering" or "offline agentic framework" finds Wright in the search results because the repository has a descriptive "About" section, rich topic tags, and proper metadata. When they share the repository link on Slack or Twitter, the social preview shows a professional description.

**Why this priority**: Without metadata and topics, Wright is invisible in GitHub search. Topic tags are the primary mechanism for GitHub discovery, and the "About" description appears in search result snippets.

**Independent Test**: Search GitHub for "ai-agent mechanical-engineering local-first" and verify Wright appears in the results. Share the repository link and verify the social preview displays the description.

**Acceptance Scenarios**:

1. **Given** the repository metadata configuration guide, **When** the repo owner applies the recommended settings, **Then** the GitHub sidebar shows the project description and 20 topic tags.
2. **Given** a user searching GitHub for "ai-agent mechanical-engineering", **When** search results are displayed, **Then** Wright appears with its description visible.
3. **Given** a documented metadata configuration, **When** the repo owner reviews it, **Then** they find step-by-step instructions for setting the description, topics, and website URL.

---

### Edge Cases

- What happens if GitHub changes the Community Profile requirements? The community health files follow well-established standards (Contributor Covenant, MIT license) that have been stable for years. If requirements change, the files can be updated independently.
- What happens if the CODEOWNERS file references GitHub usernames that don't exist? GitHub will silently skip invalid usernames. The CODEOWNERS file should use the repository owner's actual GitHub username and be updated as team members join.
- What happens if a contributor submits a security vulnerability via a public GitHub Issue despite SECURITY.md instructions? Maintainers should immediately move the discussion to a private channel (GitHub Security Advisories) and close the public issue with a note pointing to SECURITY.md.
- What happens if the `.gitignore` changes cause tracked files to remain in git history? The `.gitignore` only prevents future tracking. Existing tracked files must be explicitly removed from the index with `git rm --cached` before they disappear from the repository.
- What happens if the copyright holder in the LICENSE file needs to change? The MIT license permits relicensing by the copyright holder. The name in the LICENSE file should match the entity that owns the project (individual or organization).

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST contain a LICENSE file in the root directory with a valid MIT license, including the correct copyright holder name and the year 2026.
- **FR-002**: The repository MUST contain a CODE_OF_CONDUCT.md file using the Contributor Covenant v2.1 standard text with project-specific enforcement contact information.
- **FR-003**: The repository MUST contain a SECURITY.md file that specifies a private reporting channel, expected response timeframes, supported versions, and a prohibition on public issue filing for security vulnerabilities.
- **FR-004**: The repository MUST contain a SUPPORT.md file that directs users to the appropriate channel (Discussions, Issues, or documentation) based on their type of need.
- **FR-005**: The repository MUST contain a CONTRIBUTING.md file covering: development environment prerequisites, the spec-kit development workflow, branch naming conventions, code style enforcement rules, pull request submission process, constitution governance compliance, and guidance on finding beginner-friendly tasks.
- **FR-006**: The repository MUST contain a `.github/CODEOWNERS` file that maps file paths to designated reviewers for at least: backend code (`apps/api/`, `packages/`), frontend code (`apps/web/`), infrastructure (`docker/`, `.github/workflows/`), and specifications (`specs/`, `.specify/`).
- **FR-007**: The `.gitignore` file MUST be updated to exclude: log files (`phase*.log`, `ps_debug.log`), test output files (`tests_output*.txt`, `test-*-output.log`, `test-live-*.log`), stale screenshots (`screenshot_*.png`), and database files (`state.db`).
- **FR-008**: Any screenshots referenced by existing documentation MUST be relocated to `docs/images/` with references updated accordingly.
- **FR-009**: The repository MUST include a documented metadata configuration guide that specifies the recommended GitHub "About" description, all 20 topic tags, and instructions for the repo owner to apply them.
- **FR-010**: None of the community health files may modify existing source code (Python, TypeScript), Docker files, CI/CD workflows, or the README.md file.

### Key Entities

- **Community Health File**: A standardized document (LICENSE, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, SUPPORT) placed in the repository root or `.github/` directory that GitHub recognizes and indexes in the Community Profile.
- **CODEOWNERS Mapping**: A rule associating file path patterns with GitHub usernames/teams for automated review assignment on pull requests.
- **Repository Metadata**: Non-file configuration (description, topics, website URL) set through the GitHub web interface that affects search discoverability and social sharing.

## Success Criteria

### Measurable Outcomes

- **SC-001**: GitHub's Community Profile checker shows green checkmarks for all available community health indicators (License, Code of Conduct, Contributing, Security Policy, Support).
- **SC-002**: 100% of the 7 required community health files (LICENSE, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, CONTRIBUTING.md, CODEOWNERS, metadata guide) are present and contain complete, non-placeholder content.
- **SC-003**: The repository root directory contains zero log files, debug output files, or stale test output files in version control after the cleanup.
- **SC-004**: A new contributor can identify all development prerequisites and understand the PR submission process by reading CONTRIBUTING.md alone, without needing external guidance.
- **SC-005**: The repository metadata configuration guide contains a recommended description under 120 characters and all 20 topic tag slots populated with relevant keywords.
- **SC-006**: All community health files are created without modifying any existing source code, Docker files, CI/CD workflows, or README.md.

## Assumptions

- The copyright holder for the MIT license is the repository owner (burhop). If this is an organization, the name should be updated accordingly.
- The CODEOWNERS file will initially use the repository owner's GitHub username for all paths, since the project does not yet have a multi-person team. As contributors join, CODEOWNERS will be updated.
- The GitHub "About" metadata (description, topics, website URL) cannot be set via files — it requires the repository owner to configure them through the GitHub web interface. The deliverable for this item is a documented configuration guide.
- The SECURITY.md contact email will use the repository owner's preferred security reporting email. If no dedicated security email exists, a personal email or GitHub Security Advisories feature will be used as the reporting channel.
- The project does not yet have GitHub Discussions enabled. SUPPORT.md will reference Discussions as a future resource and provide GitHub Issues as the current primary support channel.
- Removing files from `.gitignore` tracking does not remove them from git history — a separate `git rm --cached` step is needed for any files currently tracked that should be excluded.
