# Frozen Prototype Evidence and Disposition

## Boundary and inventory

The prototype is frozen at `076-engineering-workflow-prototype` commit `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d`; local and remote refs matched during inspection. Its spec labels it reference-only and excludes production migration, durable compatibility, orchestration scaling and security certification. It is an experimental notebook, not a production branch.

The primary agent and four auditors inspected committed:

- `specs/076-engineering-workflow-prototype/{spec.md,plan.md,research.md,data-model.md,quickstart.md}`;
- all six contracts (workflow spec, canvas adapter, authoring command, capability template, generic MCP binding and checkpoint evidence);
- focused domain/component/canvas/evaluation test inventories, including deterministic routing, exact binding, headless runner, accessibility, scale and usability-integrity tests;
- checkpoint narratives and the 25-item `evidence/prototype-lessons-learned.md`;
- representative committed screenshots for the visual slice, selected canvas, 100-block scale, knowledge lookup and artifact-port concepts.

The screenshots show a promising phase-lane grammar and inspector, but the 100-block fit view is not readable as an information-design proof, and later artifact-port images are concepts rather than accepted interactions. The planned equivalent baseline/five-person comprehension study was not completed. React Flow selection is provisional. Strict JSON/Apply behavior is provisional. CP3H/CP3I live human reviews remained pending. The live four-block narrative proves orchestration observations, not an engineering oracle. No CP7 retain/hybrid/replace ADR exists.

The branch also contains inherited implementation beginning at commit `a51d1eae` that is absent from the clean `dev` baseline. It is subject to the same read-only evidence rule.

No prototype worktree was registered; the inspected `dev` worktree was clean before planning; local/remote prototype refs match. Therefore no important evidence is observably available only as uncommitted work. This cannot attest to deleted or unregistered external directories. Any former raw live-run artifact not committed is not safely recoverable evidence and cannot support a program claim.

## Allowed and prohibited use

Allowed: cite lessons, contracts, tests, screenshots, failures, measurements and hypotheses; use them to write fresh specs and acceptance tests.

Prohibited: merge/cherry-pick/wholesale promote prototype code; use it as a feature base; assume its schemas/renderer/executor/components are production decisions; cite a fixture/live run/screenshot/test as commercial, compatibility or engineering-correctness proof.

The machine-readable dispositions are authoritative in [`prototype-lesson-dispositions.json`](prototype-lesson-dispositions.json). Accepted means the invariant enters program gates, not that prototype implementation is reusable. Revised means the core finding is retained with narrower production language. Deferred leaves a named future gate.

## Key contradictions resolved

- **Fast tests vs human review:** retain fast contract tests and require human evidence for trust/usability; neither substitutes for the other.
- **React Flow selection vs production architecture:** the bakeoff is evidence only; canonical vendor-neutral contracts may proceed, permanent renderer choice needs ADR.
- **Headless success vs correctness:** UI independence is desirable; equivalence, authoritative application identity and qualified artifact/oracle evidence are separate gates.
- **One multimodal primitive vs typed routing:** preserve a canonical typed request and compatible views; do not preselect production UI/block count.
- **Semantic artifacts vs exact tool schemas:** prefer tool-independent artifacts plus adapters where justified, but allow direct reviewed schema-bound values.
- **Artifact port concepts vs component model:** accept separation of ports/connections/artifacts/components; revalidate notation and composition UX.

## Production blockers carried forward

The open P0 decisions cover canonical syntax/apply, application identity, hard tool isolation, deadline policy, output lifecycle, oracle authority, UI/headless equivalence, holdout custody, benchmark population/thresholds and third-party rights. They block the earliest relevant roadmap item and cannot be silently resolved by plan approval.
