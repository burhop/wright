# Quickstart: Execute the Rivet Compatibility Spike

This guide is used only after the human approves the slice plan and generated task list.

## Preconditions

- Be on `055-rivet-compatibility-spike` with the approved planning commit.
- Confirm the only prerequisite is umbrella commit `21d2982` or its approved descendant.
- Use an isolated working/cache location owned by `integrations/rivet/spike/`; never point the fixture at a user workspace, Wright data root, or production package directory.
- Use mock host operations and synthetic workspace identities only.

## Execute in Order

1. Run baseline acquisition and record source/package/lockfile/checksum/license inputs.
2. Build the candidate editor and generate the static asset manifest.
3. Run two editor instances with distinct synthetic workspace identities; record IO, dataset, native API, browser persistence, plugin, and debugger findings.
4. Run the Node fixture with a mock external call; capture lifecycle, cancellation, and debugger observations.
5. Repeat the supported fixture path with outbound runtime requests denied and capture the request log.
6. Produce license/security/platform/size inventories.
7. Run the full compatibility matrix twice from clean inputs.
8. Clean spike-only generated material and prove no production/user data changed.
9. Publish the evidence bundle and complete the go/conditional-go/no-go decision.

## Stop Conditions

Stop immediately and do not workaround by adding production code if any of these occur:

- no per-instance workspace-safe provider injection path exists;
- Node execution cannot be bounded/cancelled sufficiently for a later supervised runner;
- the only bridge bypasses Wright gateway/approval control;
- offline runtime downloads remain necessary;
- a license/security/platform issue lacks an accepted mitigation;
- a patch is too broad or cannot be reproduced.

Record the evidence and request an umbrella-plan amendment instead.

## Expected Handoff

A go or conditional-go result supplies the exact candidate baseline, constraints, test fixture, matrix, patch status, risk register, and required controls to the next slices. It does not itself create a workflow tab, persist a real workflow, expose a tool, or ship a runtime dependency.
