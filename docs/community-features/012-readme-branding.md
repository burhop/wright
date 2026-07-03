# Feature Brief: README Overhaul and Branding

Refresh the Wright README as a public-alpha entry point for developers, MCP
porters, demo users, and selected beta testers. The README should tell visitors
what works today, what they must bring themselves, and where to contribute
without implying a production or all-in-one engineering appliance.

## Public-Alpha Contract

The README must front-load these truths:

- Wright is alpha software for testing, MCP porting, demos, and early feedback.
- Wright is bring-your-own-AI.
- The Docker image does not bundle an LLM, API key, local model, hosted
  model, or paid engineering backend.
- Configure `LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL` for an
  OpenAI-compatible local or hosted provider.
- MCP-specific host software such as FreeCAD, OpenSCAD, CalculiX, Blender,
  vendor CAD systems, license managers, and hardware drivers is installed only
  for the selected MCP validation or usage case.
- Engineering MCP server validation follows
  `docs/mcp-catalog/mcp-server-testing-process.md`.

## Visual Identity

1. Keep the Wright logo visible at the top of the README and use assets from
   `docs/images/`.
2. Keep badges truthful for the current alpha release posture:
   - GitHub Actions status
   - MIT license
   - Python and Node versions
   - GitHub stars
   - Community/discussion links
3. GHCR is the default registry path for release images. Docker Hub remains
   optional, so Docker Hub pull badges should appear only when that publishing
   path is actively configured and documented.
4. Social preview images should use the Wright logo and concise alpha-aware
   messaging, not claims of completed production reliability.

## README Structure

### Hero

Use a short tagline that frames Wright as a local-first agent orchestrator for
physical engineering. Avoid claims that Wright includes every engineering tool,
model, solver, or cloud service.

### Why Wright?

Explain the problem and direction:

- Engineering teams need AI-assisted workflows without handing every design to a
  single hosted black box.
- Wright coordinates agents and deterministic tools while leaving LLM/provider
  choice to the operator.
- The first public alpha is for developers, MCP porters, demos, and selected
  beta feedback.
- Local and hybrid deployments are supported, but every real toolchain still
  needs explicit configuration, credentials, licenses, or host software when
  applicable.

### Feature Highlights

Highlight capabilities as alpha surfaces:

- Agent orchestration for engineering workflows.
- MCP tool registry and selected-server validation.
- Deterministic CAD, CAE, CAM, and calculation tool actuation through adapters.
- Docker appliance for the Wright API, static web UI, Hermes profile/bootstrap,
  and general validation tooling.
- BYO-AI provider configuration for local or hosted OpenAI-compatible endpoints.

Do not describe the Docker image as a complete CAD/CAE/CAM workstation.

### Screenshots

Store screenshots under `docs/images/` and show the active product surfaces:

- Agent chat interface.
- Tool registry.
- Workspace files, artifacts, logs, and viewer panels.

## Quick Start

The recommended first-run path is the minimal Docker appliance:

```bash
git clone https://github.com/burhop/wright.git
cd wright
cp docker/.env.example docker/.env
# Edit docker/.env and set LLM_API_URL, LLM_API_KEY, and LLM_API_MODEL
docker compose -f docker-compose.minimal.yml up -d --build
```

Then open:

```text
http://localhost:8080
```

The full compose file also exists for local tracing work, but the README should
route first-time alpha users to the minimal compose file and the Docker
quickstart for details.

## Architecture Section

Keep the architecture overview short and consistent with the current monorepo:

- FastAPI gateway and static web UI.
- Agent adapters and Hermes integration.
- MCP tool registry.
- Data vault and local workspace state.
- Selected MCP host dependencies installed per server, not silently bundled in
  the base image.

Use a Mermaid diagram only if it stays readable in GitHub's README renderer.

## Contributing Callout

Point contributors to:

- `CONTRIBUTING.md`
- Spec Kit workflow docs
- GitHub issues labeled for public-alpha triage
- MCP setup recipes and follow-up records

The contribution copy should invite help while making clear that alpha bugs,
missing MCP dependencies, and incomplete workflows are expected.

## Constraints

- Keep the README as a single file.
- Do not modify source code, Docker files, or CI/CD workflows as part of the
  README branding brief.
- Do not claim production readiness, bundled model access, bundled paid
  engineering backends, or universal local execution.
- Keep registry language aligned with release policy: GHCR default, Docker Hub
  optional, and stable-only `latest`.
