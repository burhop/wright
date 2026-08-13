# Quickstart: Rivet Workspace MCP Gateway Execution

This acceptance guide is designed for deterministic local validation. It does not require proprietary CAD software, paid services, credentials, GPUs, network access, or hardware.

## 1. Discover two workspace MCPs

1. Start Wright with Rivet workflow operations and the local deterministic MCP fixture profile enabled.
2. Open a test workspace containing the reviewed multi-MCP Rivet project.
3. Enable fake server Alpha and fake server Beta only for this workspace. Both expose an unqualified `inspect` tool with different schemas.
4. Open the workflow capability-binding step.

Expected:

- Discovery shows `alpha__inspect` and `beta__inspect` as separate stable identities.
- Each entry shows server revision, schema digest, validation evidence, risk/approval state, and compatibility.
- No child command, URL, environment, credential, or bearer token is shown or written to the workflow.
- A second workspace without those grants cannot see or bind them.

## 2. Review exact bindings

1. Bind node `inspect-part` to `alpha__inspect`.
2. Bind node `analyze-load` to `beta__analyze`; this fixture tool requires an exact-call approval.
3. Review the selected graph and approve the workflow revision.

Expected:

- The review displays workflow digest, graph, node-to-tool mappings, schema/server/validation identities, argument constraints, units/material assumptions, and policy effects.
- The stored review contains a canonical binding-set digest.
- Changing the project, graph, node, tool schema, server revision, validation evidence, or workspace enablement marks the review stale and disables Start.

## 3. Execute through Wright

1. Start the exact reviewed run.
2. Observe Alpha complete first and its structured result flow to the correct Rivet node.
3. When Beta reaches its required gate, approve that exact node/tool/argument set in Wright.
4. Let the workflow complete.

Expected:

- The runner receives only reserved node handles, the exact loopback bridge origin, and an opaque run token.
- Both calls appear in gateway audit evidence and fake-child receipt logs with the same workspace/session/run correlation.
- Approval is required only for Beta and cannot be reused with changed arguments.
- The terminal Run Manifest identifies the exact review, bindings, child calls, approvals, outputs, and artifacts without containing a usable token or secret.

## 4. Prove denied calls never reach a child

Repeat start/call attempts with one mutation at a time:

- disable Alpha for the workspace;
- use another workspace/session;
- remove review;
- change a node to an unbound handle;
- change Alpha's schema or server revision;
- use an expired/replayed token;
- make the tool name dynamic;
- change approved Beta arguments;
- attempt another call after cancellation.

Expected: every attempt returns a stable attributed reason and the target fake child records zero receipt for that call.

## 5. Cancel a slow child

1. Run the fixture graph using Beta's cancellable slow tool.
2. Cancel from Wright after the first child-progress event.
3. Configure one variant to acknowledge cancellation and another to ignore it until its own deadline.

Expected:

- Wright revokes run authority before stopping the runner.
- The gateway sends explicit cancellation to the active child request.
- No later node begins, and a late child result cannot publish a success artifact or change terminal state.
- The acknowledging variant records clean cancellation; the ignoring variant records truthful residue and recovery guidance.

## 6. Prove specialized lifecycle parity

Run the deterministic panel-backed BREP double and host-bridge double through the same workflow bridge.

Expected:

- Wright owns preparation, visible-panel/host status, progress, failure, cancellation, and cleanup.
- Rivet sees only the same provider list/call/result contract used by ordinary fake MCPs.
- Child lifecycle configuration and credentials never enter the graph or runner request.

## 7. Inspect UI and evidence

Verify keyboard-only binding, review, start, approval, cancellation, stale-recovery, and run-timeline journeys at wide and narrow widths. Confirm stable `data-testid` controls, text plus color status, focus restoration, live-region progress, and no secret-like values in page text or browser logs.

## 8. Optional live validation

Live probes are separate from ordinary acceptance:

- BREP: explicitly enable the installed, current validated BREP capability and run a read-only/status-oriented workflow.
- Solid Edge or another available host application: use its separately installed/versioned MCP and an explicitly enabled workspace binding on a compatible host.

Record environment, server revision, validation evidence, limitation, and cleanup truthfully. Do not accept licenses, install proprietary applications, supply credentials, contact paid services, or perform physical/machine actions merely to make a test pass.

## 9. Rollback

Disable Rivet MCP execution/authority issuance and restart Wright.

Expected:

- Existing non-MCP Rivet workflows still review and run.
- Historical bindings/manifests remain readable but no old token is reusable.
- MCP graphs fail closed with an actionable feature-disabled/review-required state.
