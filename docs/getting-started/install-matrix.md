# Install Matrix

| Use case | Recommended path | Verification | Boundary |
| --- | --- | --- | --- |
| Existing Hermes user | [Native Hermes](hermes-plugin.md) after the compatibility page names a released package-capable Hermes | `/wright start`, `/wright status`, `/wright doctor` and the displayed local UI URL | Currently blocked by released Hermes 0.18.2 being Git-only. Do not substitute a checkout. |
| Turnkey trial or third-party evaluator | Published Docker image `burhop/wright:<tag>` | Open `http://localhost:8080`; `/api/health` succeeds | BYO-AI and selected MCP host dependencies remain external. |
| Windows 11 | Native Hermes once Windows x64 public lifecycle evidence is green, or Docker Desktop | Native lifecycle evidence or container health | No Git/Node/npm requirement for native users. |
| Ubuntu 22.04/24.04 x64 | Native Hermes once Linux x64 evidence is green, or Docker Engine | Native lifecycle evidence or container health | Other architectures are not implied. |
| macOS Sonoma 14+ | Native Hermes only after the recorded architecture passes | Native lifecycle evidence | Docker/CAD solver limitations remain tool-specific. |
| Python contributor | Source checkout and [contributor workflow](https://github.com/burhop/wright/blob/main/CONTRIBUTING.md) | Dev merge gate | Manual `pip install wright-engineering` is artifact diagnosis, not the user install. |
| MCP contributor | Either runtime plus the clean selected-server process | MCP initialize, tools/list, safe backend probe, gateway proxy | Never add MCP-specific hosts to the base package/image for catalog optics. |

## Availability is evidence-driven

The packaged compatibility contract is
`src/wright_engineering/compatibility.json`. A platform is supported publicly
only when production evidence records the released Hermes version, exact Wright
wheel hash, runtime-extra lock, platform/architecture, full lifecycle result,
source isolation, and zero forbidden executables. Fixture-only or skipped runs
do not make a platform supported.

At this feature-candidate stage, `production_native_available` is `false` and
`released_hermes_version` is `null`. Docker publication remains mandatory and
independent.
