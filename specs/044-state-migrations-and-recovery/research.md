# Research: State Migrations and Recovery

## Numbered migration representation

- **Decision**: Represent migrations as ordered immutable definitions composed from a small typed operation set. Compute the recorded SHA-256 checksum from a canonical serialization of version, name, and operations.
- **Rationale**: This detects edited history without relying on source-file line endings or introspection, supports conditional legacy column adoption, and remains deterministic in wheels and source checkouts.
- **Alternatives considered**: Alembic (unnecessary dependency and external configuration for the embedded local scope); raw Python callback source hashing (unstable across packaging/formatting); `PRAGMA user_version` alone (no names, checksums, timestamps, or drift evidence).

## Legacy adoption

- **Decision**: Run the same idempotent ordered operations against fresh and unversioned legacy databases, then record each completed definition transactionally. Conditional create/add/backfill operations adopt partial historical shapes without a separate guessed-version marker.
- **Rationale**: The old boot routine tolerated partial schemas rather than publishing reliable version numbers. Applying explicit invariants is safer than inferring a version from one column.
- **Alternatives considered**: Stamp every legacy database as current (misses incomplete shapes); one monolithic baseline migration (recreates the existing audit and interruption problem); retain boot-time probes indefinitely (no immutable history).

## Transaction and lock boundary

- **Decision**: Acquire a stable sibling lifecycle lock for mutating operations, run preflight checks, and apply each migration plus its ledger row in one `BEGIN IMMEDIATE` transaction. Use a bounded SQLite busy timeout.
- **Rationale**: Per-migration transactions provide a durable last-known version and make interruption tests precise while preventing concurrent lifecycle writers.
- **Alternatives considered**: One transaction for all migrations (large lock window and no durable intermediate checkpoint); autocommit statements (partial change exposure); database-only advisory rows (not safe before the schema exists).

## Integrity and readiness

- **Decision**: Require `quick_check` and `foreign_key_check` before and after upgrade, reject future versions and checksum drift, and let any lifecycle exception escape FastAPI lifespan before runtime services are constructed.
- **Rationale**: A process that continues after uncertain state is more dangerous than an explicit unavailable service.
- **Alternatives considered**: Log-and-continue startup (current P0 finding); repair automatically (may destroy evidence/data); defer checks to first request (already serving incompatible state).

## Snapshot and restore

- **Decision**: Create consistent snapshots with SQLite's online backup API into a temporary sibling, verify them, hash bytes, write a versioned restricted manifest atomically, and only then publish both artifacts. Restore validates everything into a temporary candidate, preserves the displaced database, and uses atomic replacement after closing connections.
- **Rationale**: File copies of live WAL databases can be inconsistent. Staged verification and atomic activation keep the current database unchanged on pre-activation failure.
- **Alternatives considered**: Copy main/WAL/SHM files (race-prone); SQL dumps (slow and lossy for exact state); in-place restore (no atomic rollback boundary).

## Downgrade policy

- **Decision**: Support downgrade only by restoring a verified pre-upgrade snapshot whose manifest declares compatibility with the older release.
- **Rationale**: Reverse schema code increases destructive-path risk and cannot reliably reconstruct removed information.
- **Alternatives considered**: Down migrations (false assurance for data transforms); manual file copying (no validation); continue with newer schema (undefined behavior).

## Command surface

- **Decision**: Add an internal `wright-db` console command to `wright-data-vault` with `status`, `backup`, `upgrade`, and `restore`, plus `--json`. Do not add `data_vault` as a private dependency of the public `wright-engineering` distribution.
- **Rationale**: Meets the operator requirement now while preserving the approved public artifact boundary; Feature 047 can expose appliance operations over public protocols.
- **Alternatives considered**: Put commands in the API package (wrong ownership); add private package dependency to public CLI (violates release topology); HTTP-only maintenance endpoints (unnecessary remote mutation surface).
