# Hermes Package Plugin Contract

## Purpose

Define the Hermes capability Wright requires for a native, no-Git install. This
is an external compatibility boundary, not an invitation for Wright to modify
Hermes core at runtime.

## Required Hermes capability

Hermes MUST expose a supported, documented plugin lifecycle that accepts an
immutable Python distribution reference or local candidate artifact and manages
an entry point in the `hermes_agent.plugins` group.

The illustrative CLI below names the behavior; the final spelling is whatever a
released Hermes version documents and the compatibility fixture implements:

```text
hermes plugins install-package wright-engineering==<version> --enable
hermes plugins update-package wright-engineering==<version>
hermes plugins remove-package wright-engineering
```

Wright documentation MUST use the released interface verbatim. It MUST NOT
silently map these operations to a Git clone.

## Install request

Inputs:

- exact distribution and version, or an exact local wheel for candidate tests;
- approved index/channel (`local_candidate`, `test`, or `stable`);
- enable/disable decision;
- optional expected SHA-256;
- non-interactive mode for test and desktop orchestration.

Required behavior:

1. Resolve only the requested distribution/version/channel.
2. Verify index policy, filename, normalized version, and expected hash when
   supplied.
3. Install the base distribution without its `runtime` extra into Hermes'
   managed Python environment.
4. Discover exactly one `hermes_agent.plugins` entry named `wright`.
5. Enable it only when explicitly requested.
6. Return a machine-readable installed distribution/version/entry-point result.
7. Roll back the plugin environment or leave the previous plugin usable on
   failure.
8. Invoke no Git executable and consume no repository source.

## Update and rollback

- Update MUST stage and validate the candidate before replacing the active
  entry point.
- The previous plugin version MUST remain recoverable until Wright's runtime
  compatibility and health checks complete.
- Hermes MUST expose an exact-version rollback or equivalent transactional
  restoration used by the acceptance test.
- A plugin update MUST NOT delete `HERMES_HOME/wright/data` or external
  workspaces.

## Remove

- Remove MUST disable the entry point before deleting package files.
- Hermes MUST invoke a bounded Wright pre-remove callback or an equivalent
  documented lifecycle handshake so Wright can stop its process and remove
  managed runtime code while preserving data by default.
- Callback failure MUST produce an honest incomplete removal result; it MUST NOT
  claim that Wright is fully removed while a managed process or runtime remains.
- Explicit data purge is a separate Wright operation and is never implied by
  plugin removal.

## Compatibility handshake

Before registering commands, Wright reads the Hermes version and a stable
capability identifier. Registration fails closed with an update instruction if:

- the Hermes version is outside the packaged specifier;
- package install/update/remove capability is absent;
- lifecycle callbacks required for safe uninstall are absent; or
- the installed distribution metadata is inconsistent.

## Candidate fixture

Pull-request tests may use a small fixture implementing this exact contract, but
the fixture is not production evidence. Production release verification MUST use
the minimum released Hermes version and the published Wright artifact through
Hermes' real public interface.

## Security

- No arbitrary package specifiers supplied by an LLM are accepted.
- Index URLs and local artifacts are operator/test configuration, never chat
  content.
- Credentials remain in Hermes/package-manager credential facilities and are
  neither passed to Wright logs nor release evidence.
- Install output is redacted and bounded.
