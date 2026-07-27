# Data Model: Secrets, Container, and Provider Configuration

## CredentialReference

- `namespace`: `global`, `workspace`, `mcp`, or `integration`
- `owner_id`: stable owner identifier; empty only for global credentials
- `name`: normalized credential name
- `configured`: status exposed to clients
- `source`: environment, mounted file, fallback, or absent; never includes a value
- `updated_at`: optional non-secret audit timestamp

Identity is the tuple `(namespace, owner_id, name)`. Names are restricted to a stable uppercase identifier form. Values never appear in serialized references.

## SecretProvider

Operations:

- `get(reference) -> secret or absent`
- `set(reference, value)`
- `delete(reference)`
- `status(reference) -> CredentialReference`
- `transaction(updates, deletes)` for atomic multi-key migration

Provider implementations must not log values and must distinguish missing, inaccessible, corrupt, and permission-insecure state.

## AtomicSecretDocument

- `version`: fallback document format version
- `credentials`: mapping from canonical reference keys to values
- `metadata`: non-secret migration/provider metadata

State transitions: `absent -> valid`; `valid -> atomically replaced valid`; `valid -> absent`; `corrupt/insecure -> fail closed`. Readers see either the old complete document or the new complete document.

## CredentialMigration

- `migration_id`: stable identifier
- `state`: not-started, backed-up, imported, verified, committed, or failed
- `backup_path`: restricted local recovery artifact
- `source_keys`: known plaintext locations
- `verified_count`: number imported and read back successfully
- `failure`: redacted diagnostic

Transitions are forward-only during upgrade. Plaintext deletion occurs only in the verified-to-committed transition. Rollback reads the backup and never prints values.

## ProviderConfiguration

- `path`: owned configuration file
- `wright_keys`: fields Wright may modify
- `unknown_entries`: semantic content preserved across writes
- `revision`: digest used to detect concurrent replacement

Writes validate the prior revision, merge owned keys, fsync a temporary sibling, and replace atomically.

## ApplianceDataSet

Allowed persistent categories: Wright database/vault, workspaces, operator configuration, protected secrets, and logs explicitly retained by policy. System package directories, `/etc`, `/usr/local`, caches, and entire home directories are prohibited in the default deployment.
