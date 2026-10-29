# ROSBag MCP and the offline Robot Tracking Diagnosis example

Updated 14 October 2026. **GB10 ARM64 offline provider qualification passed**, distinct from
historical Linux x64 catalog evidence. No robot connection or physical action.

## Identity and setup

The independent packaged provider is [rosbag-mcp 0.2.0](https://pypi.org/project/rosbag-mcp/0.2.0/).
Use the [existing setup recipe](../mcp-server-setup-recipes.md#rosbag-mcp-packaged-replacement-rosbag-mcp-pypi)
and [historical clean Linux x64 evidence](../evidence/curation-2026-09-09/rosbag-pypi-linux.json).
Pins: MCP 1.28.1, rosbags 0.11.5, NumPy 2.5.3, Matplotlib 3.11.1, Pillow 12.3.0.
The historical wheel SHA-256 is
`92f8538df74b7f73ed797d25d0242fa6c03ea68978ac221757fa211337ee1ed0`.
Do not infer ARM64 availability or current engineering execution from that record.

Selected dependencies belong in an isolated provider environment/container, never
the Wright base image. No credentials are needed for offline bags. Use a fresh
workspace containing copied datasets; do not attach old campaign state, robot
networks, devices or the Docker socket to the provider.

## Ownership and meaningful handoffs

The existing `scripts/robot_tracking_mcp.py` exposes Wright's previously implemented
offline operations, not a replacement ROSBag vendor protocol. It converts the
original CSV samples to a real ROS2 bag, then computes aligned metrics from that
same bag. The independent ROSBag server inspects metadata, five topic schemas and
bounded samples. The desktop model must base its diagnosis on actual observations;
Wright owns the accepted process, validation, run and human review.

The existing `scripts/qualify-robot-campaign.py` is a direct provider qualification
probe only. It copies all three datasets, preserves invalid external observations
as missing messages, checks original topic counts, and records actual outputs.
A successful probe does **not** establish a desktop-driven workflow or completion
of its genuine review. The canonical template still needs visible local bindings.

## Validation and recovery

Keep the original frame/clock alignment contract, 1% independent metric tolerance
and one-sample event comparison. Preserve plots, timeline, metrics and original
CSV hashes. Do not infer wheel slip from command/velocity disagreement alone.
Outputs must be new; the existing offline provider refuses an already existing
output directory. Staged operation source must hash-match the executing source.
After uncertain tool results inspect the same output/run before choosing recovery;
never automatically rerun conversion or overwrite its evidence.

Missing-bag errors may arrive inside ordinary MCP content rather than `isError`.
Inspect returned content and actual files. Only exercised calls are qualified.
Historical source-checkout packaging is broken; keep the packaged replacement and
MCP 1.x pin rather than silently changing providers. No new provider bug report has
been submitted by this workstream.

## Current evidence

See the desktop prototype [progress ledger](https://github.com/burhop/wright/blob/37746c7b20ee1146c55e67dc965aa2b0a9e9992b/prototypes/desktop-harness/workspace-home-progress.md)
for the current run and remaining gaps. Provider installation, tool discovery,
actual offline analysis, canonical workflow execution and Windows UI acceptance
are separate evidence boundaries. Current observed GB10 versions/results follow below.

### 14 October 2026: GB10 ARM64 provider proof passed

Fresh selected-provider execution in the unchanged Wright baseline image
`sha256:6c5ebe4d1812e9bc4f6fc7d857a21ee2ad6488f63c0128dabc12fc9535d9b99f`
completed all three original datasets, 23:10:58–23:11:14 UTC. Python 3.12.12;
all six package pins above installed successfully. The full dependency freeze is
`/tmp/wright-desktop-robot-provider-20261014-03/versions.txt`. The container exited0;
no host packages, live provider registration or protected campaign was changed.

Actual calls: offline normalization, independent ROSBag `bag_info`,
`get_topic_schema`, bounded `get_messages_in_range` for all five topics, and
existing offline `calculate_tracking_metrics`. The probe checked original counts
(61 external observations in cases01/02, 56 in case03, one event each). Computed
position RMSE was 0.0141132m, 0.1061394m and 0.00861454m respectively. Independent
metric differences were below the unchanged 1% tolerance. All event/sample time
differences were zero; case03 retained its 13.5–16.5s missing interval. These are
synthetic dataset measurements, not physical robot certification or causal proof.

Full evidence and fresh bags/plots: `/tmp/wright-desktop-robot-provider-20261014-03/provider-proof/`.
The [compact receipt](https://github.com/burhop/wright/blob/37746c7b20ee1146c55e67dc965aa2b0a9e9992b/prototypes/desktop-harness/robot-provider-arm64-evidence.json)
records hashes and exact scope. The [reproducible launcher](https://github.com/burhop/wright/blob/37746c7b20ee1146c55e67dc965aa2b0a9e9992b/prototypes/desktop-harness/robot-provider-qualification.sh)
is ARM64/GB10-specific and retains the stopped container. This selected-container
provider proof does not rerun the catalog's full Intel/gateway matrix or qualify
a desktop-driven workflow.

Setup lessons: the read-only image's home cannot hold uv-managed Python. Set
`UV_PYTHON_INSTALL_DIR` and cache directories to private writable storage. The
selected runtime's temporary mount must permit executable binaries; explicitly
use `rw,exec,nosuid` while preserving read-only root, non-root user, no capabilities
and resource limits. Attempts01/02 terminated before useful provider execution
and remain intact. A Pydantic forward-reference warning was observed; actual
protocol/backend calls still passed. No provider defect is inferred from it.

### 29 October 2026: current isolated provider requalification

The desktop-engineering candidate built a separate selected-provider image
`sha256:c11294f132cade3fb8846d5e85886c7eaf0c68e350c9956cea23acdadaabdd02`
using the previously qualified exact dependency freeze and current offline
operation source. All three copied datasets passed the existing direct probe on
ARM64 with networking disabled, non-root execution and a read-only root. The
original 1% independent metric and one-sample event checks remain unchanged;
case 03 retained its missing interval. Source, result hashes and limits are in
`prototypes/desktop-harness/engineering-experience/evidence/robot-provider-current/`.
This is provider evidence only: current Wright gateway registration, canonical
workflow execution/review and Windows acceptance are still unverified.

The fresh Robot regression workspace subsequently completed normal command
preview, setup-plan approval/application, protocol validation and workspace
enablement for the pinned ROSBag server and existing offline operations. ROSBag
advertised 31 tools. Invocation approval remains false; no canonical run started.
The current example's separate AgentCAD corrective stage still has the ARM64
prerequisite limitation described in its guide. Exact scoped setup identities are
in `prototypes/desktop-harness/engineering-experience/evidence/robot-provider-current/workspace-setup-receipt.json`.
