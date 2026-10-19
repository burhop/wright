# Remote sign-in qualification — 19 October 2026

The customer journey is Connect → provider sign-in/code → observed Connected.
SSH forwarding is a developer diagnostic only, not a customer prerequisite.

## Implemented candidate (not yet installed)

An explicit `--remote-oauth-flow device_code` prototype setting selects the narrow
RFC 8628 client in the existing remote MCP runner. The default remains the existing
SDK authorization-code flow for local Wright/Hermes. Unsupported device grants
fail explicitly; neither another grant nor another account is substituted.
No callback receiver is started for the device flow. No new database, identity
service, provider implementation or workflow executor is introduced.

The client reuses MCP SDK 1.30.0 discovery/schema helpers and Wright's server-scoped
secret storage. It validates resource and issuer identity before sending stored
credentials, registers a public device client only when none exists, and preserves
an incompatible existing client for an explicit operator decision. Device and
refresh requests include the bound MCP resource and required scopes. Pending and
slow-down responses are polled within a bounded five-minute native check; denial,
expiry and network failures terminate without transport/grant fallback.
A refresh reference is consumed through the existing secret owner before rotation;
a crash/lost response cannot automatically replay it on restart. Fresh user sign-in
is then needed. Public-client, refresh, cancellation and restart tests are distinct
from real provider/account acceptance.

The panel exposes only the verification page and user code through existing
operator-private metadata. Device codes, bearer/refresh tokens and raw provider
responses do not enter model-facing tool results. Authentication is separate from
protocol validation, workspace availability, per-tool permission and process review.
Flow selection and remote transport/client source hashes enter the frozen runtime
profile; old sessions/runs are not retargeted. Generated UI authoring stays gated.

## Current evidence

Evidence directory: `/tmp/wright-desktop-resume-evidence-20261019/`.

- `device-discovery-probe.json`: actual public issuer metadata, isolated public
  client registration HTTP201 and device challenge HTTP200. No personal login,
  token polling or live Wright configuration change.
- `actual-device-client-probe.json`: the actual implemented client discovered the
  MCP resource and issuer, registered through the existing isolated secret owner,
  received a real device challenge and cleared presentation on controlled stop.
  No login, token polling or MCP operation completed. First composition and
  streaming-response failures are retained separately; a streaming-wire regression
  now covers the latter.
- `device-focused-final.log`:54 focused device/local-callback/private-metadata and
  OCI-policy checks pass. `device-ui-tests.log`:13 sign-in UI checks pass.
- `device-registry-native-regression.log`:846 registry/native/policy tests pass
  before the final refresh-recovery hardening; current gate must cover final bytes.
- `device-native-build.log`:self-contained panel built with no external assets.
- `security-scan-baseline/public/scan.json`: fresh DB succeeds, but prior exact
  image has five fixable High libexpat findings. Both relevant Docker stages now
  pin the fixed Debian package; rebuilt-image qualification is pending.

This is not real account authentication, actual Windows rendering/download
acceptance, a passing current repository gate, dev deployment, or completion of
connection import/private-credential/upgrade parity. The installed 0.15 runtime,
workspaces, credentials and all original evidence are unchanged.

Official standards: [OAuth device grant](https://www.rfc-editor.org/rfc/rfc8628),
[MCP authorization](https://modelcontextprotocol.io/specification/latest/basic/authorization).
Provider discovery: [SteveCAD issuer metadata](https://auth.stevecad.studio/realms/users/.well-known/openid-configuration).
OpenAI's [plugin authentication guide](https://developers.openai.com/plugins/build/auth)
describes host-to-plugin authentication; that is a separate boundary from Wright
connecting to engineering MCP providers. It does not transfer the host's provider
authorization or bypass Wright's gateway permissions.

## Current gate checkpoint

The rebuilt55583c1c ARM64 image
`sha256:f910b45559111c4ece2d4cced7be252a84098773efe1c8fb9a017a37a3f2f7b5`
passes the unchanged image-security policy with a fresh19October database.
The normal full gate then caught one formatting issue in the newly added frontend
test; the correction is mechanical and the full frontend formatting check passes.
This is not yet a passing full-gate claim. Current WebKit launch still fails on
GB10 for missing `libgstcodecparsers-1.0.so.0`; its exact log is retained. The
repository permits documenting that local limitation and separately qualifying
Chromium; supported-host CI must still exercise its normal browser matrix.
