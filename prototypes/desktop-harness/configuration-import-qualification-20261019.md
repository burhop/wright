# Native configuration import — bounded candidate

Connections → Add a custom MCP → Import MCP configuration (JSON) parses locally.
Choose a named server from Claude/VSCode-style maps or a plain server object.
Commands run on Wright's host. Only literal stdio commands and public HTTPS
endpoints in the documented subset are accepted; unsupported settings produce an
explicit local error before a host tool request. This is not full format parity.

Environment values are withheld by default. Secret-looking values are discarded;
only their declared field names enter the preview. The user may explicitly select
nonsecret public environment values. Those values remain visible in the reviewed
plan and persist through the existing importer, plan digest, registration adapter,
launch configuration and gateway configuration identity. Private values must be
entered through the sealed form after setup. Source/terms review, plan approval,
apply, protocol validation and workspace/tool enablement remain distinct.

Reused owners: config_import, install_plans, RegistryOnboardingAdapter,
DatabaseLifecycleAdapter, existing credential service and gateway. No new database,
installer, executor, vendor integration or imported execution authority. Changed
public values create a different draft/plan/provider identity; existing runs and
providers are preserved. Original raw config is not retained. Nothing accepts
credentials, grants, live runs or approvals as portable import authority.

Explicit limits: HTTP-header authentication/imports, legacy SSE/WebMCP config,
unknown extension fields, credential command arguments and arbitrary substitution
syntax are not qualified by this native subset. Importing a Windows command does
not install its runtime on GB10. Existing credential replacement and automatic
provider upgrades remain unavailable pending their own invalidation/recovery
qualification. Do not route users to the legacy updater's fabricated version.

Local evidence under `/tmp/wright-desktop-resume-evidence-20261019/`:

- `configuration-ui.log`:49 passing parser/panel tests, including file import,
  explicit public-value selection and no private value in tool arguments.
- `configuration-boundaries.log`:83 passing existing and additive scoped
  import/review/registration/credential boundary tests.
- `configuration-types.log` and `configuration-lint.log`:pass.
- `configuration-owner-final.log`:54 passing final owner/registration/scoped-preview checks.
- `desktop-validation-privacy.log`:16 passing checks; the existing private error serializer now also prevents desktop request-data/error-context reflection.
- `configuration-native-build-final.log`:2,335,946byte self-contained resource,
  no external assets.

The source-controlled credential_environment_mcp fixture verifies delivery of one
public setting and an intentionally synthetic private value, then reuses the
existing stdio protocol fixture. It is a test fixture, not an engineering provider
or a claim of real account authentication. Actual browser-to-owner proof and final
candidate gates/installation/Windows acceptance are still separate pending checks.

## Actual native browser/owner continuation

Frozen sourceca1756f3, resourceSHA256
`a6faa632fc7aad550f6fce255fc79254ad645804a3c8970d49513ca38dfa67f6`.
The actual bundle→MCP→API journey imported/reviewed/applied one exact local fixture,
then filled its missing synthetic credential through JWE. Withholding the committed
save reply produced one save, cleared the form and required a status read. The
subsequent explicit protocol validation started a real subprocess which verifies
both the public setting and exact synthetic private value before initializing and
listing tools. No tool call, workspace grant, account login or engineering run.
Fresh panel reopening retained status;480px layout has no horizontal overflow.
The fixture was then stopped once through the existing exact lifecycle control;
its workspace, source, credentials and evidence remain intact.

Receipts: `mcp-management-browser-1792417073433/report.json`,
`mcp-management-fixture-cleanup.json`, and masked screenshots in that browser
folder. Prior `mcp-management-browser-1792416894909/failure.json` records successful
setup followed by an observer expecting the wrong terminal label. Readback and
`mcp-management-observer-correction.json` verify actual `failed` validation with
missing credentials, denied start, inactive provider and disabled workspace.
The continuation read the same plan; it did not repeat setup or that denied check.
The first observer also decoded the workspace-create response incorrectly;
inventory recovery reused its one created workspace. These failures are retained.
This qualifies GB10 Chromium in a simulated desktop frame, not actual Windows.
