# Experimental chat pilot setup

Use only an isolated Wright checkout, database, workspace root and credentials.
These instructions are for the GB10 Linux ARM64 qualified lane. They do not change
an installed Wright or authorize production use, physical work or protected runs.
Read [exceptions](exceptions.md) first: remaining Codex native tools are permitted
experimentally; zero-tools has FAILED. Authoring/workflow model execution is gated.

The optional root `codex` extra pins openai-codex and openai-codex-cli-bin to 0.162.1.
A separate worker venv avoids changing the Wright application's dependency environment:

```bash
uv venv --python 3.13 /tmp/wright-codex-worker
uv pip install --python /tmp/wright-codex-worker/bin/python openai-codex==0.162.1 openai-codex-cli-bin==0.162.1
```

Create a fresh absolute private runtime root and `home` directory, owner-only 0700.
Supply suitable authorized authentication only to that isolated home; its auth file
must be private and must not be a symlink to personal CODEX_HOME. The pilot used a
private 0600 copy of authorized ChatGPT auth.json, verified the original byte digest
unchanged and removed its disposable copies. Do not print credentials. Never silently
switch to API-key billing, a different account/model or another provider.

For an isolated API process, set:

```bash
export WRIGHT_CODEX_CHAT_EXPERIMENTAL=1
export WRIGHT_CODEX_PYTHON=/tmp/wright-codex-worker/bin/python
export WRIGHT_CODEX_STATE_ROOT=/absolute/private/codex-runtime
export WRIGHT_CODEX_MODEL=gpt-6.1-sol
export WRIGHT_CODEX_EFFORT=high
export WRIGHT_CODEX_AUTH_METHOD=chatgpt
export DATABASE_PATH=/absolute/isolated/wright-state.db
export WRIGHT_WORKSPACES_DIR=/absolute/isolated/workspaces
export WRIGHT_SECRETS_PATH=/absolute/isolated/secrets.json
export WRIGHT_API_MCP_AUTOSTART=0
```

Use Wright's existing authentication/bind/origin settings for the API. The gateway
uses Wright's existing authenticated control-plane principal convention; model/tool
arguments cannot select a principal or workspace. Do not add external MCP configs
or credentials to the Codex home. Production startup rejects a pre-existing
config.toml in this private home. Only ChatGPT authentication is enabled; API-key
authentication and native Windows startup deliberately reject pending qualification.
Do not point these variables at live user state.

Choose **Codex (experimental)** in the workspace's **New chats** selector. Existing
sessions keep their saved platform. A model/effort or instruction/configuration
change requires a new session; existing sessions reject drift. The model selector
for a Codex session is read-only. Catalog presence alone does not establish access.

Only text chat and the fixed `wright__workspace_status` read are qualified. Missing
auth/runtime/configuration is an explicit failure. Attachments, confined authoring,
workflow execution, native external MCP and dollar accounting are not enabled.

For reproducible local protocol proof, run the fresh-output loopback probe:

```bash
.venv/bin/python specs/084-codex-platform-integration/probes/qualify_chat_pilot.py --sdk-python=/tmp/wright-codex-worker/bin/python --output=/tmp/new-codex-chat-proof
```

The authenticated probe sends exactly two small turns on gpt-6.1-sol/high, with a
240-second overall bound, temporary private credentials, source-file hash checks
and no automatic failed-turn retry. It uses ChatGPT access, not an API-key fallback:

```bash
.venv/bin/python specs/084-codex-platform-integration/probes/qualify_authenticated_chat.py --sdk-python=/tmp/wright-codex-worker/bin/python --auth-file=/absolute/authorized/auth.json --output=/tmp/new-codex-auth-proof
```

All probe outputs must be new directories outside Wright's protected application
paths. Restart recovery reads the exact known native turn; an unacknowledged turn
or never-materialized thread is held for reconciliation. Never replay an uncertain
effect. POSIX cleanup is locally qualified; Windows cleanup/ACLs and other host lanes
require the [separate handoff](windows-handoff.md).
