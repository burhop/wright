# Image-redesign implementation validation

Status: candidate validation in progress; final committed-subject results pending.

Integration worktree: `D:/repos/wright/.local-run/epp-f02b-writer/wright`.
Branch: `codex/080-canonical-workflow-recovery`. Baseline: `7e95b0c7`.
Commands below were run against the changing candidate, not a final commit.

| Check | Command / scope | Observed result |
|---|---|---|
| Authoring helpers and boundaries | `npm run test -- src/prototypes/workflow-recovery/authoring-objects.spec.ts src/prototypes/workflow-recovery/recovery-authoring.spec.ts src/prototypes/workflow-recovery/command-system.spec.ts` in `apps/web` | 65 passed / 3 files; exit 0 (helper agent) |
| Host authoring | `npm run test -- src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx` | 15 passed; exit 0 (host agent) |
| Renderer before added selection/trace tests | `npm run test -- src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.spec.tsx` | 7 passed; exit 0 (integration writer); expanded suite pending |
| Build | `npm run build` | Passed; 858 modules (host agent); existing Vite native-config and bundle-size warnings |
| Early real browser shell | `node scripts/recovery/capture_image_redesign.mjs --label=early-shell-continuation-1 --viewports=all --url=http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51?workflow=canonical` | 4 shell actions and 4 viewport captures; assertion pass, material visual findings recorded separately |
| Full web suite | `npm run test` in `apps/web` | 117 files / 623 tests passed; exit 0; 82.97s (integration writer). Later changes require focused rerun and final broad checkpoint. |

## Failures preserved

- Tests-first helper suite initially failed because the module did not exist.
- A stronger collection-narrowing case initially failed because collection
  outputs could feed one-valued inputs. Source and command paths now reject that
  atomically; existing single-value fan-in to collection inputs is retained.
- First Chromium launch failed with `spawn EPERM` in the sandbox before
  navigation. Separate permitted continuation captured the actual application.
- Early screenshots passed basic assertions but failed visual acceptance; see
  `image-redesign-review.md`. Passing a screenshot harness is not visual approval.

## Remaining checks

Full authoring browser journey, actual 200% zoom, final independent visual review,
storage/source regressions, scoped security/path checks, broad suite completion,
freeze identity check, Spec Kit consistency and validated exact-subject evidence.

### Later working-tree checkpoints (supersede the earlier pending observations)

Final pre-commit broad rerun: **118 web files / 642 tests passed** (97.76s),
followed by a successful TypeScript/production build (858 modules, 5.03s).
Existing Vite native-config and bundle-size warnings remain warnings, not hidden
failures. Final storage/API/operator suite: **123 passed, 5 skipped, 143 warnings**
(22.90s), including all 25 pure provenance-helper tests. Final Chromium regression
rerun: **13/13 passed** (1.2m), output `test-repair-final-20260902`.
Frozen historical spec079 tasks are byte-equivalent through Git to `b4a7e996`.

| Check | Observed result |
|---|---|
| Complete real-browser functional journey | `20260902T223458Z-functional-continuation-6`: 30/30, including exact save/reopen source/layout, stale-tab 409 conflict/compare/reload, bounded proposal/run, four viewport sizes and actual Chromium tab zoom 2.0. Raw/annotated/trace/manifest/report validator passed. |
| Independent read-only visual review | `20260902T223502Z-independent-readonly-review`: seven checks, zero mutations and unexpected diagnostics; primary 1536×1024 hierarchy accepted internally, four concrete polish findings repaired. |
| Actual 200% controls | `20260902T224417Z-zoom-continuation-1`: five checks, real 768×395 effective viewport at DPR2; Settings Apply reached by internal scrolling without applying values; Inspector/minimap collapse restores canvas space. |
| Workspace Console/maximize | `20260902T223851Z-workspace-controls-continuation-1`: separate center hit targets and open/collapse/maximize/restore pass. |
| Existing Chromium integration suite | `test-repair-20260902-run5`: 13/13, 59.2s; typed pointer/keyboard, live drag, <1s feedback, history, proposal/lineage, accessibility and mobile containment. |
| Expanded renderer | 14/14 (5.04s), plus TypeScript check exit 0; operation-aware icons and short-height minimap included. |
| Layout hash and host | 19/19 in canonical-wire + host suites: nested key order does not alter identity; changed coordinates and authority still do. |
| Broad web checkpoint | 118 files / 637 passed (97.07s). Subsequent build found two unsupported Testing Library `exact` options in test code; corrected to the library's already-exact string-name matcher. Final broad/build rerun follows. |
| Backend storage/API/operator tests | 113 passed / 5 genuine platform skips; see `image-redesign-storage-review.md`. Later provenance-helper additions have separate focused results. |
| Conformance | `python -m pytest tests/recovery/test_workflow_conformance.py -q --basetemp .test-tmp/image-redesign-conformance-final`: 36 passed, 2.52s. |
| Capability audit | 890/890 source rows, 33/33 capabilities, zero unexplained omissions. |
| Syntax fixture evaluator | JSON, YAML and engineering-source round trips/schema checks and 5/5 edit candidates each pass. Fixed fixture SHA `04cc79dad3b8177e52ab46d0c994d5d48b39f63d7483ccf504eb8d665b902b2d`; not a benchmark. |

Additional failed continuations are retained: missing favicon; retained-tab
selector ambiguity; newly named document identity rejected by cold roundtrip;
order-sensitive layout checksum; proposal overlay intercepting the Inspector.
Each repair was followed by a separate continuation, not a rewritten passing
history. Save/reopen checksum failure was not coordinate loss: captured PUT and
GET positions matched exactly; canonical key sorting fixed evidence identity.

The read-only Spec Kit prerequisite command completed through the permitted WSL
Bash process: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks
--include-tasks`. It returned the correct `080-canonical-workflow-recovery`
feature directory and all prerequisite artifacts. WSL did not detect the Windows
worktree Git metadata, so its branch validation was skipped; native Git inspection
independently identifies `codex/080-canonical-workflow-recovery`.
