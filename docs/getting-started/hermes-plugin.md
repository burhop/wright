# Native Wright for Hermes

Hermes is Wright's primary manager path. Wright remains bring-your-own-AI and
does not modify Hermes itself.

## Prerequisite and install

Hermes installs plugins from Git, so Git must be available to Hermes during
adapter install, update, and removal. Install the production thin adapter with
Hermes' documented command:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
```

The adapter is standard-library-only at import time. It stores no Wright
application code in Hermes state; `/wright start` resolves the exact compatible
`wright-engineering` artifact into Wright-owned `WRIGHT_HOME` (default
`~/.wright`). No Wright checkout, `WRIGHT_REPO_DIR`, Docker, Node.js, npm, or
manual Python package command is required.

## First start and diagnostics

```text
/wright start
/wright status
/wright doctor
```

`/wright start` creates or reuses the contained runtime, launches the packaged
API/UI, and returns its local URL. It does not build frontend assets or invoke
Git after the Hermes adapter phase. `/wright status` is read-only. `/wright
doctor` reports compatibility, contained paths, process identity, API/UI
health, data permissions, and bounded remediation without printing credentials.

## Operate, update, and roll back

```text
/wright stop
/wright start
hermes plugins update wright
/wright update <exact-version>
/wright rollback <exact-version>
```

Hermes updates the thin adapter through Git. Wright updates its own runtime
independently: it stages and checks the exact artifact and data migration before
stopping a healthy predecessor. Rollback is allowed only when packaged schema
bounds permit it. If health cannot be restored, Wright reports
`recovery_required` instead of claiming success.

## Uninstall and purge

Hermes has no pre-remove callback, so users who want Wright runtime code removed
must run the lifecycle command before removing the adapter:

```text
/wright uninstall
hermes plugins remove wright
```

`/wright uninstall` preserves `WRIGHT_HOME/data`, configuration, catalog
choices, and external workspaces. Reinstalling the adapter can reopen them.

Purge is deliberately separate:

```text
/wright purge
/wright purge <confirmation-code>
```

The first command discloses the one Wright-owned data path and a confirmation
code bound to that path and installation identity. Only the second exact command
deletes it. Broad roots, symlinks, manager configuration, and external
workspaces are refused.

## Offline operation and MCP servers

Online install/update resolves exact wheels and hashes into Wright's cache. An
offline start may reuse only a complete cache matching the manifest; a missing
or mismatched artifact fails before activation. Wright never falls back to a
checkout or mutable `latest` runtime.

The canonical catalog and provider-neutral gateway are included. CAD/CAE/CAM
host applications, licenses, drivers, and credentials remain prerequisites of
the selected MCP server, not the Wright or Hermes base installation.
