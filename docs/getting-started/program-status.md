# Program status

Wright exposes a read-only `/program-status` page backed by one immutable status
bundle. The page keeps product readiness, benchmark readiness, commercial
readiness, and program health independent. It never converts proposed customer
stories, code activity, or completed governance tasks into customer acceptance
or benchmark qualification.

## Source and identity

The publisher reads Git blobs from one exact commit, runs the authoritative
program validator for that subject, embeds the validated dashboard unchanged,
and derives the EPP-F01B supplement from the closed 20-source catalog. The
canonical `bundle_id` binds the source identity, dashboard, and supplement.
Dirty working-tree files are never observed.

```powershell
python scripts/publish-engineering-program-status.py `
  --repository . `
  --source HEAD `
  --data-root .wright-data/program-status
```

The command prints only non-secret commit, tree, program-tree, bundle, and
installation identities. Repeating it for the same commit is a byte-identical
no-op. Publication uses a same-directory temporary file, flush and filesystem
sync, validation, and atomic replacement; a failed replacement leaves the
previous `current.json` untouched.

## Runtime precedence and recovery

The API reads `<database-parent>/program-status/current.json` first. It uses the
packaged fallback only when the installed artifact is absent. An installed but
invalid or identity-mismatched artifact fails closed; it never falls back and
silently hides corruption. Republish the exact committed subject or restore the
prior known-good data-root copy to roll back.

The browser polls conditionally and atomically swaps only a fully validated new
identity. It preserves the last valid view during a failed refresh and displays
publisher health separately from program readiness.

## Packaged and lifecycle behavior

The native wheel contains the validated fallback bundle, its exact source
catalog, all five EPP-F01B schemas, the authoritative dashboard schema, and the
compiled browser application. A packaged runtime can therefore serve both
`/api/program-status` and `/program-status` without Git, a source checkout,
network access, or a frontend build.

An ordinary update, rollback, reinstall, or uninstall may replace runtime code
but must preserve `<WRIGHT_HOME>/data/program-status/current.json`. Restore the
previous immutable file to roll back status content. Only an explicitly
confirmed Wright data purge may remove it. Wright's native lifecycle matrix
checks this preservation path on Windows, Linux, and macOS.
