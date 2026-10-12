# Private LAN view of the native desktop workspace

On 11 October 2026 (America/New_York), the user requested direct private-network
access and explicitly requested bypassing the token-entry screen. The same
accepted workflow and durable run remain authoritative.

The existing Wright web view is available at:

`http://192.168.1.170:5216/workspace/a5c5778b-0546-449b-9136-1af345067703?host=openai-desktop&workflow=canonical&workflowPath=workflows%2Fdave-welcome.workflow.wflow`

The listener admits the observed Windows browser device `192.168.1.178` and the
GB10 host. Other LAN clients and foreign browser origins are rejected. The
original broad-LAN automatic-session restart was rejected by automatic approval
review; the narrower configuration was tested and approved by that review.
Changing the client address is an explicit hosting configuration change.

## Existing owners and interaction boundaries

The isolated `private-lan.vite.config.ts` composes the existing Vite web config.
At startup it privately exchanges the existing credential through Wright's
`/api/auth/session` endpoint. Workspace navigation receives the standard HttpOnly
session cookie automatically. The API credential never enters the browser,
URL, bundle, screenshot or evidence. The loopback API remains authenticated.
Exact admitted origins are translated to the API's already configured loopback
web origin, including WebSocket upgrades. No workflow executor or run-status
owner is added; backend scope, readiness, review and action enforcement remain.

The served browser exposed a pre-existing synchronous editor crash when
`crypto.subtle` is absent on LAN HTTP. The existing SHA-256 hook now catches that
absence and reports its existing unavailable value instead of crashing. It does
not invent a digest or weaken backend source/output verification. Browser
features requiring Web Crypto remain subject to their existing capability checks;
this proof covers opening the editor and viewing the existing completed result.

## Observed qualification

- Existing native tools created workspace `dave`, saved and ran
  `workflows/dave-welcome.workflow.wflow`, and accepted this conversation's reply.
- Run: `25080febba0741658ba9813a4e7497ae`; native readback remains `completed`.
- Accepted source digest:
  `183ddb9db74f6014ac2c6b0841c68c326512f6bed4cd0e29ad09c6bad3956ae8`.
- `welcome.md` digest:
  `74c3a8bf6fd7cc1634378d6f7be02b126252ce31e0b3625fa20af21818de4c59`.
- 34 targeted authentication/proxy checks and 57 editor checks passed; the
  isolated server config typecheck and browser-harness syntax check passed.
- Fresh browser context, no supplied token, no bearer header, no tracing: the
  existing capture harness opened the normal workspace Workflows control and
  read back the exact saved workflow without the token-entry screen.
- Failed first walkthrough is retained at
  `/tmp/wright-desktop-private-lan-dave-20261011-01`.
- Passing walkthrough, exact served-source checks and screenshot are retained at
  `/tmp/wright-desktop-private-lan-dave-20261011-02`.
- This is a GB10 browser verification. The user's prior screenshot establishes
  in-app page rendering at the login screen; post-change Windows rendering and
  user acceptance have not been claimed.

The capture harness's explicit `--authenticated-entry=true` flag omits tracing
without supplying a token. It still fails if a token prompt appears.

## Reproduce this exact listener

Run from the source worktree. This changes only the private web listener, not
the existing API, MCP connection, instruction bodies or durable run:

```bash
env VITE_WRIGHT_WORKFLOW_RECOVERY=1 \
  WRIGHT_WEB_API_PROXY_TARGET=http://127.0.0.1:8116 \
  WRIGHT_DESKTOP_PRIVATE_WEB_ORIGIN=http://192.168.1.170:5216 \
  WRIGHT_DESKTOP_PRIVATE_WEB_CLIENT=192.168.1.178 \
  WRIGHT_DESKTOP_PRIVATE_WEB_TOKEN_FILE=/tmp/wright-desktop-native-host-target-20261011-01/.preview-api-token \
  npm run dev --workspace=apps/web -- \
  --config ../../prototypes/desktop-harness/private-lan.vite.config.ts \
  --host 192.168.1.170 --port 5216 --strictPort
```

Rollback: stop only this owned listener and restore the previous ordinary Vite
command with the same LAN address/API target, omitting the isolated config and
private-session variables. The token form then returns. Neither operation
restarts the API or replays a workflow. Native plugin panels, full engineering
examples, model attestation and broader capability qualification remain separate.
