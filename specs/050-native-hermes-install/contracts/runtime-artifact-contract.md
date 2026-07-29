# Runtime Artifact Contract

## Distribution identity

- Public distribution: `wright-engineering`.
- Product version: exact normalized root version.
- Base installation: manager-neutral lifecycle bootstrap, compatibility metadata,
  dependency-safe CLI/MCP entry points, and packaged application code/resources;
  the separate Hermes Git adapter imports none of this code into Hermes.
- Runtime installation: the same exact distribution with the `runtime` extra in
  a Wright-owned isolated environment.
- Internal `wright-*` project distributions remain private and are never runtime
  dependencies from a public index.

## Required wheel contents

The wheel MUST contain:

- `wright_engineering` lifecycle/runtime/manager-profile modules;
- `api`, `core`, `agent_adapters`, `tool_registry`, `data_vault`, and
  `workspace_service` package modules;
- canonical engineering MCP catalog and required schema/resource files;
- release-built web UI `index.html`, hashed assets, and manifest;
- compatibility metadata and package-role documentation;
- licenses and required notices.

The wheel MUST NOT contain:

- repository metadata, specs, tests, screenshots, sandbox logs, local outputs,
  databases, credentials, tokens, `.env` files, caches, or source maps not
  explicitly admitted by policy;
- Node modules, frontend source, npm, Git, Docker clients, or MCP-specific host
  applications;
- editable paths, workspace-source references, or dependencies on private Wright
  distributions.

## Build contract

1. Install locked development dependencies in CI.
2. Test and build the frontend once.
3. Copy only inspected frontend distribution files into package data.
4. Build one wheel and one source archive from the reviewed commit.
5. Inspect paths, links, permissions, secrets, metadata, dependency graph, UI
   manifest, and canonical catalog.
6. Record artifact hashes and content manifests.
7. Reuse the exact files for candidate tests, TestPyPI, PyPI, and release
   verification; no publication-stage rebuild is allowed.

The source archive MUST be capable of producing a byte-content-equivalent wheel
for all policy-controlled files without requiring a source checkout. It may use
documented PEP 517 build requirements in the isolated build environment; end-user
runtime installation never builds the frontend.

## Runtime entry point

The runtime environment exposes a stable command equivalent to:

```text
wright runtime serve --host 127.0.0.1 --port <port> \
  --data-root <contained-path> --instance-id <uuid>
```

The bootstrap sets packaged static and data paths before importing `api.main`,
runs database readiness, and serves API and UI from one process. Secrets enter
through protected environment/config references and never command arguments.

## Dependency and platform policy

- `requires-python` and classifiers match the clean-install matrix.
- The runtime extra uses bounded direct dependencies and a tested lock/evidence
  strategy; it has no private Wright distribution requirements.
- Every claimed OS/architecture must be able to resolve wheels or otherwise pass
  the approved clean install without compilers or source repositories.
- Missing artifact/platform support fails before activation.

## Base import isolation

These imports and operations MUST work after base-only install:

```text
import wright_engineering
import wright_engineering.manager_profiles
wright --version
wright doctor
```

They MUST NOT import FastAPI, Uvicorn, application packages, or other
runtime-only dependencies. The provider-neutral MCP bridge may load only when
the explicit MCP command runs. Runtime modules may import application
dependencies only in the isolated child process.
