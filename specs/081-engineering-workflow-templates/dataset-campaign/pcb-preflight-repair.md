# PCB native project and immutable artifact preparation

The first thermistor run (`1647199a1a3144479451c8e6883f24f5`) stopped after its first board-build call returned `Project file not found`. The model then created the missing native board/project, but requesting the completed build operation again correctly hit the no-replay guard. The first build returned an error inside a successful MCP transport response. The future binding explicitly treats error payloads and failed nested pipeline steps as failures and establishes the project before its single build.

The supplied tables contain 6/14/15 components and require at least 8/15/16 paired net-label calls. Even an optimistic combined author stage needs 22/37/39 calls, before complete library searches, mounting-hole work or repairs. Symbol authoring and complete connectivity therefore have separate 32-call tasks. Every original task ID, original edge, human input and review remains present.

## Native saves also write project files

The selected KiCad image contains version 9.0.2. Its official source shows `BOARD.Save` delegates to `SaveBoard`, which calls `SaveProjectAs` unless settings are explicitly skipped. The selected MCP uses ordinary `board.Save`, including the routing SES import. Therefore recording an immutable project before routing would be incorrect even when `autoroute.net_classes` is omitted.

Primary source locations:

- [KiCad 9.0.2 Python board wrapper](https://github.com/KiCad/kicad-source-mirror/blob/9.0.2/pcbnew/python/swig/board.i#L154).
- [KiCad 9.0.2 native SaveBoard](https://github.com/KiCad/kicad-source-mirror/blob/9.0.2/pcbnew/python/scripting/pcbnew_scripting_helpers.cpp#L317).
- Selected provider `tools/pcb_pipeline.py:280` recreates the empty board and sets a default drill rule; supplied rules must be reapplied after this build.
- Selected provider `tools/pcb_autoroute.py:780` also explicitly rewrites project JSON when `net_classes` is supplied.
- Selected `tools/export.py` uses native CLI export commands; the campaign's `native_rule_check.py` runs CLI ERC/DRC, retains full report bytes and verifies that the checked source did not change.

Exact public KiCad sources and source-hash evidence are retained under `.local-run/feature-081-live/kicad-prerequisite/native-source-audit`. This is a read-only source audit, not a native simulation or a correctness qualification.

## Future 14-stage graph

1. Capture the electrical basis from the complete human inputs and sketch.
2. Review the basis through the original local approval mechanism.
3. Original author task places all actual components and saves `symbols/design.kicad_sch`.
4. Connect every supplied net and save `connected/design.kicad_sch` separately.
5. Fixed copy stages the connected schematic at `unrouted/design.kicad_sch`.
6. Native project setup creates the working PCB/project and applies initial rules. Its report records the operation; these mutable prerequisite files are not prematurely published as engineering deliverables.
7. Invoke the native build once with `approved=false`; it returns the actual placed board before routing. Complete supplied mounting holes, placement, pad/net membership and all original design/net rules, then capture `unrouted/design.kicad_pcb` and `.kicad_pro` together.
8. Fixed copy stages the unrouted PCB at `routing/design.kicad_pcb`.
9. Fixed copy stages the unrouted project at `routing/design.kicad_pro`.
10. Route the working board with the actual native router. Finish native changes before capturing both routing PCB and project. Do not change original project rules or supply new `net_classes` while routing.
11. Fixed copy publishes final `design.kicad_pcb`.
12. Fixed copy publishes final `design.kicad_pro`.
13. Fixed copy publishes final `design.kicad_sch` from the connected schematic.
14. Original verification/export task reads these final native files, runs native ERC/DRC and emits the original BOM, Gerber, drill and archive outputs. No board save, autofix or native mutation is permitted after final publication. Unexpected hash drift remains an error.

All six copies are explicit direct MCP nodes with literal workspace-relative `sourcePath` and `destinationPath`. Each source is a prior same-run generated file declared in `expected_files`. Working copy destinations have no immutable engineering artifact declaration. The three final copy destinations are each declared exactly once. Empty output subdirectories are prepared in advance; no fixture geometry or copied input is substituted for a generated deliverable.

## Verification and deployment boundary

`tests/test_pcb_campaign_stage_budgets.py` passes all three actual dataset cases without native calls. It verifies call-count bounds, all 14 stages, original edges, input mappings, six source-before-copy relationships, required destination directories, unique immutable artifact paths and final-copy declarations. Ruff passes for the preparer, enroller and test.

The preparer requires fresh qualified `wright-workspace-files__copy_file` discovery whenever a real tool catalog is supplied; offline drafts leave its digest unresolved and cannot be treated as enrolled. The enroller now accepts a fresh attempt ID and retains the scoped copy capability alongside the selected native tools. No attempt-001 source, grant or native artifact was changed by this preparation.

Following deployment of the scoped copy capability, all three fresh attempt-002 cases are enrolled. The immutable combined manifest is `.local-run/feature-081-live/campaign-execution/pcb-attempt-002.json`. Ordinary preparation passed for all three with a lifecycle rejecting tool dispatch: fourteen stages, six literal copy nodes, three final-copy artifact declarations, fourteen current tool pins, complete original input hashes/mappings, preserved original IDs/edges, and no repeated immutable native paths. Evidence is `campaign-execution/pcb-attempt-002-normal-preparation-verification.json`. The selected copy schema digest is `3d1eb786a6da2edcd2d42e858432377ffcecafc5450c20d50bac6ba7c18cc791`.

The isolated KiCad runtime now has twelve mounts: its six original input/output mounts plus six exact new attempt-002 mounts. Its original container is retained stopped as `wright-081-kicad-runtime-before-attempt002`; no container was deleted. The image, registry command, network, environment values, user, working directory, entrypoint, command, resource limits and other stable host settings are unchanged. All old file hashes, including the three native partial files, and all eighteen native tool identities are unchanged. Docker reordered environment entries, so the comparison uses their exact sorted name/value entries. The prerequisite receipt is `campaign-execution/pcb002-mount-extension.json`.

Only the selected KiCad registration was deactivated/reactivated during the extension. No shared API or other runtime was restarted. No campaign workflow, native CAD or routing operation was dispatched for this repair.
