# Feature Specification: Community Release Readiness

**Feature Branch**: `041-community-release-readiness`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Use Spec Kit to define and execute a plan for making Wright easy to install across user use cases, making Wright visible so people find it, and setting up funding paths for Wright application work."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install Wright for the Right Use Case (Priority: P1)

A prospective user can identify their use case and complete the recommended Wright install path without needing to infer which channel applies to them.

Target use cases:

- Curious user/demo user who wants the fastest local web UI.
- Windows 11 user who wants Wright on a laptop.
- Linux workstation or Dell GB10 user who wants local engineering workflows.
- Hermes Desktop user who wants Wright integration.
- Python developer who wants installable packages for extension work.
- MCP/tool contributor who wants to validate and package engineering tools.
- Enterprise evaluator who needs offline-first, security, release, and support information.
- Sponsor or customer who needs to understand what Wright does and how to support it.

**Why this priority**: Install friction blocks every other goal. A usable public release must make the correct first command obvious for each audience.

**Independent Test**: A reviewer can choose each listed use case, follow the documented path from the public entry point, and reach a clear success or readiness check without asking a maintainer which path to use.

**Acceptance Scenarios**:

1. **Given** a user wants to try Wright quickly, **When** they read the public installation guidance, **Then** they see a recommended local appliance path with required prerequisites, configuration expectations, and a verification step.
2. **Given** a Windows 11 user wants Wright locally, **When** they read the Windows guidance, **Then** they understand the supported runtime model, what runs natively, what runs in the local appliance, and how to verify the result.
3. **Given** a Linux or Dell GB10 user wants local AI and engineering workflows, **When** they read the Linux guidance, **Then** they see architecture, hardware, optional acceleration, and selected-tool limitations called out before install.
4. **Given** a Hermes Desktop user wants Wright integration, **When** they read the Hermes guidance, **Then** they understand how the desktop experience relates to the Wright local appliance and plugin.
5. **Given** a Python developer wants Wright packages, **When** they inspect package guidance, **Then** they can distinguish end-user installation from library or plugin package installation.

---

### User Story 2 - Discover and Evaluate Wright Publicly (Priority: P2)

A person who has never heard of Wright can find it through common open-source discovery channels, understand its value within minutes, and see credible proof that the project is active.

**Why this priority**: Visibility turns release work into adoption. Clear positioning, metadata, demos, and public listings help users, contributors, and partners find Wright.

**Independent Test**: A reviewer starts from a search result, package page, container page, repository page, or announcement link and can explain Wright's target user, current alpha status, primary install path, and contribution path within five minutes.

**Acceptance Scenarios**:

1. **Given** a new visitor lands on Wright's public repository or documentation, **When** they scan the first screen, **Then** they see what Wright is, who it serves, how to try it, and where to learn more.
2. **Given** a visitor discovers Wright through a package or container listing, **When** they open that listing, **Then** it links back to the repository, documentation, release notes, security information, and funding/support information.
3. **Given** an engineering AI or MCP contributor is looking for places to help, **When** they review contribution guidance, **Then** they find suitable issue categories and a safe validation process.
4. **Given** a maintainer wants to measure outreach, **When** they review launch indicators, **Then** they can track repository, package, image, documentation, and community engagement signals.

---

### User Story 3 - Fund Wright Application Work (Priority: P3)

A supporter, sponsor, customer, or partner can understand what funding Wright buys, choose an appropriate support route, and contact or sponsor the project without private backchannel instructions.

**Why this priority**: Wright needs recurring resources for application work, model evaluation, engineering tool validation, and hardware testing. Funding paths must be visible and credible before outreach.

**Independent Test**: A reviewer can identify the current funding channels, sponsor tiers or support offers, what funds are used for, and how hardware or partner support would be handled.

**Acceptance Scenarios**:

1. **Given** an individual wants to sponsor Wright, **When** they follow the funding guidance, **Then** they reach an active sponsorship path and understand how funds help.
2. **Given** a company wants paid support or integration work, **When** they review the commercial-support guidance, **Then** they see appropriate engagement types and a contact path.
3. **Given** a hardware, cloud, or ecosystem partner evaluates Wright, **When** they review the partner brief, **Then** they can understand the local-first engineering AI value proposition and what validation or co-marketing is requested.
4. **Given** maintainers receive funds or donated resources, **When** they update public materials, **Then** project users can see the funding purpose and project status without ambiguity.

### Edge Cases

- A desired public name is unavailable or conflicts with an existing package, image, account, or project.
- A release channel is available but not yet suitable for stable users.
- A platform can run the local appliance but cannot run every selected engineering tool or GPU workflow.
- A user expects a full desktop GUI inside the local appliance when the supported model is native desktop plus local service.
- External funding or partner programs change eligibility, benefits, or terms.
- Public materials must avoid implying bundled LLMs, proprietary engineering tools, licenses, credentials, or cloud services.
- Enterprise evaluators require offline-first and security posture clarity before trying the product.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The public installation experience MUST list the supported user use cases and provide one recommended first path for each.
- **FR-002**: The public installation experience MUST clearly distinguish end-user appliance installation from developer package installation.
- **FR-003**: The public installation experience MUST define how users verify a successful install for each primary path.
- **FR-004**: The public installation experience MUST identify platform limitations and dependencies before users begin installation.
- **FR-005**: The release readiness materials MUST address Windows 11, Linux workstation, Dell GB10-class Linux, Hermes Desktop integration, Python developer, MCP contributor, enterprise evaluator, and sponsor/customer audiences.
- **FR-006**: The project MUST define a package naming strategy, including fallback names when a desired public name is unavailable.
- **FR-007**: The project MUST define a container distribution strategy that covers public image names, tag expectations, platform support, and verification expectations.
- **FR-008**: The project MUST ensure public package and container listings point to the canonical repository, documentation, release notes, issue tracker, security policy, and funding/support information.
- **FR-009**: The project MUST provide public-facing positioning that states what Wright does, who it is for, alpha status, local-first constraints, and bring-your-own-AI expectations.
- **FR-010**: The project MUST provide a visibility checklist covering repository metadata, documentation landing pages, demos, release notes, community contribution paths, and launch/outreach channels.
- **FR-011**: The project MUST define adoption and visibility indicators maintainers can monitor after launch.
- **FR-012**: The project MUST expose an active funding path for individual sponsorship.
- **FR-013**: The project MUST define whether project-level funding uses an individual sponsor profile, organization sponsor profile, fiscal host, company, or a combination.
- **FR-014**: The project MUST describe what funding supports, including compute, model/API testing, hardware validation, MCP catalog work, release hardening, and integration support.
- **FR-015**: The project MUST define commercial and partner support offers without implying unavailable commitments.
- **FR-016**: The project MUST identify relevant ecosystem partner programs and the materials needed to apply or engage.
- **FR-017**: The project MUST preserve Wright's offline-first and local-first messaging across installation, visibility, and funding materials.
- **FR-018**: The project MUST avoid publishing instructions that require unavailable secrets, private maintainer access, proprietary licenses, bundled model weights, or unverified platform support.

### Key Entities *(include if feature involves data)*

- **Use Case**: A target audience and installation/evaluation goal, including prerequisites, recommended path, verification step, and known limitations.
- **Distribution Channel**: A public mechanism through which users obtain Wright or Wright components, including package, container, source, plugin, or desktop integration channels.
- **Public Listing**: A package, container, repository, documentation, or announcement surface that describes Wright and routes users to canonical support and release information.
- **Funding Channel**: A sponsorship, fiscal host, commercial support, hardware support, cloud/API credit, or partner program route that supports Wright work.
- **Partner Brief**: A concise public or semi-public artifact explaining Wright's value proposition, validation needs, and requested support for ecosystem partners.
- **Visibility Indicator**: A measurable adoption signal such as package downloads, image pulls, repository stars, release downloads, documentation visits, discussions, or support inquiries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can identify the correct install path for each listed use case in under three minutes from the public repository or documentation entry point.
- **SC-002**: At least three primary install paths include a verification step that a maintainer or reviewer can execute or inspect during release readiness review.
- **SC-003**: Public package and container listings for supported release channels include canonical links to repository, documentation, issues, security policy, releases, and funding/support information.
- **SC-004**: The repository and documentation explain Wright's value proposition, alpha status, local-first model, and bring-your-own-AI expectations on their primary public entry surfaces.
- **SC-005**: The project has at least one active individual sponsorship path and a documented decision for project-level funding structure.
- **SC-006**: The project has a documented partner outreach packet for hardware, cloud, or ecosystem programs, including NVIDIA and Dell-aligned positioning.
- **SC-007**: The release readiness checklist can be reviewed by maintainers without unresolved public naming, platform support, or funding-path decisions.
- **SC-008**: Launch readiness materials define at least five visibility indicators for post-launch review.

## Assumptions

- Wright remains public-alpha software during this feature.
- The public PyPI alpha package is `wright-engineering`; `wright` is unavailable and component package publication is deferred for alpha.
- The public Docker Hub alpha image is `burhop/wright`; GHCR should use `ghcr.io/burhop/wright` for matching public image names.
- The public contact address is `wright@makerengineer.com`; inbound email automation is handled by the website/Resend setup outside this repository.
- Docker or equivalent local appliance distribution is the preferred end-user path for the first public release.
- Python package distribution is primarily for developers, plugins, and selected runtime components unless a dedicated end-user bootstrapper is explicitly approved.
- Hermes Desktop packaging is treated as a native desktop concern that can connect to or manage the Wright local service; it is not assumed to run as a full desktop GUI inside a container.
- Windows 11 support is expected through a local Linux container runtime unless later evidence supports a separate native Windows application package.
- Dell GB10-class support may require separate validation for processor architecture, acceleration, and selected engineering tools.
- Funding setup can begin with existing maintainer sponsorship and evolve toward an organization, company, or fiscal host as project needs mature.
- Public materials must be accurate even when external registries, funding platforms, or partner programs change over time.
