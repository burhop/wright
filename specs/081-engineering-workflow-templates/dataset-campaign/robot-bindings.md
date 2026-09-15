# Robot tracking campaign: selected offline runtime

Three fresh real template instances are saved and enrolled, without dispatch, in
`.local-run/feature-081-live/campaign-execution/robot-attempt-002.json`.
Each has the original `inspect_bag`, `align_and_measure`, and
`evidence_diagnosis` semantic IDs and both original order connections. Added
normalization, diagnosis drafting, and final collection make six canonical
steps. The original engineer review is a durable local-review checkpoint;
collection executes only after that checkpoint resumes.

The reusable binding is
`tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json`.
The preparer stages every original CSV, profile, prompt, business context and
route PNG unchanged, plus an explicit survey/time JSON contract and authored
operation source. It never supplies a precomputed bag, trajectory or metrics.
The real workflow creates those files under its own fresh attempt.

Attempt 001 is preserved: cases 01 and 02 actually generated bags, but the batch
stopped on response formatting and oversized inline inspection respectively;
case 03 remained unstarted. The corrected attempt 002 requires the actual bag,
metadata, conversion manifest, timeline, overlay and metrics. Copied operation
source remains pinned input/ancillary provenance, not a generated deliverable.
Native ROSBag still performs actual bag metadata, all five topic-schema calls,
and real sample extraction before metrics. Extraction is bounded to two messages
per topic; the saved inspection projects relevant fields below 12,000 characters
and records omitted covariance fields. Full records remain in the same-run bag,
which the unchanged fixed metrics operation reads in full. Neither uploaded data
nor enrolled attempt 001 operation source was altered by these preparation fixes.

## Selected setup and actual qualification

Followed `docs/mcp-catalog/mcp-server-testing-process.md`. A fresh Intel Linux
Wright image `sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`
was used. Only selected dependencies were installed into disposable virtual
environments; the base image was unchanged:

```sh
uv venv --python 3.12 /tmp/robot-env
uv pip install --python /tmp/robot-env/bin/python rosbag-mcp==0.2.0 mcp==1.28.1 rosbags==0.11.5 numpy==2.5.3 matplotlib==3.11.1 pillow==12.3.0
```

The resulting interpreter is Python 3.12.12. The existing clean qualifier passed
three direct String-message queries and both Wright/Hermes gateway layers.
The new opt-in `scripts/qualify-robot-campaign.py` then passed real numeric
conversion, native schema/range extraction, and computed results for all three
uploaded scenarios. This prerequisite test is not a canonical campaign run.
Full local evidence is under
`.local-run/feature-081-live/robot-campaign/actual-mcp-probe-003/evidence.json`;
the redacted scoped summary is
`docs/mcp-catalog/evidence/feature-081-robot-campaign.json`.

The persistent selected runtime is `wright-081-robot-runtime`. It mounts only
the disposable demo workspace at `/workspace` read/write and repository scripts
at `/operations` read-only. No ports, physical robot connection, ROS graph or
controller is opened. Its two normal API registrations are:

| Role | Local server ID | Selected tools |
|---|---|---|
| Native ROSBag | `413c3100-cd94-4436-b34a-5fa0373985a9` | `bag_info`, `get_topic_schema`, `get_messages_in_range`, `get_message_at_time` |
| Fixed offline operation | `c7279493-594a-4e17-b38e-673395a5f987` | `normalize_csv_to_ros2`, `calculate_tracking_metrics` |

Both use `docker exec -i` into that container. Native executable is
`/tmp/robot-env/bin/rosbag-mcp`; the companion executable is
`/tmp/robot-env/bin/python /operations/robot_tracking_mcp.py` with
`WRIGHT_ROBOT_WORKSPACE=/workspace`. They were registered with
`default_enabled:false`, installed, enabled only in demo session
`wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a`, and activated through normal
API operations. Discovery returned 31 native tools and two fixed operations.
No original catalog entry or public curation claim was changed.

`scripts/install-robot-campaign-mcp.py --execute --output <new-report.json>`
records each API result. Reuse its report on interruption to avoid duplicate
registration. The companion has no arbitrary Python execution tool. It checks
that the staged source hash equals its actual operation source and confines
inputs, source and output to the same explicit attempt. Existing output
directories fail closed. Exact discovered schemas are retained in
`runtime-registration.json`, each staging manifest and the integration grant.

## Observable normalization and engineering treatment

All five CSV topics become real ROS2 SQLite/CDR messages using the Humble type
store. Nanosecond timestamps derive with decimal arithmetic from the fixed
2026-01-01 UTC epoch. Recording timestamps use acquisition `time_s`; external
headers use `timestamp_s` unchanged. Events retain their complete original CSV
row as JSON text in `std_msgs/msg/String`. Invalid external poses are omitted,
never set to zero. Unknown odometry covariance is IEEE NaN, explicitly
documented as unknown rather than fabricated measurement confidence.

| Case | Supplied survey/time treatment | Retained external samples |
|---|---|---:|
| Aisle seam | Already map-aligned and common clock | 61 |
| Corner | `x_map=x_tracker-1`, `y_map=y_tracker+2`; subtract 0.150 s from header once | 61 |
| Figure eight | Common map/clock; omit invalid poses at 14.0–16.0 s | 56 |

Native `bag_info`, `get_topic_schema` and bounded five-topic message extraction
execute before analysis. Native `analyze_path_tracking` expects `nav_msgs/Path`
and does not apply this uploaded survey/clock contract; it is deliberately not
used as evidence for these PoseStamped uploads. Native `analyze_wheel_slip`
also overstates what velocity disagreement establishes. The authored fixed
operation instead reads actual CDR messages, samples the planned path at
corrected external measurement times, unwraps planned yaw, wraps yaw residuals,
and does not interpolate missing external measurements.

NumPy and scalar reductions independently compute position/lateral RMSE and
enforce the original one-percent comparison. Event content is checked against
its bag timestamp and correlated with the continuously recorded odometry within
the original one-sample bound. This catches execution and consistency problems;
it is not a newly claimed complete engineering-validation suite. The campaign's
content-validity metric remains zero.

Each attempt produces actual bag DB3/YAML, conversion source/manifest, native
inspection evidence, timeline CSV, unaligned/aligned trajectory SVG, metrics
JSON, analysis source, human-context-grounded diagnosis Markdown and a final
artifact index after review. The manifest hashes the original CSVs, schemas,
serialization version, source and output bytes. The original CSVs are inputs;
they are not counted as generated engineering outputs.

## Problems, results and retest

Problem: the clean image's interpreter did not expose mounted API/adapter
sources. Solution: set explicit repository package `src` paths for the existing
qualification harness, without changing the base. Result: direct and both
gateway probes passed.

Problem: an early probe used the nonexistent `list_topics` alias; ROSBag returns
an error string without setting `isError`. Solution: validate tool names against
actual `tools/list`, use `get_topic_schema`, and parse actual message counts.
Result: probe 001 is not valid schema evidence; probes 002 and final 003 pass.

Problem: broad native navigation tools do not implement supplied frame/time
alignment. Solution: retain native inspection and add the source-bound fixed
offline operation. Result: all three cases generated real artifacts; no fixture
outputs or physical actions were substituted.

Three canonical binding tests pass. Three selected-environment operation tests
pass, covering preserved 150 ms header offsets, one-time correction refusal,
unknown covariance, missing-pose exclusion, output replay refusal, source drift
and cross-attempt/path escape rejection. The selected tests intentionally skip
when ROSBag dependencies are absent from a general development environment.

To prepare a later attempt, first create a new template instance through the
normal API, then run `scripts/prepare-robot-dataset-campaign.py` with
`--instance-source`, `--scenario`, `--attempt`, the actual `--workspace-root`, and
`--server-map .local-run/feature-081-live/robot-campaign/runtime-registration.json`.
Use `scripts/enroll_engineering_dataset_case.py` to save and enroll the exact
source/input identities. The root campaign runner serializes actual dispatch.
