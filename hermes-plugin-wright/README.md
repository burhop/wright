# Wright Hermes Git Plugin

This directory is the official production thin adapter between released Hermes
and the manager-neutral Wright runtime. It is mirrored at
`https://github.com/burhop/hermes-plugin-wright`; Wright's monorepo remains the
source of truth.

## Stable Install

Hermes installs and updates the adapter with its real Git plugin commands:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
hermes plugins update wright
```

Git is a Hermes adapter prerequisite. The plugin itself imports only Python's
standard library, resolves a Wright-owned `WRIGHT_HOME` (default `~/.wright`),
installs the exact `wright-engineering` application artifact into an isolated
bootstrap environment, and projects `/wright` commands to Wright's public
lifecycle CLI. The Wright runtime never imports into the Hermes process.

After installation:

```text
/wright setup-browser
/wright start
/wright status
/wright doctor
/wright stop
/wright update
/wright rollback
```

For browser use, prepare the connection **before the first `/wright start`**.
`/wright setup-browser` reports the invoking Hermes environment's MCP dependency
status and prepares profile-local API settings. If the optional MCP extra is
missing, follow its displayed same-interpreter, same-version installation command
and restart Hermes. Start the printed Hermes gateway command in a second terminal,
keep that terminal running, then use `/wright start` and open its URL. The browser's
actual connection indicators establish readiness. If Wright was already running,
stop it before starting it again to pick up the new connection settings.

## MCP client readiness

Wright's isolated runtime and the Hermes MCP client have separate dependencies.
`/wright start` and `/wright doctor` report when this Hermes environment lacks its
optional MCP SDK. A configured `wrightgateway` entry alone does not prove tool
discovery. For a pip-managed Hermes installation, the diagnostic prints a command
using that interpreter and the same installed Hermes version to install its
`mcp` extra. Review/run it, then restart Hermes. Checkout/uv installations should
use their supported MCP-extra setup. Wright does not silently install packages
into Hermes. Provider CAD hosts and accounts remain separate prerequisites.

The installed gateway profile explicitly carries only the native `WRIGHT_HOME`
path, so an MCP client's isolated subprocess can find Wright's existing local
control-plane credential. It does not copy API/model tokens into configuration.
Browser chat additionally requires a running Hermes HTTP gateway; working terminal
MCP tools do not establish that browser connection.

If the Wright browser reports Hermes unavailable, run `/wright setup-browser`.
This prepares local API settings for the current Hermes profile and creates a
private key when needed. It preserves existing custom connections and explicit
disabled settings. Follow the printed command to start Hermes Gateway in a second
terminal, then restart Wright and refresh its page. The command prepares settings;
the browser's actual connection status establishes whether the service is ready.
Hermes continues to own its API server, model configuration and approvals.

Native workflow model requests use the installed Hermes SDK and the invoking
profile when that runtime is available. They do not require Hermes's HTTP model
selection extension. The bootstrap passes this binding only to Wright's child
process and preserves explicit custom transport/role settings. No credentials
are copied. Wright still probes and freezes the actual provider/model before a
run; missing or changed configuration remains a readiness/continuation error.
Browser chat continues to require the separately running Hermes gateway.

In terminal sessions, `/wright start` reports preparation immediately and shows
elapsed updates while its existing lifecycle operation is running.

## Update and removal

Hermes retains the adapter's `plugin.yaml` and `.git` metadata so its standard update command can fetch and verify the current mirror commit. Wright runtime updates remain separate `/wright update` operations.

Hermes 0.19 has no plugin pre-remove callback. Safely remove Wright with:

```text
/wright uninstall
hermes plugins remove wright
```

Normal uninstall preserves `WRIGHT_HOME/data`. To delete Wright-owned data,
request `/wright purge`, inspect the disclosed path and confirmation code, then
repeat the command with that code before removing the adapter.

## Development validation

Feature and pull-request validation uses an isolated local Git repository and
candidate wheelhouse. Do not install an unreleased branch as a production
substitute. The release train verifies the mirror commit, its generated
`PROVENANCE.md`, and the exact compatible
[`wright-engineering`](https://pypi.org/project/wright-engineering/) artifact.

## Migration From the Monorepo Subdirectory

Remove an older subdirectory-installed adapter and reinstall from the stable
root mirror shown above. Component packages remain workspace-local development
projects; their application modules ship inside the one public Wright runtime.

- Source: <https://github.com/burhop/wright>
- Issues: <https://github.com/burhop/wright/issues>
- Releases: <https://github.com/burhop/wright/releases>
