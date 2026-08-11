# Rivet workflows in Wright

Wright embeds the Rivet 2 graph canvas while keeping workflow files, review
state, execution, AI credentials, and MCP policy under Wright's control. The
canvas and Wright chat operate on the same saved workflow revision.

## AI availability

The sparkle controls use the Codex subscription already configured in Hermes.
They do not require or accept an OpenAI API key. Wright gives the browser a
short-lived token for a same-origin compatibility endpoint; only the Python
host can attach the long-lived Hermes credential. If Hermes is unavailable,
the canvas remains usable for editing and saving and shows an unavailable AI
indicator.

This path still uses Hermes's agent loop, so model time dominates latency. It
will not be as fast as a raw OpenAI API request. Wright starts progress
immediately, avoids additional model hops, and records bridge, upstream,
translation, MCP, and runner timings without recording prompts or credentials.

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
revision and digest to match the UI. The current revision must also have a
durable `approved` review. Progress, cancellation, bounded terminal output,
duration, and failure reason are projected back into the canvas toolbar.

Editing and saving creates a new revision, which requires a new review before
it can run. This prevents either the canvas or an agent from running changes
that were not the reviewed bytes.

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

Creation and execution remain subject to Wright gateway approval. Execution
also requires the exact saved revision/digest and its durable workflow review.
The MCP and canvas call the same runner and persist the same bounded run/event
records. Disabling this managed server preserves all other MCP registrations.

Enabling Rivet Workflows in the workspace MCP selector is the operator's scoped
grant for revision-checked Rivet creation and graph edits from Wright chat. It
does not grant generic workspace writes or machine control. Running still
requires the exact current revision to be approved separately in the workflow
review UI; disabling Rivet Workflows revokes the scoped chat-write grant.

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
```

Rollback does not require changing Hermes. Disable `WRIGHT_RIVET_AI_ENABLED`
to retain local editing without sparkle AI, disable runner/operations to block
execution, or disable the managed `rivet-workflows` server to remove chat
tools. Stop the owned editor/runner processes to revoke their ephemeral tokens.
Workflow files, reviews, and prior bounded run history remain intact.

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
[`specs/067-rivet-hermes-ai/quickstart.md`](../specs/067-rivet-hermes-ai/quickstart.md).
