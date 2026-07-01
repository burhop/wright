<p align="center">
  <img src="docs/images/wright-logo.png" width="180" alt="Wright Logo">
</p>

<h1 align="center">Wright</h1>

<p align="center">
  <strong>Public-alpha, local-first agent orchestration for physical engineering.</strong>
</p>

<p align="center">
  <a href="https://github.com/burhop/wright/actions/workflows/python-quality.yml"><img src="https://github.com/burhop/wright/actions/workflows/python-quality.yml/badge.svg" alt="Python CI"></a>
  <a href="https://github.com/burhop/wright/actions/workflows/frontend-quality.yml"><img src="https://github.com/burhop/wright/actions/workflows/frontend-quality.yml/badge.svg" alt="Frontend CI"></a>
  <a href="https://github.com/burhop/wright/actions/workflows/docker-build.yml"><img src="https://github.com/burhop/wright/actions/workflows/docker-build.yml/badge.svg" alt="Docker Build"></a>
  <a href="https://github.com/burhop/wright/actions/workflows/docs-deploy.yml"><img src="https://github.com/burhop/wright/actions/workflows/docs-deploy.yml/badge.svg" alt="Docs"></a>
  <a href="https://github.com/burhop/wright/actions/workflows/public-alpha-safety.yml"><img src="https://github.com/burhop/wright/actions/workflows/public-alpha-safety.yml/badge.svg" alt="Security Scan"></a>
  <a href="https://github.com/burhop/wright/actions/workflows/release.yml"><img src="https://github.com/burhop/wright/actions/workflows/release.yml/badge.svg" alt="Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-22%2B-green.svg" alt="Node 22+"></a>
  <a href="https://github.com/burhop/wright/pkgs/container/wright-agent"><img src="https://img.shields.io/badge/image-GHCR-blue" alt="GHCR image"></a>
  <a href="https://github.com/burhop/wright/discussions"><img src="https://img.shields.io/badge/discussions-GitHub-orange?logo=github" alt="GitHub Discussions"></a>
  <a href="https://github.com/burhop/wright/stargazers"><img src="https://img.shields.io/github/stars/burhop/wright.svg?style=social" alt="GitHub stars"></a>
</p>

---

## Public Alpha Status

Wright is alpha software for developer testing, MCP porting, demos, and selected
beta feedback. Expect rough edges, incomplete workflows, and changing APIs.

Wright is bring-your-own-AI. The repository and Docker image do not bundle an
LLM, API key, local model, hosted model, or paid engineering backend. Configure
`LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL` for an OpenAI-compatible
endpoint, a local model server, or a hosted provider.

MCP-specific host software such as FreeCAD, OpenSCAD, CalculiX, Blender, vendor
CAD systems, license managers, or hardware drivers is installed only for the
selected MCP validation or usage case. It is not part of the base Docker image.
Engineering MCP server validation follows
[the clean-container process](docs/mcp-catalog/mcp-server-testing-process.md).

## Why Wright?

Engineering teams need AI-assisted workflows without handing every design to a
single hosted black box. Wright coordinates agents and deterministic tools while
leaving LLM/provider choice, credentials, licenses, and host software under the
operator's control.

The first public alpha is aimed at developers, MCP porters, demo users, and
selected beta feedback. Local and hybrid deployments are supported, but real
engineering toolchains still require explicit configuration.

## What Works Today

- Agent orchestration surfaces for engineering workflows.
- MCP tool registry metadata and selected-server validation paths.
- Deterministic CAD, CAE, CAM, and calculation tool actuation through adapters.
- Docker appliance for the Wright API, static web UI, Hermes profile/bootstrap,
  and general validation tooling.
- BYO-AI configuration for local or hosted OpenAI-compatible endpoints.

The Docker appliance is not a complete CAD/CAE/CAM workstation and does not
silently install every possible backend.

## User Interface

### Agent Chat Interface

Interact with local LLM agents to iterate on designs, request modifications, or
write code.

![Agent Chat Interface](docs/images/screenshot_agent_chat.png)

### Tool Registry

View engineering tools, MCP status, and validation metadata available to agents.

![Tool Registry](docs/images/screenshot_tool_registry.png)

### File Vault

Browse STEP, STL, G-code, and other artifacts generated during design turns.

![File Vault](docs/images/screenshot_file_vault.png)

## Quick Start

### Docker Appliance

Start the local alpha appliance with Docker Compose. This path runs Wright and
Hermes integration services locally, then connects them to your own LLM endpoint.

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

The default `docker-compose.yml` also starts Jaeger and maps Wright to
`http://localhost:8000`. See the
[Docker quickstart](docs/getting-started/quickstart-docker.md) and
[Docker deployment guide](docs/user-guide/docker.md) for LAN access, local model
server, persistent volume, and cleanup examples.

For development outside Docker, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Images and Releases

GHCR is Wright's default public release image registry:

```text
ghcr.io/burhop/wright-agent:<tag>
```

Docker Hub publishing is optional and only runs when maintainers configure
`DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository secrets. Prerelease tags
such as `v0.1.0-alpha.1` do not move `latest`; stable tags may.

## Architecture

Wright is a modular monorepo with a FastAPI gateway, React/Vite web UI, Hermes
integration, MCP tool registry, and local workspace state.

```mermaid
flowchart TD
    User([User Web Browser]) -->|HTTP / WebSockets| API[FastAPI API Gateway]
    API -->|Routing| Agent[Agent Adapters and Hermes]
    API -->|Routing| MCP[MCP Tool Registry]
    Agent -->|Uses| MCP
    MCP -->|Selected server| Tools[CAD, CAE, CAM, calculators]
    API -->|Database and files| Vault[SQLite, LanceDB, File Vault]
```

### Repository Structure

```text
wright/
|-- apps/
|   |-- api/                    # FastAPI gateway
|   `-- web/                    # React + Vite frontend
|-- packages/
|   |-- core/                   # Shared domain models and logging
|   |-- agent_adapters/         # Adapter pattern for agent runtimes
|   |-- tool_registry/          # MCP registry and validation logic
|   `-- data_vault/             # SQLite, LanceDB, and filesystem vault
|-- hermes-plugin-wright/       # Wright Hermes plugin and catalog seed data
|-- tests/
|   |-- ui-integration/         # Playwright integration tests
|   `-- e2e/                    # Smoke and system tests
|-- docker/                     # Dockerfile and supervisord configuration
|-- docs/                       # Documentation site content and runbooks
|-- specs/                      # Spec Kit feature artifacts
`-- .github/                   # Community templates and CI workflows
```

Refer to [docs/virtual_engineer_architecture.pdf](docs/virtual_engineer_architecture.pdf)
for the formal architecture analysis and [constitution.md](constitution.md) for
core project engineering standards.

## Development

Run the main local quality gates:

```bash
uv run pytest
uv run ruff check apps/api/ packages/
uv run ruff format --check apps/api/ packages/
npm ci
npx -w apps/web eslint .
npx prettier --check apps/web/
npx tsc --noEmit -p apps/web/tsconfig.app.json
npm run test --workspace=apps/web
npm run build --workspace=apps/web
mkdocs build --strict
```

Helper scripts live in [scripts/](scripts), including public-alpha leak scans,
Docker smoke tests, CI failure log fetching, and release checks.

## Spec Kit

Wright uses [spec-kit](https://github.com/github/spec-kit) for design-led
feature work. Most substantive changes should start with a feature spec, plan,
tasks, and implementation checklist under `specs/`.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for
local setup, branch discipline, testing, pull request expectations, and the
Spec Kit workflow.

Looking for a place to start? Browse issues labeled
[`good-first-issue`](https://github.com/burhop/wright/labels/good-first-issue).

## Community and Support

- Ask usage questions in
  [GitHub Discussions](https://github.com/burhop/wright/discussions).
- Report reproducible bugs with
  [GitHub Issues](https://github.com/burhop/wright/issues/new/choose).
- Report security issues privately using [SECURITY.md](SECURITY.md); do not
  open public security issues.

## Support and Sponsorship

Wright is open source, but integration testing, model evaluation, and engineering
tool adapters require ongoing resources.

- API, token, and compute sponsorships help cover continuous LLM testing.
- Hardware contributions help test local-first and air-gapped deployments.
- Tool ecosystem contributions help expand the MCP catalog safely.
- Code, docs, and Spec Kit contributions help harden the public alpha.

[Sponsor Wright on GitHub](https://github.com/sponsors/burhop)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Star History and Contributors

[![Star History Chart](https://api.star-history.com/svg?repos=burhop/wright&type=Date)](https://github.com/burhop/wright)

<a href="https://github.com/burhop/wright/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=burhop/wright" alt="Contributors list">
</a>
