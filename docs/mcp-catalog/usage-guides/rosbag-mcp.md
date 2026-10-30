# ROSBag MCP usage guide

Last updated: 27 October 2026. Status: historical Linux x64 known-message retrieval
verified; customer009 installed and passed onboarding on native Linux ARM64.
Prepared returning-customer013 then made four actual read-only recording calls
after normal gateway recovery. That establishes narrow bag/topic/sample retrieval
on this ARM64 candidate; numeric analysis, export and a complete robot diagnosis
remain unverified by this campaign.

## Identity and sources

- Independent package: [rosbag-mcp 0.2.0](https://pypi.org/project/rosbag-mcp/0.2.0/),
  wheel SHA-256 `92f8538df74b7f73ed797d25d0242fa6c03ea68978ac221757fa211337ee1ed0`.
- Catalog identity: `rosbag-mcp-pypi`, alias `rosbag-mcp`.
- Reuse the exact command and pins in the
  [setup recipe](../mcp-server-setup-recipes.md#rosbag-mcp-packaged-replacement-rosbag-mcp-pypi).
- [Historical qualification](../evidence/curation-2026-09-09/rosbag-pypi-linux.json)
  records Python 3.12.12, MCP SDK 1.28.1 and rosbags 0.11.5 in an isolated Intel Linux
  container. It is not native ARM64 or current-platform qualification.

## Installation and readiness

No ROS installation, CAD application, credentials or physical robot is required
for the documented offline SQLite bag operation. A readable real ROS 2 bag and its
metadata are required; CSV files renamed to .db3 are not a bag. Wright's existing
catalog uses isolated Python 3.12 via `uv` and explicit SDK/data-stack pins. Inspect
current computer setup and the literal install plan before connecting; retain
unknown-platform warnings. Package installation and tool discovery do not prove
correct diagnosis. Do not add provider packages to the standard VM/base image.

Customer008 reached installation review but was blocked because Wright's catalog
omitted the license. The exact pinned wheel's METADATA declares `License-Expression:
MIT`, matching the versioned PyPI metadata. The catalog now records MIT; no publisher
acceptance was supplied. This corrects metadata only, not ARM64 support or engineering
qualification. The [primary-source receipt](../../../artifacts/first-contact/synthetic-beta-003/receipts/rosbag-020-license-source.json)
records both source identities and the retained wheel metadata. The wheel contains
no separate license file; this observation identifies the publisher's declaration,
not an independent legal assessment. Customer009 recovered this installation barrier on immutable011; its exact
[report](../../../artifacts/first-contact/synthetic-beta-003/session-records/gh3-engineer-009/report.json)
and [onboarding screen](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-engineer-009/e00149.png)
retain the observation. The existing catalog qualification scope is unchanged.

## Verified workflows and successful calls

Historical qualification initialized the MCP session, discovered 31 tools and
called `bag_info` and `get_message_at_time` in three fresh direct sessions and
through both Wright gateway layers. A two-message `/chatter` bag returned `hello`
at Unix time 1700000000.0. Independent SQLite/CDR inspection confirmed two messages,
timestamps 1700000000000000000/1700000001000000000ns and hello/world payloads.

The recorded `get_message_at_time` schema requires `topic` (string), `timestamp`
(number, Unix seconds); optional `bag_path` (string) and `tolerance` (number).
Example historical input: topic `/chatter`, timestamp1700000000.0, bag_path pointing
to the actual qualified bag. Rediscover current contracts before binding; do not
invent this file on a different machine or treat tool-count/version text as proof.
Full exact schemas and outputs remain in the qualification evidence.

For the existing Robot Tracking Diagnosis example, preserve its full requirements:
actual recorded topics, frame/clock contract, numeric alignment and metrics,
timeline, trajectory chart and evidence-linked diagnosis. Known-message retrieval
alone does not meet that job. The fictional supplied CSV scenario includes its
[conversion mapping](../../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/bag-conversion.md).
The existing `scripts/robot_tracking_operations.py::convert_csv_to_bag` is input
preparation, not evidence that this provider or a Wright workflow ran. Retain source
hashes, epoch, message schemas, unknown covariance and timing offsets. Later tools
must consume actual recorded outputs, not an invented model summary.

Customer013's prepared connection visit took6:11.938, excluding installation of
Wright and workspace preparation. The exact [call/result records](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-tool-connect-013/recorded-provider-calls.json)
and [reconciliation receipt](../../../artifacts/first-contact/synthetic-beta-003/receipts/gh3-tool-connect-013-provider-use.json)
confirm bag_info, two get_message_at_time calls and get_messages_in_range. The
fictional bag contained245 messages across five topics over30seconds. Actual pose
query: topic/wright_test/external_pose, timestamp1767225615, tolerance0.5seconds,
with bag_path/home/customer/Downloads/robot-floor-seam-v1/recording/. It returned
map-frame position(3.3,0.045,0)m and quaternion(0,0,0,1), recorded at that timestamp.
The event-range query returnedE01, “Front caster crossed taped floor seam”, also
at1767225615. These are retained provider responses, not a model-only narrative.
Do not reuse the machine-local path elsewhere or infer causation from the note.
No managed workflow, complete diagnosis or engineering acceptance was established.

## Pitfalls and recovery

- Keep MCP 1.28.1: the earlier unconstrained range selected incompatible SDK 2.x.
- A missing-bag error appeared in normal text content; `isError=false` did not
  establish success. Inspect actual payloads and exact output files.
- Paths and bag access belong to the installed provider's environment. A host path
  is not automatically available in a container or workspace.
- Customer009 observed ARM64 package initialization and31 discovered tools, but
  Hermes retained its earlier callable list after provider enablement. The requested
  sample retrieval was not attempted at the provider boundary in009. In013, Wright
  detected the changed selection; the customer followed normal foreground gateway
  stop/restart guidance and then made actual retrieval calls. The Active badge still
  preceded chat readiness. This is Wright integration/UI friction, not evidence of
  a provider defect or broad numeric qualification.
- Broader ARM64 engineering behavior and larger-bag performance remain unverified.
  Record the exact blocked step rather than declare a provider defect.
- Reconcile uncertain work before replay, especially any unqualified write/export.

## Validation, authority and limitations

Offline digital analysis only. No connection to production ROS, controller change,
physical operation, engineering acceptance or simulated human review is granted.
Distinguish transport, package installation, actual numeric output and engineering
validity. Preserve exact dataset requirements; correlate events without asserting
causes that the data cannot establish. No content-validity credit from file presence.

## Bugs, follow-ups and maintenance

No provider bug report submitted by this campaign. Source-repository recovery,
maintenance continuity, native-platform setup, broader tools and repeat adoption
remain open. Add fresh exact use and recovery evidence here after an actual
customer run; retain the historical Intel/container scope above.

The later prepared015retry did not reach ROSBag: its early restart advice was
noticed, but Wright's restart-recognition gate persisted after the normal restart.
The gateway registered51tools before two rejected queries; audit/session rows
recorded zero provider calls. This is a separate Wright recovery regression, not
a reversal of013's narrow retrieval evidence or a ROSBag defect. Retained
[failed retry](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-tool-connect-015/details.json).

Prepared017 retried the same connection task after Wright corrected when it
observes the pre-restart gateway identity. The customer independently restarted
from early advice and obtained the same recorded pose/event in6:23.878. The
[actual call records](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-tool-connect-017/recorded-provider-calls.json)
and [reconciliation](../../../artifacts/first-contact/synthetic-beta-003/receipts/gh3-tool-connect-017-provider-use.json)
show set_bag_path,bag_info and get_message_at_time twice. set_bag_path selects
the provider session directory; the remaining calls read the bag. This confirms
the narrow post-restart retrieval path, not a managed run or numerical diagnosis.
The manual terminal handoff and unclear computer-check feedback remain Wright
usability issues. The original beta report is unreviewed; no provider defect was
established or reported.
