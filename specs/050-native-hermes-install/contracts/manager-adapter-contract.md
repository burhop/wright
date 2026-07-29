# Manager Adapter Contract

## Purpose

Define how Hermes, Codex, and future agent managers install or connect
to one manager-neutral Wright runtime. Manager adapters contain installation and
configuration projection only; Wright lifecycle, workspace, catalog, and MCP
business rules remain in `wright-engineering`.

## Common boundary

Every supported adapter MUST:

1. identify its manager and adapter protocol version;
2. use that manager's documented installation or MCP configuration interface;
3. resolve the Wright runtime under `WRIGHT_HOME`, never manager-owned state;
4. invoke Wright through the public CLI/lifecycle or STDIO/Streamable HTTP MCP
   contract;
5. keep manager-specific prerequisites and configuration out of Wright core;
6. expose no credentials in arguments, logs, manifests, or release evidence;
7. prove compatibility and packaged-runtime identity before support is claimed.

Removing one adapter does not uninstall or purge the shared Wright runtime.
`wright native uninstall` and the separately confirmed purge operation own those
effects.

## Hermes Git adapter

Hermes 0.19 installs and updates plugins from Git. Git is therefore an explicit
Hermes adapter prerequisite and is allowed only during these operations:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
hermes plugins update wright
hermes plugins remove wright
```

The installed adapter MUST be standard-library-only at import time. `/wright
start` creates or reuses a contained bootstrap interpreter, downloads the exact
compatible `wright-engineering` wheel through Python's package tooling, records
its immutable identity, and invokes the public Wright lifecycle in a subprocess.
After Git installation finishes, no Wright runtime command may invoke Git or
read the adapter checkout as application source.

Released Hermes does not accept an immutable ref selector in its install
command. Release verification MUST therefore compare the installed clone's Git
HEAD with the recorded mirror commit and compare its `provenance.json` source
commit with the Wright release commit before any lifecycle command runs.

Hermes removal has no pre-remove lifecycle hook in the released plugin API.
Documentation MUST therefore direct users who want runtime-code removal to run
`/wright uninstall` before `hermes plugins remove wright`. Data purge remains a
separate confirmed Wright operation.

## Codex adapter

Codex consumes Wright directly through a plugin-bundled or user/project MCP
profile. The profile launches the installed `wright mcp serve --stdio ...`
command or connects to Wright's authenticated Streamable HTTP endpoint. A Codex
plugin may bundle skills and MCP configuration, but MUST NOT duplicate runtime
lifecycle or require Hermes.

Codex support evidence validates the plugin manifest/profile, starts the
packaged Wright MCP bridge, completes MCP initialize/list/call, and verifies the
same runtime identity and tool contract used by other managers.

## Deferred OpenClaw adapter

OpenClaw integration is future work. This delivery defines no supported
OpenClaw adapter, installation path, compatibility claim, or release evidence
requirement. The manager-neutral Wright runtime MUST remain reusable by a later
adapter without adding OpenClaw or Node.js/npm dependencies now.

## Candidate and release evidence

Pull requests use local immutable adapter subjects and a local Wright
wheelhouse. Production verification uses published adapter identities:

- Hermes: immutable Git tag/commit;
- Codex: versioned plugin archive/marketplace identity when publicly claimed;
- Wright: exact PyPI wheel filename and SHA-256.

Evidence records manager version, adapter identity, prerequisites observed,
runtime identity, MCP transport/result, and lifecycle result. It fails if a
manager-specific prerequisite is observed outside its adapter phase.
