# Wright inside the desktop harness — local prototype

Current native-chat private-network viewing evidence is recorded in
[private-lan-access.md](private-lan-access.md). Workspace `dave` and its completed
welcome workflow now open through an automatically established browser session
for the observed Windows device, using the existing Wright UI and authentication
owner. Fresh GB10 browser verification passed; post-change Windows user acceptance
remains separate. Earlier qualification checkpoints below retain their scopes.

The editor now explains queued desktop AI tasks instead of only saying Running.
[Reasoning progress evidence](reasoning-progress.md) records actual native replies,
normal editor Run/reload/completion checks, and the remaining manual chat-turn
boundary. Automatic same-conversation wakeup is not yet qualified.

This prototype connects the actual desktop conversation to Wright's existing
source runtime. It does not start Hermes, another model service, or an SDK agent
worker. The MCP SDK is a transport library, not the reasoning provider.

Development now continues in `/tmp/wright-openai-desktop-harness-prototype-next`.
The original worktree stays clean at local checkpoint `a17acb85` for the prepared
Windows connection experiment; its paths and runtime bytes are unchanged. The
new checkout applies the tested live-owner admission guard and corrects three
formatting issues. Its leased response/action profiles are now qualified for the
specified reconnect/read-only boundaries. A fresh abrupt API-restart probe also
retains the pending response task and rejects a late answer without its live
consumer; automatic interrupted-task continuation and broader cases remain.
Do not point an existing connection or retained run at it automatically.

The final combined source at cb0d11a2 has fresh real-MCP controls for image
preparation denial, ordinary text completion and one exact permitted inspection;
see qualified-final-profile-evidence.json. This does not replace installed
Windows acceptance or the full original engineering runs. completion-audit.md
records the remaining requirements explicitly.

The development MCP lifecycle renews a 30-second lease every 5 seconds. Abrupt
child loss eventually disables connection readiness/new mutation admission;
pending Wright requests remain durable. Heartbeat failure stops the bridge,
without retrying workflow writes. Reconnect uses a new explicit MCP initialization
and reconciles the same live run. Closing a desktop chat may leave its MCP process
alive; chat/panel closure and unattended wakeup require installed-host testing.
Lease liveness does not attest model availability or private conversation state.

`lease_reconcile_probe.py` has separate observation and completion phases. The
observation phase reads an already recorded, confirmed MCP-child loss, checks
expired readiness and denied mutation, and retains the pending run/evidence.
It never initializes a new connection. Completion explicitly initializes MCP,
reads the exact live run/task and submits `lease-desktop-answer.json` once. The
file must contain this desktop's actual answer and original request/binding
digests; no test model or replacement run is supplied. Both phases refuse to
overwrite previous evidence. Observe and reconcile the original run before any
retry; this helper is not automatic API-restart recovery.

The hosted Wright UI omits its chat and model controls. Standalone Wright keeps
them. Existing accepted-source, editor, input, supervisor, recorder and gateway
owners remain authoritative; the bridge never executes the workflow graph.

## What currently works

The isolated MCP protocol client has created a workspace, saved a workflow,
prepared inputs, started a durable run, transported replies authored by this
desktop conversation, and read the completed result. The served browser enters
through Workflows and displays the real workflow and output.

A second digital fixture paused at its declared input, disconnected, survived a
controlled Wright API restart, reconnected, rejected an invalid selection and
completed the same run. Its previous output bytes were retained. Browser reload
also retained the checkpoint/common working view. With the connection absent,
the view correctly blocked continuation; a connected Submit-button walkthrough
is now qualified separately: the actual common-view form submits the declared
synthetic choice and the desktop's next task carries it into the same run. Exact
completed-view reload/close and retained first-output bytes after a durable-wait
API restart are recorded in qualified-connected-checkpoint-evidence.json. The
initial capture's final selector failure is retained; it is not a full capture pass.

Installed-plugin loading and display inside the desktop right panel are not yet
verified. Gateway tasks, CAD/application work, external actions and generated
process-UI authoring remain gated. Full engineering examples have not run here.

## Current editor and original-example readiness checks

The existing browser harness has an opt-in `desktop-authoring` registration for
the current editor. It retains private authenticated evidence, exact served
source snapshots, diagnostics and screenshot reporting. It performs no model
call or workflow run. Full legacy/installed acceptance remains separate.

Prepare a **fresh** private state through the normal template/source owners:

```bash
.venv/bin/python prototypes/desktop-harness/existing_examples_probe.py --state-dir /tmp/wright-desktop-originals-new
.venv/bin/python prototypes/desktop-harness/preview_server.py --state-dir /tmp/wright-desktop-originals-new --port 8114 --web-port 5214
VITE_WRIGHT_WORKFLOW_RECOVERY=1 WRIGHT_WEB_API_PROXY_TARGET=http://127.0.0.1:8114 npm run dev --workspace=apps/web -- --host 127.0.0.1 --port 5214 --strictPort
```

Read `existing-examples.json` for the generated `editor_workspace.workspace_id`.
Use that exact ID in the ordinary hosted workspace URL, with a new evidence root:

```bash
node scripts/recovery/capture_image_redesign.mjs --mode=desktop-authoring --hosted-desktop=true --url=http://127.0.0.1:5214/workspace/EXACT_GENERATED_WORKSPACE_ID?host=openai-desktop --auth-token-file=/tmp/wright-desktop-originals-new/.preview-api-token --evidence-root=/tmp/wright-desktop-authoring-new
```

Do not use the placeholder literally or another workspace. The helper reads the
private token file without placing its value in the command/report. Full network
tracing is omitted in authenticated mode to prevent credential capture; clean
screenshots begin after unlock. To continue selected checks on a saved test file,
use explicit `--only`, `--continue-workflow` and the matching generated `--session`.
Retain failed evidence and reconcile the saved source rather than recreating it.

The original manufacturing/Robot sources and scenario data are preserved as
fresh copies, with no runs/approvals copied. Their catalog definitions are unbound
drafts and retain their explicit readiness blocks. The original full assignment
needs qualified bindings/tools/validation/reviews; these checks never replace it
with a simplified substitute or claim an engineering execution.

## Reproduce an isolated protocol experiment

From the feature worktree, use its locked dependencies. No global installation
or existing user workspace is needed:

```bash
UV_CACHE_DIR=/tmp/wright-desktop-prototype-uv-cache uv sync --frozen --all-packages --all-groups --extra runtime
npm ci --cache /tmp/wright-desktop-prototype-npm-cache
```

Choose a **fresh** state directory and unused API/web ports. Do not delete or
overwrite a previous experiment. Example startup in two terminals:

```bash
.venv/bin/python -u prototypes/desktop-harness/preview_server.py --state-dir /tmp/wright-desktop-experiment-new --port 8101 --web-port 5201 --enable-desktop-bridge
VITE_WRIGHT_WORKFLOW_RECOVERY=1 WRIGHT_WEB_API_PROXY_TARGET=http://127.0.0.1:8101 npm run dev --workspace=apps/web -- --host 127.0.0.1 --port 5201 --strictPort
```

The API writes a private token file and public connection descriptor in that
state directory. Credentials must not enter chat, screenshots, tool arguments
or command-line options. Browser unlock uses the normal authentication flow;
the local MCP helper reads the private credential file directly.

Start the one-task probe:

```bash
.venv/bin/python prototypes/desktop-harness/protocol_probe.py --state-dir /tmp/wright-desktop-experiment-new
```

It exposes the actual bounded task and waits for this desktop conversation to
author `desktop-protocol-answer.json`. That transport spike requires an operator
to relay the displayed request to the desktop; it is not the final installed
plugin experience. Preserve exact request/binding digests and response identity.
The `reply` field contains the task's validated JSON envelope as a string.
Never put a fixture or model-worker answer in that file and call it desktop
reasoning. The probe records its accepted receipt and terminal snapshot.

## Confined read-only gateway experiment

The default bridge still gates tool tasks. Use a fresh private state and free
ports to opt into the separately qualified single-inspection profile:

```bash
.venv/bin/python prototypes/desktop-harness/preview_server.py --state-dir /tmp/wright-desktop-gateway-new --port 8110 --web-port 5210 --enable-desktop-bridge --enable-confined-inspection
VITE_WRIGHT_WORKFLOW_RECOVERY=1 WRIGHT_WEB_API_PROXY_TARGET=http://127.0.0.1:8110 npm run dev --workspace=apps/web -- --host 127.0.0.1 --port 5210 --strictPort
.venv/bin/python prototypes/desktop-harness/mcp_gateway_probe.py --state-dir /tmp/wright-desktop-gateway-new --qualified-read /tmp/wright-desktop-gateway-proof-20261011-02
```

The prerequisite proof is retained on GB10. The helper seeds clean fixture data
and enrolls the existing exact private source/input/schema/output grant through
local test management. Enrollment is not an HTTP/MCP capability or engineering
approval. It first proves that starting without the grant is denied.

The helper shows each actual action task and waits for this desktop conversation
to author `desktop-gateway-action-1.json` and `desktop-gateway-action-2.json`.
Each contains request ID/digests, a stable response ID and a typed `decision`
assistant envelope. The first proposes the exact advertised inspection; the
second derives the result from Wright's observed tool return. Neither helper
supplies an LLM response. Other tool scopes remain unavailable.

The retained proof 05 disconnected after the first accepted proposal because of
a controller polling race. The corrected helper waits for the requested decision
ordinal. `mcp_gateway_reconcile.py` reconnected to that exact run and submitted
only its pending final decision, retaining one successful dispatch. This narrow
reconciliation helper refuses an existing reconciliation record rather than
replaying it. It does not qualify every interruption or uncertain-write case.

The prepared plugin currently targets proof 05's tested profile. It remains a
connection candidate requiring specific live-configuration approval and host
verification; updating local package files does not install the plugin.

The checkpoint probe uses the existing Feature 083 synthetic comparison fixture:

For submission through the **normal working view**, use `--phase ui-continue`
after its start phase reaches a durable wait. That mode keeps MCP live, checks
invalid-input denial and relays the next desktop task; it does not submit the
valid choice. `capture-preview.mjs ... checkpoint-connected` exercises the form.
Use `checkpoint-completed` only for readback of an already-completed exact run;
it never submits or starts. Preserve failed captures and accepted receipts.

```bash
.venv/bin/python prototypes/desktop-harness/checkpoint_probe.py --state-dir /tmp/wright-desktop-experiment-new --phase start
```

It awaits the desktop-authored `checkpoint-first-answer.json`, reaches a durable
input wait, then disconnects. Read its evidence before changing anything. A
controlled restart may stop only that verified owned server, after observing
terminal state, then start the same state/configuration again. Do not restart a
process because an observation timed out.

For this **synthetic fixture only**, prepare `checkpoint-test-choice.json` with
`{"selection":"a"}` or `{"selection":"b"}` and run:

```bash
.venv/bin/python prototypes/desktop-harness/checkpoint_probe.py --state-dir /tmp/wright-desktop-experiment-new --phase continue
```

It first reconciles the same waiting run and unchanged outputs, tests rejection
of `c`, submits the selected test label and waits for the desktop-authored second
reply. A lost response requires inspecting saved receipts; do not restart this
helper or replay an uncertain write blindly.

## Installed-plugin journey to verify next

The approved GB10 plugin 0.1.1 is installed. A fresh native desktop chat,
**Wright desktop prototype on GB10**, completed its actual connection-status
tool with `connected: true`. Read [native-host-connection.md](native-host-connection.md),
[native-fresh-chat-evidence.json](native-fresh-chat-evidence.json) and
[fresh-chat-handoff.md](fresh-chat-handoff.md). The original chat still lacks
tools despite refresh; further journey proof belongs to the fresh chat.
The earlier Windows-wrapper proposal/target remains separate and unchanged.
Never redirect an installed plugin or existing session silently.

After approved installation and actual tool discovery, the desktop agent should:

1. Read `wright_connection_status` and explain missing capabilities.
2. Create a workspace with `wright_workspace_create`; retain its exact IDs.
3. Author ordinary workflow source with the existing language and save through
   `wright_workflow_create`. Read it back; Wright embeds versioned defaults.
4. Prepare inputs with `wright_process_prepare`, then start once using its
   snapshot/digest and a unique request ID.
5. Read `wright_reasoning_pending`, reason about the exact saved task and submit
   its JSON-as-text through `wright_reasoning_answer`.
6. Inspect `wright_process_read`; answer only a declared input through
   `wright_process_respond`. Reviews/external approvals have separate authority.
7. Open the returned hosted URL beside chat. Verify normal Workflows entry,
   editing, saved results and same-run continuation in the actual desktop.

This sequence is a planned installed-plugin walkthrough, not completion evidence.
The plugin's skill carries these boundaries; its prose is not a security grant.

## Evidence and next work

See [plan.md](plan.md), [tasks.md](tasks.md), [evidence.md](evidence.md),
[capabilities.md](capabilities.md) and [gallery/README.md](gallery/README.md).
The retained protocol summary is [qualified-protocol-evidence.json](qualified-protocol-evidence.json).
Do not publish, push, merge, release or perform physical actions from this prototype.

### GB10 browser qualification limitation — 15 October 2026

At 3a1a2007, the remaining full-gate Playwright stage completed with 161 passed,
5 skipped and 18 WebKit launch failures. All 18 failed before page creation: the
installed WebKit 2336 binary lacked `libgstcodecparsers-1.0.so.0` (and dependency
inspection also found missing libavif). Four Ubuntu ARM64 libraries were unpacked
only into `/tmp/wright-webkit-runtime-20261015-01`; an unchanged private browser
copy then aborted with SIGABRT inside libWPEWebKit before opening a test page.
The backtrace and failed attempts remain. The host uses 65536-byte pages; that is
an observed property, not a proven cause. No system package, installed browser
cache, sandbox setting or rendering policy was changed to obtain a pass.

This is not a WebKit pass or a complete green merge-gate receipt. Chromium,
Firefox and desktop-profile results do not qualify WebKit or actual Windows
native-panel acceptance. Current-head CI on a supported host remains required.
See `browser-gate-evidence.json`; raw traces/report archive and retained backend
state are under `/tmp/wright-desktop-gates-20261015-01`. The strict-docs failure
was separately corrected and verified; all Python and 1874frontend tests passed.
