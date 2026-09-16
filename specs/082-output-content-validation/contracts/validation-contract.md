# Validation contract for feature 082

The [complete service, reader, numerical, RTM and CLI contract](../../081-engineering-workflow-templates/content-validation/contracts/validation-contract.md) is adopted unchanged except for these explicit integration clarifications.

## Source roots and bootstrap audit

`audit-generation` is a target command, not an installed command. T001 first audits direct source files and read-only runtime records. T010 implements this as a reusable service and thin CLI, using the same evidence contract. Campaign/source/runtime roots are separately authorized read-only inputs; `--state` and report paths refer only to the validation-owned root. Do not make relative paths accidentally resolve into another worktree's writable state.

## Review and error semantics

`record-review` must use a real authority context. Neither a caller-provided actor string nor the legacy artifact-review local-workspace label proves human identity. When identity/type cannot be established, reject the decision and retain a pending review. A failed measured predicate is fail; a crashed or invalid evaluator is error. Preserve both known engineering failures and operational errors in mixed reports.

## Compatibility

Keep adopted commands, state vocabulary, identity keys, immutable late-review behavior, cancellation and exit codes: 0 success/all required checks pass; 1 conclusive content/design failure; 2 request/framework/reader error; 3 deferred/blocked/inconclusive/stale/pending review; 130 cancelled. Mixed precedence is 2 > 3 > 1 > 0; detailed verdicts are never discarded.

No generation dispatch or printer/supplier action is added. Qualify native readers on disposable working copies with exact process ownership and unchanged originals.
