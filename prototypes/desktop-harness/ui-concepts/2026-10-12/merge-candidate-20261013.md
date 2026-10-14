# Current-dev desktop prototype merge candidate

This PR delivers one experimental host-adaptive workflow UI beside the OpenAI
desktop conversation. Wright retains accepted source, durable execution,
validation, permitted tools, checkpoints and recovery. The shared canvas and
editor capabilities remain common with Hermes. The host supplies conversation
reasoning; no SDK model worker or second executor is added.

The local candidate is rebased on dev `c1a8d009` (SteveCAD PR151). It rebuilds the
self-contained panel with locked JS SDK1.32.1 and ext-apps1.7.5, MCP Python1.28.1,
Python3.13.12 and isolated Node22.22.2. The fresh resource is
`08f146c976f273936b218408edd380e6936860e38d10ce2e0d9f054a1f0906ca`,
2,185,196bytes, with no external assets. Candidate0.5.0 retains the same18tools;
it is prepared, not installed. Installed0.4.0 and its state remain preserved.

Both actual SteveCAD sources are copied byte-exactly into a new test workspace,
opened through MCP and the served Workflows control, and captured with no browser
JavaScript errors. Unsupported preparation is explicitly rejected with503 before
any model/provider call. These are source/UI tests, not CAD execution or native
Windows0.5.0 acceptance. Existing engineering evidence and genuine review waits
are untouched. See `working-view-evidence/candidate-source-ui-0.5.0.json` and
`working-view-evidence/stevecad-source-ui-0.5.0/`.

Focused prototype/dispatch checks pass71; previous rebase checks pass113 with
five installed-Hermes-source skips. All repository push/merge gates and current
PR CI still apply. Formatting preflight found27frontend files and onePython
file; only changed candidate files were formatted. No gate was relaxed.

SteveCAD is not connected in this prototype state. The user has been asked for
an already-authorized GB10 instance, or whether a fresh OAuth connection is
needed. Live gateway/CAD qualification depends on that information. The default
profile remains digital text/checkpoints; generated process-UI authoring,
SteveCAD CAD/image/export execution, agent-global native-tool control and
automatic chat wakeup/reasoning restart remain unqualified or unavailable.
Actual harness model/build/usage remain unreported. Do not substitute Hermes or
claim a source-view test qualifies the full engineering chain.

The best new images are `stevecad-native-source.png` and `stevecad-source.png`.
Label them **GB10 browser prototype**. Suggested caption: “SteveCAD workflows on
Wright's shared canvas. We're testing the desktop experience while keeping
execution and evidence under Wright's control.” No social publication is performed.
