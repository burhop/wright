# Wright with Hermes Desktop

Hermes Desktop uses the same native package-plugin contract as Hermes CLI. There
is no separate Wright Desktop bundle, copied plugin folder, source checkout, or
frontend build for a normal user.

## Current status

Native activation is intentionally blocked while the released Hermes line is
Git-only. The Wright compatibility contract currently records
`production_native_available: false`. Continue to use the mandatory Docker
appliance for a turnkey public build; use the legacy Git mirror only to migrate
an existing older test installation, not as proof of native support.

When a released Hermes version provides `python-distribution-v1`, install the
exact Wright version through Hermes:

```text
hermes plugins install-package wright-engineering==<version> --enable
```

Restart Desktop if it does not reload newly installed entry points, then use:

```text
/wright start
/wright status
/wright doctor
```

The first start creates the contained runtime automatically and returns the UI
URL. Configuration and data live under the active `HERMES_HOME/wright` boundary,
not under a repository.

## Hermes gateway

Wright connects to Hermes through Hermes' configured local API/gateway. Enable
that feature in Hermes using the documentation for the released compatible
version. Wright reads Hermes-owned configuration and does not copy or rewrite
Desktop plugin directories. If `/wright status` reports Hermes disconnected,
check the Hermes gateway itself before changing Wright data.

## LLM status

The Wright LLM status is separate from the Hermes gateway. Configure a local or
hosted OpenAI-compatible endpoint in the normal Wright setup UI or approved
configuration. Credentials are not included in logs, diagnostics, package
artifacts, or release evidence.

## Removal

Use `/wright uninstall` before package removal when the released Hermes does not
automatically invoke the registered pre-remove hook. This stops the verified
process and removes runtime code while preserving data. Use `/wright purge` only
when you intend to delete the disclosed Wright data path permanently.
