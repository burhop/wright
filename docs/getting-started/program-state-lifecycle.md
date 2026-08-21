# Engineering Program State Lifecycle

Wright treats the Capability Library, local model library, workspace grants,
Rivet bindings/manifests, scenario reports, caches, and evidence as durable
engineering state. Ordinary update, rollback, restart, and uninstall must not
silently discard that state or make stale evidence appear current.

## Persistent roots

Native installs keep managed data beneath the Wright data root. Docker profiles
mount named volumes for `/home/agent/.local/share/wright`,
`/home/agent/workspace`, `/home/agent/.config/wright`, and
`/home/agent/.hermes`; logs use their own named volume. Container layers are
not a persistence mechanism. The image-family manifest records the same roots.

The state inventory exposes logical roots and safe counts/digests, never local
paths or rows. It covers catalog snapshots and overrides, explicit disablement,
workspace scope, model content/installations/evidence/references, workflow
binding sets and run manifests, scenario reports/assertions, and retained
cache/evidence identities.

## Update and restart

Before activation Wright checks the candidate's data-schema range, captures the
predecessor state, creates the database backup required by the migration, and
runs additive migrations atomically. An immutable operation identity makes the
same exact plan idempotent; reusing it for different schema bounds is refused.
The active runtime remains usable until candidate installation, verification,
migration, and activation checkpoints succeed. Interrupted staging returns to
the prior runtime or an explicit recovery-required state, never a mixed-version
success.

Catalog, model, binding, and report bytes may remain cached across update, but
an identity change invalidates affected readiness, review, and diagnostic
previews. Cached bytes preserve reproducibility, not authority.

## Rollback

Rollback activates a retained runtime only when it can read the current data
schema. It never implicitly restores an old database backup. If newer durable
state is outside the older runtime's range, Wright leaves the newer data in
place, records `quarantined-from-older-runtime` metadata, keeps the current
runtime active, and directs the operator to a compatible runtime or the
explicit backup-recovery procedure. No newer data is deleted or exposed as
current to an incompatible runtime.

## Offline behavior

After a successful install/update/rollback, bundled or verified cached catalog
snapshots, installed model packages, workspace bindings, and retained scenario
reports remain readable with zero network requests. A remote-only refresh is a
separate unavailable action; it must not disable unrelated local capability or
evidence reads. Hosted MCPs still require their own network/auth prerequisites.

## Uninstall, reinstall, and purge

Uninstall removes the executable runtime while retaining user data and
reference-held evidence. Reinstall reopens compatible retained data and does
not replay installs, enables, workflow starts, exports, or approvals.

Purge is separate, destructive, and path-bound. Wright previews the exact owned
scope and requires the matching confirmation code. Reference-safe deletion
refuses content still required by an installation, workspace, workflow run,
scenario report, export, lease, evidence record, or rollback. Reclaimable cache
is distinguished from irreversible user-state deletion. Broad roots, symlinks,
wrong confirmation, and ambiguous scopes fail closed.

Use support diagnostics before lifecycle recovery. The diagnostic export is
local and inert; lifecycle actions never grant physical machine authority.
