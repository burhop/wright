# Capability and version matrix

Qualification date: 11 October 2026. Experimental prototype. "Verified" below
refers only to its specified local boundary, not arbitrary provider compatibility.

| Component | Observed version/identity | Qualification |
|---|---|---|
| Source baseline | remote dev `ba2fad68`; local prototype checkpoint `a17acb85` | Windows worktree frozen at checkpoint; same feature branch continues in prototype-next; old checkout/pilot retained |
| GB10 host | Linux ARM64; Python 3.13.12 | locked dependencies and live digital MCP proofs |
| Python MCP client/server | `mcp==1.28.1`, from `uv.lock` | initialized stdio; 12 tools in gateway profile (earlier profile 11); protocol `2025-11-25` |
| Local Codex CLI | `0.159.2` | help inspected; plugin commands not executed |
| OpenAI desktop GUI | unreported | installed plugin/right-panel experience unverified |
| Desktop model | requested/displayed by user; transport reports no identity | replies authored in actual chat; no independent model attestation |
| Node | `22.22.0` | frontend build/focused tests/browser preview work; below jsdom 30's declared `22.22.2` minimum |
| Runtime profile | SHA-256 of adapter/dispatch/backend/transport + MCP version + confined-inspection flag | retained in observable frozen binding; does not hash every dependency |

| Capability | Status | Evidence / limit |
|---|---|---|
| Desktop plugin with skills + MCP | documented upstream; local package prepared | Windows host confirmed; resolved Windows setup and live installation approval still required |
| Workspace create/source save | locally verified | real MCP protocol client and existing owners |
| Desktop conversation provides workflow reasoning | locally verified | actual chat-authored replies; canonical runs completed; no model worker |
| Existing editor/result viewer without Wright chat | locally verified in browser | normal Workflows entry; no agent/inference API requests in capture |
| Current hosted editor authoring | 11 focused browser cases verified | direct inputs/instructions, typed keyboard connection/rejection, live drag/pan/zoom, Undo/Redo, source/layout reopening, managed-field rejection, real CAS and compact layout; full legacy/installed acceptance separate |
| Desktop right panel / native plugin UI | unverified | earlier app-open request had no observed response/rendering proof; no automatic retry |
| Declared input / same-run continuation | locally verified | synthetic fixture; invalid selection denied; original run and first output retained |
| Connected working-view input submission | locally verified in served browser | actual Submit sends one declared choice, next desktop task uses it, same run completes; exact reload/close and preserved first output after API restart; native desktop and event-stream attachment separate |
| Restart at durable declared input wait | locally verified | controlled isolated API SIGTERM/restart with same observable binding |
| Abrupt API restart during pending reasoning | current leased response profile locally verified for retention/denial | same run/request retained, stable start attaches without replay, dead-owner answer denied 409 and no output; automatic continuation unsupported. Frozen Windows baseline retains its earlier failed admission |
| Live-owner admission patch | isolated candidate qualified; applied in development, not Windows target | live reply completes; post-SIGKILL reply denied 409 with no replay; current leased response profile now passes fresh SIGKILL/reopen probe; frozen Windows target retains its recorded limitation |
| Restart during an uncertain tool effect | unverified; gated | no automatic request/effect replay permitted |
| Normal MCP disconnect | locally verified | pending reasoning preserved; reconnect/cancel and input continuation checked |
| Abrupt MCP loss/liveness expiry | new development profiles locally verified | 30-second lease/5-second pulse; actual child death, mutation denial, pending preservation and same-live-run reconnect; exact expiry boundary in controlled-clock tests; frozen Windows checkpoint still has membership-only behavior |
| Cancellation / late reply denial | locally verified | proof 02; canonical cancellation followed by HTTP 409 |
| Scope/auth/invalid reply/configuration drift | locally verified at tested boundaries | live denials plus strict repository/adapter tests |
| Inspectable Wright instructions / handoff receipts | locally verified | embedded versioned assets, exact request/reply identity; observable boundary only |
| Provider-internal prompts / exact upstream model receipt | unavailable at this transport | no fabricated evidence |
| Global desktop native-tool ceiling | unverified | prompt guidance is not enforcement; earlier failures/exception retained |
| Read-only Wright gateway task | locally verified, separately opt-in | exact privately enrolled source/input/schema; one `inspect_file` dispatch; ungranted start 403; other scopes remain gated |
| Typed action proposals through MCP | locally verified | bounded typed envelope; existing runtime validates and dispatches; reconnect completes same run without repeating inspection |
| Formatted development response/action profiles | locally verified for specified boundaries | leased response reconnect completes same live run; separately opt-in action profile completes one granted inspection; response restart retention/denial separately qualified; uncertain effects and installed host remain separate |
| Other MCP/CAD/application/external-action tasks | gated | preserve original contracts and explicitly qualify each dependent capability |
| Confined generated process-UI authoring | gated | distinct from ordinary workflow-source authoring through desktop tools |
| Manufacturing preparation / Robot Tracking Diagnosis | original fresh copies/readiness verified; execution unqualified | original scenario hashes retained, 20 template tests pass; both catalog drafts block supported execution type/configuration; full bindings, tools, validation/reviews and meaningful runs remain required |
| Standalone Hermes / OpenClaw stub | 32 focused regressions pass | full gates and broader installed behavior separate |
| Earlier Codex-inside-Wright chat pilot | preserved; 40 controlled regression tests pass | separate worktree, no live model/auth rerun or replacement |
| Windows desktop → GB10 | proposed, unverified | prepared SSH stdio + loopback web-forward handoff; executable/authorized alias and installed loading require Windows observations |
| Docker / Linux x64 | unverified | no cross-host compatibility claim; broader product packaging outside this prototype |

Official sources:
[plugin packaging and local marketplaces](https://developers.openai.com/plugins/build/plugins),
[complete plugin testing](https://developers.openai.com/plugins/deploy/connect-chatgpt),
[desktop browser](https://learn.chatgpt.com/docs/browser) and
[MCP configuration](https://learn.chatgpt.com/docs/extend/mcp).
Documented support does not establish this package's availability in this user's app.
