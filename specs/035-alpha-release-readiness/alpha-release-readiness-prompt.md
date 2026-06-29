# Wright Alpha Release Readiness Prompt

Use this prompt with Codex or another coding agent when preparing Wright for its
first public alpha release.

```text
You are working in the Wright repository. Your goal is to get `main` into a
clean, credible first public alpha state for developer exposure, MCP porting,
demos, and selected beta testers.

This is not a marketing-only pass. Treat it as a release-readiness sprint across
source, Docker distribution, CI, test coverage, documentation, GitHub project
hygiene, UI polish, security, and roadmap clarity.

Start by reading and following:

- AGENTS.md
- specs/034-engineering-mcp-catalog/plan.md
- docs/mcp-catalog/mcp-server-testing-process.md
- README.md
- ROADMAP.md
- docs/deployment-configurations.md
- docs/hermes-desktop-wright.md
- docs/contributing/testing.md
- docker/container-manifest.md
- existing GitHub templates and workflows under .github/

Important constraints:

- Wright is alpha software. Keep the docs honest: this release is for testing,
  MCP porting, demonstrations, and early developer feedback.
- Wright is bring-your-own-AI. Do not imply that an LLM, API key, local model,
  or hosted model is bundled unless it actually is.
- Preserve offline-first/local-first behavior.
- Do not add MCP-specific host software to the base Docker image just to make
  catalog validation pass. Follow docs/mcp-catalog/mcp-server-testing-process.md.
- Do not auto-enable unsafe, proprietary, credential-bound, hardware-bound, or
  destructive MCP actions.
- Keep work compatible with the existing modular monorepo boundaries:
  apps/api, apps/web, packages/*, hermes-plugin-wright, docker, docs, tests.
- If the working tree contains user changes, preserve them and work around them.
- Prefer small, reviewable commits or implementation slices if the work is too
  large for one PR.

Primary objective:

Prepare Wright so a public developer can discover the repo, understand alpha
status, choose a supported install path, run the software with their own LLM,
report useful bugs, and trust that CI catches the highest-risk regressions.

Deliverables:

1. Release readiness audit

   Produce an initial audit before editing broadly. Cover:

   - Current package and app structure.
   - Existing Docker images, compose files, ports, health checks, env vars, and
     persistent volume behavior.
   - Existing CI jobs and which tests they run.
   - Existing README, docs site, getting-started docs, Docker docs, Hermes
     plugin docs, roadmap, support, security, contributing, issue templates,
     pull request templates, release workflows, and versioning docs.
   - Existing UI theme/token/component consistency.
   - Data leak and secret exposure risks.
   - Current public-readiness gaps ranked by severity and release impact.

   Save the audit somewhere durable, for example:

   - docs/alpha-release-readiness.md
   - or specs/<next-feature>-alpha-release-readiness/

2. Docker distribution

   Design, implement, and document two public-use Linux Docker images:

   - Wright appliance image for NVIDIA DGX Spark, Dell GB10, and similar
     local-AI workstations.
   - Wright plus Hermes Desktop Linux image, with Hermes Desktop installed and
     Wright installed/configured so users can start from the image.

   For each image, document and test:

   - Supported architectures and any limits. Be explicit about linux/amd64,
     linux/arm64, NVIDIA GPU passthrough, and DGX Spark/GB10 assumptions.
   - Whether the image requires NVIDIA Container Toolkit, CUDA driver
     passthrough, `--gpus all`, or host GPU drivers.
   - Required and optional environment variables:
     LLM_API_URL, LLM_API_KEY, LLM_API_MODEL, UI_THEME, HERMES_API_BASE_URL,
     API_SERVER_KEY, PUBLIC_BASE_URL, CORS/allowed-host settings if present.
   - Port behavior and external access:
     Wright UI/API port, Hermes gateway port if exposed, any Hermes Desktop or
     VNC/noVNC/display ports, binding to 0.0.0.0, Docker `-p` examples, LAN
     access examples, and reverse proxy notes.
   - Persistent volume behavior:
     workspaces, `.hermes`, SQLite state, generated CAD artifacts, logs, and
     user configuration.
   - Run examples:
     minimal local run, LAN-accessible run, NVIDIA GPU run, external LLM run,
     local host LLM run using host.docker.internal or host networking, and
     persistent-volume run.
   - Health checks and smoke tests:
     API health, frontend served, Hermes gateway reachable when expected, LLM
     health shown as configured or clearly degraded, and safe MCP catalog probe.
   - Publication plan:
     image names, tags, GHCR and/or Docker Hub publishing, alpha tags, immutable
     version tags, latest tag policy, SBOM/provenance if practical.

   Avoid pretending GUI-in-Docker is simple. If Hermes Desktop in Docker needs
   X11, Wayland, VNC, noVNC, xpra, or another display strategy, document the
   chosen approach clearly with security tradeoffs.

3. Test and CI/CD hardening

   Create a well-organized regression suite that a solo maintainer can rely on.
   Keep as much as practical in CI.

   Cover at minimum:

   - Python unit tests for package/domain logic.
   - FastAPI route tests for health, setup, agent/Hermes connection, MCP
     registry/catalog APIs, and failure modes.
   - React component and state tests for core UI flows.
   - Playwright UI tests for the main supported workflows:
     setup/status, tool registry browsing, safe MCP install/status display,
     agent connection state, file vault basics, and theme/layout regressions.
   - Docker smoke tests for the public appliance image.
   - Clean-container MCP validation according to
     docs/mcp-catalog/mcp-server-testing-process.md.
   - Windows/Hermes Desktop tests only where the repo already supports them or
     where they can be run without fragile/manual steps.

   CI should include:

   - Python lint/type/test gate.
   - Frontend lint/type/build/test gate.
   - Playwright gate where stable in CI.
   - Docker build and smoke gate for release images.
   - Docs link/build check if docs are published.
   - Secret scanning or leak detection gate if available.
   - Release workflow dry run or validation for alpha tags.

   Keep the test taxonomy documented. Add a clear "run this before release"
   command list for the maintainer.

4. Alpha README and documentation

   Update README and relevant docs so new users immediately understand:

   - Wright is alpha.
   - The release exists for testing, MCP porting, demos, and feedback.
   - Wright is bring-your-own-AI.
   - What works today and what is intentionally incomplete.
   - Which deployment path they should choose.
   - How to report bugs.
   - Where to find roadmap and MCP contribution information.

   Create or update getting-started docs for the three main scenarios:

   - GB10/DGX Spark-like install and run.
   - PC install and run.
   - Add the Wright plugin to an existing Hermes setup.

   Include example Hermes LLM configuration using an OpenAI-compatible endpoint,
   local model server, and hosted API style. Link to official Hermes
   documentation for deeper configuration details; verify current links before
   publishing.

   Docs must include working commands, expected URLs, port mapping examples,
   troubleshooting for common LLM/Hermes/API failures, and a clear uninstall or
   cleanup path where practical.

5. GitHub bug reporting and community readiness

   Ensure GitHub Issues are ready for public use:

   - Bug report template asks for deployment path, image tag/version, commit SHA,
     OS, Docker version, browser, LLM provider/model, Hermes version, logs,
     screenshots, and reproduction steps.
   - Feature request template exists.
   - Config encourages appropriate contact links and does not disable blank
     issues unless intentional.
   - Labels exist or are documented: bug, needs-triage, alpha, docker, docs,
     mcp, ui, hermes, good-first-issue.
   - CONTRIBUTING, SECURITY, SUPPORT, CODE_OF_CONDUCT, license, PR template, and
     release notes are current.

6. Public repository launch plan

   Create a checklist for making the repo public:

   - Run secret scanning against the working tree and history.
   - Check for accidental credentials, local paths, private hostnames, tokens,
     generated databases, logs, screenshots with sensitive content, and
     proprietary design files.
   - Confirm .gitignore/.dockerignore exclude runtime state:
     SQLite files, logs, pid files, env files, generated artifacts, local
     Hermes state, caches, and test output.
   - Confirm license and third-party notices are accurate.
   - Confirm repository description, topics, social preview, README badges, and
     release metadata are ready.
   - Confirm default branch protection and required checks.
   - Confirm GitHub Discussions or another support channel is configured if
     referenced.
   - Confirm GHCR/Docker Hub repositories, package names, and version tags.
   - Register or prepare submissions for relevant open-source discovery places:
     GitHub topics, Docker Hub/GHCR, PyPI if packages are published, npm if
     frontend/plugin packages are published, MCP/community registries, awesome
     lists, project websites, and docs index pages. Do not submit anything
     automatically without maintainer approval.

7. UI cleanup and consistency

   Audit and improve the UI so it feels consistent with Wright's existing
   design tokens and compatible with Hermes, OpenClaw, and other agent-hosted
   environments.

   Focus on:

   - Consistent spacing, typography, contrast, tokens, and theme behavior.
   - Responsive behavior on desktop and reasonable tablet/laptop widths.
   - Stable layouts with no overlapping text or card shifts.
   - Clear status states for Hermes, LLM, API, Docker, and MCP servers.
   - Accessible labels, keyboard navigation, and useful empty/error/loading
     states.
   - No decorative redesign that distracts from the engineering workflow.
   - Screenshots or Playwright visual checks for the main pages if practical.

8. Roadmap and MCP backlog

   Update the roadmap for alpha-era future work. Include:

   - MCP catalog improvements.
   - Web MCP support.
   - Process flow/workflow support.
   - OpenClaw support.
   - Hermes Desktop deeper integration.
   - Better local LLM setup flows.
   - Security hardening and workspace isolation.
   - CAD/CAE/CAM artifact viewers and validation.
   - MCP Apps or embedded UI panels where appropriate.

   Add or update a needed MCP servers list. Group by priority and risk:

   - Core open-source CAD/geometry.
   - FEA/CFD/simulation.
   - CAM/slicing/manufacturing.
   - Electronics/EDA.
   - PLM/PDM/documentation.
   - Vendor/proprietary integrations needing licenses or SDKs.
   - Browser/Web MCP candidates.

   Each candidate should have source URL if known, status, dependency burden,
   platform support, safety notes, and next action.

Execution approach:

1. Audit first. Do not start broad rewrites until the release gaps are visible.
2. Propose a phase plan with small implementation slices.
3. Implement the highest-value alpha blockers first.
4. Preserve existing behavior unless the audit proves it is wrong.
5. Add or update tests alongside code changes.
6. Run targeted tests after each meaningful slice.
7. Run the full practical release gate before declaring readiness.
8. Leave clear follow-up issues for anything too large or blocked.

Definition of done:

- A maintainer can build or pull the public alpha Docker image and open Wright
  from outside the container using documented ports and URLs.
- A GB10/DGX Spark-like user has a clear run path, including GPU and local LLM
  notes.
- A PC user has a clear run path.
- An existing Hermes user has a clear plugin-only install path.
- README and docs clearly say alpha and bring-your-own-AI.
- Bug reporting through GitHub Issues is ready.
- The public launch checklist is complete enough to prevent obvious data leaks.
- CI covers the main regression risks and documents remaining manual gates.
- The UI has a consistent alpha-quality baseline.
- Roadmap and MCP backlog explain what comes next.
- All changed code/docs are verified with the strongest practical tests in the
  current environment.

When finished, report:

- What changed.
- What tests/checks passed.
- What was not tested and why.
- Remaining alpha blockers.
- Recommended next release step.
```
