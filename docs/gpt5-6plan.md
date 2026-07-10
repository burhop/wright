# Wright Professionalization, Release, and Codex Integration Plan

**Status:** Proposed; audit and planning only  
**Audit cutoff:** 2026-07-10, America/New_York  
**Repository:** D:\repos\wright  
**Local baseline:** dev at 7f3f7416c59271c4c8ed9ee1420aee431a0f4619  
**Target outcome:** A secure, maintainable open-source appliance with tested Python and OCI distribution, a direct Codex integration, and an optional first-class Hermes integration.

This plan is based on the checked-out source, fetched upstream refs, published artifacts, local verification, and primary-source product documentation. It does not authorize implementation, publication, or a release.

## 1. Executive verdict

Wright has a credible foundation: a uv monorepo, FastAPI/Pydantic boundaries, SQLite-first storage, agent adapter contracts, server-side MCP safety decisions, offline test seams, clean-container MCP evidence rules, and strong community scaffolding. Specs 037 and 038 established useful transition points and their focused tests are healthy.

Wright is not release-grade yet. Several documented guarantees are aspirational, and some exposed operations amount to unauthenticated local code execution. The project should not publish an application release or a stable Hermes plugin until the P0 controls in this plan are complete.

The recommended product architecture is:

1. Keep the full Wright application in a hardened OCI appliance.
2. Keep wright-engineering as the sole public Wright Python distribution.
3. Evolve wright-engineering into the supported CLI, diagnostics client, configuration installer, and local STDIO MCP bridge to a running Wright appliance.
4. Implement one host-neutral Wright GatewayService and current MCP transports. Codex and Hermes consume the same service independently.
5. Ship a Codex plugin as the polished Codex experience. Do not require Hermes for Codex.
6. Retain hermes-plugin-wright as an optional, thin lifecycle/discovery integration after its public dependency and configuration problems are fixed.
7. Keep internal monorepo packages private until their names, APIs, and dependency contracts are intentionally stabilized.

### Five highest-risk findings

| Rank | ID | Priority | Finding | Release consequence |
| --- | --- | --- | --- | --- |
| 1 | SEC-01/SEC-02 | P0 | The control plane has wildcard CORS, no effective authentication/RBAC, executable custom MCP commands, direct Python execution, and workspace path escapes through backups, symlinks, and global /tmp. | A hostile page or local process may reach code-execution and file operations. Block public release. |
| 2 | SEC-03/CTR-01 | P0 | API, Git, MCP, and Hermes secrets are plaintext or observable; Git tokens enter process arguments; default keys, passwordless sudo, raw protocol logging, and broad persisted system volumes widen impact. | Credentials can leak and compromise survives image upgrades. Block public release. |
| 3 | DATA-01/ISO-01 | P0 | Unversioned startup migrations can fail while the API continues; one global active gateway session can fall back to the most recently updated workspace. | State corruption and cross-project tool disclosure are possible. Block direct Codex release. |
| 4 | REL-01/PKG-01 | P0/P1 | Upstream release automation rebuilds and pushes an image different from the image CI scanned; Python publishing skips exact clean-install checks; the published sdist includes nearly the entire monorepo. | Published artifacts are not demonstrably the tested artifacts. Freeze tag publication until corrected. |
| 5 | MCP-01/ARC-01 | P1 | The Wright gateway is a handwritten, legacy, Hermes-oriented tools-only proxy; service boundaries remain transitional and include reverse dependencies. | Codex safety/approval behavior is incomplete and maintenance cost will keep rising. |

## 2. Dated baseline

### 2.1 Source state

The working tree was clean before this document was created.

| Ref | Commit | Date | Relationship |
| --- | --- | --- | --- |
| Local dev | 7f3f7416c59271c4c8ed9ee1420aee431a0f4619 | 2026-07-01 | Audit target; 27 commits behind origin/dev and 32 behind origin/main |
| origin/dev | edaded4f88051fe79456ddba1ce0d0859117b8d6 | 2026-07-03 | Contains later Python packaging, Hermes mirror, release-readiness, UI, and session work |
| origin/main | e8cfb182c9060cfbd057ef645d913be9a613088a | 2026-07-03 | Production ref; includes the Python publish artifact-path correction |

The first implementation task must integrate and retest current upstream. This plan records local defects even when later upstream work touches the same files; a finding is closed only by evidence after integration.

### 2.2 Published state

| Surface | Verified state on 2026-07-10 |
| --- | --- |
| PyPI | wright-engineering 0.1.0 was uploaded 2026-07-03 with Trusted Publishing and PEP 740 provenance. The wheel is 7,528 bytes and 7 files; the sdist is 4,277,833 bytes and 963 files and contains most of the monorepo. Source: [PyPI project](https://pypi.org/project/wright-engineering/0.1.0/). |
| Git tags/releases | The public repository has no Git tags or GitHub Releases. Sources: [GitHub Releases](https://github.com/burhop/wright/releases) and [tags API](https://api.github.com/repos/burhop/wright/tags). |
| Docker Hub | burhop/wright exists but has no tags. Source: [Docker Hub tags API](https://hub.docker.com/v2/repositories/burhop/wright/tags?page_size=100). |
| GHCR | The anonymous package page returns 404, so an image is absent or not public. Source: [GHCR package page](https://github.com/burhop/wright/pkgs/container/wright). |
| Hermes plugin | The proposed mirror depends on wright-tool-registry, which is not published. The advertised stable install is therefore not a clean public-index install. |
| Name safety | The PyPI distributions wright and wright-core belong to unrelated projects. The unrelated wright distribution also exports wright and wright-mcp console commands. |

The published wright-engineering 0.1.0 sdist should receive an immediate sensitive-content review. If it contains no secret or prohibited material, publish a corrected patch rather than yanking solely for size. PyPI artifacts are immutable.

### 2.3 Codex and Hermes state

| Product | Verified state on 2026-07-10 | Architectural implication |
| --- | --- | --- |
| Codex | Codex joined the ChatGPT desktop app on 2026-07-09. The latest listed CLI release is 0.144.1. Version 0.144.0 added writes approval behavior and interactive MCP authentication. Source: [Codex changelog](https://learn.chatgpt.com/docs/changelog). | Design for desktop, CLI, and IDE from one MCP configuration; test approval annotations. |
| Codex MCP host | Supports STDIO and Streamable HTTP, server instructions, bearer/OAuth auth, user/project config, tool filters, and auto, prompt, writes, and approve policies. Desktop, CLI, and IDE share config. Source: [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). | A standards-compliant Wright MCP service is the shortest supported path. |
| Codex plugins | Plugins can bundle skills and MCP configuration and use a marketplace manifest. Source: [Codex plugin guide](https://learn.chatgpt.com/docs/build-plugins). | Package workflow guidance with MCP discovery rather than requiring manual configuration forever. |
| Codex app-server | Intended for products embedding Codex with auth, history, approvals, and streamed events; the SDK is preferable for jobs/CI. Source: [Codex app-server](https://learn.chatgpt.com/docs/app-server). | Defer unless Wright itself needs to host a Codex chat runtime. |
| Hermes | Latest release is 0.18.2 / v2026.7.7.2 from 2026-07-08; local Docker pins 0.17.0. Source: [Hermes releases](https://github.com/NousResearch/hermes-agent/releases). | Upgrade only with a clean compatibility matrix. |
| Hermes/Codex | Hermes has an openai-codex provider, a Codex MCP preset, and an opt-in beta Codex app-server runtime. Source: [Hermes Codex runtime](https://hermes-agent.nousresearch.com/docs/user-guide/features/codex-app-server-runtime). | These are different directions and must not replace direct Wright-to-Codex MCP. |
| MCP specification | Current stable protocol version is 2025-11-25. Sources: [lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), [transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), and [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools). | The hard-coded 2024-11-05 response and partial tool schema need replacement. |

### 2.4 Verification performed

| Command/scope | Result |
| --- | --- |
| uv run pytest -q packages/core packages/agent_adapters packages/tool_registry packages/workspace_service packages/data_vault | 91 passed in 12.34s |
| uv run pytest -q apps/api/tests | 122 passed, 1 warning in 38.41s |
| uv run pytest -q tests --ignore=tests/e2e-live | 78 passed, 1 warning in 3.51s |
| uv run pytest -q hermes-plugin-wright/tests | 79 passed in 125.35s |
| npm run test --workspace=apps/web | 21 files and 69 tests passed |
| uv run ruff check apps/api packages | Passed |
| uv run ruff format --check apps/api packages | 110 files passed |
| uv run python scripts/generate-frontend-contracts.py --check | Passed, but the generator is not schema-derived |
| Ruff against hermes-plugin-wright | 12 findings; the plugin is excluded from the current CI lint scope |
| npm lint and production build | Passed; emitted a 1,227.48 kB JavaScript chunk and a code-splitting warning |
| mkdocs build --strict | Not run locally because mkdocs is not in the local development environment |
| One monolithic uv run pytest -q invocation | Exceeded a 124-second command timeout; all constituent Python suites passed separately |

The slow Hermes suite should be a separate CI job with its own cache and timeout. Passing tests are valuable evidence, but they do not cover the P0 threat paths or release artifact identity.

## 3. Current architecture

~~~mermaid
flowchart TD
    UI["React/Vite UI"] --> API["FastAPI routers"]
    API --> WS["workspace_service facade"]
    API --> CORE["core.workspace and direct helpers"]
    API --> REG["tool_registry"]
    WS --> CORE
    WS --> REG
    WS --> ADAPTERS["agent_adapters"]
    WS --> VAULT["data_vault"]
    CORE -. "dynamic reverse import" .-> REG
    HERMES["Hermes plugin/runtime"] --> LEGACY["handwritten STDIO Wright gateway"]
    LEGACY --> REST["FastAPI REST + bespoke SSE"]
    REST --> REG
    REG --> CHILD["selected child MCP servers"]
~~~

The diagram exposes three problems:

- The API and workspace_service both reach around intended ownership boundaries.
- core is not a lower-level package because it dynamically imports tool_registry.
- The agent-facing gateway is a second transport implementation over REST/SSE rather than a transport adapter over one application service.

### 3.1 Dependency facts

The intended package direction is not enforced. workspace_service imports concrete Hermes/OpenClaw materializers, core helpers, registry storage, and direct SQL. core dynamically imports tool_registry even though tool_registry declares a dependency on core. The only fitness test, tests/test_import_boundaries.py:7-34, prohibits packages importing apps/api but does not encode the full graph.

The largest ownership hotspots remain:

| File | Approximate lines | Risk |
| --- | ---: | --- |
| apps/web/src/components/chat/WorkspacePanel.tsx | 3,045 | 36 local states, 20 effects, mixed session/file/Git/MCP/layout behavior |
| packages/tool_registry/src/tool_registry/engineering_catalog.py | 2,728 | Code-owned data, difficult review, divergent from plugin YAML |
| apps/web/src/components/tools/ToolCard.tsx | 1,643 | 19 local states and mixed lifecycle/credential/presentation behavior |
| packages/core/src/core/workspace.py | 1,459 | Storage, Git, paths, process execution, runtime sync, legacy behavior |
| apps/api/src/api/routers/workspace.py | 967 | Transport plus filesystem, Git, SQLite, config, runtime orchestration |
| hermes-plugin-wright/commands.py | 953 | Lifecycle, UI, networking, process, and install behavior |

## 4. Evidence-backed findings

Priority meanings:

- P0: Release blocker or plausible data/code-execution boundary failure.
- P1: Must be completed before calling the project professional/stable.
- P2: Important maintainability, portability, or operability improvement.
- P3: Useful follow-on after the higher-risk work.

| ID | Priority | Confidence | Evidence | Impact and required response |
| --- | --- | --- | --- | --- |
| SEC-01 | P0 | High | apps/api/src/api/main.py:61-68 allows all origins/methods/headers; routers at 121-129 have no global auth. apps/api/src/api/routers/mcp.py:112-129 accepts custom commands; packages/tool_registry/src/tool_registry/services.py:131-148 can start them. | Treat custom MCP registration, settings, logs, Python execution, and lifecycle operations as an authenticated control plane. Add strict origins, WebSocket checks, local session tokens, RBAC, and an admin boundary. |
| SEC-02 | P0 | High | apps/api/src/api/routers/workspace.py:149-171 and 195-210 join unvalidated backup IDs; core/workspace.py:688-715 allows global /tmp; 717-724 uses non-real-path containment; 790-816 follows directory symlinks. | Introduce one WorkspacePath capability using resolved containment/no-follow semantics, fixed-format backup IDs, workspace-local scratch, Windows drive/UNC tests, and symlink/race tests. |
| SEC-03 | P0 | High | settings.py:48-80 returns stored API keys; schemas/settings.py:5-14 models plaintext values; migrate.py:220-234 stores git_token; core/workspace.py:1123-1204 embeds tokens in Git URLs. | Put all secrets behind a provider interface, return status only, migrate plaintext values, and use askpass/credential helpers rather than process arguments. |
| SEC-04 | P0 | High | tool_registry/secrets.py:71-105 truncates/writes around separate lock operations; stdio.py:60-90 and 220-277 logs commands/protocol/stderr; logs.py:13-35 exposes logs without auth. | Use one atomic locked transaction with a separate lock file, temp file, fsync, and replace. Redact by default and authenticate log access. |
| CTR-01 | P0 | High | docker/Dockerfile:51-81 installs sudo and grants NOPASSWD; supervisord.conf:20,33 hard-code wright-dev-key; entrypoint.sh:7-8,45-71,97,106 logs endpoints and writes provider keys; Compose persists /home, /usr/local, /opt, /var/lib, /var/cache, and /etc. | Remove sudo/default keys, generate or require secrets, narrow volumes to Wright data, make the root filesystem/capabilities restrictive, and test upgrades across image versions. |
| DATA-01 | P0 | High | main.py:38-50 continues after migration failure. migrate.py:15-347 mixes unversioned schema, deletes, catalog reset, and seeding. | Add numbered/checksummed transactional migrations, preflight backup/integrity checks, fail-closed readiness, and previous-release upgrade/restore fixtures. |
| ISO-01 | P0 | High | core/workspace.py:119-168 persists one active_gateway_session_id and falls back to the most recently updated workspace. | Bind workspace identity immutably per STDIO process or authenticated HTTP MCP session. Never use recent activity as authorization. |
| CFG-01 | P0 | High | wright_gateway_sync.py:35-38 and 61-75 replaces the full mcp_servers map; tests do not preserve unknown servers. entrypoint.sh:45-80 rewrites Hermes config on every boot. | Use host-specific, merge-only, locked, atomic, idempotent writers with backup, validation, dry-run, and rollback. Preserve all unowned keys. |
| REL-01 | P0 | High | origin/main docker-build.yml:54-75 builds/scans one local image; release.yml:88-99 rebuilds and pushes another image, then publishes at 110-117 without a dependency on CI. Trivy is non-blocking. | Freeze tag publication. Build a candidate once by digest, scan/smoke that digest, then promote registry tags without rebuilding. |
| HERMES-01 | P0 | High | origin/main hermes-plugin-wright/pyproject.toml:8-14 depends on unpublished wright-tool-registry. wright-core is unrelated on PyPI. | Disable the stable install claim. Make the plugin self-contained or depend only on the public protocol/CLI. Add a public-index clean-install gate. |
| MCP-01 | P1 | High | tool_registry/gateway.py:71-83 ignores the requested version and returns 2024-11-05; 23-43 and 163-165 swallow failures; 38-40 and 85-148 write concurrently; it supports only list/call. | Replace handwritten wire handling with a pinned official MCP SDK. Negotiate versions, serialize outbound STDIO, implement standard errors/cancellation/progress, and share one GatewayService across transports. |
| MCP-02 | P1 | High | api/routers/gateway.py:73-84 emits only name, description, inputSchema. models.py:131-138 stores no title, annotations, outputSchema, or structured result contract. | Add reviewed per-tool metadata and provenance. Preserve Wright policy as authority; MCP annotations are client hints, not authorization. |
| MCP-03 | P1 | High | api/routers/gateway.py:101-110 creates an empty ApprovalContext or adds only workspace_id, while safety.py:25-34 and 54-167 requires approval sets. | Persist and hydrate Wright approval grants for gateway calls, separate machine/workspace scope, expire/revoke grants, and audit every decision. |
| ARC-01 | P1 | High | workspace_service/service.py:10-36 imports concrete adapters and many core helpers; 272-369 performs subprocess/SQL. core/workspace.py:228-280 dynamically imports tool_registry. | Complete the application-service extraction and enforce a one-way package graph. core must contain pure domain contracts, not higher-level runtime behavior. |
| ARC-02 | P1 | High | workspace router directly performs file, Git, SQLite, config, and runtime work; wright_gateway_sync.py:92-96 imports a router to notify it. | Make routes translation-only and move notification ports into application infrastructure. Add AST/import fitness tests for all allowed edges. |
| CAT-01 | P1 | High | engineering_catalog.py contains 42 entries; plugin YAML contains 34, with only 10 IDs shared. Current tests do not compare the real sources. | Choose one packaged, schema-validated catalog data source and generate API/plugin views. Keep validation evidence separate and preserve clean-container rules. |
| FE-01 | P1 | High | generate-frontend-contracts.py:9-105 returns a literal string; no production frontend imports the generated file. | Export deterministic OpenAPI/JSON Schema, generate a typed client, use it in production, and fail CI on regeneration diff. |
| PKG-01 | P1 | High | origin/main publish workflow ignores its required version input, invokes --skip-clean-install, has no concurrency or tag/version validation, and published an oversized sdist. | Fix 0.1.1 packaging, validate contents, install wheel and sdist on supported Python, and promote identical artifacts from TestPyPI to PyPI. |
| PKG-02 | P1 | High | Local packages have independent hard-coded versions and unbounded internal dependencies; plugin is 1.0.0 while root is 0.1.0. | Adopt an explicit product/integration version policy and ensure no public artifact references a private/unowned distribution. |
| OCI-01 | P1 | High | Dockerfile uses unpinned base tags, uv:latest, apt-get upgrade, unchecked linux-64/latest micromamba, and lower-only dependency upgrades. | Pin digests/versions/checksums and generate a dependency inventory. Do not claim arm64 until the architecture-specific path passes a native smoke test. |
| CI-01 | P1 | High | Python >=3.11 is declared but only 3.13 is tested; mypy is warning-only; Hermes plugin is outside lint; actions use moving tags; no coverage gate. | Add supported-version matrices, staged blocking types/coverage, plugin lint/package tests, full action SHAs, dependency review, CodeQL, audits, and license checks. |
| OBS-01 | P2 | High | tracing.py obtains the default tracer without configuring a provider/exporter; telemetry tests allow no-active-span; Compose advertises Jaeger. | Configure local tracing in lifespan, make remote export explicit/default-off, test actual span export, propagate traceparent and Wright correlation IDs, and remove import-time log filesystem writes. |
| LIFE-01 | P2 | High | core/workspace.py:556-592 spawns unowned tasks; manager.py:58-94 lacks per-server lifecycle locks; sync subprocesses run in async request paths. | Add an owned reconciliation coordinator, per-server locks/generations, bounded workers, timeouts, and cancellation. Separate workspace provisioning from read access. |
| UI-01 | P2 | High | WorkspacePanel and ToolCard remain multi-responsibility hotspots; production build emits a 1.2 MB chunk. | Characterize flows, extract use-case hooks and panels, consolidate the API client, and code-split heavy viewers. Do not split only to reduce line counts. |
| DOC-01 | P1 | High | constitution.md requires a CUDA/FreeCAD/CalculiX thick base, conflicting with the mandatory clean-container policy. It also mandates auth/RBAC, LanceDB, and Jaeger as if implemented. | Amend the constitution through its governance process. Separate current guarantees from desired capabilities and make status claims executable. |
| OSS-01 | P2 | High | Strong community files exist, but no governance/maintainer/deprecation policy was found; CHANGELOG.md stops before July work; stale local file URLs and support claims remain. | Keep the community scaffolding, add governance/compatibility/release ownership, archive historical plans, update the changelog, and test docs examples. |

## 5. Keep, refactor, replace, delete

| Decision | Scope |
| --- | --- |
| Keep | uv monorepo; FastAPI/Pydantic; SQLite local-first model; agent registry concept; typed MCP safety decisions; redaction helpers; clean-container validation plan/evidence model; offline tests; MIT license; README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, issue/PR templates, CODEOWNERS, Dependabot; design tokens. |
| Refactor | workspace_service into real use cases and ports; agent-specific context materializers; MCP lifecycle; GatewayService; secret provider; host config writers; logging/tracing; API composition root; catalog loader; UI API client and use-case hooks; public CLI. |
| Replace | Monolithic startup migration; handwritten MCP protocol loop; literal frontend type generator; duplicate catalog sources; ad-hoc path sanitizers; plaintext settings/Git/MCP secret storage; independent release rebuilds. |
| Delete after characterization | Legacy core.activate_workspace; global /tmp exception; sys.modules/WRIGHT_TESTING production branches; default wright-dev-key; passwordless sudo; broad system-directory volumes; stale claims that auth/RAG/tracing are complete; duplicated frontend interfaces and command/catalog data. |
| Defer | Public SDK; embedded Codex app-server adapter; arm64 release claim; remote multi-user deployment; additional public internal distributions. Each needs a separate contract and support policy. |

## 6. Target architecture

~~~mermaid
flowchart TD
    subgraph Hosts["Supported hosts"]
      CODEX["Codex desktop / CLI / IDE"]
      HERMES["Hermes default runtime"]
      WEB["Wright web UI"]
    end

    CODEX --> MCPSTDIO["MCP STDIO adapter"]
    CODEX --> MCPHTTP["MCP Streamable HTTP adapter"]
    HERMES --> MCPSTDIO
    HERMES --> MCPHTTP
    WEB --> API["FastAPI HTTP/WebSocket adapters"]

    MCPSTDIO --> GATEWAY["GatewayService"]
    MCPHTTP --> GATEWAY
    API --> APP["Workspace application use cases"]
    API --> GATEWAY

    APP --> WSPORT["Workspace repository / file / Git ports"]
    APP --> AGENTPORT["Agent runtime port"]
    APP --> GATEWAY
    GATEWAY --> POLICY["Catalog + tool safety policy"]
    GATEWAY --> RUNNERS["Child MCP lifecycle coordinator"]

    WSPORT --> SQLITE["SQLite/filesystem adapters"]
    AGENTPORT --> HERMESAD["Hermes adapter"]
    AGENTPORT -. "optional future" .-> CODEXAD["Codex app-server adapter"]
    RUNNERS --> CHILD["Selected engineering MCP servers"]
~~~

### 6.1 Package ownership

| Package/surface | Owned responsibilities | Forbidden dependencies/behavior |
| --- | --- | --- |
| packages/core | Pure domain identifiers, value objects, error taxonomy, redaction/telemetry contracts | No SQLite, subprocess, filesystem mutation, provider config, or dynamic import of higher packages |
| packages/data_vault | SQLite connection policy, repositories, numbered migrations, backup/integrity/restore, artifact metadata | No FastAPI or agent provider imports |
| packages/tool_registry | Canonical catalog, tool metadata, safety policy, GatewayService, lifecycle ports/coordinator, validation plan/evidence | No API router imports; no UI; no direct provider config |
| packages/agent_adapters | AgentRuntime interface plus Hermes implementation and provider-specific context/config adapters | No generic workspace persistence or canonical catalog |
| packages/workspace_service | Application use cases coordinating repositories, paths, Git/process ports, agent context, and GatewayService | No HTTP types; no concrete global singleton selection inside use cases |
| apps/api | Composition root and HTTP/WebSocket/MCP-HTTP transport translation | No domain SQL, subprocess, file, Git, or provider-config business logic |
| apps/web | Generated API client, UI-specific view models, feature hooks/components | No duplicated backend contracts or raw fetch scattered through components |
| root wright_engineering package | Public CLI, diagnostics, API client, STDIO MCP bridge, safe host-config installer | No full appliance runtime, private package dependency, or embedded CAD/CAE host software |
| hermes-plugin-wright | Optional Hermes commands and discovery/bootstrap UX over public Wright protocols | No duplicate catalog, private monorepo dependency, or destructive config replacement |
| integrations/codex-wright | Codex plugin manifest, MCP profile, Wright workflow skills, marketplace metadata | No separate business rules; delegate to public CLI/MCP service |

### 6.2 Enforced dependency direction

~~~text
core
  ^
  +-- data_vault
  +-- tool_registry
  +-- agent_adapters
          ^       ^       ^
          +-------+-------+
              workspace_service
                     ^
                apps/api

wright_engineering and integration plugins consume public protocols,
not private package internals.
~~~

Add an explicit dependency manifest and an AST/import test that fails every unapproved edge, including dynamic imports. Use a temporary compatibility adapter while moving code; do not create a second permanent service graph.

## 7. Public artifact topology

| Artifact | Decision | Version policy | Installation/verification |
| --- | --- | --- | --- |
| wright-engineering | Sole public Python distribution. Expand it into a lightweight CLI, doctor, integration installer, API client, and STDIO MCP bridge. | Same product version as the Wright OCI release. | Prefer uvx --from wright-engineering==VERSION or uv tool install. Test wheel and sdist in clean environments. |
| wright command | Keep as a convenience alias during alpha, but document that an unrelated distribution exports the same command. Add collision detection and a canonical wright-engineering executable if necessary. | Compatibility alias follows the distribution. | Codex plugin should invoke an explicit pinned distribution, not rely on an ambiguous PATH install. |
| Full application | OCI only. Do not attempt to put the React application, Hermes runtime, supervisor, or OS dependencies into PyPI. | Product SemVer, including prerelease suffixes. | ghcr.io/burhop/wright@sha256:DIGEST is canonical; Docker Hub is a byte-identical mirror. |
| Internal Python packages | Workspace-private. Mark Private :: Do Not Upload and remove them from public dependency graphs. Rename generic distributions/imports only through a dedicated migration. | Internal lockstep or explicitly private independent versions. | Built/tested in the monorepo, never pulled from public PyPI. |
| Codex plugin | Versioned GitHub Release asset and repository marketplace entry. Bundles manifest, MCP configuration, skills, and docs. | Same compatible product version; manifest declares required CLI range. | Install through Codex plugin UX or repository marketplace; verify manifest and archive checksum. |
| hermes-plugin-wright | Optional public integration only after it has no unpublished dependency and a clean Hermes load matrix. | Independent plugin SemVer with explicit Wright/Hermes compatibility. | Clean public-index install, entry-point discovery, enable, upgrade, uninstall, and rollback tests. |
| SDK | Deferred until API compatibility and deprecation policies exist. | Separate only when public API stability is intentional. | None in the first professional release. |

### 7.1 Intended CLI experience

Target commands, to be finalized by the CLI specification:

~~~bash
uv tool install wright-engineering
wright doctor
wright appliance status
wright mcp serve --stdio --api-url http://127.0.0.1:8000 --workspace .
wright integration install codex --scope project --transport stdio --dry-run
wright integration install hermes --scope user --transport http --dry-run
~~~

Every config-writing command must support dry-run, show changed keys without values, merge only Wright-owned keys, make an atomic backup, validate the result, and be idempotent.

## 8. Direct Codex integration ADR

### 8.1 Decision

Adopt a provider-neutral Wright MCP service as the direct Codex boundary. Deliver manual/project configuration first, then a Codex plugin that bundles the workflow skill and MCP profile. Hermes is not in the direct path.

| Option | Decision | Reason |
| --- | --- | --- |
| Direct Wright MCP over STDIO/HTTP | Accept as primary | Native Codex capability, least coupling, reuses Wright policy, works across desktop/CLI/IDE, and also serves Hermes |
| Codex plugin with Wright MCP + skills | Accept as polished follow-on | Best installation/discovery UX and a home for workflow instructions without duplicating logic |
| Wright CLI + skill only | Keep as complementary fallback | Useful for deterministic operations, but a skill alone cannot expose live typed tools/resources or policy metadata |
| Wright embeds Codex app-server | Defer to a separate product ADR | Correct only if the Wright UI becomes a Codex host; it adds auth, history, approval, event, and compatibility responsibilities |
| Hermes Codex app-server runtime | Optional compatibility | Useful to Hermes users, but beta, adds another process/config/auth layer, and omits some Hermes tools |
| Hermes launches codex mcp-server | Reject for this goal | Reverse direction: exposes Codex to an MCP client; it does not expose Wright to Codex |
| Codex consumes Hermes mcp serve | Reject as Wright boundary | Exposes Hermes conversation/channel operations, not Wright’s engineering service contract |

### 8.2 Required MCP service behavior

The existing gateway is migration compatibility only. The replacement must:

- Use the official Python MCP SDK pinned to a tested range.
- Negotiate the client-requested supported protocol rather than hard-code 2024-11-05.
- Implement standards-compliant STDIO and Streamable HTTP from the same GatewayService.
- Return JSON-RPC parse/method/tool errors rather than silently dropping failures.
- Serialize STDIO output through one queue.
- Support cancellation, progress where useful, bounded timeouts, graceful shutdown, and list-changed notifications.
- Supply concise initialization instructions containing safety, workspace, and rate-limit guidance.
- Bind one explicit workspace to each local process/session.
- Authenticate remote HTTP, validate Origin, use loopback by default, isolate sessions, and rate-limit administrative operations.
- Preserve structuredContent and outputSchema when downstream tools provide them.
- Sanitize downstream content before logs/UI without corrupting protocol results.
- Hydrate and audit Wright approval grants. Client approval is not a substitute for server authorization.

### 8.3 Tool/resource surface

Do not mechanically expose every REST endpoint. Offer stable task-oriented operations and curated downstream engineering tools.

| Capability | Initial MCP form | Safety posture |
| --- | --- | --- |
| Workspace/catalog/tool status | Read-only tools and resources | readOnlyHint true; no secret values |
| Workspace selection/context | Session-local tool | Mutates only the bound MCP session; never global recent-workspace state |
| Artifact list/read/metadata | Resources plus read-only tools | Confined to resolved workspace root |
| Tool enable/install/config | Administrative tools | Always authenticated; prompt/writes; catalog and machine approval required |
| Engineering tool calls | Dynamically surfaced curated tools with stable prefix/ID | Per-tool readOnly/destructive/idempotent/openWorld hints plus authoritative Wright policy |
| Validation planning | Read-only tool | Does not claim actual validation |
| Clean-container validation | Explicit operator tool or CLI only | High-risk, opt-in, auditable; must follow docs/mcp-catalog/mcp-server-testing-process.md |
| Long operations | MCP tasks/progress only where clients and SDK support the tested contract | Cancellable, bounded, and resumable where feasible |

Candidate resources:

- wright://workspace/WORKSPACE_ID/manifest
- wright://workspace/WORKSPACE_ID/artifacts
- wright://catalog/SERVER_ID
- wright://validation/SERVER_ID/latest

### 8.4 Installation UX

Source checkout:

~~~bash
codex mcp add wright -- uv run wright mcp serve --stdio --workspace .
~~~

Pinned PyPI bridge:

~~~bash
codex mcp add wright -- uvx --from wright-engineering==VERSION wright mcp serve --stdio --workspace .
~~~

Local appliance:

~~~toml
[mcp_servers.wright]
url = "http://127.0.0.1:8000/mcp"
bearer_token_env_var = "WRIGHT_MCP_TOKEN"
required = true
default_tools_approval_mode = "writes"
startup_timeout_sec = 20
tool_timeout_sec = 120
~~~

The HTTP endpoint is the right path for the Docker appliance and remote hosts. STDIO is the right local bridge when the CLI is installed beside Codex. ChatGPT web cannot read a local Codex config; that case requires an approved plugin and reachable authenticated remote MCP service.

### 8.5 Codex plugin target

~~~text
integrations/codex-wright/
+-- .codex-plugin/plugin.json
+-- .mcp.json
+-- skills/wright-engineering/SKILL.md
+-- assets/
+-- README.md

.agents/plugins/marketplace.json
~~~

The plugin must declare its Wright CLI/appliance prerequisites, use a pinned compatible range, contain no credentials, and avoid hooks in the MVP unless a concrete enforcement need justifies them.

## 9. Hermes and Codex/Hermes ADR

### 9.1 Decision

Hermes remains optional and first-class. The stable Hermes path is Hermes consuming the same Wright MCP server as Codex. The Hermes plugin becomes a thin lifecycle/discovery layer. The Codex app-server runtime is an optional beta compatibility preset, not Wright’s primary Codex architecture.

| Direction | Model/tool-loop owner | Decision |
| --- | --- | --- |
| Hermes -> Wright MCP | Hermes owns the model/tool loop; Wright owns engineering policy/execution | Supported secondary path |
| Codex -> Wright MCP | Codex owns the model/tool loop; Wright owns engineering policy/execution | Primary Codex path |
| Hermes openai-codex provider | Hermes tool loop with an OpenAI/Codex model provider and Hermes auth store | Document as model selection, not direct Codex integration |
| Hermes -> Codex app-server -> Wright MCP | Codex executes shell/patch/MCP inside a Hermes session shell | Optional beta; separate auth and a pinned tested matrix |
| Hermes -> codex mcp-server | Hermes delegates coding work to Codex | Reverse direction; not a Wright exposure mechanism |
| Codex -> hermes mcp serve | Codex accesses Hermes conversations/channels/approvals | Optional unrelated integration; not the engineering service |
| Wright -> Codex app-server adapter | Wright embeds Codex runtime in its UI | Deferred |

### 9.2 Compatibility matrix

| Host/surface | Target Wright path | Support condition |
| --- | --- | --- |
| Codex CLI 0.144.1 | STDIO or HTTP Wright MCP | Primary reference version |
| ChatGPT desktop Codex on Windows/macOS | Shared Codex MCP config/plugin | Primary; verify restart/install UX |
| Codex IDE extension | Shared Codex MCP config/plugin | Primary |
| Codex remote/cloud executor | Installed bridge in remote environment or reachable HTTP | Local desktop Wright is not implicitly reachable |
| Hermes 0.18.2 default runtime | Same STDIO/HTTP Wright MCP | Supported secondary reference |
| Local pinned Hermes 0.17.0 | Legacy compatibility during upgrade only | Test, migrate, then remove from supported matrix on a dated policy |
| Hermes codex_app_server | Migrated Wright MCP configuration | Optional beta; separate codex login; verify missing delegate_task, memory, session_search, and todo behavior |
| Wright Docker | HTTP /mcp | Target; the current REST/SSE proxy is not that transport |
| Current Wright gateway | 2024-11-05 tools-only proxy | Compatibility period only |

### 9.3 Hermes-specific corrections

- Upgrade Docker from Hermes 0.17.0 to the chosen supported release only after clean wheel/plugin/runtime tests.
- Add hermes plugins enable wright to current 0.18.x installation documentation.
- Verify the current entry-point contract from a built wheel, not a flat source directory.
- Do not rely on custom manifest keys such as min_hermes_version unless the current Hermes loader enforces them; enforce compatibility in dependency metadata, runtime checks, and CI.
- Replace the token/fingerprint-only openai-codex health check with an explicit capability/readiness probe.
- Remove duplicate catalog ownership and duplicated slash-command data.
- Deep-merge the owned MCP key and preserve users’ existing servers, including configurations later migrated into Codex.
- Treat plugins as in-process privileged code. Whole-process OS/container isolation remains the meaningful boundary for untrusted tool/web content.

## 10. Coordinated release pipeline

### 10.1 Release flow

~~~mermaid
flowchart TD
    TAG["Protected reviewed SemVer tag"] --> PRE["Preflight: source, version, changelog, policy"]
    PRE --> CI["Python/OS + frontend + docs + contracts + security gates"]
    CI --> PYBUILD["Build wheel + sdist once"]
    CI --> OCIBUILD["Build per-arch candidate images once"]
    PYBUILD --> PYTEST["Metadata, content, README, wheel/sdist installs, CLI tests"]
    OCIBUILD --> OCITEST["Push SHA candidate; scan + smoke exact digests"]
    PYTEST --> TESTPYPI["TestPyPI exact files"]
    OCITEST --> ATTEST["SBOM, max provenance, keyless digest attestations"]
    TESTPYPI --> APPROVE["Protected release approval"]
    ATTEST --> APPROVE
    APPROVE --> PYPI["PyPI exact files"]
    APPROVE --> PROMOTE["Promote tested OCI digest to version tags"]
    PROMOTE --> MIRROR["Copy identical manifest to Docker Hub"]
    PYPI --> VERIFY["Post-publish install/pull/attestation verification"]
    MIRROR --> VERIFY
    VERIFY --> DOCS["Deploy versioned docs"]
    DOCS --> GHREL["Publish immutable GitHub Release last"]
~~~

### 10.2 Required controls

1. One product version source. Validate Git tag, PEP 440 version, OCI labels/tags, changelog, plugin compatibility, and API version.
2. One release run and immutable artifacts. TestPyPI and PyPI consume the same downloaded files.
3. Per-product/version concurrency. Existing identical hashes are idempotent; differing hashes fail.
4. Protected testpypi, pypi, release, and dockerhub environments with tag restrictions and reviewers.
5. Least privilege by job. PyPI publication receives id-token: write only; container and attestation jobs receive only required scopes.
6. Full commit SHA pins for third-party Actions, updated by Dependabot.
7. Exact artifact content policies:
   - explicit Hatch wheel and sdist includes;
   - no secrets, specs, screenshots, sandbox scripts, or unrelated packages in the CLI distribution;
   - twine check --strict;
   - wheel-content checks;
   - build/install from sdist;
   - console and import smoke tests.
8. Python supported-version matrix. Either cap requires-python to tested versions or test every admitted active version. Start with 3.11-3.14 if dependencies support it.
9. Pinned Node LTS for CI and Docker; align versions.
10. Blocking fixable High/Critical image policy with reviewed, expiring exceptions and scheduled rescans.
11. Explicit provenance: mode=max, SBOM, PEP 740 package attestations, GitHub OCI digest attestations, checksums, and user-facing verification commands.
12. Keep engineering MCP validation in the separate clean-container workflow; never make the base image a universal CAD workstation.

### 10.3 Container policy

- Canonical image: ghcr.io/burhop/wright.
- Optional byte-identical mirror: burhop/wright on Docker Hub.
- Immutable tags: version and git SHA. Mutable latest only moves after stable verification.
- Build and push SHA candidates first; smoke and scan by digest; promote without rebuilding.
- Start with linux/amd64. Add linux/arm64 only after:
  - micromamba URL selection is architecture-aware and checksum-pinned;
  - every binary dependency has an arm64 path;
  - the exact image passes a native arm64 smoke test;
  - release notes state any engineering-tool limitations.
- Persist only application data/config/workspaces. Never persist whole /etc, /opt, /usr/local, or /var trees.
- Run as a non-root user without sudo, drop capabilities, set no-new-privileges, and use a read-only root filesystem where the application permits.
- Generate local keys/tokens at first initialization or require them; no universal development credential in a published image.

### 10.4 Rollback

- PyPI: publish a corrected patch. Yank only broken, incompatible, vulnerable, or disclosed releases; never overwrite files.
- OCI: never move immutable version/SHA tags. Repoint only mutable aliases, quarantine the bad digest, and publish a patch.
- Database: pre-upgrade backup plus schema/integrity manifest; restore only through a documented command and version check.
- Configuration: atomic writer creates a timestamped backup and supports dry-run/restore.
- Multi-registry release: record the tested digest/hashes in a release manifest so promotion is safely retryable.
- GitHub Release: remain draft until all post-publish checks pass; publish last.

## 11. Dependency-ordered implementation roadmap

Effort scale: XS < 1 day, S 1-3 days, M 3-5 days, L 1-2 weeks. Estimates assume two experienced engineers and exclude external account approval delays.

### Phase 0 — Establish an honest baseline

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R0.1 | P0 | Integrate origin/main into the implementation baseline without losing this plan; reconcile specs 039-041, packaging work, and UI/session changes. | None | Run all split Python suites, web tests/build, package checks, and docs. Roll back by restoring the pre-integration branch. Document accepted upstream findings. S / medium. Done when every finding is marked open, closed, or changed against one reviewed commit. |
| R0.2 | P0 | Amend constitution.md and add ADRs for thin base/clean-container policy, security modes, public artifacts, and provider-neutral MCP. | R0.1 | Constitution governance approval; docs tests assert no contradictory thick-base/auth-complete claims. No code migration. S / high governance. Done when current guarantees and target principles are distinct. |
| R0.3 | P0 | Add characterization and security regression tests before moving code: tests/security, path fixtures, config fixtures, migration fixtures, concurrent workspaces, and public artifact contents. | R0.1 | Tests initially reproduce each P0 and then become blocking. Add pytest markers and CI partitions. Roll back by removing tests only before implementation starts. M / low. Done when each P0 has an executable failing/passing contract. |

### Phase 1 — Close P0 safety and data risks

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R1.1 | P0 | Security control plane in apps/api: strict configured origins, loopback session/token auth, WebSocket checks, RBAC/admin dependencies, protected logs/settings/MCP/execute routes. | R0.2-R0.3 | Unauthorized/cross-origin tests fail closed; authenticated local quickstart works; remote bind refuses startup without secure mode. Feature flag permits short compatibility rollback. Update threat model and deployment docs. L / high. Done with no unauthenticated mutating/code-execution route. |
| R1.2 | P0 | WorkspacePath capability and backup IDs in workspace_service/core; replace global /tmp with workspace/.wright/tmp; no-follow/real-path validation across Windows and POSIX. | R0.3 | Tests cover absolute backup IDs, .., symlink/junction, UNC/drive paths, cycles, race attempts, and valid files. Compatibility scanner reports unsafe legacy paths. M / high. Done when every file operation uses one capability. |
| R1.3 | P0 | SecretProvider abstraction for settings, Git, MCP, and integration auth; atomic fallback store; masked API responses; Git askpass/credential helper; log redaction. | R1.1 | Migration moves plaintext DB values, keeps encrypted/OS-keyring or mounted-secret fallback, verifies no token in DB/API/argv/logs. Backup enables rollback. Update recovery/key rotation docs. L / high. Done after a leak scan and concurrency tests. |
| R1.4 | P0 | Harden docker/Dockerfile, entrypoint, supervisord, and Compose: remove sudo/default key/logged URL, narrow volumes, drop privileges/capabilities, safe YAML/config generation. | R1.1/R1.3 | Container smoke runs non-root with no universal key; restart/upgrade retains only documented data; security scan and secret scan pass. Keep a temporary legacy Compose file for one migration release. M / high. |
| R1.5 | P0 | Numbered transactional migrations and repositories in data_vault; remove schema/catalog mutation from boot routine; fail readiness closed. | R0.3/R1.3 | Fresh DB, each supported prior schema, interrupted migration, corruption, backup/restore, and downgrade/restore tests. CLI commands: db status, backup, upgrade, restore. Compatibility wrapper can invoke the new runner for one release. L / high. |
| R1.6 | P0 | Per-session workspace binding and merge-only host config writers; remove recent-workspace fallback and whole-map replacement. Files: core/workspace.py, workspace_service, wright_gateway_sync.py, adapter config writers. | R0.3/R1.2 | Two concurrent MCP sessions cannot see/call each other’s tools. Golden configs preserve unknown Codex/Hermes entries/comments where supported. Atomic crash/concurrency tests pass. M / high. |

### Phase 2 — Complete architecture ownership

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R2.1 | P1 | Declare/enforce full dependency graph; make core pure; introduce repository, Git, process, path, agent, gateway, and notification ports. | R1.2/R1.5/R1.6 | AST/import fitness test catches direct and dynamic forbidden edges; all existing behavior passes through compatibility adapters. ADR and package READMEs updated. M / medium. |
| R2.2 | P1 | Move workspace CRUD, files, backups, Git, context, settings, and execution into PR-sized workspace_service use cases; make API routes translators. | R2.1 | Route tests plus direct use-case tests preserve response compatibility. Blocking work uses bounded executors/timeouts. Delete legacy core.activate_workspace after call graph proves unused. L / high. |
| R2.3 | P1 | Introduce owned MCP lifecycle coordinator with per-server locks/generations, awaitable reconciliation, cancellation, and graceful shutdown. | R2.1 | Concurrency, restart, failure, shutdown, and timeout tests pass without leaked tasks/processes. Compatibility manager delegates to coordinator. M / high. |
| R2.4 | P1 | Replace Python/YAML catalog duplication with one schema-validated packaged resource; add per-tool safety metadata, provenance, and validation dates. | R2.1 | Exact real-catalog ID/count/metadata parity across API/plugin; wheel resource test; no passed validation without complete clean-container evidence. Migration maps existing IDs. M / medium. |
| R2.5 | P2 | Configure actual OTel provider/exporter in lifespan, W3C context, Wright correlation, repository/lifecycle spans, and side-effect-free logging. | R2.1/R1.3 | In-memory exporter tests assert spans/redaction; remote export remains default-off; no import-time log file creation. Update observability runbook. M / medium. |
| R2.6 | P1/P2 | Generate OpenAPI/JSON Schema and a typed frontend client; migrate live services; split WorkspacePanel/ToolCard by use case and code-split viewers. | R2.2 | Regenerate-and-diff CI; no duplicate backend types; existing 69+ UI tests and Playwright flows pass; bundle budget enforced. Keep adapter wrappers during incremental migration. L / medium. |

### Phase 3 — Make distribution and CI trustworthy

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R3.1 | P1 | Artifact/naming ADR; explicit Hatch sdist/wheel includes; Private classifier on internals; sensitive-content review of 0.1.0; corrected wright-engineering patch. | R0.1/R0.2 | Wheel/sdist content manifests are small and intentional; twine/readme/content checks pass. Publish only after R3.3; do not yank 0.1.0 unless disclosure is found. S / medium. |
| R3.2 | P1 | Build public CLI skeleton in src/wright_engineering: version, doctor, appliance status, integration dry-run, stable command/collision handling. | R3.1/R1.1 | Clean 3.11-3.14 wheel/sdist installs, --version, doctor, uninstall/reinstall, no private imports. Update PyPI README and CLI reference. M / medium. |
| R3.3 | P1 | Harden publish-python-packages workflow: one version/tag, concurrency, full SHA actions, exact clean installs, TestPyPI then protected approval then PyPI, post-install and attestation verification. | R3.1/R3.2 | Rehearsal publishes exact hashes to TestPyPI; production environment has OIDC and reviewer; retries reject differing hashes. Disable old dispatch/tag path. M / high. |
| R3.4 | P1 | Reproducible OCI build: pinned bases/tools/checksums, Node LTS alignment, no apt upgrade, dependency lock/inventory, minimal runtime. | R1.4 | Rebuild comparison is documented; image contents/labels/license inventory pass; exact amd64 image smoke passes. Keep old Dockerfile only on a rollback branch. M / high. |
| R3.5 | P1 | Unified release workflow: build candidate digests once, blocking scan/smoke, SBOM/max provenance/keyless attest, promote GHCR tags, mirror same manifest, verify, docs, GitHub Release last. | R3.3/R3.4 | Dry-run release manifest records all hashes/digests; published candidate verification commands pass. Remove independent tag builds. L / high. |
| R3.6 | P1/P2 | CI matrix and supply chain: Python/OS support, Hermes job, blocking staged types/coverage, Node LTS, docs examples, dependency review, CodeQL, Python/npm audits, license rules, full action SHAs. | R0.3 | Required branch checks map to support policy; expensive/live/clean-container suites are scheduled or manual. Baseline thresholds ratchet upward, not arbitrarily block legacy code. M / medium. |
| R3.7 | P2 | Add arm64 candidate build only after architecture-aware micromamba/dependencies and a native smoke runner. | R3.4/R3.5 | Native arm64 API/Hermes/workspace smoke and manifest inspection pass; otherwise remain amd64-only with honest docs. S-M / medium. |

### Phase 4 — Deliver direct Codex support

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R4.1 | P1 | Extract GatewayService in tool_registry and implement current STDIO MCP with official SDK, negotiated versions, instructions, serialized writes, errors, cancellation, and explicit workspace. | R1.6/R2.3/R2.4 | MCP Inspector fixtures plus Codex 0.144.1 list/call/listChanged/concurrency/error tests. Keep legacy gateway behind a feature flag for one release. L / high. |
| R4.2 | P1 | Expose authenticated Streamable HTTP /mcp in apps/api over the same service; Origin/session/rate-limit policy. | R4.1/R1.1 | Codex HTTP smoke, reconnect/cancel, two-session isolation, bearer/OAuth path, loopback default. REST/SSE gateway remains only during migration. M / high. |
| R4.3 | P1 | Add reviewed tool annotations/output schemas/structured results, approval hydration, task-oriented management tools, and catalog/workspace/artifact resources. | R4.1/R2.4 | Codex writes policy prompts only for appropriate tools; server policy blocks calls even if client auto-approves; every decision is audited. M / high. |
| R4.4 | P1 | Put STDIO bridge and config installer in wright-engineering; create integrations/codex-wright plugin, skill, MCP manifest, and marketplace entry. | R3.2/R4.1/R4.2 | Source, pinned uvx, local Docker HTTP, plugin install/uninstall, dry-run/config preservation, and doctor tests pass. Archive is attached to release manifest. M / medium. |
| R4.5 | P2 | Real host compatibility matrix: Codex CLI, ChatGPT desktop on Windows/macOS, IDE, and remote executor constraints. | R4.4/R3.5 | Evidence records exact versions/platforms, screenshots/logs without secrets, and known limitations. Do not claim unsupported surfaces. S-M / external. |

### Phase 5 — Reintroduce a safe Hermes integration

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R5.1 | P1 | Upgrade/test Hermes 0.18.2, plugin enable flow, built-wheel entry point, config migration, and real health probes; set supported range. | R1.6/R3.6/R4.1 | Matrix covers current pin, migration target, plugin load, MCP list/call, upgrade/uninstall. Docker rollback pins the prior image digest. M / high. |
| R5.2 | P1 | Thin hermes-plugin-wright to public API/MCP/CLI; remove private wright-tool-registry dependency and duplicate catalog/transport logic; repair mirror docs. | R5.1/R3.2/R4.1 | Clean public-index install in a fresh environment, hermes plugins enable wright, lifecycle commands, no unknown package downloads. Stable mirror remains disabled until this passes. M / high. |
| R5.3 | P2 | Test/document openai-codex provider, Codex MCP preset, and beta codex_app_server as distinct optional modes. Do not build a Wright Codex adapter yet. | R5.1/R4.5 | Separate auth/config ownership diagrams; missing-tool behavior; toggle/rollback; current Codex/Hermes pinned matrix. S / medium/external. |

### Phase 6 — Open-source release rehearsal

| ID | Pri | Scope and likely files | Depends on | Acceptance, migration/rollback, docs, effort/risk, definition of done |
| --- | --- | --- | --- | --- |
| R6.1 | P2 | Governance, maintainers/release owners, compatibility/deprecation policy, security advisory process, changelog, ADR index, docs truth/archive pass. | R0.2 and completed feature docs | Maintainers approve; docs examples execute in CI; no local file URLs or unsupported artifact claims. S-M / governance. |
| R6.2 | P1 | End-to-end release candidate rehearsal from a protected commit through TestPyPI, candidate OCI digest, attestations, upgrade/backup/restore, Codex/Hermes smokes, and draft GitHub Release. | All P0 and R3-R5 | Release checklist has zero waived P0/P1 gates; all published claims link to evidence. Rollback/yank/quarantine drill succeeds. M / high/external. |

### 11.1 Milestone gates

| Milestone | Required exit gate |
| --- | --- |
| M0: Honest baseline | Upstream integrated; constitution/ADRs approved; each P0 has a regression test |
| M1: Safe local alpha | Auth/control plane, path confinement, secrets, container, migrations, session/config isolation complete |
| M2: Maintainable core | Dependency graph enforced; routes thin; lifecycle/catalog/contracts corrected |
| M3: Trustworthy artifacts | Correct PyPI files, exact-artifact OCI/PyPI promotion, CI/security/attestations in place |
| M4: Codex preview | Direct STDIO/HTTP MCP and Codex plugin pass the reference matrix |
| M5: Hermes preview | Thin plugin clean-installs and both hosts consume the same MCP service |
| M6: Professional public release | Full release rehearsal and rollback drill pass; docs and registry claims match artifacts |

## 12. Rejected alternatives

1. **Big-bang rewrite:** rejected. Existing tests and seams have value; use characterization plus reversible ownership moves.
2. **Hermes as the mandatory Codex bridge:** rejected. It adds beta runtime, two auth/config boundaries, and unnecessary coupling.
3. **Expose REST mechanically as MCP:** rejected. MCP tools need stable task semantics, per-tool safety metadata, workspace/session identity, and structured results.
4. **Publish every monorepo package:** rejected. Names collide, APIs are not stable, and public dependency confusion already breaks the proposed Hermes install.
5. **Put the full appliance on PyPI:** rejected. The UI, Hermes, supervisor, and OS dependencies belong in OCI; PyPI should deliver a lightweight integration/client tool.
6. **Keep independent tag builds for CI and release:** rejected. Publication must promote the exact tested digest.
7. **Claim arm64 based on Buildx alone:** rejected. The current micromamba and engineering dependency paths are architecture-specific.
8. **Add CAD/CAE/MCP host applications to the base image:** rejected by the clean-container policy and supply-chain/size concerns.
9. **Treat MCP annotations or Codex approval as authorization:** rejected. Annotations are hints; Wright policy remains authoritative.
10. **Call aspirational docs implemented:** rejected. Status and guarantees must be backed by executable evidence.

## 13. Assumptions and maintainer decisions

The plan makes these defaults unless maintainers explicitly choose otherwise:

- Docker remains the full-application delivery mechanism for the next public releases.
- wright-engineering remains the owned public Python name.
- The product is single-user/local-first by default. Any LAN/remote mode must be explicitly authenticated.
- No external identity provider is required for the local mode; remote OAuth is a later deployment feature.
- Existing API response shapes remain compatible until a versioned API policy approves changes.
- Hermes remains supported but optional.
- Clean-container MCP validation remains operator-invoked and separate from fast tests.

Maintainer decisions required before implementation:

1. Approve the constitution amendment and explicit local-versus-remote security modes.
2. Confirm the public package/console-command naming policy and registry ownership.
3. Configure protected GitHub environments and PyPI Trusted Publishers with required reviewers.
4. Choose the supported Python, Node LTS, Codex, Hermes, OS, and architecture ranges.
5. Decide whether Docker Hub remains a supported mirror or GHCR becomes the only registry.
6. Choose the fallback secret-provider design for air-gapped Windows/Linux/macOS installs.
7. Confirm whether multi-user/RBAC is a release requirement or whether the first release is explicitly single-user.

## 14. Recommended Spec Kit sequence

Upstream already contains feature numbers 039-041, so new implementation should start after reconciling those artifacts:

1. 042-security-control-plane-and-workspace-confinement
2. 043-secrets-container-and-provider-config
3. 044-state-migrations-and-recovery
4. 045-package-boundary-and-workspace-use-cases
5. 046-gateway-service-and-mcp-2025-11-25
6. 047-python-oci-release-train
7. 048-codex-wright-plugin
8. 049-hermes-thin-integration
9. 050-openapi-frontend-contracts-and-ui-modularity
10. 051-observability-lifecycle-and-release-rehearsal

Each feature must run specify, clarify, plan, tasks, analyze, and checklist before implementation. No feature should combine a P0 security migration with unrelated UI cleanup.

## 15. Primary-source research appendix

All sources below were accessed on 2026-07-10.

### Codex and MCP

- [Codex changelog](https://learn.chatgpt.com/docs/changelog)
- [Codex MCP configuration and transports](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Build Codex plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Codex app-server](https://learn.chatgpt.com/docs/app-server)
- [Run Codex as an MCP server](https://learn.chatgpt.com/docs/mcp-server)
- [MCP 2025-11-25 lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [MCP 2025-11-25 transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP 2025-11-25 tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP 2025-11-25 schema](https://modelcontextprotocol.io/specification/2025-11-25/schema)

### Hermes

- [Hermes Agent releases](https://github.com/NousResearch/hermes-agent/releases)
- [Hermes Agent on PyPI](https://pypi.org/project/hermes-agent/)
- [Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
- [Hermes plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins)
- [Hermes Codex app-server runtime](https://hermes-agent.nousresearch.com/docs/user-guide/features/codex-app-server-runtime)
- [Hermes providers](https://hermes-agent.nousresearch.com/docs/integrations/providers/)
- [Hermes security policy](https://github.com/NousResearch/hermes-agent/security/policy)

### Packaging and release engineering

- [wright-engineering 0.1.0 on PyPI](https://pypi.org/project/wright-engineering/0.1.0/)
- [PyPA Trusted Publishing workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PyPI attestations](https://docs.pypi.org/attestations/)
- [PyPI yanking](https://docs.pypi.org/project-management/yanking/)
- [Pyproject metadata guidance](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Distribution versus import packages](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/)
- [uv build](https://docs.astral.sh/uv/concepts/projects/build/)
- [Docker GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/)
- [Docker multi-platform builds](https://docs.docker.com/build/ci/github-actions/multi-platform/)
- [GitHub artifact attestations](https://docs.github.com/en/enterprise-cloud%40latest/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub Actions security hardening](https://docs.github.com/en/code-security/tutorials/secure-your-organization/protect-against-threats)
- [GitHub-hosted arm64 runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Node release status](https://nodejs.org/en/about/previous-releases)
- [Python active versions](https://www.python.org/downloads/)

## 16. Definition of a professional first release

Wright is ready for a professional public release only when:

- Every P0 finding is closed by an executable regression test and a reviewed threat model.
- Database upgrade, failure, backup, and restore have been exercised from the previous public state.
- The published Python files and OCI digest are the exact artifacts tested and attested.
- Registry names, tags, docs, badges, and install commands resolve to real public artifacts.
- Direct Codex use works without Hermes.
- Hermes uses the same provider-neutral Wright MCP boundary and its optional plugin clean-installs from public sources.
- Supported Python, Node, OS, architecture, Codex, and Hermes versions are evidence-backed.
- High-risk engineering MCP validation still follows the clean-container process and no base-image shortcut was introduced.
- Governance, release ownership, security reporting, deprecation, compatibility, and rollback policies are published.
- A maintainer can reproduce the release and a new contributor can reproduce the development and test environment from the documentation.
