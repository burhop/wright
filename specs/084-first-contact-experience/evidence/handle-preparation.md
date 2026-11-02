# Printed02 preparation handoff

Status: local source implementation and focused fixtures verified on 23 October
2026. This is T008 preparation evidence, not a live handle run, installed/served
proof, successful provider qualification, T011 correction proof or engineering
acceptance. No provider was installed/called and no workflow was started by this
work.

## Accepted-source and scenario identities

The existing `examples/process-interfaces/printed-replacement-part/prepare.py`
accepts an explicit `scenario_id`; omission preserves Printed01. Printed02 uses
`scenarios/printed-replacement-part-02.json` (six unchanged original inputs plus
original profile raw-byte SHA-256) and the adjacent versioned instruction asset.
Every staged input is digest recorded; instruction bodies are copied into the
proposed source. Earlier accepted sources keep their existing bodies/identities.

The base template remains `printed-replacement-part`. The new catalog starter is
`replacement-drawer-handle`; these have different task IDs. The prepared input
`scenario-binding.json` records the intended starter/scenario origin.
`preparation.json` retains base-template and proposed-source digests, exact input
hashes and the normal proposed acceptance path. Its legacy `feature` label still
identifies the reused 083 preparation mechanism, not a live 084 completion claim.
The integrator must accept this transformed proposal through the existing source
service and bind/open that resulting accepted revision. Do not reuse starter
block IDs or assume a starter-bound UI is compatible; use common-view fallback
until exact contract/subject bindings are checked.

## Preserved engineering contract

- The original full Printed02 profile is selected explicitly and checked against
  coverage metadata. All 10 requirements and 18 checks remain unchanged; the
  shared helper rejects scenario/profile mismatch and cross-family selection.
- The original 96 mm mounting reference and five-wall/40% PETG profiles are
  mandatory. Wheel-only native-inspection/retained-source bindings fail before
  staging. Configured geometry requires an explicit matching basis scenario.
- A durable local geometry review consumes actual repaired mesh, geometry-only
  preview, construction/repair observations and original inputs before every
  slicer stage. Basis and final exact-output review remain separately declared;
  none grants physical authority or authenticated engineering acceptance.
- The original repaired mesh keeps its original X/Y/Z frame and remains the
  full-profile/final-package subject. The handle study consumes those repaired
  bytes, not construction output. Auxiliary pads-down/side STL candidates retain
  source hashes and proper rigid matrices. Candidate mesh integrity gates precede
  slicing; comparison recomputes transformations and checks source/candidate/
  package/path-view/profile correspondence, area/volume and transformed spans.
  Original model-axis envelope checks are never applied to rotated side axes or
  weakened. Both actual support views feed the final review; support contact and
  removability remain human inspection work, not inferred from path counts.
- This remains authored source on the existing configured MCP, validator,
  review and run-path mechanisms. There is no new runner or vendor adapter.

## Focused verification

Command (isolated already-prepared Python environment, no shared environment sync):

```text
/tmp/wright084-quality-venv/bin/python -m pytest tests/test_process_interface_examples.py tests/test_handle_orientation_study.py tests/test_wheel_orientation_study.py -q
139 passed in 3.40s
```

This includes the existing wheel and substantially different heat-spreader source
checks, both configured/AI geometry modes, frozen original input/profile checks,
all three local reviews, geometry-before-slicer ordering, separate run paths,
wrong scenario/material/profile/capability rejection, asymmetric mesh numerical
checks and tampered source/candidate/matrix/profile/package/preview rejection.
Numerical fixtures are explicitly synthetic; they do not establish a handle's
engineering validity. Ruff passed for the changed Python files and tests.
`git diff --check` passed. No full repository/installed/browser gate was run here.

The new configured-recipe regression caught an unassigned metadata input in the
first draft; the prepared configured tool receives only its mapped arguments and
file dependencies. Instruction metadata stays on the AI/review surfaces. The
final focused run above covers the correction.

## Explicit Orca follow-up (23 October 2026)

The opt-in `slice_binding.kind=orca-shell-3mf-v1` now authors the actual independent
`shell_execute` contract for Orca 2.4.2. It preserves the original repaired STL and
prepares Core3MF model coordinates plus declared pads-down/side build matrices.
Exactly two candidate slices are declared; selected outputs feed the original
final-package path. No native rotation flag or new executor is introduced.

The original process file is pinned and staged. The selected file must differ
only in automatic support-wall `"-1"`→`"0"`. Original and derived validator files,
reference digests, unchanged baseline, explicit mapping and selected orientation
are retained as connected initial/final review inputs. The original 18 checks
are retained, with the explicit slice-lineage provenance amendment; 25 additive
checks bring the derived profile to 43. Both real packages must preserve original
geometry through the prepared transform, identify the selected engine, contain
the original required inventory and report the required effective settings.
The original model-axis envelope checks remain unchanged. See the separate
[reader evidence](standard-3mf-reader.md) for its numerical bound and controls.

The authored inspector retains warning text as response evidence and independently
requires native `result.json.return_code == 0`, actual settings and package bytes.
It reuses the passive path reader with the exact `;VT0` / `; filament end gcode`
nominal section observed in the retained fixture. Unclassified features and the
unverified startup/shutdown scope remain visible. Counts/lengths do not establish
contact or removability; the exact views, inverse model matrices and effective
extruder offset join the final review.

Optional typed `workflow_id` replaces only the workflow identifier, preserving the
ordinary starter identity for the integrator's existing source CAS. The staged
`source-transformation.json` maps all seven starter roles to prepared task IDs and
explicitly grants no execution authority. Root's read-only run disclosure is
attached to initial review after all final blocks/settings are authored; its
per-call/agent-loop limits are checked against the compiled source. Unknown
estimates stay unknown; ordinary model timeouts are not presented as enforced
tool deadlines or total run/spend limits.

Follow-up focused verification:

```text
/tmp/wright084-quality-venv/bin/python -m pytest tests/test_process_interface_examples.py tests/test_orca_preparation.py tests/test_handle_orientation_study.py tests/test_wheel_orientation_study.py -q
159 passed in 4.00s
```

The new operation controls use exact retained tiny native package bytes alongside
clearly controlled receipt/settings fixtures. They establish passive reader and
authored-operation behaviour, not provider success on a handle. Both orientation
selections compile with exact dynamic run paths, original requirement/check
preservation, pre-slice review, explicit shell call limits, mismatch rejection
before staging and stable starter identity. The package fixture does not satisfy
the original handle inventory; that requirement is deliberately retained.

## Handoff gaps and limits

Configured Blender argument follow-up: construction and repair now author distinct
`*-blender-call.json` argument assets containing the unchanged pinned `code` and
the original `prompt.txt` decoded directly from its frozen UTF-8 bytes. This
preserves its CRLF sequences in `user_prompt`. The original code-only proposal
assets and hashes remain unchanged. Static complete-argument copies join the
initial review; only the actual submitted argument assets declare run-path
substitution. No executor or adapter merges arguments. The focused configured
operation regressions passed (13 passed, 115 deselected in 2.30s), including exact
prompt byte roundtrip before and after actual run-path input binding, both stages,
original code/proposal retention, and existing independent/wheel contracts.
This establishes authored argument correctness, not an observed provider call.

1. Default authoring still expects existing `slice_model_file` arguments and the
   qualified `ok:true` plus exact source/output/plate response. Original profile02
   still names `actual_local_bambu_slice`. The newly probed Orca `shell_execute`
   contract supplies neither; do not call it through this binding or relabel its
   results. The explicit opt-in above is a distinct accepted-source/profile
   revision; exact real provider binding remains integrator work.
2. The new opt-in can declare either final orientation through standard 3MF;
   actual handle roundtrip, full-profile findings, final review and a visible
   correction with exact downstream invalidation/reuse still need proof. Native
   Orca rotation remains unqualified and unused. T011 stays pending.
3. Actual geometry/repair recipes, complete provider profiles, mounted-file
   handoffs, real package parsing, accepted-source promotion, process UI binding,
   ordinary workspace/native Hermes journey and human review still need proof.
   Missing capabilities stay visible. No real printer operation is authorized.
