# Missing MCP credential entry — candidate qualification

User journey: Connections → completed setup → API keys and configuration values
→ Enter missing credentials → Save → check provider → explicit workspace enable.
OAuth remains the separate provider sign-in path. Existing configured values are
never returned or replaced by this prototype form. Stop an active provider before
editing; no provider restart, validation, permission or workflow action is implied.

The native panel encrypts field values using standard compact JWE before the
app-only MCP boundary. Only ciphertext and an opaque one-use form ID enter tool
arguments. Wright decrypts into its existing `save_credentials` service and secret
store. No new identity service, database, scheduler or generic encrypted proxy.
This does not conceal an operator's form from the trusted desktop hosting it.

A form expires after five minutes, exists only in API-process memory, and binds
workspace, desktop session, completed plan/digest, exact provider and current
configuration/field readiness. It is consumed before decrypt/save. Changed scope,
configuration, unsupported crypto/algorithms, unknown fields, oversized inputs,
expiry, restart and duplicate submission fail closed. Lost acknowledgements
require a status read; configured booleans cannot prove an uncertain replacement
value. Missing-to-present credential status invalidates the existing protocol
validation binding. Replacement of existing credentials is deliberately unavailable
until its continuation/invalidation semantics are qualified; the legacy updater's
reported success is not a substitute.

Pinned libraries: `jwcrypto==1.6.1` and browser `jose==6.2.5`, exact lock files;
RSA-OAEP-256/A256GCM only, no compression. Runtime records the crypto version and
credential-form module hash. Public keys are operator metadata; private keys and
plaintext never enter model-facing results. Form controls retain host styling and
the common working view/editor are unchanged.

Evidence: `/tmp/wright-desktop-resume-evidence-20261019/`:

- `sealed-form-spike.json`: real Node WebCrypto→Python JWE interoperability.
- `credential-boundaries-final.log`:69 passing synthetic exact-scope, operator,
  crypto, drift, one-use/restart and existing-owner tests.
- `credential-ui-verified.log`:32 passing UI tests; real encryption, no plaintext
  tool arguments, lost-ack reconciliation, no-encryption rejection and sign-in race.
- `credential-types-verified.log`: TypeScript passes.
- `credential-native-build.log`: actual self-contained native resource,
  2,331,295bytes, zero external assets.

Actual browser-to-secret-owner proof, final bundle regression, current full gates,
installation and Windows acceptance remain separate pending checks. The installed
0.15 service, user workspaces, credentials and earlier evidence are unchanged.

References: [JWCrypto JWE](https://jwcrypto.readthedocs.io/en/latest/jwe.html),
[jose](https://github.com/panva/jose),
[OpenAI tool-result metadata](https://developers.openai.com/plugins/reference).
