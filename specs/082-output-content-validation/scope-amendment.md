# Scope amendment: process output validator

**Date:** 2026-09-16. **Authority:** the user's clarification in this task.

The requested product is a validator called during a process to check a previous
step, return actionable feedback to its producing AI, and supply readable evidence
to user reports. The reporting application is being developed in another branch.
This document records the change from the earlier corpus-validation plan.

## Keep from the earlier analysis

- Requirements with source references, frozen methods, units, datums and tolerances.
- Reusable readers and checks, including shared CAD geometry checks.
- Actual-file observations rather than a generator's claim of success.
- Explicit failure, missing-evidence and evaluator-error states.
- Immutable output revisions, findings and requirements traceability.
- The [30 input-pack seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md), especially the jig and heat examples.
- Meaningful tests of the validator itself, distinct from the delivered capability.

## Replace in the active 082 package

| Earlier plan | Current scope |
|---|---|
| Run a final 30-case validation campaign | Invoke a reusable check inside a canonical process, also callable directly |
| Wait for every flow to produce data before any implementation | Check readiness of each bound subject at invocation; missing unrelated cases do not block development |
| End with a backlog of generator defects | Return a structured correction packet and support an explicitly configured, bounded producer revision loop |
| Build a dashboard and validation report UI here | Publish a versioned result/report contract for the other branch; add only process-check authoring/status integration here |
| Implement every family before calling the framework useful | Deliver a working process slice with structured output, CAD geometry and numerical checks; catalog remaining family capabilities honestly |
| Store runtime profiles only in test datasets | Package reusable profiles/resources with the runtime; keep test fixtures separate |

Submitting the revised goal explicitly approves replacing the former all-30-output
**G0 activation gate for this feature**. Until then, this is a proposed plan change,
not authority to start implementation.
Its valuable identity and stability checks become per-subject runtime rules.
The dated [24/30 snapshot](evidence/readiness-2026-09-16.json) remains historical
evidence, not a current audit or a development prerequisite.

All 30 packs still inform the capability inventory. Version 1 does not claim all
30 designs are verified or implement every specialized solver/manufacturing
reader. The expansion map must identify unsupported checks; they cannot pass by
default. A validation result always states its checked scope.

## Authority and precedence

Current user instructions and the constitution control. This amendment and the
updated 082 spec/plan/contracts/tasks are the implementation authority after
human plan approval. The 081 bundle remains engineering reference material;
its campaign activation rules and UI scope do not override this amendment once approved.
The preceding 082 documents are retained in Git history at `0a48f88f`.

This task produces a plan and a saved `/goal`, not implementation or an active
goal. Submitting the saved goal approves the revised planning package. Later
milestone reviews follow the constitution and any explicit user authorization.
