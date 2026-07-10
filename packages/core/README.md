# wright-core

`wright-core` contains shared domain models, structured logging helpers, and common utilities used by the Wright local-first engineering appliance.

Credential callers use `CredentialReference` and the `SecretProvider` protocol;
secret values cross that boundary only at the final operation that needs them.
The default provider checks environment and mounted secret files before using
the owner-only atomic local fallback.

The main Wright repository is the source of truth for development, issues, documentation, and releases:

- Source: https://github.com/burhop/wright/tree/main/packages/core
- Issues: https://github.com/burhop/wright/issues
- Documentation: https://burhop.github.io/wright/
- Releases: https://github.com/burhop/wright/releases

This package is published so thin distribution surfaces, including the Wright Hermes plugin mirror, can install shared Wright runtime code without a monorepo checkout.
