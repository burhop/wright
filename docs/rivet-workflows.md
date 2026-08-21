# Rivet workflows in Wright

Wright embeds the Rivet 2 graph canvas while keeping workflow files, execution,
AI credentials, and MCP policy under Wright's control. The canvas and Wright
chat operate on the same saved workflow revision.

## AI availability

The sparkle controls use the Codex subscription already configured in Hermes.
They do not require or accept an OpenAI API key. Wright gives the browser a
short-lived token for a same-origin compatibility endpoint; only the Python
host can attach the long-lived Hermes credential. If Hermes is unavailable,
the canvas remains usable for editing and saving and shows an unavailable AI
indicator.

This path still uses Hermes's agent loop, so model time dominates latency. It
will not be as fast as a raw OpenAI API request. Wright starts progress
immediately and records bridge, upstream, translation, MCP, and runner timings
without recording prompts or credentials. Invalid structured Graph Builder
actions can require one bounded repair model call.

## Templates and files

Use the book icon in the Rivet toolbar to create a workflow from Wright's
reviewed template catalog. Workflow content remains authoritative at:

```text
<workspace>/workflows/<slug>/workflow.rivet-project
```

The tab label is the workflow filename. Rivet project chrome, provider/key
settings, and unrelated Rivet application areas are not exposed in Wright.

## Running from the canvas

Save the canvas before running. The Run panel accepts an optional graph name
and a JSON object of inputs. Wright re-reads the file and requires its exact
revision and digest to match the UI. A saved revision is ready to run; there is
no separate workflow approval step. Progress, cancellation, retained terminal
outputs, duration, and failure diagnosis appear in the collapsible **Run
Inspector** below the canvas. The main Run icon starts the saved main graph
immediately; the adjacent Run Options control accepts an alternate graph or
JSON inputs.

The inspector has four views:

- **Outputs** renders every retained named result by type, including explicit
  null/no-output states, structured values, safe links, and authorized
  artifacts. Large values show that they were bounded; redacted values disclose
  that redaction occurred. Copy and JSON export use the same safe projection.
- **Steps** shows ordered node/tool execution with text and icons in addition to
  color. Selecting a current step focuses its canvas node. A historical step
  whose node no longer exists is reported explicitly and does not change the
  workflow.
- **Diagnosis** identifies the failed boundary, tool, trace, residue possibility,
  and a plain-language recovery. Schema version 1 offers full saved-revision
  rerun only; it never implies that replaying one external step is safe.
- **History** shows recent runs scoped to this workspace, session, and workflow,
  with their immutable revision identities.

Refreshing the browser does not start another run. Wright finds the same active
run from durable scoped records, resumes incremental inspection from its event
cursor, and stops polling after a terminal state. Collapsing the inspector
returns its vertical space to the canvas while retaining compact status,
elapsed time, and progress.

Output and step completeness are explicit. **Incomplete** means the safe
projection was bounded or older evidence did not contain that field; it does
not change a successful run into a failure. Export technical evidence when a
supportable diagnostic record is needed.

Editing and saving creates a new revision. The run request remains bound to
those exact saved bytes, so a stale browser or agent cannot run a different
revision accidentally.

## Wright-managed MCP

Wright ships one internal `rivet-workflows` MCP. It is workspace-confined by
trusted launch environment supplied by the gateway; workspace paths and IDs
are deliberately absent from tool arguments. It does not belong in the public
engineering MCP catalog.

The namespaced tools visible to Hermes are:

- `list_templates`
- `list_workflows`
- `inspect_workflow`
- `create_workflow`
- `validate_workflow`
- `run_workflow`

Creation and execution require the exact saved revision/digest and remain
subject to Wright validation and workspace MCP policy. The MCP and canvas call
the same runner and persist the same bounded run/event records. Disabling this
managed server preserves all other MCP registrations.

Enabling Rivet Workflows in the workspace MCP selector is the operator's scoped
grant for revision-checked Rivet creation and graph edits from Wright chat. It
does not grant generic workspace writes or machine control. Running still
requires the exact current saved revision; disabling Rivet Workflows revokes
the scoped chat-write grant.

## Configuration and rollback

Native Wright enables the packaged editor and workflow services. Development
launches can control the feature with these default-off flags:

```text
WRIGHT_RIVET_WORKFLOWS_ENABLED=1
WRIGHT_RIVET_EDITOR_ENABLED=1
WRIGHT_RIVET_AI_ENABLED=1
WRIGHT_RIVET_RUNNER_ENABLED=1
WRIGHT_RIVET_REAL_EXECUTION_ENABLED=1
WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED=1
WRIGHT_RIVET_MCP_GATEWAY_ENABLED=1
```

Rollback does not require changing Hermes. Disable `WRIGHT_RIVET_AI_ENABLED`
to retain local editing without sparkle AI, disable runner/operations to block
execution, or disable the managed `rivet-workflows` server to remove chat
tools. Stop the owned editor/runner processes to revoke their ephemeral tokens.
Workflow files and prior bounded run history remain intact.

## Verification

Normal tests use controlled local Hermes doubles and never contact a
subscription. The two live canaries require both the pytest marker expression
and the environment opt-in:

```bash
WRIGHT_RIVET_LIVE_AI=1 uv run pytest -m rivet_live_ai \
  tests/e2e/test_rivet_hermes_ai_live.py -v
```

The canaries make one Rivet-shaped structured tool request and one Wright chat
request using the Rivet MCP. Without both opt-ins they skip before resolving
or contacting Hermes. The complete deterministic recipe is in
the
[`specs/067-rivet-hermes-ai/quickstart.md`](https://github.com/burhop/wright/blob/dev/specs/067-rivet-hermes-ai/quickstart.md)
source guide.
