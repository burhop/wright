# Data Model: State Migrations and Recovery

## Migration Definition

- `version`: positive contiguous integer, unique and immutable
- `name`: stable human-readable slug
- `operations`: ordered canonical operation values
- `checksum`: SHA-256 over canonical version/name/operations serialization

Validation: definitions start at 1, are contiguous, have unique names, and match any stored entry for the same version.

## Migration Ledger Entry

- `version`: primary key matching one definition
- `name`: recorded definition name
- `checksum`: exact definition checksum
- `applied_at`: UTC timestamp
- `duration_ms`: non-negative elapsed time
- `product_version`: Wright version applying the change

Relationship: every ledger entry must match exactly one installed migration definition. Gaps, unknown future versions, or checksum/name drift make the database not ready.

## Database Status

- `path`: normalized database path (never row data)
- `exists`: whether a database file exists
- `integrity`: `ok`, `corrupt`, `locked`, or `unavailable`
- `foreign_keys_ok`: boolean
- `current_version`: highest contiguous verified ledger version, or 0
- `target_version`: highest installed definition version
- `pending`: ordered versions not yet applied
- `compatible`: boolean
- `ready`: boolean; true only when current, checksums match, and integrity passes
- `message`: redacted actionable summary

State transitions: absent/legacy -> pending -> upgrading -> ready; any validation failure -> blocked. Status itself performs no transition.

## Backup Manifest

- `format_version`: manifest contract version
- `backup_id`: timestamp plus random suffix
- `created_at`: UTC timestamp
- `source_name`: database filename only
- `database_file`: snapshot filename
- `database_sha256`: digest of snapshot bytes
- `database_size`: byte count
- `schema_version`: verified ledger version
- `migration_checksums`: ordered version/checksum pairs
- `integrity_check`: recorded success evidence
- `foreign_key_check`: recorded success evidence
- `product_version`: creating Wright version
- `compatible_product_range`: declared restore compatibility

Validation: required fields, safe sibling filename, supported format/schema, exact digest and size, exact installed migration checksums, and successful live recheck of the snapshot.

## State Backup

- Snapshot database file
- Adjacent manifest file
- Optional displaced-database rollback snapshot produced by restore

Lifecycle: staging -> verified -> published -> restore candidate -> active or rejected. A rejected candidate never replaces active state.

## Lifecycle Lock

- Stable sibling lock path derived from the active database path
- Exclusive owner for upgrade, backup publication, and restore activation
- Bounded acquisition/busy failure

The lock contains no secret or row data and is not deleted between operations, avoiding inode/handle races.

## Existing Application Data

Migrations preserve MCP servers/tools, workspaces, workspace-agent sessions, agent contexts, chat messages, system settings, and Feature 043 migration markers. Catalog metadata reconciliation is an application operation after readiness and is not represented in the migration ledger.
