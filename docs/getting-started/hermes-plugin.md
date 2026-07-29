# Native Wright for Hermes

This is Wright's primary user installation path. It is designed so Hermes users
need no Git, Docker, Node.js, npm, Wright source checkout, `WRIGHT_REPO_DIR`, or
manual Python package command.

Wright remains bring-your-own-AI and does not bundle an LLM. Configure the
model endpoint and credentials through Hermes using its supported setup flow.

## Availability gate

Do not advertise this path as released until
`src/wright_engineering/compatibility.json` sets
`production_native_available` to `true` and names a
`released_hermes_version`. The currently verified Hermes 0.19.0 interface says
it installs plugins from Git repositories; it does not satisfy Wright's required
`python-distribution-v1` package install/update/rollback/remove contract.

The command spelling below is the contract Wright's release workflow expects.
It becomes user-ready only when a released Hermes documents and passes it:

```text
hermes plugins install-package wright-engineering==<version> --enable
```

Hermes must resolve the exact public wheel, verify its identity, install only
the base entry point in its managed environment, and report the managed plugin
interpreter. It must not translate the request into a Git clone.

## First start

In Hermes, run:

```text
/wright start
/wright status
/wright doctor
```

`/wright start` automatically installs the exact same distribution's `runtime`
extra into a versioned environment under `HERMES_HOME/wright/runtimes`, launches
the packaged API and UI, and returns the local URL. It does not build frontend
assets and does not invoke Git, Docker, Node.js, npm, npx, or pnpm.

`/wright status` is read-only. `/wright doctor` reports compatibility, contained
paths, process ownership, API/UI health, data permissions, Hermes/MCP/catalog
probes, and bounded remediation without printing credentials.

## Operate and update

```text
/wright stop
/wright start
/wright update <exact-version>
/wright rollback <exact-version>
```

Start is idempotent across concurrent Hermes sessions. Update stages and checks
the exact artifact and data migration before it stops the healthy predecessor.
The predecessor remains retained until candidate health succeeds. Rollback is
allowed only when the current data schema fits the predecessor's packaged
bounds; Wright never restores an older backup silently.

If either version cannot become healthy, Wright reports `recovery_required`
instead of claiming success. Run `/wright doctor` and follow the recorded
recovery evidence.

## Uninstall and purge

```text
/wright uninstall
/wright purge
/wright purge <confirmation-code>
```

Uninstall stops only the identity-verified Wright process and removes managed
runtime/cache code. It preserves `HERMES_HOME/wright/data`, configuration,
catalog choices, and external workspaces so reinstall can reopen them.

Purge is deliberately separate. The first call displays the one Wright-owned
data path and a confirmation code bound to that path and installation identity.
Only the second exact call deletes it. Symlinks, broad roots, unrelated Hermes
configuration, and external workspaces are refused.

## Offline and cached operation

An online install/update resolves an exact wheel and all platform-compatible
runtime wheels into the approved Hermes/package cache. A later offline start may
reuse only artifacts whose filename, version, channel, and SHA-256 still match
the manifest. Network loss with a complete valid cache is supported; a missing
or mismatched artifact fails before activation. Wright never falls back to a
checkout or mutable `latest` request.

## MCP servers and providers

The packaged canonical catalog and provider-neutral Wright gateway are included.
MCP servers remain independent integrations. Install CAD/CAE/CAM host software,
licenses, drivers, and credentials only for the selected server; neither native
Wright nor Docker includes them merely to make catalog validation pass.

## Legacy Git-plugin migration

`burhop/hermes-plugin-wright` remains a one-release migration delegate for older
Git-plugin installations. It is not native release evidence. Once package-based
Hermes is available, remove the legacy plugin through its old interface and
install the public `wright-engineering` version through the released package
command. Default runtime uninstall preserves Wright data across that migration.
