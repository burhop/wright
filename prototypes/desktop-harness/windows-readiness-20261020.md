# Windows engineering readiness repair

Baseline: dev `40b6270ec5e9bc1c1e9c61c20a0bf50269f35b82`.
Branch: `codex/windows-astra-readiness`.
Original Windows evidence remains in
`.local-run/windows-engineering-pilot-handoff-20261020/`; it is not a passing
readiness report. Local GB10 evidence is retained separately at
`/tmp/wright-windows-readiness-evidence-20261020/`.

## Agreed division of work

The user approved a separate Windows-local Hermes/Astra pilot for engineering
workflow authoring/refinement and execution, including helpers and recovery.
This does not change the desktop integration direction. Windows owns live
engineering qualification; GB10 delivers shared fixes through GitHub and then
returns to desktop UI improvements. No shared drive, SSH or GB10 service is a
Windows runtime dependency. Roadster reconstruction remains on hold.

## Findings and disposition

| Finding | Implemented response | Qualification boundary |
|---|---|---|
| R1 shared Hermes selects Sol | Document an isolated named Astra profile/API and existing SDK execution route; supply a bounded explicit-model probe. Map native Hermes relogin failures to the existing safe auth-required category. | No existing/shared profile changed. This host's isolated probe reports `SCOPED_MODEL_AUTH_REQUIRED` with zero inference requests. Actual Windows authoring, execution and provider requests remain required. |
| R2 Docker-only unlock text | Use instance/launcher-neutral Wright access guidance and document local private token retrieval. | Enforced authentication is preserved; wrong tokens still fail. |
| R3 protected initialization before login | Move tool/session/surface providers and saved-theme initialization inside the existing authentication gate. | Browser test observes zero protected requests before login, rejection of a bad token, then initialization after unlock and reload. |
| R4 Node range mismatch | Declare the locked engine ranges in root package metadata and document `npm ci --engine-strict` with an isolated supported runtime. | Existing Node 22.22.0 fails EBADENGINE; isolated Node 26 passes. Node 25 is excluded by the declared range. No global upgrade or dependency update. |
| R5 lifecycle endpoint on direct Uvicorn | Return the normal structured 503 `native_lifecycle_unavailable` diagnostic when no native manager challenge exists. | `/api/health` stays healthy. Existing challenged native identity behavior remains covered. No fabricated challenge. |

## Reused mechanisms and scope

Keep the existing authentication/session owner, normal workspace routes, shared
editor, SDK/HTTP adapters, model freezing, invocation redaction, gateway,
validator and durable run/review/recovery services. No second executor, general
authentication framework or vendor-specific workaround was added.

The model probe makes one model-only response through the existing SDK transport.
It refuses a shared/default profile or mismatched resolved provider/model before
inference, records observable request evidence, preserves distinct reported model
identity, and refuses to overwrite an earlier evidence directory. It does not
qualify workflow authoring or an engineering correction loop by itself.

Workflow runs retain the existing exact source/instruction/model/tool identities.
The existing continuation checks reject changed routes before inference.
Translation correction is tested through the actual bridge/SDK dispatch code
using controlled responses: both initial and repair requests carry the same
frozen route and retained instruction/request evidence. Controlled responses
prove routing behavior, not an Astra inference or engineering result.

The normal editor's capabilities remain unchanged. Served browser regression
covers workspace source save/reopen, CAS conflicts, diagram/source/AI review and
layout with controlled API fixtures. These tests do not replace Windows
observation or a real persisted workspace journey.

## Evidence and remaining work

- `focused-python-final.log`: 80 authentication/lifecycle/routing/rework/resume
  regressions passed before the additional relogin-category correction.
- `worker-probe-tests.log`: 28 worker/probe checks passed including that
  correction, no shared-profile inference and no leaked credential text.
- `astra-no-credentials/report.json`: retained pre-fix generic unavailable.
- `astra-auth-required/report.json`: post-fix explicit auth-required, zero
  invocation records. Credentials were not copied or obtained from another app.
- `node-incompatible.log`, `node-compatible.log`: strict engine checks.
- `browser-workspace-final.log`: served Chromium authentication/editor checks.

Repository gates and exact GitHub delivery are recorded after completion.
No Windows readiness or live model/provider success is claimed here.

Windows must complete the
[pilot instructions](../../docs/getting-started/windows-engineering-pilot.md):
normal authenticated workspace creation, source/diagram save and reopen,
actual Astra authoring/refinement and execution/helper/correction/recovery
requests, same-run durable resume, and a bounded real producer → measurement →
correction → revalidation loop. The pocket-defect fixture was inventoried but
not transferred; use its original Windows-local source and record hashes.
Retain explicit artifact identities and hold dependent work on nested provider
errors. Prove new shared mechanisms with a substantially different existing
workflow. Preserve historical failed runs, prior Roadster models and all evidence.
