# Visual progress and unpublished media

The user requested approximately twenty additional images over the next few
hours, including actual SteveCAD views, varied angles, subsequent renderings and
video. Deliver useful views at engineering milestones, not an end-only batch.
No marketing publication is authorized.

| Additional item | Delivered in chat | Evidence |
|---|---|---|
| 1. Joint isometric, actual SteveCAD | 11 October | `provider-guidance/joint-rev3-isometric-1.png` |
| 2. Joint top, actual SteveCAD | 11 October | `provider-guidance/joint-rev3-top-1.png` |
| 3. Joint front, actual SteveCAD | 11 October | `provider-guidance/joint-rev3-front-1.png` |
| 4–6. Joint isometric/top/front renderings | 11 October, tool image display; isometric also embedded in chat | `joint-003/outputs/render_{isometric,top,front}.png` |
| 7. Joint +90° pose, neutral CAD viewer | 11 October | `../joint-motion-media/joint-positive-90.png` |
| 8. Joint −90° pose, neutral CAD viewer | 11 October | `../joint-motion-media/joint-negative-90.png` |
| 9. Joint zero pose, neutral CAD viewer | 11 October, tool image display | `../joint-motion-media/joint-zero.png` |
| 10. First robot isometric, native mesh viewer | 11 October, tool display and chat embed | `../robot-arm-media/initial-rev1/robot-isometric.png` |
| 11–12. First robot top/front, native mesh viewer | 11 October, tool image display | `../robot-arm-media/initial-rev1/robot-{top,front}.png` |
| 13. Revision-2 robot isometric | 11 October, tool image display | `../robot-arm-media/corrected-rev2/robot-isometric.png` |
| 14–15. Revision-2 robot top/front | 11 October, tool image display; top clipping and stale footer disclosed | `../robot-arm-media/corrected-rev2/robot-{top,front}.png` |
| 16–17. Reframed revision-2 diagnostic isometric/top | 11 October, tool image display; actual fit FAIL shown | `../robot-arm-media/diagnostic-rev2/robot-{isometric,top}.png` |
| 18. Native revision-3 upper-arm isometric | 11 October local / 12 October UTC, tool image display | `../robot-arm-media/corrected-rev3/robot-rev3-native-upper-arm-1.png` |
| 19–20. Native revision-3 gripper isometric/top | 11 October local / 12 October UTC, tool image display; diagnostic, failed revision | `../robot-arm-media/corrected-rev3/robot-rev3-native-gripper{,-top}-1.png` |
| 21–24. Revision-4 native isometric and three derived renderings | 11 October local / 12 October UTC, tool image display; failed-fit diagnostic revision, rendering fidelity concerns | `robot-arm-007/outputs/cad-isometric.png`, `robot-arm-007/outputs/render_{isometric,top,front}.png` |
| 25–26. Revision-5 native isometric and derived isometric | 11 October local / 12 October UTC, tool image display; native fit FAIL, derivative changes board/base detail | `robot-arm-008/outputs/{cad-isometric,render_isometric}.png` |
| 27–28. Revision-5 colored STEP geometry isometric/top | 11 October local / 12 October UTC, tool image display; exact geometry, failed revision explicitly labeled | `../robot-arm-media/corrected-rev5/robot-{isometric,top}.png` |
| 29–30. Revision-6 folded/reach geometry poses | 11 October local / 12 October UTC, tool image display; actual geometry/native joint frames, physical operation untested | `../robot-arm-media/corrected-rev6/motion/robot-{folded,reach}.png` |
| 31–33. Revision-7 isometric/top/front derivatives | 11 October local / 12 October UTC, tool image display; diagnostic color/fidelity failures retained | `robot-arm-010/outputs/render_{isometric,top,front}.png` |

The joint images are revision 3, build `39af23dd-b6df-4d59-81d0-c84fcb8a4035` of document
`43bc0df4-4658-477b-a63e-09b281b6f86f`, under
`artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/`.
Captured-image receipts retain exact bytes and hashes. Uniform capture coloring
does not establish the requested presentation finishes.
The robot previews use their stated revision's actual mesh archive. Revision 2
is document `167ef21f-6679-4e4d-8917-14dc067893d6`, build
`3b8bac04-ef45-4606-ba87-f5bd55bfb817`, 48 instances, with failed native fit/motion.
Reframed diagnostic captures preserve the earlier raw images and show that FAIL.
Display colors identify parts and are not yet qualified
native Studio appearance. No motion acceptance is implied by these static views.

Next useful milestones: purchased hardware and its
mounting bay; robot base, shoulder, elbow and wrist/gripper; complete arm poses;
three final arm renderings; assembly/print layout and review previews. Track
actual delivered images here. A plan or an undisplayed file does not count.

Delivered: a 12-second WebM VP9 clip, two cycles through actual 0/+90/−90/0
keyframes using native exported meshes, recorded in a local Three.js 0.185.1
viewer. `artifacts/stevecad-demonstrations/joint-motion-media/media-provenance.json`
retains hashes, inputs and scope; `mesh-verification.json` passes binary STL
extent, closed-edge incidence and volume checks against the native manifest.
This is actual geometry playback, not a SteveCAD Studio recording or a new
collision computation. A browser check recorded no page errors.
The delivered H264 MP4 is 11.405 seconds, 1280 × 720, 142 encoded frames.
Independent decoding samples twelve distinct frames at one-second intervals.
The requested 30 fps is separate from the achieved average recording rate.
At the user's request, `joint-motion-x.mp4` was exported as H264 High/yuv420p,
1280 × 720, constant 30 fps, silent AAC-LC, MP4 fast-start. ffprobe reports
11.566667 seconds and 257320 bytes. This transcode repeats existing frames;
it does not add new motion samples or improve the original capture rate.
The file was delivered for the user's upload; no X publication was performed.

The user supplied a styled SteveCAD assembly example and requested a stronger
native CAD presentation than uniform cyan captures. The verified API is
`Model.material(material, bodies=None, finish=None, color=None)`: finish and color
are appearance-only; the material is a physical library ID. No methods named
`appearance` or `color` were found. Qualifying native styled captures remains
pending; do not claim the neutral viewer or AI render is a Studio screenshot.

Focused native `inspect_model(show=[...], checks=[])` now succeeded for the
revision-3 upper arm and gripper in roughly three to five seconds. These are
actual provider images, bound to build `ad1c0f2c-490f-4767-834b-20349fefeeec`.
They still use uniform coloring despite the verified source material/color
assignments; do not claim that these captures show Studio appearance. A fresh
whole-assembly revision-3 image timed out. Smaller views qualify diagnostic
capture only, not the three required final whole-assembly orientations.

The image audit preserves a real repeated-instance visibility-label discrepancy
in the gripper captures; identity/build and byte hashes pass, while reported
drawn-instance labels fail the requested selection. A separate two-box native
reproduction confirms the provider defect. Do not treat the gripper captures'
label list as independently verified identities. See `corrected-rev3/capture-audit.json`
and `qualification/stevecad-visibility-repro/verification.json`.

SteveCAD Studio motion-video capture remains pending. Prefer its supported Motion-tab
video export, which is a Studio UI operation rather than a discovered MCP tool.
If a neutral CAD viewer is recorded using exported real geometry and the built
joint transforms, label its application and provenance explicitly. Do not label
generated motion imagery as CAD validation or physical operation. Preserve raw
captures and media provenance; renderings remain presentation assets.

Revision 4 and 5 whole-assembly native captures succeeded. Their presentation
derivatives still require visual review: revision 4 changed the exposed board,
and revision 5 isometric adds/changes the board platform while the top view uses
green on the tray. The automated review's broader fidelity PASS is therefore not
accepted as an independent geometry-preservation finding. Preserve both artifacts
and the discrepancy. These are not the final marketing selections.

The revision-5 STEP export is independently imported with build123d 0.10.0 in
the cached selected AgentCAD 0.6.0 environment, without network. It contains 110
placed children and 119 solids; five printed cradles are disconnected. Repeated
STEP labels name first instances, so each of 110 diagnostic STL exports is mapped
by unique actual world bounds (1e-5 mm) and rounded native volume (.001 mm³).
All STL hashes and closed-edge checks pass; maximum relative volume error is
0.00041540825. The connected printed-part requirement FAILS. The three colored
viewer captures preserve this failed revision and native appearance metadata.
These are standard STEP tessellations in a neutral Three.js viewer, not native
bodies_mesh downloads or Studio screenshots. No AgentCAD MCP call is claimed.
See `../robot-arm-media/corrected-rev5/{manifest,mesh-verification,preview-provenance}.json`.

Delivered revision-6 arm video:
`../robot-arm-media/corrected-rev6/motion/robot-arm-motion-x.mp4`.
The 8-second movie has 192 deterministic CAD frames at24fps, 1280×720 H264 High
with yuv420p, silent AAC-LC and MP4 fast-start. Full independent decoding succeeds;
eight cropped CAD-region samples at one-second intervals are distinct. All110
geometry instances load; the viewer uses saved native joint parents, oriented
axes/origins, coupling ratios and five linear keyframes. Native exact-solid
five-pose fits and33 motion samples clear at this revision; the movie does not
extend their coverage or establish physical operation. Four named pose images,
native geometry/kinematics hashes, frame method and encoded-media details are
retained in `motion-provenance.json` and `x-export.json`. No marketing posting
or claim of Studio capture is made. The geometry is independently connected;
printing, slicing and operating tests remain unverified.

Revision-7 delivery now includes three final native geometry studio renderings
(`render-isometric-final.png`, `render-top-final.png`, `render-front-final.png`)
and an exact-revision8-second MP4. The front and top finals were shown in the
12 October05:22UTC continuation; these are useful arm images, unlike the black
Blender viewport-control capture. The image count already exceeded the requested
additional20; frequency and useful views remain the goal rather than filler.

The final selected PNGs come from native Blender Cycles512-sample rendering of
the110 checked STEP-derived meshes, with geometry unchanged. The imagegen
cleanup experiment added fastener details and was excluded. All rejected
candidates and the source/provenance records remain discoverable. The selected
MP4 is H.264/AAC,720p24fps,8s,515047bytes and passes full decoding. It uses native
joint transforms in a neutral viewer, not Studio capture or physical operation.

An additive illustrated review under
`../robot-arm-media/corrected-rev7/design-package/design-review.html` presents
the three SteveCAD captures beside these three final renderings, the video,
exact STEP/STL/BOM/assembly deliverables and scoped verification. Desktop/mobile
image, link, layout and video metadata checks pass. The accompanying
`robot-arm-rev7-unpublished-marketing.zip` contains the three selected images,
MP4, provenance and accurate draft captions; no publication is authorized or
performed. Native renders remain supplemental until the saved process owns
their actual artifact handoff.

A new1000×720 native preview was shown from the actual connected AgentCAD→Blender
run on12October06:10UTC. It uses all110 exact-source placed components, supplied
colors and32 Cycles samples. It is visibly noisier than the selected512-sample
finals and is not substituted for them. The entire standard STEP→GLB→PNG chain
completed in18.269seconds; both artifact hashes and actual world-vertex identity
checks pass. This removes manual mesh staging within that qualified chain, while
automatic SteveCAD ticket transfer and the main seven-stage binding remain open.
See`qualification/native-mesh-render-chain-002/verification.json`.

### 12 October 2026, 12:49 UTC — curated robot social-media collection

The user's requested collection is now under
`artifacts/stevecad-demonstrations/robot-arm-media/corrected-rev7/social-media-001/`.
It contains 20 numbered images: six actual SteveCAD MCP views (three fresh
right/gripper/electronics captures), three unchanged final native Blender
renderings, four native-joint poses in a neutral CAD viewer, two actual Wright
workspace screenshots, and five clearly labeled evidence graphics. The graphics
cover native solids/dimensions, sampled fit/motion, oriented STL integrity,
conservative electronics headroom, and the retained original review findings.
They are presentation summaries of saved evidence, not replacement validation
reports or application screenshots. Original results remain 10 PASS, four
UNVERIFIED and two FAIL among the 16 recorded tests, with deferred work separate.

A fresh, camera-only 360-degree orbit uses the exact revision-7 STEP triangles
in the home pose. The selected tighter camera version is 12 seconds / 288
deterministic frames, 1280×720, 24 fps, H.264 High/yuv420p with silent AAC and
MP4 fast-start. Its SHA256 is
`86355db6f1aa1713d99425336bb23e1c9c815853f1b06929def761c8bc9c5798`.
The earlier wider orbit remains diagnostic evidence. The collection also
includes the existing eight-second joint-motion MP4. Both decode fully. These
are neutral CAD-viewer recordings, not Studio screen capture, a new clearance
simulation, or physical robot footage.

The successful read-only Wright walkthrough is retained at
`artifacts/ui-walkthrough/prompt-to-reviewed-cad/robot-social-001/`. It opens the
exact completed robot run through the normal Workflows and Previous runs
controls. A subsequent larger-viewport attempt stopped at the editor entry;
its timeout and raw screenshot remain at `robot-social-002/` and were not
substituted for the successful images. Both walkthrough artifact structures
validate. No product code or run state was changed for this media work.

`index.html` provides a responsive gallery, full-size image links and both
videos; `contact-sheet.png`, `captions.md`, `manifest.json` and numeric evidence
are included. Desktop/mobile checks verify all 20 images, local links, both
video metadata records and no horizontal overflow. The 50-member ZIP
`robot-arm-rev7-social-media-20-images.zip` is 12,322,637 bytes; every member's
bytes match its source. Its SHA256 is
`229b100915b54d03b6876ddada3bcc5fad069a33002cf5aac4ae0645952ba5dd`.
Native final renderings and supplemental checks remain separate from the main
saved workflow's current bindings. Printing, assembly, strength, drives and
powered operation remain untested. Nothing has been posted or published.
