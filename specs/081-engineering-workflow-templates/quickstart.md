# Planning and Implementation Quickstart

## Current boundary

The local feature is in progress on `codex/081-engineering-workflow-templates`.
The user approved implementation and the unattended dataset testing cycle,
including the focused recovery and application-lifecycle amendment. Read
[dataset-campaign/execution-state.md](dataset-campaign/execution-state.md),
[focused recovery](dataset-campaign/focused-recovery.md), and
[the current goal prompt](dataset-campaign/goal.md) before resuming. Select Sol
in the app before submitting the prompt; saving this document starts no worker.
The original planning walkthrough below is historical. Local campaign authority
does not authorize real printer/supplier writes, purchases, publication or release.

## Reviewer walkthrough

1. Confirm the ten titles and ordering in [workflow-acceptance.md](contracts/workflow-acceptance.md).
2. Review the dropdown/instance behavior in [template-api.md](contracts/template-api.md) against `docs/contributing/workflow-ui-integration.md` and the feature-080 north star.
3. Confirm the 3D workflow treats image scale, supports, slice output, printer transfer, receipt, and physical print as separate facts.
4. Confirm the Pi workflow pins the board model/source and rejects substituted CFD geometry or theoretical-only values.
5. Confirm the sheet-metal workflow preserves the recovered design-check/rework/DXF gates and requires a distinct human supplier handoff without ordering or payment.
6. Review [approval-resume.md](contracts/approval-resume.md), especially exact-subject invalidation and unknown-outcome reconciliation.
7. Confirm social-media support creates a local evidence package only and that the plan contains no usability study.

## After explicit plan approval

Run `/speckit-tasks`, then `/speckit-analyze`. Resolve all high/critical findings before `/speckit-implement`. Implement the UI milestone first and verify the served build by entering a normal workspace and using Workflow/Workflows. Preserve every existing authoring acceptance action.

For each server integration, follow `docs/mcp-catalog/mcp-server-testing-process.md`. Store qualification evidence separately from template/run evidence. A discovered or protocol-responsive server stays unverified until a real backend result, Wright execution, artifact check, and independent engineering assertions pass.

Use [implementation-goal.md](implementation-goal.md) as the proposed implementation goal after plan approval.
