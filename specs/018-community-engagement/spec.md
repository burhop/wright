# Feature Specification: Community Engagement Infrastructure

**Feature Branch**: `018-community-engagement`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Set up the communication channels, example projects, and marketing assets needed to attract users and contributors to Wright."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Examples and Getting Started (Priority: P1)

As a new user discovering Wright, I want to run self-contained, working example projects using Docker so that I can quickly understand Wright's CAD and analysis capabilities.

**Why this priority**: It is the most critical MVP component for user activation. If users cannot quickly run examples to see the value, they will not engage further with the community.

**Independent Test**: Execute the example projects against a running Wright Docker agent container and verify they generate the expected results (API connection check, bracket design, and bolt analysis) without local development environment setups.

**Acceptance Scenarios**:

1. **Given** a running Wright Docker container, **When** a user executes the `quickstart` script, **Then** it successfully connects to the API and outputs a verification message.
2. **Given** a running Wright Docker container, **When** a user runs the `bracket-design` example, **Then** it runs the CAD tool via the API and outputs a completed CAD file in the output directory.
3. **Given** a running Wright Docker container, **When** a user runs the `bolt-analysis` example, **Then** it processes the calculation inputs and outputs stress analysis reports.

---

### User Story 2 - Community Communication Channels & Integrations (Priority: P2)

As a user or contributor, I want to easily find and join the project's Discord server and GitHub Discussions, and find clear guidelines on how to get support or contribute.

**Why this priority**: Establishes the communication loops so that users who run the examples can ask questions, get support, and collaborate on future feature work.

**Independent Test**: Verify all links to Discord and Discussions are present and correct in `README.md`, `CONTRIBUTING.md`, `SUPPORT.md`, and the docs site, and verification/moderation instructions are clearly documented.

**Acceptance Scenarios**:

1. **Given** a visitor on the GitHub repository page or documentation site, **When** they view the README or navigation header, **Then** they see direct links to join the Discord server and visit GitHub Discussions.
2. **Given** a user joining the Discord server, **When** they land on the server, **Then** they are presented with a configured list of standard channels (`#announcements`, `#general`, `#support`, `#contributing`, `#showcase`, `#off-topic`), basic rules, and spam filters.

---

### User Story 3 - Launch Assets and Contributor Curation (Priority: P3)

As a project maintainer preparing to launch Wright, I want high-quality draft blog posts, a demo video script, curated good first issues, and contributor recognition tooling ready so that the launch is professional and welcoming.

**Why this priority**: Helps scale the project visibility and contributor base after the core community channels are established.

**Independent Test**: Verify that the blog post draft, demo script, curated issues, awesome list submission drafts, and contributor recognition configurations exist as complete documents in the workspace with no placeholders.

**Acceptance Scenarios**:

1. **Given** the need to share the project with the public, **When** the maintainer opens `docs/blog/introducing-wright.md`, **Then** they find a complete, ready-to-publish 1500-2000 word blog post detailing the local-first architecture and features.
2. **Given** a new code contribution, **When** the contribution is merged, **Then** the maintainer can add the contributor to `.all-contributorsrc` and update the README contributors list using the documented recognition tools.

---

### Edge Cases

- **Expired Discord invite links**: If the invite link configured in README or docs expires or becomes invalid, users will be unable to join. The Discord setup instructions must explicitly guide the administrator to create a permanent, non-expiring invite link.
- **Running examples without Docker**: If a user runs the example scripts without a running Wright Docker container or local server, the scripts must fail gracefully with a clear error message directing them to start the container.
- **Fast-evolving API endpoints**: If API endpoints change, example projects will fail. The examples must only use stable, public-facing API endpoints.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain a `docs/community/discord-admin.md` file detailing the Discord server channel architecture, permission model, rules configuration, and permanent link creation instructions.
- **FR-002**: The README.md, CONTRIBUTING.md, and SUPPORT.md files MUST be updated to include links to the Discord server and GitHub Discussions.
- **FR-003**: The project MUST contain three runnable example projects under `examples/` (`quickstart/`, `bracket-design/`, and `bolt-analysis/`), each including a `README.md` with instructions.
- **FR-004**: Example projects MUST run against the standard Wright Docker agent container, using standard inputs, without needing local code compilation or extra packages.
- **FR-005**: The project MUST include draft files: `docs/blog/introducing-wright.md` (launch blog post), `docs/demo-script.md` (video demo walkthrough), `docs/good-first-issues.md` (5-10 curated tasks for new contributors), and `docs/awesome-list-submissions.md` (Awesome list PR descriptions).
- **FR-006**: A contributor recognition config `.all-contributorsrc` MUST be initialized in the root directory, and contributor recognition instructions/commands added to `CONTRIBUTING.md` and the `README.md`.
- **FR-007**: A star-history.com badge embed MUST be added to `README.md` to track project engagement.

### Key Entities

- **all-contributors configuration**: Structured configuration file `.all-contributorsrc` that tracks contributor names, profile links, and types of contributions (code, docs, design) to auto-render contributors.
- **example-project structure**: Relies on a unified layout including a project script, a dedicated `README.md` for running instructions, input templates, and expected output configurations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can launch the Wright container and successfully execute any of the three example projects in under 5 minutes.
- **SC-002**: 100% of entry points (Discord invite links, GitHub Discussions references) in root markdown files are active, clickable, and lead to the correct targets.
- **SC-003**: The launch blog post and demo script drafts are complete (containing at least 1500 words for the post and a full scene-by-scene script for the video) with zero "TODO" or placeholder markers.
- **SC-004**: Adding a new contributor to the project takes under 1 minute using the configured all-contributors workspace tool.

## Assumptions

- **Target Audience**: Users running the examples have basic experience running shell commands and Docker.
- **Offline Capabilities**: Example projects are designed to run in offline environments, matching Wright's offline-first architecture.
- **API Stability**: The examples will utilize only the core, stable endpoints of the Wright API.
