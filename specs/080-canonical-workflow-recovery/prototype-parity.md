# Prototype and Recovery Parity

## Current image-led catch-up — 2026-09-02

The historical subjects below do **not** prove completion of the selected
object-palette image. The active amendment is FR-058–FR-066 / T081–T092.

| Approved decision | Current implementation | Acceptance state |
|---|---|---|
| Compact Create rail; seven curated groups | Seventeen configurable native templates, independent IDs, keyboard creation | Focused tests pass; complete browser journey pending |
| Temporary Inputs navigator; one editor | Source-classified readiness, real text/file editing in contextual Inspector | Early browser reviewed; full persistence proof pending |
| Canvas dominates workspace | Agent pane closed by default, full-width page, readable initial zoom, collapsible Inspector/run details/minimap | Two early screenshot iterations reviewed; exact final comparison pending |
| Small distinct interfaces and traceable flow | Named endpoint disclosure, independent exact handles, optional focus-path dimming | Component tests pass; browser connection/drag proof pending |
| Editable engineering Source and one file per workflow | Existing parser/commands retained; named files, scalar input configuration, separate versioned positions | Source/helper/storage tests pass; final cross-surface walkthrough pending |
| Truthful proposal/run states | Example suggestion and fixed local simulation; unbound templates do not execute | Existing guards retained and tested; final walkthrough pending |

Independent findings, repairs and current evidence are tracked in
`evidence/image-redesign-checklist.md`, `evidence/image-redesign-review.md`, and
`evidence/image-redesign-validation.md`. No frozen evidence is rewritten. No
Rivet code or quarantined implementation was imported.

## Historical recovery evidence (unchanged subjects)

**Frozen production checkpoint**: `b4a7e996` after T027

**Frozen visual prototype**: `e7bb75c1` (read-only evidence)

**Recovery treatment**: feature-gated workspace **Workflows** surface at `/workspace/<real-id>?workflow=canonical`; no global recovery route or navigation entry

**Historical T051 approval baseline**: commit `f9237763d6fa6e9748dfb7b713e753a7fc4b4d17`, tree `aeca6ab8294dd54112d3e9ac10148537af32b0f0`, walkthrough manifest `f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347`

**Prior automated correction subject**: commit `c5fb7d8e4a722f84956ebe22085e7fdf38b1b1d5`, tree `148a935edd38e9abe91b9ed284cd04882acf59c6`, [12/12 passing continuation-5 walkthrough](../../artifacts/ui-walkthrough/workflow-recovery-usability/20260901T151651Z-continuation-5/report.html), manifest `e661bf45ff1449abc87399b928156fc336f367f260368a2966645a0026afd96e`
**Current workspace-owned correction subject**: commit `38b409bf149a1241cc87cdedd48f83fed16b5050`, tree `452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6`, [24/24 passing continuation-14 walkthrough](../../artifacts/ui-walkthrough/workflow-recovery-usability/20260901T200836Z-continuation-14/report.html), manifest `b8764a02ef83dfc52b65714de0cdbb05071feb9c0ebf4f5fde4995a2870cf335`

| Capability | Checkpoint D | Frozen prototype | Recovery concept | Disposition / remaining proof |
|---|---|---|---|---|
| Closed semantic model | bounded draft | competing prototype shapes | complete vNext recovery IR | promote only after product/architecture approval |
| Validation/diagnostics | retained, tested | partial | strict kernel, stable `WFR-*` diagnostics | retain kernel behavior; expand source spans later |
| Immutable revisions/CAS | retained production foundation | simulated | one visible workspace `.workflow.wflow` source uses side-effect-free read, idempotent create-if-absent bootstrap on Workflows entry, and compare-and-swap save; re-entry cannot overwrite existing source, and host revision/digest/integrity records remain outside engineer-authored source | continuation 14 proves first-entry 404/201 bootstrap, real saves, stale 409 containment, compare/copy, and explicit reload; T052–T054 historical production sidecars remain separate |
| Renderer adapter | retained | renderer-specific experiments | reused unchanged via `DraftCanvasRenderer` | retain |
| Block/flow visual hierarchy | lane/form dominated | strong | nine-step overview without decorative phase lanes, persistent relationship labels, or per-port metadata; compact blocks show role, name, state, and input/output counts while complete detail remains on focus/selection | historical `f9237763` direction approval and prior `c5fb7d8e` correction evidence are preserved; latest hands-on density correction passes the complete 14-journey Chromium suite and 24-step exact walkthrough |
| Workspace ownership and entry | absent | not addressed | select a real workspace, then open **Workflows** at `/workspace/<real-id>?workflow=canonical`; that explicit action bootstraps and immediately opens the default only when absent, while ordinary workspace entry creates nothing and workflow creation/viewing has no global destination | focused tests and continuation 14 prove real-workspace entry, exactly one initial bootstrap, absence of global recovery navigation, and unchanged existing-source reload |
| Workflow-file and status authority | draft identity spread across the composer | experimental | one compact bar identifies `workflows/mounting-bracket.workflow.wflow`, synchronized Diagram/Source/inspector views, save state, validation, provisional authority, and simulation mode | one visible semantic file is the engineer contract; layout/test state and host-managed revision/digest metadata stay separate |
| Input-source clarity | provisional form fields | incomplete | reference images, engineer-authored text/common document, and approved company context have explicit provenance and all feed one reviewed design specification | three-source connections and common-document preview pass in current Chromium evidence; no fictional PDF brief |
| Tolerance timing | mixed with early requirements | conceptual | initial input stage explicitly defers tolerance work; selecting CAD/downstream work reveals Check dimensions and tolerances using the CAD model and reviewed specification | current S01/S03 evidence passes |
| Direct block movement | bounded custom interaction | disabled | node moves live before mouse-up while revision and accepted digests stay fixed; release commits only the layout digest | continuation-14 S19–S20 capture live pre-release motion and layout-only release against the exact workspace subject |
| Direct connection | absent/indirect | disabled | real typed handle pointer and keyboard contracts | pointer and keyboard Chromium tests pass; approved direction retained |
| Disconnect and identity | limited | visual only | edge labels stay keyboard selectable with stable relationship identity while pointer-overlap geometry does not obstruct normal node clicks | keyboard selection and ordinary pointer-click evidence pass |
| Typed port language | weak | strong visual | small left/right sockets and compact input/output counts lead; friendly names appear on focus/selection and exact type/cardinality remains in the inspector | three-treatment evidence remains available; requesting-engineer feedback replaces the visually heavy hybrid default with compact dots |
| Engineering item vs handle | not applicable | ambiguous | the socket connects; the selected-step inspector opens or inspects its file, model, report, or record | automated distinction passes without repeating an Open control on every node |
| Diagram/Source/Side by side | diagram + read-only text | experimental | lossless editable engineering-source projection using workflow, item/input, task, prompt/instructions, settings, and optional group vocabulary | internal IR and host metadata remain technical machinery rather than user-authored syntax |
| Invalid-source containment | absent | conceptual | invalid draft retained; graph/revision unchanged | browser and kernel tests pass |
| Selection sync | partial | prototype | semantic ID drives block, source range, inspector | browser and walkthrough evidence pass |
| Mixed AI/human authority | implicit | conceptual | reviewed specification says `AI drafts; engineer reviews`, shows an AI prompt with current-workflow provenance, and derives an engineer checklist from the step's accept/revise paths; manufacturing check remains an AI prompt | current inspector and progressive Technical details captures pass without implying AI approval authority |
| AI multi-block proposal | excluded | conceptual | assumptions, warnings, diff, ghost preview, reject/accept | simulated only; acceptance advances once |
| Run overlay | excluded | strong visual fixtures | queued/running/needs-input/blocked/failed/stale/succeeded | UI remains simulated; T054 separately proves durable immutable production run records |
| Recovery action | excluded | fixture | add the missing 6061-T6 decision to the reviewed design specification with explicit downstream consequence | bounded simulation only; current wording follows direct mechanical-engineer feedback |
| Attachment and output persistence | excluded | fixture | the workspace save persists only the visible workflow source; attachment selection, simulated run state, report, and STEP download remain demo-only state/static fixtures | browser interaction must not be described as durable workspace attachment or output persistence |
| Output recognition/lineage | excluded | visual concept | bracket preview, report, STEP download, producer/run/revision/type/digest | continuation-14 S24 verifies simulated labeling, complete lineage, report open, and downloaded fixture digest; no real manufacturing claim |
| Accessibility | later checkpoint | partial | stable controls, focus trap/return, keyboard handles/component disclosure, 2× scale, named accessibility tree, axe zero serious/critical, reduced motion | automated Chromium coverage and the fresh workspace-owned walkthrough pass; one requesting engineer's formative review is not the five-participant protocol or real screen-reader evidence, so T056 remains open |
| Fixed-height desktop containment | page-oriented shell | unproven | 1070×791 application has no document/page scrolling; bounded columns own any necessary internal scrolling | implementation, automated viewport contract, and exact walkthrough pass; representative usability remains open |
| Mobile containment | not target | unproven | 390×844 no document overflow | prior annotated walkthrough captured; representative usability open |
| Reusable component collapse | unproven | model-only | compact Review group / Details / issue summary; stable internal scopes and targets appear only after explicit disclosure | T055 renderer and latest Chromium tests pass without semantic/revision mutation |
| Bounded search and 100-node behavior | unproven | one non-qualifying run | no step search for 25 or fewer steps; deterministic compact mode, fit/minimap, stable identity search and selection at 26 or more | T055 automated large-graph behavior passes; representative production performance remains open |
| Security and RBAC | retained workspace/session and capability policies | not qualified | exact workspace/session hiding, one-shot mutating scope, administrator-only attachment, secret rejection | T057 canonical local slice passes; no external runtime or release authority added |
| Offline and store isolation | retained local-first foundation | not qualified | independent definition/layout/run sidecars and restart/reconnect with network hard-failed | T057 passes; T059 exact wheel plus Windows update/rollback/uninstall/purge and Docker smoke pass |

## What is deliberately not copied

- Prototype-owned semantic or run authority.
- Automatic AI mutation or execution affordances.
- Vendor graph serialization as persistence.
- The frozen shell’s lane/form-first grammar.
- Claims from the prototype’s unrun five-person study.

## Current conclusion

The recovery concept reaches functional parity with the useful canvas-first direction and surpasses the frozen prototype on direct manipulation, explicit source provenance, contextual downstream work, mixed-authority inspection, paired editing, proposal review, invalid containment, bounded run recovery, reusable-component inspection, and stable-identity navigation. The [approval record](evidence/product-approval.md) preserves the historical `f9237763` baseline and honestly binds the conditional direction approval to the current `38b409bf` correction after exact material-equivalence verification; it does not claim that the requesting user personally executed the final walkthrough. The [digest-bound comparison](evidence/prototype-side-by-side.md) and continuation-5 walkthrough remain prior automated formative evidence. The current correction moves authoring into a real workspace, makes Source an engineer-facing script rather than internal IR, adds one visible `.workflow.wflow` file that is idempotently bootstrapped on Workflows entry and protected by compare-and-swap, and proves the compact overview-first treatment in continuation 14. T056's five-participant moderated usability and real assistive-technology evidence, qualifying engineering oracles, and public/cross-platform release gates remain downstream obligations.
