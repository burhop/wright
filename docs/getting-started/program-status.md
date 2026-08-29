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
