# Capability and version qualification

Checked 11 October 2026 on GB10 Linux ARM64. **Opt-in experimental chat pilot**
under the accepted native-tool exception. Process-UI model authoring and workflow
execution remain gated. Documentation, deterministic tests and actual runtime
observations are separate evidence classes.

## Preferred route and versions

Use public low-level Python `CodexClient` controlling documented app-server stdio.
The SDK exposes lifecycle, notifications and explicit approval handling; no private
stdio implementation or maintained runtime fork is needed. Stable SDK maturity
[does not remove the experimental app-server command](https://learn.chatgpt.com/docs/app-server).

| Option | Documented status | Decision |
| --- | --- | --- |
| Official Python SDK + app-server | [SDK stable](https://learn.chatgpt.com/docs/codex-sdk); app-server experimental | Preferred pinned integration; clean isolated worker and explicit denial |
| Narrow public JSON-RPC client | Protocol documented; command experimental | Reserve if SDK lifecycle controls become insufficient; cannot add a missing tool ceiling |
| Noninteractive CLI | [Documented automation/resume/JSON output](https://learn.chatgpt.com/docs/non-interactive-mode) | Development jobs; inferior fit for Wright interactive approval/event ownership |
| Historical Codex MCP-server wrapper/private APIs | [MCP-server removed](https://learn.chatgpt.com/docs/mcp-server) | Unsupported embedding route |
| Codex Cloud | Hosted development tasks | Separate from Wright embedded execution; not tested here |

| Component | Pinned/observed version | Qualification |
| --- | --- | --- |
| Python SDK | openai-codex 0.162.1 | Installed separately and used in real probes; optional locked Wright extra |
| CLI runtime | openai-codex-cli-bin 0.162.1 | Exact SDK dependency; runtime thread version checked; mismatches rejected |
| Desktop Codex | Existing 0.159.2 | Unchanged; not this integration runtime |
| Model/effort/auth | gpt-6.1-sol / high / ChatGPT | Actual bounded authenticated turns and same-thread restart continuation passed |
| Wright source baseline | dev ba2fad68c181165b96b9c15c40b1a1f63c88acb3 | Dedicated feature worktree; installed command not used as baseline |
| Host | GB10 Linux ARM64 / Python 3.13 | Actual native process launch/cleanup and browser tests; other hosts distinct |

The [0.162.1 official release](https://github.com/openai/codex/releases/tag/rust-v0.162.1)
and public schema are the version boundary. SDK typed thread-start params omit
experimental dynamicTools; its public dictionary interface passes the documented
experimental field. Upgrades require regeneration/inspection and qualification.

## Capability matrix

Supported means locally qualified within the stated pilot scope. Experimental
means an upstream/runtime authority limit or accepted exception remains. Unverified
means no local proof; unavailable means Wright deliberately rejects the capability.

| Capability | Status | Evidence / limit |
| --- | --- | --- |
| Interactive text and streaming | Supported pilot / experimental runtime | Actual authenticated adapter and served HTTP/browser turn; text only |
| Model/auth readiness | Supported for selected ChatGPT model | Catalog + account/identity check and actual access; catalog alone is not entitlement |
| History and same-thread restart | Supported after a materialized turn | Local fixture and authenticated two-turn restart; exact native ID retained |
| Never-used thread after restart | Unavailable continuation limitation | Native history not materialized; never silently replace its ID |
| Default change with old sessions | Supported | Saved platform routing for path/query/body; cache reuse and mixed-session API tests |
| Cancellation | Supported on GB10 | Intent/ACK distinct from persisted interrupted terminal; local runtime fixture |
| Worker disconnect/restart | Supported with holds | Known turn reconciliation; lost ACK remains unknown; no automatic submission retry |
| Failures/denials/late/overflow/reroutes | Supported fail-closed handling | Deterministic transport/adapter tests; uncertain native effects are not proved safe |
| Read-only Wright gateway | Supported narrow pilot | Real runtime callback + GatewayService; exact scope/principal freeze and normal audit |
| Codex native external MCP stdio/HTTP | Unverified / not configured | Dynamic-tool bridge is not MCP interoperability proof |
| Native Codex tools | Experimental accepted exception | collaboration.list_agents executed despite flags, no approval; all remaining tools unqualified |
| Enforced zero executable tools | Unsupported by tested public protocol / FAILED | Public schema lacks ceiling; Rust internal ToolPolicy is not a public client control |
| Process-UI model authoring | Unavailable / gated | Capabilities false; restricted invocation rejected; cached Hermes owner cannot substitute |
| Manual editor and saved/common views | Preserved | Served normal Workflows entry and current reviewed editor acceptance; no model work |
| Workflow-task model execution | Unavailable / gated | Codex workflow start requests rejected before runs; existing executor unchanged |
| Frozen replaceable assets/config | Supported for chat | Saved actual instruction/config/tool snapshots and digests; drift rejected before submission |
| Request/tool evidence | Supported at observed boundaries | SDK calls/notifications and gateway receipts; no inferred provider prompt or external effect |
| Usage and dollar cost | Limited / unverified | Protocol usage events may be retained; no qualified accounting, price or billing-cost UI |
| API-key route and billing | Unverified / gated | Factory rejects it; no billing fallback; stable key identity not qualified |
| Broader tools, attachments, role substitution | Unavailable | Fixed read descriptor and text-only input; no arbitrary permission grants |
| Docker Linux ARM64 | Supported scoped fixture / experimental | Clean exact image, offline API/Hermes smoke, private optional SDK worker gateway/denial/cancellation/restart with no external network; image-security policy passed |
| Docker authenticated/packaged browser and SDK inventory security | Unverified | Credential-free mounted worker proof does not establish live access, packaged browser parity or worker dependency scan |
| Linux x64 and native Windows | Unverified; native Windows gated | Native ARM64/container observations and wheels do not establish those host lanes |
| Production support | Unavailable | Experimental runtime and incomplete repository/host gates |

## Regression and qualification limits

Core/DataVault/adapters pass **1018 tests, 18 optional skips**. Mixed-platform routing,
workflow denial, role substitution, transport uncertainty and frontend lifecycle
checks are recorded in the evidence index; the corrected full API suite passes 772 tests.
Full repository gates have not passed:
Docker 27.5.1 ARM64 now has an immutable clean-archive candidate: exact-image smoke,
scoped Codex lifecycle fixture and Trivy 0.70.0 policy scan passed. Earlier missing-image
failures remain retained. The broader merge gate stopped at the old startup fixture; its correction passes
the full API suite, but the remaining whole gate has not been rerun. Exact results
and passed precursor tranches are in the evidence index.
The unchanged frontend/root npm lock audit reports 13 inherited findings (including
5 high and 1 critical); those are distinct from the image scanner inventory.
Manufacturing exact-byte baseline failures remain preserved;
Robot contrasting regressions are offline shared-mechanism checks, not Codex workflow
execution. No physical or human engineering acceptance is claimed.

See [evidence](evidence.md), [exceptions](exceptions.md), [installation](quickstart.md)
and [Windows handoff](windows-handoff.md) for exact scopes and remaining work.
