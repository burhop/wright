# SteveCAD workflow code checkpoint

12 October 2026. The user requested completing and checking in the current code.
Additional example runs are deferred. This checkpoint preserves delivered code
and useful engineering evidence without claiming that all remaining campaign
requirements, user acceptance or physical robot tests have passed.

## Delivered behavior and ownership

SteveCAD is an independently connected remote OAuth MCP provider. Wright's
existing durable runtime, gateway, file/result storage and model adapters own
execution and evidence. The workflow accepts a design prompt, produces its
specification and preconstruction test plan, builds and inspects exact CAD,
passes the actual STEP through AgentCAD to Blender, and creates an illustrated
review with three original captures and three native renderings.

The shared changes provide explicit MCP image-output bindings, bounded
same-operation reconciliation, saved context budgets, complete assembly
observation transport and evidence redaction for one-use transfer credentials.
They retain existing scope, argument, replay, deadline, model and approval
enforcement. Native provider protocols remain external. No additional executor
or independent UI job-state authority is introduced.

The native source's camera correction is prospective v20. Its real bracket
render and source/compile checks are retained; the last completed full process
and same-source reuse proof use v19. These are different verification scopes.

## Retained engineering outputs

- Original four-hole block: eight CAD checks and ten final review requirements
  pass; exact numeric geometry, file hashes, all six images and report rendering
  are independently checked. Runtime: 617.248 seconds.
- Six-hole block: same accepted v19 source and frozen routing, changed input,
  fresh run and correct final geometry. Runtime: 542.533 seconds. Original
  review retains an unrequested intermediate-stock-state test as UNVERIFIED.
- Bracket: correct envelope, volume and bores; original review 11 PASS /
  one UNVERIFIED. The same exported geometry now has supplemental measured
  6.00 mm base/upright walls and a corrected native top image. Original evidence
  retains its missing measurement and camera mismatch. Runtime: 1204.087 seconds.
- Robot revision 7: 110 solids, 18 unique print meshes / 28 printed quantities,
  BOM, assembly instructions, joint ranges, three final native renderings,
  illustrated review and H.264 MP4 media. Original review remains 10 PASS /
  four UNVERIFIED / two FAIL. Additive exact-STEP audits record 14,364 sampled
  printed-pair evaluations (minimum non-seat gap 0.400 mm, zero overlap) and
  29 aligned fastener stacks with 66 measured planar bearing pairs. They do not
  rewrite the original review.

The commit retains a selected evidence set rather than every historical run,
scratch file and duplicate media archive. Additional original records remain
in the local worktree. The committed evidence index records exact paths/hashes
and the selection boundary. No source, original CAD or local run evidence is
deleted as part of check-in.

## Durable MCP knowledge

[Usage guides](../mcp-catalog/usage-guides/README.md) cover SteveCAD, KiCad,
AgentCAD, Blender and the file-transfer MCP. The common template and AGENTS.md
require a discoverable guide for every server installed or used. Guides record
observed versions, successful schemas/examples, evidence, prerequisites,
pitfalls, recovery and unverified capabilities, without credentials.

## Validation and remaining limits

Current source-bound regression, lint, format, source regeneration, exact
artifact and credential checks are recorded in the committed check-in evidence.
An initial Windows sandbox test stalled; the isolated mocked test passes
outside it. That diagnostic is not reported as a passing full test run.

The broader different-live-workflow qualification of the new shared mechanisms
remains open. The latest workflow-editor walkthrough has a retained clipped
diagram finding. The confirmed SteveCAD visibility bug has a minimal redacted
packet but no supported submission/report ID. Full native-process joint/robot
proof and physical printing, assembly, strength, motor sizing, drive transmission
and powered operation remain unverified. The user's CM5 and official IO Board
are recorded; provisional servo choices still need actual hardware confirmation.

Code check-in is distinct from `dev` integration, a production release, public
marketing publication and human engineering acceptance. Required push/merge
gates apply before those separately authorized actions.

## Pre-merge image-selector correction

The integration review reproduced a literal-selector mismatch: Python's value
equality let boolean `true` select a response whose request argument was numeric
`1`, including nested objects. The corrected matcher compares complete JSON
representations and rejects unsupported/nonfinite data, preserving boolean and
numeric distinctions. Negative controls cover both boolean values, nested
objects and lists; a positive control retains identical nested boolean requests
with different object-key order. The earlier 275-test checkpoint remains
historical evidence; current merge/push gate results are recorded separately.

The full integration gate also caught stale catalog test inputs after SteveCAD
expanded the current catalog from 81 to 82 entries. The historical 69/70-entry
update scenarios now read an immutable fixture, and the current status assertion
includes SteveCAD in the preview category. All 532 registry tests pass after this
correction. The stdio framing test that timed out in the initial full run passes
both independently and in the complete corrected suite; its 30-second deadline
and protocol assertions remain unchanged.
