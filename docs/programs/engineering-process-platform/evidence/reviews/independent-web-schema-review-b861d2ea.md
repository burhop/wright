# Independent frontend schema portability review

Reviewed correction: `b861d2ea1c33c569bbcc32950120073f246c4c96`, compared with `99cee2dc`.
Reviewed tree: `2f2b4c65d6f4c401e41b47ba90e89a0d3e6cc7ed`.
Reviewer: independently delegated `native_candidate_review`; authored none of this change.

**No actionable P1/P2 finding. Correction accepted for the reviewed scope.**

The production milestone decoder now imports a schema resource inside `apps/web/src/contracts`, which is included by the Docker frontend stage's existing `COPY apps/web/ apps/web/`. The prior runtime import reached into `specs`, which is excluded from the Docker context and was not copied into that stage. The decoder now uses the imported projection directly; its validation/recomputation logic is otherwise unchanged.

Independently ran the three focused packaging checks in the exact detached correction checkout: **3 passed in 0.25 seconds**. They resolve the actual runtime import within `apps/web`, compare its parsed JSON with the identical milestone projection in both authoritative schema copies, validate it as JSON Schema 2020-12, and ensure it has no unresolved `$ref` dependencies. Also inspected `.dockerignore` and the actual Docker frontend copy/build sequence. This is a distribution copy protected by equality checks, not a new source of language or dashboard semantics.

No full frontend suite or Docker build was run by this reviewer for this small correction. Required combined-candidate build, container and delivery gates remain separate. This report supplies bounded technical review only and does not claim those gates, human acceptance, or deployment are complete.
