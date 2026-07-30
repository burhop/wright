# Workspace Surfaces UX and Accessibility Contract

This document makes the host interaction requirements deterministic. Embedded
application content remains responsible for its own internal accessibility;
Wright is responsible for host controls, transitions, disclosure, isolation,
fallback, and preventing a nonconforming source from being presented as fully
accessible.

## Presentation Eligibility and Disclosure

| Source profile | Workspace panel | System browser | Required fallback/disclosure |
|---|---|---|---|
| Existing file | Existing provider contract | Only when the provider exposes an authorized browser-safe resource | Preserve the existing viewer when browser presentation is absent |
| Durable/typed display | Required | Optional authorized read-only presentation of the same revision | Safe text/table/download fallback when a renderer is unavailable |
| Managed app, including BREP | When a distinct preview origin and upstream framing policy permit | When declared; required safe alternative if panel is ineligible | State framing/isolation/host reason without weakening CSP/XFO |
| WebMCP-aware managed app | Same as its managed-app declaration | Same managed instance when shareable | Wright scoped SDK remains available; native WebMCP absence is not a failure |
| Packaged MCP App | Only after MCP Apps negotiation and sandbox support | No raw privileged App Bridge in a general browser tab | Show meaningful tool-result/resource fallback; a separate declared managed app may provide browser UI |
| Approved arbitrary URL | Browser-enforced view-only iframe when policy and framing permit | Required direct-navigation option | No proxy, credentials, bridge, lifecycle, or claim that iframe failure is fully diagnosable |
| Explicit active Python HTML | Isolated unprivileged panel only | Optional isolated read-only presentation if policy supports it | Safe sanitized/text representation; no bridge in either presentation |

Before start/open, the chooser shows source kind and version, trust profile,
eligible presentations, whether panel/browser share state, and the consequence
of isolated mode. A shareable source reuses the same ready/starting instance for
simultaneous panel/browser requests. An isolated source creates a new instance
per presentation and requires that difference to be acknowledged before launch.
An ineligible remembered preference is never silently substituted: Wright names
the reason, selects the highest-priority safe eligible presentation, and lets the
user change the remembered choice.

## Commands and Consequences

| Command | Immediate effect | Runtime/output effect | Recovery |
|---|---|---|---|
| Close presentation | Revoke and remove only that panel/browser view | Apply declared lifetime; workspace-lifetime app keeps running | Open a new authorized presentation |
| Close surface tab | Close its panel presentation and retain durable surface intent | Does not imply runtime stop or output deletion | Reopen from workspace surfaces |
| Detach to browser | Activate an authorized browser presentation, then close the panel only after browser-open succeeds | Share the instance when declared shareable | Reopen panel; browser failure leaves panel intact |
| Stop application | Revoke every presentation/instance grant, stop and reconcile the owned tree | Runtime becomes stopped/failed; durable declaration remains | Restart creates a new generation |
| Delete durable output | Require destructive confirmation that states retention/recovery policy; remove current workspace surface intent and schedule payload cleanup | Does not stop unrelated runtimes | Restore only through the stated vault/backup retention path; never imply undo when none exists |

## Truthful Status and Valid Actions

`reconciling`, `reconnecting`, and `frame-status-unknown` are UI projections,
not additional durable lifecycle states.

| Projection | Required message | Valid primary actions |
|---|---|---|
| `declared` | Not running/presented | Start, close, diagnostics |
| `starting` | Readiness progress and bound | Cancel/stop, diagnostics; no usable frame |
| `ready` | Presentation and health are current | Open panel/browser, focus, close presentation, restart/stop, diagnostics |
| `unhealthy` | Last safe health result and retryability | Retry health, restart/stop, browser fallback if eligible, diagnostics |
| `reconciling` | Persisted intent is not yet authority | Diagnostics, cancel/close; no open until reconciliation completes |
| `reconnecting` | Existing presentation is re-authorizing current generation | Retry, close, diagnostics; stale content is visibly inert |
| `stopped` | Runtime is not running | Restart, close surface, diagnostics |
| `failed` | Stable safe error and correlation ID | Only projected retry/restart/reconcile/close actions, diagnostics |
| `frame-status-unknown` | Browser enforcement may have blocked embedding | Open in browser, retry panel, help; never claim healthy iframe content |

Blank frames, stale interactive snapshots, and disabled controls without an
explanation are prohibited.

## Layout and Retention

All sizing is computed from the workspace panel container, not the viewport.
Layout schema version 2 stores a basis-point ratio keyed by user, workspace, and
normal/focus mode; values are clamped only after current container constraints
are evaluated, and malformed/legacy values produce a documented default.

- Wide layout minimums: chat 320 CSS px, surface 480 CSS px, separator hit target
  8 CSS px. Chat defaults to 38% in normal mode and 360 CSS px in focus mode,
  capped at 50% of the available container and 720 CSS px.
- Focus mode hides non-chat workspace chrome that is not needed for surface
  control and assigns all remaining space to the active surface. Chat stays
  visible, operable, resizable, and live.
- If both minimums plus the separator cannot fit, Wright enters narrow mode. A
  semantic two-option Chat/Surface switcher shows one pane at a time, preserves
  both mounted states when policy allows, announces updates in the hidden pane,
  and reversibly restores the previous wide ratio.
- Requirements hold at 200% browser zoom and with platform text scaling. Essential
  host controls cannot be clipped; overflow uses a labeled menu.
- Up to six stateful live/MCP/WebMCP hosts are retained per workspace by default.
  Static/suspendable hosts are evicted first. Before a stateful host is reloaded,
  Wright names the surface, explains potential state loss, and offers keep,
  reload, or open in browser. Closing a presentation remains exact-once.

## Keyboard and Focus Model

- Surface tabs use `tablist`/`tab`/`tabpanel`. Exactly one tab is in the roving
  tab order. Left/Right move, Home/End jump, Enter/Space select, and Delete or
  the documented close control closes a closable tab. Reordering is not part of
  version 1; no undocumented drag-only ordering is exposed.
- After tab close, focus moves to the next tab, otherwise the previous tab, then
  the surfaces heading when none remain. Mode changes restore focus to the
  initiating control or the selected surface toolbar.
- The pane divider is a focusable `separator` with orientation and numeric
  `aria-valuemin`, `aria-valuemax`, and `aria-valuenow`. Arrows adjust 2%,
  PageUp/PageDown adjust 10%, Home/End select the legal extremes, and focus is
  visibly distinguishable.
- Host focus order is chat controls, surface tabs, surface toolbar, embedded
  content, and the return-to-host sentinel. `F6` cycles host regions while focus
  is in Wright chrome. Labeled controls before and after the frame move focus to
  embedded content or back to surface controls/chat.
- Wright-owned and approved managed-app fixtures must not trap Tab or hide focus.
  If arbitrary/nonconforming cross-origin content traps focus and Wright cannot
  prove escape behavior, the panel is labeled unverified and the system-browser
  fallback is offered; Wright does not claim host JavaScript can intercept every
  key inside a hostile cross-origin frame. Electron additionally provides its
  tested application-level return-to-host accelerator.
- Every interactive host control has an accessible name, visible focus, and a
  stable `data-testid`; automated gates allow zero critical or serious axe
  violations, and manual keyboard, zoom, high-contrast, and screen-reader spot
  checks cover the complete host journey.

## Beginner Graph Input and Revision Behavior

The no-optional-dependency graph helpers accept ordinary finite numeric
sequences. Line/scatter require equal non-empty `x`/`y` lengths; bar requires
equal non-empty labels/values; histogram requires a non-empty numeric sequence
and uses documented bins or an explicit positive bin count. Strings are not
silently coerced to numbers. Non-finite values report the first failing field
and index. The default 100,000-point-per-series and envelope limits come from
`policy-defaults.md`; larger input is rejected before partial publication with
an example-linked reduction/aggregation suggestion.

Required helper fields are title, axis labels where applicable, and a non-empty
accessibility description. Typed interactive results include an accessible
table or text fallback. A missing optional adapter names the package/extra and a
baseline Wright alternative; no viewer action installs it implicitly.

Using the same `display_id` atomically advances the current revision; a duplicate
idempotency key returns the prior revision; a stale revision is retained only as
history and never becomes current. Omitting `display_id` creates a new logical
surface. The UI labels revision/time and offers explicit history selection when
history is retained, so an update cannot be mistaken for a new output.

## Capability Consent and Diagnostics

Consent identifies the app/source and immutable version, owning workspace,
requested operation and bounded data categories/parameters, risk tier, why it is
requested, effective policy restrictions, duration/expiry, available persistence
scope, and what denial means. Allow, deny, and cancel are distinct, plain-language
actions; high-risk/mutating requests do not offer remembered persistence by
default. Administrator-only decisions are labeled rather than shown as a usable
engineer action.

Diagnostics categorize failures as readiness, health/runtime, framing/host,
permission/policy, target/transport, protocol/version, renderer/data, or cleanup.
Every category provides a stable code, safe explanation, correlation ID,
retryability, and the next valid action. It never exposes a credential, target
pin, sensitive URL/query, protected content, or internal identifier as the only
explanation.
