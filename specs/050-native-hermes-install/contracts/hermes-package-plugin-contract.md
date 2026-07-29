# Hermes Git Plugin Contract

## Purpose

Bind Wright to the released Hermes plugin interface without asking Wright to
modify Hermes or invent new Hermes commands. Hermes owns Git plugin
installation and command registration. Wright owns its isolated runtime
lifecycle.

## Released Hermes interface

The supported production path uses the released CLI verbatim:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
hermes plugins update wright
hermes plugins remove wright
```

Git is a documented prerequisite of this Hermes phase. Because released Hermes
does not accept a ref selector for install, verification compares the installed
clone's HEAD with the recorded mirror commit and its provenance with the Wright
release commit before running the adapter.

## Adapter import contract

The Git checkout contains `plugin.yaml`, `__init__.py`, `commands.py`, and a
standard-library-only bootstrap. Loading and registering `/wright`:

- imports no `wright_engineering`, FastAPI, MCP, or application module;
- performs no network, package installation, process start, or filesystem
  mutation;
- registers only documented commands supported by Hermes 0.19;
- stores no secrets and reads no Wright repository path.

## Runtime bootstrap

On the first `/wright start`, the adapter:

1. resolves a safe `WRIGHT_HOME` independent of `HERMES_HOME`;
2. creates or reuses a contained versioned bootstrap environment;
3. obtains one exact compatible `wright-engineering` wheel from the configured
   stable/test/local channel using the current Python interpreter;
4. verifies normalized version and recorded hash/provenance;
5. invokes `wright native start` in a subprocess with the exact artifact
   identity supplied through bounded environment values;
6. returns Wright's structured lifecycle result through a concise Hermes
   projection.

The user never issues a Python package command. After the Hermes Git operation
finishes, Wright bootstrap, start, status, update, rollback, uninstall, purge,
and MCP operation do not invoke Git or consume the adapter checkout as
application source.

## Update and rollback

`hermes plugins update wright` updates only the thin adapter. `/wright update
[version]` and `/wright rollback [version]` manage exact Wright runtime
artifacts independently under `WRIGHT_HOME`. A Git adapter update must not
delete Wright runtime or user data.

Hermes adapter recovery restores a previously verified mirror commit through
the release process. Wright runtime rollback uses the retained runtime
predecessor and data-schema policy; neither silently rolls back user data.

## Remove

Released Hermes 0.19 exposes no plugin-removal callback. Wright MUST NOT
register or depend on an imaginary `pre_remove` hook. The safe removal sequence
is:

```text
/wright uninstall
hermes plugins remove wright
```

The first command removes Wright-managed executable/runtime state and preserves
user data. The second removes only the Hermes adapter checkout. Explicit purge
remains a separate confirmation-bound Wright command.

## Candidate acceptance

Pull-request validation installs the adapter using a real Hermes 0.19 process
from a temporary immutable Git repository/ref, points its bootstrap at a local
candidate wheelhouse, then removes Git from the audited runtime PATH. Production
verification repeats the flow with the published adapter commit and PyPI wheel.

## Security

- Package version/channel inputs come from signed release configuration or test
  fixtures, never untrusted chat text.
- Bootstrap commands are argument arrays with no shell evaluation.
- Index credentials remain in package-manager facilities and are redacted from
  output and evidence.
- Adapter paths, `HERMES_HOME`, and Codex state are outside Wright purge scope.
