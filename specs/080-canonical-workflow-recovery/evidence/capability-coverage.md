# Capability Coverage Audit

**Result**: PASS

- 881 unique source requirements mapped.
- 33 of 33 canonical capabilities represented.
- 11/11 product gates, 100/100 customer stories, and 25/25 prototype lessons present.
- Every relevant legacy/frozen `FR-*` and `SC-*` is keyed by source path, so repeated local IDs cannot collide.
- Unexplained omissions: 0.

## Source counts

| Source | Rows |
|---|---:|
| `docs/programs/engineering-process-platform/customer-process-user-stories.md` | 100 |
| `docs/programs/engineering-process-platform/decision-register.json` | 20 |
| `docs/programs/engineering-process-platform/gates.md` | 34 |
| `docs/programs/engineering-process-platform/prototype-lesson-dispositions.json` | 25 |
| `git:e7bb75c1:specs/076-engineering-workflow-prototype/spec.md` | 54 |
| `specs/054-rivet-workflow-integration/spec.md` | 40 |
| `specs/055-rivet-compatibility-spike/spec.md` | 21 |
| `specs/056-rivet-workspace-persistence/spec.md` | 15 |
| `specs/057-rivet-headless-runner/spec.md` | 1 |
| `specs/058-rivet-editor-host-adapters/spec.md` | 12 |
| `specs/059-rivet-workspace-tab/spec.md` | 1 |
| `specs/060-rivet-wright-nodes/spec.md` | 1 |
| `specs/061-rivet-workflow-operations/spec.md` | 6 |
| `specs/064-retained-editor-host/spec.md` | 8 |
| `specs/066-rivet2-canvas/spec.md` | 29 |
| `specs/067-rivet-hermes-ai/spec.md` | 31 |
| `specs/068-capability-library/spec.md` | 45 |
| `specs/069-rivet-mcp-gateway/spec.md` | 45 |
| `specs/070-engineering-scenario-harness/spec.md` | 46 |
| `specs/071-local-engineering-model-library/spec.md` | 55 |
| `specs/072-chatter-rivet-scenarios/spec.md` | 48 |
| `specs/073-program-hardening/spec.md` | 51 |
| `specs/074-windows-mcp-qualification/spec.md` | 30 |
| `specs/075-rivet-run-inspector/spec.md` | 32 |
| `specs/078-process-definition-view/spec.md` | 23 |
| `specs/079-visual-workflow-composition/spec.md` | 30 |
| `specs/080-canonical-workflow-recovery/spec.md` | 78 |

The CSV is the exhaustive machine trace. `capability-inventory.md` is the review-oriented roll-up; neither changes the authority or passing status of its sources.
