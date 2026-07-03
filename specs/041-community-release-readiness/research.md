# Research: Community Release Readiness

## Decision: Treat Docker as the primary end-user appliance path

**Rationale**: Wright already ships an appliance-style Dockerfile and Compose files that combine the API, web UI, Hermes gateway integration, and local state. This is the fastest path for curious users, Windows 11 users through Linux containers, and Linux workstation users.

**Alternatives considered**:

- Source checkout as the default install path: useful for contributors, but too much friction for first-time users.
- PyPI as the primary end-user install path: attractive command shape, but Wright includes a web app, containerized services, local state, and optional tool/runtime dependencies that do not fit cleanly into a single Python package today.
- Native desktop as the default path: potentially valuable later, but it requires separate packaging and support expectations.

## Decision: Publish one alpha PyPI project, `wright-engineering`

**Rationale**: `wright` and `wright-core` are already taken on PyPI, and publishing multiple interdependent component packages would create avoidable dependency and ownership risk for the public alpha. The alpha should expose a single user-facing package, `wright-engineering`, through PyPI/TestPyPI Trusted Publishing. Component package publication is deferred until package names, dependency boundaries, and Hermes mirror requirements are reworked deliberately.

**Setup status**:

- PyPI account and 2FA are configured.
- TestPyPI account and 2FA are configured.
- Trusted Publishing pending publishers are configured for `wright-engineering` with GitHub owner `burhop`, repository `wright`, workflow `publish-python-packages.yml`, and environments `pypi`/`testpypi`.

**Alternatives considered**:

- Publish `wright`: rejected because the name is taken.
- Publish existing component package names such as `wright-core`: rejected because at least `wright-core` is taken by someone else and the component dependency graph is not alpha-ready for public PyPI.
- Publish a broad name such as `engineering`: rejected because it is too generic and not clearly owned by Wright.
- Avoid PyPI until stable: rejected because a small public helper package is useful for discovery and future CLI/bootstrap workflows.

## Decision: Publish one image name with multi-platform variants where validation permits

**Rationale**: One public image name is easier for users. Multi-platform manifests allow Windows 11 Docker Desktop and Linux workstations to pull the matching Linux image variant automatically when both variants are published.

**Alternatives considered**:

- Separate image names per platform: clearer for maintainers, but more confusing for users and documentation.
- Only publish amd64: simpler initially, but incomplete for Dell GB10-class ARM Linux systems.
- Publish unvalidated arm64: creates support risk and contradicts the public-alpha safety posture.

## Decision: Keep Hermes Desktop packaging separate from the Wright container

**Rationale**: Docker is appropriate for the local Wright service and web UI. Native desktop application packaging has different expectations and should connect to or manage the local service rather than being presented as a Windows GUI inside a container.

**Alternatives considered**:

- Windows container with Hermes Desktop and Wright: poor fit for Linux hosts and GUI desktop expectations.
- Bundle everything in the Wright appliance: raises image size, platform, and support complexity.

## Decision: Use public docs and repository metadata as the first visibility layer

**Rationale**: The README, docs landing pages, package listings, container listing, release notes, and GitHub metadata are the discovery surfaces users already encounter. They should consistently answer what Wright is, who it is for, how to try it, and how to contribute or sponsor.

**Alternatives considered**:

- Start with marketing campaigns before docs are ready: generates attention before users can succeed.
- Build a separate marketing site first: useful later, but unnecessary before public-alpha install paths are solid.

## Decision: Start funding with existing GitHub Sponsors and document the evolution path

**Rationale**: The repository already has a GitHub sponsor button. The next step is to explain what funds support and decide whether project-level funding should use an organization, fiscal host, company, or combination.

**Alternatives considered**:

- Wait for a company structure before accepting support: delays early support and hardware/resource contributions.
- Only use individual sponsorship forever: simple, but may not fit transparent project expenses, customer invoicing, or contributor payouts.

## Decision: Prepare NVIDIA and Dell partner materials as a brief, not a code dependency

**Rationale**: Wright's ties to local AI, workstations, and engineering automation make NVIDIA and Dell relevant for partner outreach. The release-readiness feature should prepare a concise brief and application checklist without adding vendor dependencies to the product.

**Alternatives considered**:

- Add vendor-specific runtime behavior now: premature and outside public-alpha release readiness.
- Ignore partner programs until after launch: misses a useful funding and validation route.
