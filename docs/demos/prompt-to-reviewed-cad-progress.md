# Prompt-to-reviewed-CAD goal progression

Goal adopted 11 October 2026. This replaces the three-demo portfolio; protected
thermal/mount/PCB subjects remain separate. Local digital work continues on
`codex/stevecad-engineering-demos` in the isolated worktree and Wright instance
at `http://wright.localhost:8891/`. No release or marketing publication is implied.

## Check-in direction — 12 October 2026

The user requested completing and checking in the code, ending the current
return to simpler example runs. No new joint or robot run is being started for
this checkpoint. The delivered code, source definitions, MCP guides and measured
evidence are being reviewed and committed separately from completion of the
remaining engineering campaign. The full engineering goal is not claimed complete.

The bracket run completed in 1204.087 seconds on unchanged v19. Its original
CAD review has 11 PASS and R06 UNVERIFIED. A real AgentCAD MCP measurement of
the same STEP now confirms both opposing-plane wall separations as 6.00 mm.
The independent visual review caught a 180-degree roll in the original top
render; the corrected native top image is retained as an addendum. The original
outputs and review remain unchanged. Native Blender observation confirms no
active render and screen-right +X / screen-up +Y for the corrected image.

The prospective v20 source corrects that camera convention and records screen
axes. Compilation and source diff confirm that only the three render tasks
change; geometry, instructions, inspection and tool bindings are unchanged.
It has not been accepted or run as a full process. The robot's additive exact
STEP fastener audit maps 110 instances, verifies all 25 M3 and four M5 stacks,
and records 66 planar bearing pairs with no positive overlap. All 29 stacks
have bearing contacts at both ends in the home pose. Threads, torque, physical
engagement and the missing native hardware-contact declarations remain separate.

See [check-in scope](stevecad-check-in.md) for code validation and retained
limitations. MCP usage-guide practice now applies to every installed or used
server, with a shared template and explicit verification status.

## Prior evidence — 12 October, 19:43 UTC

The native-render workflow has completed its original four-hole assignment with
all ten final review requirements passing. `block-native-006`, run
`15a0b7ad27374a0e9375923cc4dc2725`, took 617.248 seconds. The original specification,
preconstruction test plan, eight geometry checks, independent numeric audit,
STEP/GLB transfer receipts, six images and final review are retained together.
The exact original outputs are unchanged. Separate visual inspection confirms
the three image pairs and neutral-gray rendering scope; the saved report loads
all six images without browser errors or horizontal overflow. This proves the
digital block process, not physical or user acceptance.

| Requirement | Current authoritative evidence / remaining work |
|---|---|
| One reusable seven-stage process | Accepted v19, 16 execution tasks; source digest `77c35b95c93eb6d0dc220d26391f809d67ef8c4bb20ad35004c0f35e574fd35e` |
| Specification and test plan before construction | Original files and ordered events in `block-native-006/run.redacted.json.gz` |
| Actual geometry verification | `block-native-006/independent-geometry-audit.json` and original provider receipts; one solid, all four bores, extents and analytical volume pass |
| Three corresponding CAD/native-render views | `block-native-006/native-run-audit.json` and `visual-review-audit.json`; exact revision/build, unique mesh match, six actual images |
| Illustrated review | `block-native-006/outputs/design_review.html`: 10 PASS, zero FAIL/UNVERIFIED; browser/visual checks retained |
| Changed-prompt reuse of final native source | `six-hole-native-001`, run `bddd667df90544018d1b2d1d004abf1a`, completed in 542.533 s. Exact source/routing equality and producer order pass `qualification/generic-render-binding-001/v19-reuse-audit.json`. Final supplied geometry, native handoff and all three image pairs pass; original review retains R02 UNVERIFIED for an added intermediate-stock-state test |
| Bracket and joint | Fresh `bracket-native-001`, run `90087fceacdc494d91eaff6f65d9173d`, started 19:33:51 UTC on unchanged v19. Its input makes final-geometry scope explicit and requests native blue-gray appearance metadata. Earlier measured examples remain; bracket outcome and joint native progression pending |
| Robot package | Owned document `167ef21f-6679-4e4d-8917-14dc067893d6` revision 7, 110 solids; 18 unique printable meshes / 28 quantities. Original `robot-arm-010` review retains 10 PASS / 4 UNVERIFIED / 2 FAIL. Passive exact-STEP audit now verifies all 14,364 printed-pair checks at five poses and 33 samples: minimum non-seat gap 0.400 mm, maximum overlap zero. Additive evidence does not rewrite the original review or prove continuous/physical motion |
| Final renderings and media | Three selected 512-sample native robot renderings, 20-image social package, two H.264 MP4s and printable kit retained under `robot-arm-media/corrected-rev7/`; unpublished. Final native-process assembly proof remains pending |
| MCP guidance and bugs | Guides for SteveCAD, KiCad, AgentCAD, Blender and shell transfer; confirmed visibility defect has a redacted minimal packet but no supported submission/report ID yet |
| Workspace UI | Prior actual workspace evidence retained; latest v15 authoring walkthrough stopped on clipped diagram. Saved HTML checks do not close that UI finding |
| Disk space | Disposable-cache cleanup retained separately; latest check C: 17.8 GiB, D: 96.4 GiB free. Source, CAD, evidence and media preserved |

The preceding cleanup response rechecked disk state; it made no new CAD change.
This continuation inspected the existing run, observed terminal completion through
Wright's normal API, retained and audited its results, and started the authorized
same-source reuse proof. No duplicate or protected run was started.

The robot clearance audit is now terminal and retained at
`qualification/robot-sampled-clearance-001/`: 583.623 seconds in a disposable,
offline selected CAD environment with read-only inputs. Its raw report has
13,414 non-seat and 950 declared-seat pair observations, minimum non-seat
distance 0.40000000000000036 mm, and maximum overlap 0.0 mm³. The original STEP
and executed source hashes were rechecked. The illustrated report, PNG,
browser check and exact audit source are retained. This supplements original
R08 with measured sampled-clearance evidence; remaining fastener-stack and
main-process assembly proof work is unchanged.

## Historical evidence checkpoint — earlier 12 October

| Requirement | Evidence / disposition |
|---|---|
| One prompt and reusable seven-stage process | v7 saved source; original default regenerates digest `d4dfe869ecdc366b158a762da7904b96a8cdb91e5ab0d70ad7ac6acb7eb06a89`; eight tasks because three implement rendering |
| Preconstruction design document and test plan | Separate indexed Markdown outputs; durable events place both before creation in completed block runs |
| Editable SteveCAD geometry and actual tests | Exact document/revision/build receipts, raw tool observations and independent audits for `block-008` and `six-hole-005` |
| Three CAD orientations and three renderings | Six actual image files per completed block run; captured-byte hashes and downstream image input/output records |
| Illustrated reviews | Original HTML reports retained; four-hole browser check loads six images without overflow; six-hole loads images but has desktop overflow |
| Reuse with changed prompt | Both v7 start receipts identify the same process; distinct input digests and run IDs |
| Bracket | `bracket-004` completed in 439.38 s on v8; exact document `a83df269-84ff-4083-9a2e-ee094ab8760d` revision 2, build `15d4ed7f-701d-4049-98d3-67e6d43099d2`; numerical envelope, bores and volume pass; upright thickness remains UNVERIFIED; all six images load without overflow |
| Mating joint assembly | `joint-003` completed 498.11 s on v9, exact revision 3/build `39af23dd-b6df-4d59-81d0-c84fcb8a4035`; three solids, real joint and 25-sample motion verified; original review preserves axis-convention FAIL and unverified FDM screening; six images and browser check pass |
| Printable robot arm | Same owned document `167ef21f-6679-4e4d-8917-14dc067893d6`, now revision 3/full build `ad1c0f2c-490f-4767-834b-20349fefeeec`, 51 solids, valid materials and no component feature errors. Native absolute fit and 33-sample motion still FAIL. `robot-arm-005` stopped honestly on those defects after the large-observation transport corrections passed live; the next changed input preserves accepted v11. Printable kit/review/media acceptance remains pending |
| Actual CAD/motion video and unpublished marketing | Delivered a neutral CAD-viewer clip using native STL meshes and returned joint keyframes; mesh audit passes; Studio capture and final arm marketing package pending |
| Future-agent MCP knowledge | SteveCAD and KiCad guides plus shared usage-guide standard saved; qualification/setup owners retained |
| Bug reporting | Repeated-instance visibility/identity defect confirmed with a minimal two-box example and live contract/control evidence. Redacted report packet prepared; signed-in supported submission and report ID still pending. Robot geometry failures remain separate |
| Shared image handoff generality | 171 distinct affected tests passed; different-provider automated case exists; substantially different live workflow still pending before broad integration |

## Findings and next actions

The completed block geometry matches its supplied dimensions and hole patterns.
The model-written reviews also introduced or retained nongeometric provenance
findings. Preserve original plans and findings. Supply existing receipts where
they resolve source/run provenance; image derivation establishes lineage, not
exact mathematical equivalence of generated pixels and CAD geometry. Do not
weaken existing tests after the fact. New prompts distinguish API implementation
choices from engineering acceptance requirements.

The bracket and joint now have completed evidence exports and passive independent
audits. Full tool-completion payloads are retained separately because diagnostic
envelopes may be truncated. The exporter remains an evidence reader, not another
executor. Preserve the original generated review verdicts alongside its narrower
arithmetic/identity checks.

Assembly progression may require a visible revision to the same process because
v7's inspection task exposes only `read_design` and `inspect_model`, with eight
calls. Discover actual assembly/motion/export schemas first, qualify the smallest
joint, then add only the necessary capabilities and output bindings. Preserve
accepted v7 and its frozen model routing. Current Wright runs use their recorded
`gpt-5.6-sol` settings; the Codex chat's model selection is a separate boundary.

### Verified limitation and v8 correction

`bracket-001` failed on a transient read-only provider lookup before creation;
that same lookup succeeded in a retained independent gateway check.
`bracket-002` created one document and a queued build; Wright incorrectly rejected
SteveCAD's documented same-revision status observation. An independent observation
confirmed the same build completed, with the correct envelope and volume. Its
component nevertheless had a redundant combine feature error. `bracket-003`
attempted an empty edit, which SteveCAD rejected; no revision was saved.

One exact operator correction removed that redundant combine in the same
document, creating revision 2. `bracket-004` consumes the corrected existing
document through the accepted v8 workflow, without creation or further edits.
Preserve the separate operator receipt and original failed run: this is assisted
recovery, not proof that the earlier autonomous correction worked.

v8 digest `bb147fa8b39ca003a69b76d772b0156fcd991eda08b160b4318b53b9468ab084`
adds a typed bounded pending-operation observation contract, recovery instructions,
component-error checks, narrowly targeted reference discovery, assembly inspection
capabilities and report wrapping. The v7 source is retained under `versions/` and
in each original run. The new runtime uses existing execution/gateway/evidence
owners; focused suites passed 85 and 82 tests (overlapping counts). No provider
bug was filed. `joint-002` now supplies live queued-to-terminal runtime proof:
one exact build receipt passed through queued/running/running/succeeded with
three polls. That run later failed during a separate combined inspection.

The next input, `prompts/04-pivot-joint.txt`, started after the bracket's seven
stages and browser check completed. Its retained limitations explicitly include
pin retention and absence of physical operating tests. Process completion does
not remove the bracket's unverified upright-thickness finding.

### Robot hardware supplied by the user

The user confirmed a Raspberry Pi Compute Module 5 and the official CM5 IO
Board on 11 October. The module variant, board revision, cooler, servo models
and Arduino model remain unspecified. Preserve this as supplied design input;
do not silently replace it with a Raspberry Pi 4 or assume an Arduino model.
The candidate MG996R/MG90S profiles are explicitly provisional references.

The official CM5 STEP and revision-2 IO Board KiCad archives were downloaded
and checksum/CRC checked under `artifacts/stevecad-demonstrations/robot-hardware/`.
They are references, not proof of a qualified SteveCAD import. SteveCAD's actual
catalog query returned one simplified MG90S envelope and no MG996R match. Exact
import/upload references and query receipts are retained. The hardware basis is
`examples/stevecad-demonstrations/prompt-to-reviewed-cad/robot-hardware-basis.json`.
Final digital validation must state which dimensions came from native models,
manufacturer drawings, catalog envelopes or declared assumptions. Purchased
electronics and servos stay separate from printable-part exports.

Record new measurements, elapsed times, known blockers and exact revision
identities here. The goal remains incomplete until the entire requested robot-arm
and media package passes a requirement-by-requirement completion audit. Physical
printing, assembly and operation remain explicitly untested unless performed.

### Robot revision 3 and next local correction

`robot-arm-003` saved revision 2, full build
`3b8bac04-ef45-4606-ba87-f5bd55bfb817`, 48 instances, no feature errors, and
actual failed fit/33-sample motion. It then exceeded the default total model
context budget. `robot-arm-004` stopped before edits on a separate oversized
tool-envelope guard. v11 preserves v10 instructions and exposes an explicit
400000-byte MCP context setting for creation/inspection; recorded defaults and
model routing remain unchanged. See [transport qualification](assembly-observation-transport.md).

`robot-arm-005`, run `7b28e20235014ab1b9a9372345d1cb18`, completed both
preconstruction documents, read the exact existing source, saved one correction
and generated revision 3 in 510.25 seconds before returning a measured FAIL.
The native report no longer lists the earlier electronics-bay/adjacent-beam
collisions, but still records ten absolute rest-state pairs and three moving
pairs. The largest rest overlap is tray/yaw cradle (4673.970 mm³); moving
forearm/elbow-yoke and palm/wrist-yoke reach 200.997/201.179 mm³. No broad clear
verdict follows from fewer pairs. Valid `fdm-petg` colors/materials now have
native evidence. Earlier `petg` diagnostics and all source revisions remain.

The next input `05-tabletop-robot-arm-local-corrections.txt` retains the supplied
assignment and specifies local bridge, open-cradle, horn, guide and mounting
corrections from those witnesses. Shoulder seating stays intact; elbow/wrist
bridges move to their parent side. Stationary yaw housing moves below the
shoulder inside the same footprint. Required frame, link lengths, retained
pivots, joint ranges, pose values and sampled path stay explicit. This remains
a changed design prompt on v11, not a new robot-only workflow or executor.

Revision-2 native mesh diagnostics now have properly framed whole-assembly
captures with their actual FAIL label. They are a neutral geometry viewer,
not Studio screenshots. The one revision-3 native mesh download timed out;
its error is retained without repeated submission. Final native captures,
verified printable exports, renderings and illustrated review remain pending.

`robot-arm-006`, run `2a3acec7322c476492b59e532b1c461d`, reused that exact v11
source with the local-corrections prompt. Its new design document and test plan
completed before the creation task read revision 3. It stopped after 250.35 s
on malformed model-decision output, with no CAD write dispatched. The recorded
repair input exposes the actual 94-byte upstream message: “API call failed after
3 retries: Our servers are currently overloaded. Please try again later.” The
same message hash appears in the primary and repair responses; this is not a
SteveCAD bug or a changed CAD revision. A later tool-free normal-adapter
availability probe returned an invalid unattended outcome; availability was not
established. No automatic restart or model-route substitution occurred.

Three focused revision-3 native images now succeed; the whole-assembly capture
still timed out. Approximately twenty additional images have been shown in chat,
including diagnostic views, with application/revision/failed-fit scope disclosed.
The v11 served-workspace walkthrough passed through Workflows, diagram and common
view, then closed its test tab through Wright. Its redacted trace and validated
report are under `artifacts/ui-walkthrough/prompt-to-reviewed-cad/2026-10-12T0004Z-v11/`.
Focused lint passed. The last full artifact scan passed 1137 files and 99 exact
output-manifest hashes before the latest focused images/probe receipts.

Automatic approval review rejected a proposed direct raw-response probe because
it bypassed the normal workflow adapter and could send recorded messages to an
external model route. That command did not run and was not retried indirectly.
Existing adapter evidence and unaffected CAD/documentation work were preserved.

The native capture audit then found gripper selectors returning wrist instance
labels. A small owned reproduction confirmed the provider defect independently:
`show=["second_marker"]` gives the second box's X100..110 bounds but labels
`first_marker`; the first-instance control includes both X0..110 bounds. Exact
source, a successful two-solid build, current live tool contract, original text
and structured responses and native images exclude a Wright rename or invalid
model as the cause. The report packet is
`qualification/stevecad-visibility-repro/visibility-reproduction.zip`, prepared
not submitted. No report ID or signed-in Studio browser-control runtime exists
in this session. This does not invalidate or excuse real arm fit failures.

The later small availability probe through the **normal** Wright adapter passed
with the original frozen model route. `robot-arm-007`, run
`3ea757233ab84ce19d8f879c61b1a52f`, therefore started fresh on accepted v11 at
00:29:06 UTC, 12 October (11 October local). Its actual input bindings are
byte-equivalent to 006's prompt, SHA-256
`cda22af4f50dea27589c5830536fc280d80b637bcf35f53b8cde9e4a278fb2a2`.
The prior failed run dispatched no CAD write. Snapshot digests differ because
their identities differ; this does not imply changed prompt values. The fresh
run is live and has completed its new design document; no new CAD revision is
claimed yet. `robot-arm-007/recovery-basis.json` retains the recovery evidence.

This goal turn made progress: actual revision-3 build/failed-fit evidence was
preserved, a full prospective local correction was specified, fresh unchanged-
workflow recovery started after verified model availability, twenty delivered
images were indexed, v11's served working view passed, and a native provider
defect received a tested minimal report packet. The full robot/print/review/media
objective remains active and incomplete. Latest credential/output scan passed
1176 files and 101 exact output-manifest hashes before this recovery note.

## 12 October UTC / 11 October local: complete review and measured topology correction

The previous goal turn delivered and reprobed the X-compatible MP4 successfully;
it was progress on the requested media deliverable. The goal remains active.

`robot-arm-007` ended failed after 1110.57 seconds because its final review
exceeded the 180-second model limit. All seven preceding execution tasks and ten
output files remain. Actual revision 4/build `cff14d5c-e6bb-49bd-b8b2-eafa5c6f24c6`
has 55 solids, no feature/material errors, and 33 clear moving samples. Absolute
fit still fails at two interfaces, and six guide/cradle M3 stacks are missing.
The complete native STEP was downloaded and independently imported: valid,
55 solids, volume 751772.0317768176 mm³. No print release follows.

Prospective v12 revises only saved instructions: design/test-plan word allowances
2600/2200, explicit subset/line scoping, geometry-preserving render wording and a
1500-word review bound. Existing eight execution tasks, output contracts,
runtime, gateway, profile, 400000-byte context budget and model route are reused.
Its accepted digest is
`d355a1419944e2914ae5a1a302808b84e78d9cb35b5d955ecbb0204f0ec9bc77`.
No editor/common-view/client contract changes are made; existing views remain
usable. A v12 served-view proof is still pending. V1–V7 ownership, exact evidence
identities, invalidation and missing-capability behaviour remain as documented.

`robot-arm-008`, run `a8b67c9266d847529be7a7dec69d1911`, completed the process
after 1169.85 seconds at 01:51:25 UTC. Final review took 66.37 seconds, removing
the previous review-timeout failure. Completion of execution does not mean
engineering PASS: the review and actual native tests FAIL. Revision 5/build
`90328fa5-48fd-43b3-991b-de36b5c84f4c` has 110 instances, 119 solids, 28 printed
instances/18 unique definitions, five retainers and 25 M3 stacks. All five static
fits fail; all 33 sampled moving checks remain clear. Source snapshots, complete
outputs, raw/redacted receipts, timings and passive audit are preserved.

An independently imported STEP identifies five disconnected cradles: yaw two
solids, shoulder and elbow three each, wrist three, gripper three. Their bosses
touch tangentially. Actual files also show four missing palm holes, posts at Y18
instead of Y23, a missing shoulder fastening bore, and ten cap bolt heads at the
wrong end. Exact measured overlaps are 50.354, 42.412, 31.809, 7.516 and 4.864 mm³.
The gripper stand now seats without penetration at cover Z17 but its intended
contact was omitted. The new input preserves clearance standards and enumerates
only real zero-penetration seats; it does not permit nonzero overlap.

The revision-5 STEP exported once through the gateway in approximately three
seconds. A restricted local client had stalled before its pre-dispatch output
directory/marker; its exact owned parent/child identity was verified and only
that client stopped before the permitted export. Wright and its runs were not
restarted. The successful export is bound to the same revision/build. It is a
diagnostic failed-fit artifact, not a final print package. Standard STEP reading
and tessellation use cached selected AgentCAD environment libraries, no network,
with no MCP call or new host software in the Wright base image. All 110 placed
meshes match unique native bounds/volume; all closed-edge/hash checks pass, but
printed connected topology fails. Colored geometry captures now preserve actual
orange/charcoal bodies. Twenty-eight additional images have been shown in chat.

`robot-arm-009`, run `cd808aafd9514ec1b6a8d634e72491ee`, started at 02:11:46 UTC
on the SAME accepted v12 with changed input
`05-tabletop-robot-arm-measured-fit-correction.txt`. Its design document and
preconstruction test plan completed; the generation invocation started at
02:16:41 UTC and remains live at this checkpoint. Do not restart because an
observation times out. This correction adds real boss webs, missing bores and
correct transforms, retains all old evidence, and tests axes as oriented lines
rather than inventing a fixed representative point. No revised geometry success,
print release, physical verification or human acceptance is claimed yet.

Remaining work includes actual corrected fits/connected topology, verified
print-oriented exports, final faithful renderings, arm motion media, full review
package, supported bug submission, v12 served-view evidence and independent
shared-mechanism proof with a substantially different existing workflow. The
completed historical digital examples and protected campaign are unchanged.

### Revision 6: actual fit and connected-solid milestone

The live 009 run above subsequently ended failed after 425.72 seconds at
02:18:51 UTC, after saving successful revision 6/build
`82a810f5-a5f5-481f-84d3-fd997dfaa4bd`. All five whole-assembly absolute fits
now CLEAR with zero issues. The native 8-second/33-sample check also clears.
The five disconnected cradle definitions are fixed: the exported STEP has 110
valid solids/110 placed children, with all 28 printed instances connected.
STEP SHA-256 is
`5dd481d4250251743b5ccec1c63adf1e9625fb4d4f4469393ef156cfde587df3`.
All 110 independently tessellated meshes map by unique bounds/volume, pass exact
hash/closed-edge checks, and differ in volume by at most 0.041541% from B-rep.
This proves the stated digital fit/topology/export scope, not walls, slicing,
strength, physical fit, torque or human acceptance.

009's failure is a measured post-build context limit, not failed CAD: the latest
read-design and generate-model observations alone contain 357214 and 300922
UTF-8 content bytes before the bridge's lossless encoding/projection. The intended
messages serialize to 926195 bytes. No next model request was sent. Actual offline
bridge rendering of the same evidence uses seven parts, maximum 65536 characters,
411321 transport bytes. The existing 400000 allowance is insufficient. This
does not authorize truncating evidence or changing backend guards.

Prospective v13 changes ONLY the two existing typed MCP context budgets to
1048576 bytes. All instructions, model/profile selection, tasks/ports, runtime,
gateway and semantic policies otherwise match v12 exactly. Old v12 bytes are
preserved under `versions/prompt-to-reviewed-cad-v12.workflow.wflow`; preparation,
authoring-shape/compilation and focused lint pass. The offline exact-context
check passes, with no HTTP request or tool call. Its receipt is
`qualification/assembly-observation-transport/revision6-context-v13.json`.
This bounded configuration change affects a new accepted source only; it does
not resume 009 or change its frozen budget/instructions.

`robot-arm-010`, run `3ab6b30fac054902aaccdcfce3789cb2`, started at 02:32:43 UTC
on accepted v13 digest
`1fb0c11ca47e88416ecc97245ff9d610836dfdc60d9eeaa45f1612fbfb7e6795`.
Its changed prompt preserves revision-6 geometry and asks for one metadata/notes
batch giving native local print orientations and complete subsequent validation,
three captures/renders and review. No geometry change is permitted merely to
produce another revision. It completed the new document and preconstruction
plan, then started generation at 02:38:38 UTC. It remains live at this checkpoint.

An actual revision-6 arm motion MP4 is now delivered: 1280×720, H264 High/yuv420p,
24 fps, 192 deterministic frames, AAC-LC silent stereo, exactly 8 seconds,
515865 bytes, fast-start. The independent full decode succeeds; eight one-second
CAD-region samples differ after excluding headers/footers. The viewer uses the
actual STEP triangles, recorded native joint tree/origins/oriented axes,
coupling ratios and linear keyframes. Four pose captures and hashed provenance
are retained under `robot-arm-media/corrected-rev6/motion/`. It is neutral
geometry playback, not Studio recording, physics or physical operation. It
remains unpublished. The final exact-revision print/review/render package,
supported bug report and full completion audit still remain.

### v13 completes the process; remaining acceptance gaps stay explicit

010 completed at 02:51:20 UTC after1117.18 seconds (18.62 minutes). All eight
execution tasks completed: design115.45 s, plan74.99 s, creation326.13 s,
validation413.55 s, renders38.55/37.54/35.55 s, review68.78 s. Revision7/build
`780f3196-07b2-4590-b102-1cdd9a73b6cf` has110 solids/instances and all five
native fits clear. Larger-context continuation has actual normal-runtime proof.
All18 unique printed definitions now have their declared local directions.
All component source files, native body metadata, world extents, joint tree and
poses match6 exactly; only print metadata/notes changed. The saved7 source and
comparison receipt are retained. Its independent25mm reserve-bounds audit also
passes for five states and33 samples.

The normal Workflows → saved v13 → common view → tab close walkthrough passes;
its report validator and redacted trace pass under
`artifacts/ui-walkthrough/prompt-to-reviewed-cad/2026-10-12T0238Z-v13/`.
The six-image review loads without browser errors or horizontal overflow.
Actual engineering review remains FAIL/UNVERIFIED:

- Generated R09 demands five unique cradle definitions, while five instances
  reuse four definitions. The model was not duplicated to satisfy that extra
  count. Original plan/FAIL remain; exact subjects are recorded separately.
- R10 lacks explicit hardware bearing-pair declarations and a measured stack
  register. Native fit PASS does not erase this documentation gap.
- The old passive six-Palm-bolt predicate counted all eight group bolts,
  including two gripper-retainer bolts. All six specifically required guide/
  stand bolts exist and are rigid to Palm. The old failed predicate remains;
  `robot-arm-010/requirement-scope-addendum.json` records the exact subjects.
- Whole-design FDM used+Z despite show filtering; this does not accept all
  declared print directions. Warnings, support/bridge and physical checks remain.
- Three new presentation derivatives remain diagnostic: top colors the tray
  green and changes the module; isometric changes the thin PCB/base; front changes
  module/gripper details. These are not final faithful marketing assets.
- One exact-revision7 STEP request timed out, with no file transferred and no
  repeated submission. Verified6 exports/video are not relabeled as7.

Thirty-three additional images have been shown, plus the arm MP4. Latest scan
passes1643 files and135 exact output hashes before this note. The goal remains
active: final oriented exports, accurate renderings/marketing package, review
gaps, supported bug submission and complete audit remain. No CAD run is live now.

### Exact-revision export, final native renderings and curated package — 12 October

The preceding video-export turn made progress: both delivered MP4s were probed
and fully decoded successfully. The revision-7 MP4 is 515047 bytes, 1280×720 at
24 fps, 8 seconds, H.264 High/yuv420p with AAC-LC audio. Its SHA-256 is
`41214826e2b81784742e51cf96987b91167c4c518c546b82d9169ae3d48ba11e`.

The earlier STEP observation timeout was reconciled by a read of the exact
revision/build, which reported the cached STEP artifact. One retrieval then
succeeded without rebuilding or creating a revision. The independently read
1449929-byte STEP has 110 valid placed solids. World meshes preserve exact
native instance identities by unique bounds and volume, with maximum relative
tessellation volume error 0.00041540825. The 18 unique printed definitions are
connected solids. Their inverse assembly placements, native local print
directions and bed-zero transformations produce 28 nominal printed pieces.
All oriented STL integrity and transform checks pass, including closure,
connectivity, positive winding, ≤0.1% volume error and 220×220×250 mm bounds.
This does not qualify supports, slicing, real hardware fit or operation.

The existing independent Blender MCP1.9.1 / Blender4.3.2 was registered only in
the isolated workspace and imported the 110 actual STEP-derived meshes. Three
final native Cycles CPU renderings use 512 samples and projected-CAD-bound
orthographic framing. Safe mode stayed enabled. Black screenshot fallback
(missing host NumPy), absent OpenImageDenoise, overexposure and one clipped view
were identified as selected-host/authoring issues and preserved. Native jobs
were observed before subsequent renders; a gateway observation timeout did not
trigger a replay. These are supplemental exact-geometry images. The saved v13
rendering stages still use AI image editing, so reusable Blender binding remains
unfinished; the original fidelity failures are not erased.

At 05:22 UTC, a new additive illustrated review and unpublished marketing bundle
are assembled under `robot-arm-media/corrected-rev7/`. The review retains the
original design document, preconstruction plan, validation and failed review;
it links exact STEP, oriented STLs, modeled/printed BOMs, assembly instructions,
six capture/render images and the revision-7 MP4. Desktop1440px and mobile390px
browser checks pass: all six images and links load, no horizontal overflow or
page errors, and the MP4 reports1280×720/8s. The marketing captions explicitly
retain simplified/provisional hardware, digital-motion scope and unverified
physical operation. Nothing was uploaded or published.

Current remaining work: saved-process rendering handoff, prospectively corrected
requirement subjects and real contact/clearance evidence, declared-orientation
manufacturing screening, confirmed visibility-bug submission through the
supported channel, substantially different live proof before any shared-code
promotion, and full goal audit. Keep the goal active and original FAILs intact.

The native PNG handoff is now separately proved in the normal durable runtime:
run`498f6f64564445a4a8787cdab529a6d1` completed in6.302seconds at05:34:25UTC.
It imported110 checked immutable revision7 meshes in fresh helper003, then
produced and bound a new640×480/16-sample PNG using existing direct MCP-tool
`expected_files`/`expected_file_ports`. Independent decode, nonblack-image,
native FINISHED/110-mesh identity and runtime output-hash checks pass.
Evidence lives under`qualification/blender-file-handoff-001/`. Initial bare-tool
and unpinned-schema declarations were stopped by readiness before execution;
the corrected gateway name/schema source and all rejected receipts are retained.
No runtime implementation or model settings changed. This establishes the
renderer-output mechanism, not the main process's upstream export/tessellation.

Inspection of the existing cached AgentCAD MCP source shows its standard-format
`export(step_file,formats,cwd,build_dir)` tool can produce STL/GLB/OBJ and returns
per-mesh validation separately from source CAD validation. This is a potential
independent owner for the next handoff, not a live-qualified AgentCAD MCP call.
The already used offline build123d library checks remain distinct. No alternate
CAD-authoring campaign or protected process was started.

### Automatic standard-geometry handoff qualified — 12 October06:10UTC

The preceding goal turn made concrete progress: curated revision7 design/review
and unpublished marketing packages, plus the normal durable native-file proof.
This continuation qualifies the next substantive actual provider handoff.

The existing independent AgentCAD MCP0.6.0 selected source measures the exact
SteveCAD STEP through Wright:110 solids,831 faces,783118.7196mm³ and native CAD
validity pass. The source URL was initially wrong operator metadata; installed
Project-URL and the primary repository corrected it, and only that owned first
registration was disabled/uninstalled before any export. Its read evidence remains.
The correct-source native GLB export run`bbbe2ed4c4bb4ec98d819df649d305ab`
completed in4.717seconds. Its1273896-byte GLB has110 closed components, with
separate source-CAD/written-mesh validation. Independent standard glTF world
transform checks match every source STEP instance unambiguously. See the new
AgentCAD usage guide and`qualification/agentcad-format-export-001/`.

Native Blender4.3.2 uses Python3.13.15 in this selected host, while its MCP
entrypoint uses3.12. A checksum-pinned NumPy2.3.4/cp313 Linux wheel was added
only to a new selected provider image/private bootstrap path, not Wright's base
image/runtime extra. Fresh helper004's actual startup confirms it. No provider
protocol or safe-mode source was changed.

A single accepted-source chain now exports actual STEP through AgentCAD, pins
the fresh connected GLB file into Blender's native importer, restores supplied
presentation colors by actual geometry identity and writes a native PNG. The
first run failed our comparison of rotated local bounding-box corners, which
are conservative rather than exact world extents. That was an authoring error,
not a provider defect. A visible source revision measures actual world-space
vertices instead and creates a fresh owned native scene/fresh outputs. The
failed run and partial import evidence remain.

Corrected run`7f626fb8ae424bfd9ec9d7910ad27be4` on digest
`5c42c7ca3dc319a95c1f0b6a3807d7b223e0713c04d4da29ada24389a4b19055`
completed in18.269seconds. Exact runtime GLB/PNG hashes, native FINISHED,
110 closed mesh components,110 unique source-geometry matches and PNG decode
pass. Maximum actual-vertex extent error is0.049864mm; this is tessellated
presentation scope. The1000×720/32-sample image was shown as a quick preview;
selected final512-sample files remain unchanged. No model calls or runtime
implementation changes were needed for the chain. Evidence is under
`qualification/native-mesh-render-chain-{001,002}/`.

The diagnostic STEP-mesh helper also had a stale loop variable in its
`native_extent_mm` output field. Mapping candidates, actual `extent_mm`, volumes
and mesh bytes were correct. The future helper is fixed; all110 revision7
entries were rechecked against exact native instance bounds/volumes and hashes.
The original manifests remain with a109-field additive correction at
`robot-arm-media/corrected-rev7/mesh-extent-field-addendum.json`. Do not treat
that old metadata field as an independent measurement or blame a provider.

Main v13 is still unchanged and its original presentation/review failures remain.
The new chain's initial STEP was supplied qualified input. Automatic SteveCAD
transfer and generic per-design renderer arguments still need binding into one
new main-process revision. The shared redactor now recognizes upload/download
one-use HTTP ticket headers in maps, returned commands and nested JSON text,
while retaining public report-ticket IDs. Nine source-bound focused checks and
Ruff pass. A broader gate is running with a fresh workspace temp folder after
the default Windows temp fixture errored; its one affected diagnostic check
passes with that folder. Only the identified controlled failing test process
was stopped. The serving runtime has not been upgraded for the redactor yet;
no live main-process download ticket is requested before transport/output
persistence boundaries are proved. See`automatic-cad-render-handoff.md`.

The supported visibility-bug submission, real hardware contacts/clearance and
declared-orientation screening, main-process changed-prompt proof and full goal
audit remain. No marketing publication, physical operation or user acceptance.

### 12 October 2026, 12:49 UTC — requested media delivery

The robot's curated social-media set now includes 20 source-attributed images,
a fresh 12-second 360-degree camera orbit MP4 and the eight-second joint-motion
MP4. Six images come from SteveCAD MCP; three are the selected native Blender
finals; four show saved poses; two are actual Wright UI; five are labeled
evidence graphics, including the original FAIL/UNVERIFIED results. The portable
gallery, contact sheet, captions and verified 50-member ZIP are under
`robot-arm-media/corrected-rev7/social-media-001/`; see the media progress record
for exact paths, scopes, hashes and the preserved larger-viewport UI failure.
Desktop/mobile media checks and both complete video decodes pass. No publication
or acceptance has occurred. This fulfills the requested media collection, not
the remaining main-process integration or engineering work.

Correction to the preceding gate observation: the broader redaction-test handle
was subsequently unavailable and no matching controlled process remained. Its
final outcome was not captured; do not count it as passing or still running.
The nine focused source-bound checks retain their earlier PASS evidence. Runtime
persistence privacy and the other goal items remain open.

### 12 October 2026, 17:05 UTC — automatic transfer qualification

The earlier Windows async test stalls were traced to the sandbox blocking
Python's local socket pair. With that access, 24 focused and 164 affected checks
pass; Ruff and formatting pass. Only the identified stalled test processes were
stopped. No provider operation was stopped. The owned isolated API was reloaded
from tested source after all 36 recorded runs were terminal; protected campaign
subjects remain untouched.

The source changes redact credential-bearing run writes, observer events and
API results while preserving current execution values and public provenance.
Credential-bearing interaction checkpoints fail before storage. Saved artifact
contents remain explicit workflow responsibility. An unmodified independent
generic shell MCP is now available through the ordinary gateway in a minimal,
restricted selected Linux container; no Wright base dependencies were added.
Its usage guide records exact versions, isolation, result checks and limitations.

Live canary `ce271458f5774ba0b80cac7cd9823e64` passed in 3.440 seconds. The next
native tool received the synthetic value unchanged; run evidence was redacted
and 265 files/logs/database scans found no raw value. The first canary remains
as failed qualification evidence: it consumed the wrong envelope, and the shell
provider returned command stderr without MCP error. Runtime completion alone
was not counted as success. Corrected source and output checks are retained.

Run `bc1a2538fa2944f8b72a62ed3cdf6b9b` now owns the cached robot revision 7
export, scoped automatic file transfer, AgentCAD mesh conversion and three
native Blender views. At this entry it is still executing. Inspect its exact
record before claiming success. The robot placement/color reference is supplied;
generic changed-prompt integration into main v14 remains outstanding. No real
hardware validation, bug submission, publication or user acceptance is claimed.

### 12 October 2026 — automatic three-view handoff passed

Run `646d7a74c124431e8979c3acea4b01de` completed the actual SteveCAD export,
scoped credential-private download, AgentCAD mesh and three native Blender
images in 62.007 seconds with zero model calls. Exact source/file identities,
HTTP 200, native validation, 110 unique instance matches and maximum actual
vertex-bound error 0.049864 mm are checked in
`qualification/automatic-native-render-chain-007/verification.json`.
The 64-sample qualification views do not replace the selected 512-sample finals.

All preceding attempts remain. Their corrections cover refreshed OAuth,
rediscovered optional `wait_s` schema, completed pending builds, ignored pipeline
stdin, newline rejection and Blender's native safe-mode restrictions. No active
provider operation was stopped or safety mode disabled. Both old and new builds
are full mode; the reason for new full-build IDs at unchanged revision is unknown.
Actual returned build identity is retained, with no claim of byte-identical STEP.

The text-port privacy canary also passes, with no raw synthetic header in 276
scanned evidence/log/database files. Main v13 still owns its original results;
generic per-design arguments and changed-prompt proof remain the next work.

### 12 October 2026, 17:58 UTC — generic successor running

The native renderer now derives body names, world bounds and colors from current
built SteveCAD metadata for both parts and assemblies. The selected jq checks
pass on actual retained one-body and 110-body data, reject invalid meshes and
wrong document/revision identities, and produce native-safe arguments within
the selected provider's size limit. These are offline binding checks, not a
claim that the main live process passed.

Main v14 run `c53c0b8828054ca697a7460b854fe14e` failed in CAD authoring after
the model corrected an improperly anchored through-hole operation. It then
requested a duplicate document read, which the existing replay guard rejected.
The failure, two design revisions and completed documents are retained. No
renderer ran and no provider bug is asserted. V15 adds explicit body-top-face
anchoring and instructions to consume write/generate receipts without redundant
reads. It preserves v13's instruction snapshot and the same seven logical stages.

Fresh original-block run `3fae6c8dfd5847afbb36ec8accc4308e` passed readiness and
started at 17:58:12 UTC. Source digest
`d47bfa0b4ede89129b07ea489ffd032ed549117900b3730c319e938784732be9`.
It remains executing at this checkpoint. No protected campaign, physical action,
publication or review authority changed.

The v15 authoring walkthrough opens the exact source through the workspace's
Workflows control. The harness reported success, but visual audit found that
Fit workflow to view clips the diagram above and below the canvas. The final
walkthrough is marked blocked, with its original automated report retained;
no UI repair or further navigation was attempted. Artifact root:
`artifacts/ui-walkthrough/prompt-cad-native/20261012-v15-authoring-001/`.
Trace privacy and walkthrough structure checks pass. This is navigation evidence
and a recorded usability issue, not complete editor visibility acceptance.

### 12 October 2026 — native review and disk cleanup checkpoint

V15 exhausted its permitted CAD correction on an invalid Python face accessor.
V16's literal face selector guidance allowed the original block to complete in
584.022 seconds (run `1242198c903d46eda931d46ac68d772b`). All ten CAD checks and
the independent geometry/file handoff audit passed. The final illustrated
review failed R11 because the fallback material was blue-gray while the prompt
required neutral gray. That failure is retained; there is no overall acceptance.

A launch-ordering mistake started `block-native-004` with the old palette before
the corrected source preparation finished. The normal cancellation API rejected
the request because this MCP process has no qualified cancellation capability.
The run was allowed to finish and reached completed execution at
2026-10-12T18:33:20.690933Z. This does not establish visual acceptance of the
corrected palette. Its detailed review still needs retention and inspection.
The prepared neutral-palette source is
`78a0505ad940ee5cfaa85e74a42cb7eb4cc4b2b02f0a57dcca8e524bc6c8924e`;
v18 acceptance and its changed-prompt proof have not started. The launcher now
requires an expected source digest for that next revision.

At the user's disk-space request, new CAD runs were deferred and cleanup became
the immediate task. Initial free space was C: 2,276,372,480 bytes and
D: 790,331,392 bytes. Removed only regenerable caches: old Docker builder data,
npm download cache, pip download/build cache, and 59 September security-scan
`cache/db/trivy.db` files totaling 81,775,116,288 bytes. The scan reports, logs,
database metadata, engineering outputs, source and live application databases
remain. The exact scanner-cache inventory and deletion receipt are in the base
checkout's `.local-run/disk-cleanup-scan-cache-{candidates,result}-20261012.json`.
Python cache pruning used uv's in-use checks, without `--force`.

This task's saved workspace was 0.440 GiB; its worktree artifacts and local
scratch were 1.126 and 0.340 GiB respectively. Provider images/dependencies add
storage separately. The social image ZIP and final orbit MP4 still match their
previous SHA-256 hashes; all 23 running Docker containers remain running.
For future work, check free space before large builds/render batches, reuse
provider images and download caches, and keep final evidence separately from
disposable dependency caches. Do not accumulate a copied scanner database for
every historical scan or delete active runs/designs to reclaim space.

### 12 October 2026, 19:08 UTC — neutral rendering passes; authoring scope corrected

V18 run `ec2aba2b913043048695ae94844be23b` completed in 728.469 seconds. The
independent numeric geometry and actual-file audit passes, with one matched
native mesh and maximum vertex-bound error 0.000002831 mm. All nine generated
CAD-stage tests pass; the review loads all six images without overflow. The
three renders now show neutral gray. Original CAD captures retain green/cyan
provider display colors. The generated R09 test incorrectly broadened the
accepted authoring instruction's rendering-only finish scope to all six images,
so its final review is preserved as 11 PASS / 1 FAIL. The generated isometric
direction also conflicts with the configured native convention; the additive
visual audit records that rather than claiming its original R10 PASS proves it.

V19 addresses that demonstrated general authorship problem before construction.
Test planning and final review now directly receive the original user prompt.
The design/test guidance distinguishes provider-colored geometric captures from
rendered appearance unless CAD display color is explicitly requested. It states
the actual supported camera conventions and scales prose for simple parts while
retaining supplied requirements. The prior sources, plans and verdicts remain.
Exact source comparison proves that only three authoring task declarations and
two original-prompt connections changed; CAD creation, inspection, native tool
arguments and embedded instruction assets are unchanged. Real source compilation,
regeneration, Ruff and format checks pass. Evidence:
`qualification/generic-render-binding-001/v19-authoring-change-audit.json`.

Original-prompt attempt `block-native-006`, run
`15a0b7ad27374a0e9375923cc4dc2725`, passed readiness and started at 19:08:27 UTC.
Accepted normalized source digest:
`77c35b95c93eb6d0dc220d26391f809d67ef8c4bb20ad35004c0f35e574fd35e`.
This checkpoint does not claim its completion, reuse proof or engineering
acceptance. Native images still use the qualified 128-sample proof configuration;
the 512-sample robot marketing finals remain separate.
