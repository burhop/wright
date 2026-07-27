# wright-core

`wright-core` contains only side-effect-neutral domain identifiers, value
objects, error taxonomy, redaction, telemetry context, and shared protocols.
It does not own SQLite queries, filesystem mutation, subprocess execution,
workspace orchestration, provider configuration, or imports of higher-level
packages.

Credential callers use `CredentialReference` and the `SecretProvider` protocol;
secret values cross that boundary only at the final operation that needs them.
The API composition root installs a provider implementation owned by
`wright-data-vault`; core never selects or constructs one.

Approved dependencies are declared in
`architecture/python-packages.toml` and enforced by
`tests/test_import_boundaries.py`, including local and dynamic imports.

The main Wright repository is the source of truth for development, issues, documentation, and releases:

- Source: https://github.com/burhop/wright/tree/main/packages/core
- Issues: https://github.com/burhop/wright/issues
- Documentation: https://burhop.github.io/wright/
- Releases: https://github.com/burhop/wright/releases

This package is internal for the current public-alpha topology and is not an
independently supported public distribution.
