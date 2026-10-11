# Research and scope reconciliation

**Updated:** 2026-09-16. Repository review for the process-validator scope; no new external product recommendations.

## Decisions

| Decision | Rationale | Alternative considered |
|---|---|---|
| Runtime validator, callable directly and inside canonical processes | User needs checks between steps, not a corpus QA gate | Keep only a post-run campaign CLI |
| Replace global G0 on approval of the revised goal | One stable producer output can be checked while unrelated flows remain unfinished | Block all development on 30 completed outputs |
| Extend existing design-check scheduler | It already routes feedback, preserves attempts and bounds rework | Build another graph runner |
| Add explicit local validator mode | Current design checks require MCP/JSON/read-only CAD | Pretend existing CAD-only restrictions already support generic checks |
| Reuse EngineeringResult with revision identity | Supports values/files/CAD/analysis and producer provenance | Use file paths or run:step:port IDs as immutable subjects |
| Deterministic measurement plus attributed judgment | A fluent report does not establish geometry or numeric correctness | Let a critic AI invent authoritative numeric verdicts |
| Typed repair packets with readable explanations | Both the producing AI and reporting users need the same facts | Free-text corrections or opaque test failures only |
| One safe producer/check revision segment first | Bounds side effects and works with existing scheduler | Arbitrary multi-producer graph rewinds |
| Report schema/Markdown/RTM contract here | Reporting UI is being built in another branch | Build a duplicate dashboard and report application |
| Package runtime profiles | Native installed runtime must work without source/test checkout | Leave production profiles under tests only |
| Three initial capabilities plus 30-pack support map | Establishes the process loop and shared geometry/numerics before expanding readers | Claim all 30 are supported by a generic schema checker |

## Repository evidence reviewed

- `packages/workspace_service/src/workspace_service/workflow_source_execution.py`: canonical compile/execution; design-check restrictions; producer prompt feedback; revision snapshots and result invalidation.
- `workflow_design_check.py`: evidence guards and one CAD producer/check rework path.
- `workflow_results.py`: provider-neutral EngineeringResult, representations, provenance and verification/diagnostic roles.
- `workflow_run_record.py`: result projection and invalidation on design_revision.
- `workflow_mcp_execution.py`: read-only check tooling and subject restrictions.
- `workflow_async_operations.py`: materialization of remote operations.
- `engineering_scenario_assertions.py`, `engineering_scenario_artifacts.py`: reusable plugins/normalization; summaries still require actual-file evidence.
- `workflow_engineering_assertions.py`: legacy exception-to-fail conversion needs an explicit bridge.
- `workflow_artifact_review.py`: local unauthenticated attribution is not proof of human acceptance.
- `packages/core/src/core/tools.py`: BaseTool requirement.
- `docs/contributing/workflow-ui-integration.md`: preserve the reviewed editor and verify served workspace entry.
- Jig source CSV and retained heat-inspection notes confirm useful geometric/numerical pilot requirements.

A bounded read-only Spec Kit research agent independently reviewed the runtime integration points. No process, solver, generation campaign or application takeover was performed.

## Earlier engineering analysis retained

The [081 research](../081-engineering-workflow-templates/content-validation/research.md) preserves the original primary-source basis and D01–D09 decisions. Reuse independent measurements, semantic checks, source baselines, explicit outcome states, meaningful valid/defective controls, current model authority and requirements traceability. Its post-run activation, all-family delivery and dashboard sequencing are historical after approval of this amendment.

The [30-case seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md) remain requirement discovery material. Keep jig arc-center versus point-on-curve behavior, exact datum/clearance definitions, heat field/refinement evidence, Modelica derivative/thermostat semantics, Pi manufacturer-source authority and narrow sheet-metal amendments when their capabilities are implemented.

## Implementation discovery, not unresolved design

T001/T002 resolve exact transport registration and canonical source-schema extension locations, qualified local reader versions, pilot artifact formats and source hashes. These are bounded code/evidence discovery tasks. They do not authorize installing all native tools, replacing the editor, auditing other branches or rerunning the corpus. Missing required pilot dependencies receive concrete blockers while independent implementation continues.

## Spec Kit execution

Read constitution v3.1.1, current feature selector, plan/tasks templates and installed skill instructions. Ran setup-plan.sh and setup-tasks.sh through Git Bash; both resolved feature 082 without overwriting existing templates.

Before/after plan and tasks hooks are optional: `/speckit-git-commit`; after-plan also offers `/speckit-agent-context-update`. No mandatory hook applies. Automatic optional hook execution was skipped; the managed AGENTS section is updated explicitly as the plan workflow requires. A normal focused documentation commit may save the finished handoff.

Planning review and task generation belong to this user-requested planning turn. Runtime implementation, deployment, a persistent goal and report-branch edits are not started.
