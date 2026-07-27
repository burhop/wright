# Research: Secrets, Container, and Provider Configuration

## Shared credential boundary

- **Decision**: Use a `SecretProvider` protocol with environment, mounted-file, and atomic owner-only file implementations composed by precedence. Callers use stable credential references and receive values only at the final operation boundary.
- **Rationale**: Works air-gapped across Windows/Linux, supports container-mounted secrets, avoids a mandatory daemon, and lets a future OS-keyring adapter slot in without changing callers.
- **Alternatives considered**: Mandatory OS keyring (not reliable in headless containers); encrypted file with application-bundled key (security theater); SQLite encryption (adds key bootstrap and Feature 044 coupling).

## Atomic fallback transactions

- **Decision**: Lock a separate stable lock file across read-modify-write; write a same-directory temporary file; flush and fsync; set owner-only permissions; atomically replace; fsync the parent directory where supported.
- **Rationale**: Locking the data inode is unsafe across replace and truncating before locking loses data. A stable lock file serializes all writers while replace prevents partial JSON visibility.
- **Alternatives considered**: In-process locks (do not protect multiple processes); direct truncate/write (crash corruption); append journal (unnecessary complexity before Feature 044).

## Plaintext migration

- **Decision**: Discover known legacy keys, create an owner-only backup, import and verify each value through the provider, then remove plaintext in one SQLite transaction. Record an idempotent marker only after verification; fail readiness closed on error.
- **Rationale**: Prevents partial serving and preserves rollback. The seam can later be called by Feature 044's numbered runner without changing its behavior.
- **Alternatives considered**: Lazy migration on read (leaves plaintext indefinitely); delete-first migration (data loss); best-effort startup warning (serves insecure state).

## Git authentication

- **Decision**: Preserve clean remote URLs and provide credentials through a short-lived askpass helper/environment with redacted errors and guaranteed cleanup.
- **Rationale**: Tokens never enter argv, remote config, or URLs and reserved characters need no URL interpolation.
- **Alternatives considered**: Tokenized HTTPS URLs (observable); global credential helper mutation (destructive host side effect); stdin for Git commands that do not support it consistently.

## Log and protocol redaction

- **Decision**: Redact structured fields by normalized key and replace registered secret values before any log/trace/API sink; log MCP methods and sizes rather than raw messages, commands, stdout, or stderr.
- **Rationale**: Sink-side cleanup is too late and raw protocol logging has unbounded credential exposure.
- **Alternatives considered**: Regex-only redaction (misses arbitrary values); disabling all diagnostics (unnecessary loss of operability); relying on client approvals (not an authorization or confidentiality control).

## Container hardening

- **Decision**: Remove sudo and default credentials; require/generated per-install secrets; keep processes non-root; add `no-new-privileges`, drop capabilities, use read-only root filesystem with explicit tmpfs/writable data paths, and replace broad OS volumes with Wright-owned data volumes.
- **Rationale**: Limits compromise impact and ensures image upgrades replace system state while retaining user data.
- **Alternatives considered**: Keep passwordless sudo for debugging (release blocker); persist entire home/system trees (compromise persistence); bake secrets into image/config (shared leakage).

## Configuration preservation

- **Decision**: Parse supported configuration formats, merge only Wright-owned keys, and atomically replace while retaining unknown semantic entries; preserve comments where the format/parser supports round-tripping.
- **Rationale**: Prevents destructive replacement and supports multiple independent providers.
- **Alternatives considered**: Rewrite whole files from templates (data loss); append duplicate blocks (ambiguous precedence); defer all configuration changes (leaves P0 exposure).
