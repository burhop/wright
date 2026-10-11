# Preparation and qualification follow-up, 10 October 2026 (068–069)

The previous goal turn made concrete progress through the settings repair and
066/067 evidence. This turn addresses the preparation issue found by that
walkthrough and reconciles retained qualification evidence. The full goal stays
active; this is not engineering release or completion of M0–M5.

## Engineer journey and shared implementation

The engineer opens an existing process, chooses **Prepare another run**, reviews
the inputs and selects **Prepare and check inputs**. Previously the focus-wheel
form displayed 45 individual saved file inputs before reaching that action.

The common working view now groups declared defaults under **Saved defaults**.
They remain expandable, editable and linked to their exact blocks. Unanswered
inputs, inputs with unresolved dependencies, locally invalid defaults and live
capability choices stay outside that disclosure. A preparation error or blocked
readiness expands the defaults. Editing still invalidates readiness; recorded
run inputs remain visible, frozen and sourced from that run's actual values.

This uses the existing interaction snapshot, InputEditor, shared field feedback,
readiness panel and backend/client calls. No new binding schema, executor,
prompt policy or vendor behavior is introduced. The definition of readiness and
the values sent by `prepare()` are unchanged. The shared-kit/client versions and
saved custom-interface contracts are unchanged; the common fallback receives
the presentation improvement.

## Visual evidence through the served workspace

- [Before: individual saved inputs](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-167-workspace-shell-current/screenshots/raw/06-prepare-after.png).
- [After: wheel preparation](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-168-preparation-defaults/screenshots/raw/02-prepare-after.png).
- [Smaller window](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-168-preparation-defaults/screenshots/raw/04-narrow-after.png).
- [Different process: heat-spreader preparation](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-168-preparation-defaults/screenshots/raw/06-thermal-after.png).
- [Seven-step walkthrough and manual repeat](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-168-preparation-defaults/report.html).

The actual production build 34 shows 45 wheel defaults and 13 thermal defaults.
Expanding the wheel group exposes all 45 controls and their input-step links.
The preparation action is in the initial viewport and remains visible at
1024×768, without horizontal overflow. The original wheel result reopens with
the exact sliced package. All seven steps pass, browser diagnostics are empty,
and the walkthrough structure validates. Desktop, narrow and thermal screenshots
were visually inspected.

This is a passive preparation/navigation check. No readiness submission, Start,
review or engineering tool call was sent. Providers remain stopped, and the UI
correctly reports their missing availability. Their disabled Start controls are
not a new readiness failure caused by grouping. A fresh engineering execution
is not needed to prove a change limited to presentation; retained source/runtime
evidence stays separate.

## Regression and preservation

The final affected suites pass **168 tests**:

| Suite | Passed | Scope |
| --- | ---: | --- |
| CommonProcessView | 59 | Includes five new default-grouping cases, mutation boundaries, readiness, recorded inputs and review behavior. |
| ProcessWorkspaceTab | 15 | Existing workspace integration and retained process subjects. |
| ProcessUIKit | 83 | Shared controls and readers; JSDOM does not prove WebGL rendering. |
| Process view recovery | 11 | Existing durable client recovery behavior. |

The first combined run retained one slider test failure: it expected layer 2
while the label still showed layer 30. That case and its full suite passed when
isolated. The test now waits for the asynchronous reader mount and effects
before changing the slider. The full affected batch then passes. The production
toolpath viewer was not changed. Initial failure, isolated checks and final
reports remain under the private control root; no failed result was overwritten.
The existing JSDOM canvas-unavailable warnings remain disclosed.

`preparation-ui-audit-068.json` records exact source/test hashes, build and browser
observations. It verifies the unchanged set and hashes of **52 run records**,
**198 prior wheel files**, **64 latest wheel files**, and both accepted wheel and
thermal workflow sources. Type checking and the production build pass. The API
was not restarted; no CAD application was launched.

## Retained Linux CAD qualification reconciliation (069)

The independent `linux-qualification-current-audit-069b.json` confirms:

- The retained clean-base observation reports x86_64 with no FreeCAD binary or
  Python module before selected-provider setup.
- The installed provider checkout remains commit
  `63acb305573194a011641ab13ccfb391fe95769f`; native startup/restart records identify
  FreeCAD 1.1.1.
- **53 files** retain their hashes: the original 38 artifacts, four pre-restart
  recovery copies, six new post-restart artifacts and five final recovery copies.
  The original records' 42-before / 48-after counts reconcile exactly.
- Both native archives open as valid ZIPs and contain one editable `Part::Box`:
  10×8×6 mm and the genuine 12×8×6 mm variant. A passive binary-STL read independently
  confirms the base specimen's 12 triangles, paired opposite edges, 10×8×6 mm
  extent and signed volume 480 mm³.
- Two retained authenticated gateway records include initialize, tools/list and
  successful native document-list calls. Direct MCP and gateway observations
  during the stopped-backend interval both record explicit connection-refused
  errors with `isError=true`.
- The exact qualification container is currently `exited`. No qualification or
  engineering provider was restarted for this audit.

The initial passive reader attempted to import an unavailable optional mesh
library and stopped before any action. The final reader uses only the standard
library for the small binary specimen. An initial 49-file audit is retained;
the extended audit adds the four earlier recovery copies and reconciles counts.

This strengthens M1's retained Linux evidence without claiming a new live
qualification, Windows recovery coverage, CAD suitability for manufacture,
standards conformance or completion of the dock's native deliverables.

## Remaining work

Audit 065 still governs the full requirement list. The dock decision and native
package, actual existing swim-lane integration, final two-job presentation and
remaining evidence correspondence remain incomplete. The large-file warning
setting's missing consumer from 066 is also unresolved. No acceptance gate was
removed and no pending human review was answered by these checks.
