# Install Matrix

| Use case | Recommended path | Verification | Boundary |
| --- | --- | --- | --- |
| Hermes user | [Native Hermes](hermes-plugin.md) | `/wright start`, `/wright status`, `/wright doctor` | Git is a Hermes adapter prerequisite; Wright runtime commands need no checkout, Docker, or Node/npm. |
| Codex user | [Direct Codex MCP](codex.md) | `codex mcp get wright` and MCP initialize/list | Hermes is not in the path. |
| OpenClaw user | Future integration | Not currently verified or supported | OpenClaw is not part of this release gate. |
| Turnkey evaluator | Published Docker image `burhop/wright:<tag>` | Open `http://localhost:8080`; `/api/health` succeeds | BYO-AI and selected MCP hosts remain external. |
| Windows 11 | Hermes, Codex, or Docker Desktop after its recorded Windows x64 evidence is green | Manager lifecycle/MCP evidence or container health | No unrecorded architecture claim. |
| Ubuntu 22.04/24.04 | Hermes, Codex, or Docker Engine after its recorded Linux x64/arm64 evidence is green | Manager lifecycle/MCP evidence or container health | Other architectures are not implied. |
| macOS Sonoma 14+ | Hermes or Codex after its recorded x64/arm64 run passes | Manager lifecycle/MCP evidence | CAD solver limits remain tool-specific. |
| Python contributor | Source checkout and contributor workflow | Dev merge gate | Manual package installation is for development or diagnosis. |
| MCP contributor | Any runtime plus the clean selected-server process | initialize, tools/list, safe backend probe, gateway proxy | Never add MCP-specific hosts to the base package/image for catalog optics. |

## Availability is evidence-driven

`src/wright_engineering/compatibility.json` records runtime and manager protocol
compatibility. Production evidence records each released adapter identity, the
exact Wright wheel hash, runtime-extra lock, platform/architecture, lifecycle or
MCP result, source isolation, and forbidden-executable audit. Fixture-only or
skipped runs do not make a platform supported. Docker publication to both GHCR
and Docker Hub remains mandatory and independent.

Every supporting record is bound to one immutable artifact digest, operating
system, architecture, manager profile, storage profile, source-isolated
candidate, forbidden-executable audit, and passed install/start/status/doctor/
use/stop/update/persistence/rollback/uninstall/offline checks. Evidence from a
different artifact, platform, or architecture remains visible but cannot fill
that record. Unavailable Windows, Linux, or macOS hosts remain explicitly
unverified and do not turn contract or fixture results into support claims.

For retained-state behavior and the exact difference between update, rollback,
uninstall, and purge, see [Engineering Program State Lifecycle](program-state-lifecycle.md).
