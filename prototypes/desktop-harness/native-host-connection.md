# Native GB10-hosted desktop connection proposal

The user approved the scoped GB10 installation. Version 0.1.1 is installed and
enabled; the existing daemon accepted a queued MCP refresh. This active turn
still has no Wright connection. See native-host-install-evidence.json. This adds
a choice; the delivered Windows SSH-wrapper
archive and its frozen target are retained without modification.

## Correction to the earlier host assumption

The app reports this chat's execution host as
`remote-ssh-discovered:promaxgb10-9666`, with GB10 workspace
`/home/burhop/repos/wright`. The GUI being on Windows does not by itself imply
that this chat's MCP commands execute on Windows. Official documentation describes
remote project execution and configuration shared by clients on the same Codex
host. That supports trying native GB10 configuration first for this chat; it
does not yet prove this private plugin loads in the installed app.

Sources: [remote connections](https://learn.chatgpt.com/docs/remote-connections)
and [host MCP configuration](https://learn.chatgpt.com/docs/extend/mcp).
Observed facts, command checks and hashes: native-host-candidate-evidence.json.

## Exact package and prepared target

- Separate marketplace/plugin: `wright-desktop-gb10-prototype`.
- Package root:
  `/tmp/wright-openai-desktop-harness-prototype-next/prototypes/desktop-harness/native-host-candidate`.
- MCP server entry: `wright-desktop-gb10`, executing the pinned new-worktree
  Python and bridge directly on GB10. No nested Windows SSH process or model
  worker is introduced. The unchanged existing workflow skill is copied/versioned.
- Fresh private state: `/tmp/wright-desktop-native-host-target-20261011-01`.
- API: GB10 loopback 8116; editor: GB10 loopback 5216, proxying API internally.
- Qualified combined runtime profile: `wright-desktop-prototype:94544ecd94c725d808397776d6e8703cc6aa250656da6e7ee3afdb24b57ff522`.
- The exact manifest command initialized real MCP protocol 2025-11-25 and
  listed 12 tools. Connection read succeeded; workspace/start/request counts
  remain zero. This is protocol verification, not installed-host acceptance.

The API reads its credential from a private local file. No credential is included
in this package, command, chat or screenshot. Other tools and original-image
inputs remain gated; confined inspection requires an exact private enrollment
that the plugin cannot create.

## Approved changes — executed

On GB10, for this existing remote chat's host:

```bash
codex plugin marketplace add /tmp/wright-openai-desktop-harness-prototype-next/prototypes/desktop-harness/native-host-candidate
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype
```

CLI 0.159.2 help confirms the install form. Marketplace registration, cache
installation and enablement were observed. The initial portable 0.1.0 package
loaded its skill but omitted bundled MCP. The tested 0.1.1 package uses the
documented `.codex-plugin/plugin.json` and `.mcp.json` compatibility layout.
A fresh metadata-only loader discovers 12 tools; the actual active chat still
reports zero Wright servers after the accepted refresh queue. Preserve a private
before/after configuration comparison and change only this plugin/marketplace
in `/home/burhop/.codex/config.toml` and its cache. Inspection found no Wright
plugin/MCP entries; before config SHA-256 was
695791b28bbf618adb8d4dd7e7926fa7b5fd71a843b123b446456537310d75fb; after is
2056dbaf239dc1f64776e2baa97ce959de6b28bc3dfeeb839a7280fcb13f3da1.
Only the named marketplace source/type and plugin enablement changed. The
installer cleaned old cache version 0.1.0; its exact package and failures remain
in `/tmp/wright-desktop-native-install-20261011-01/source-0.1.0`. Never restore
a full old configuration over concurrent changes.

Do not quit/restart the desktop or interrupt other chats. Public
`config/mcpServer/reload` accepted a refresh queue without a daemon restart.
Its protocol has no thread filter; this queues loaded-thread refresh, while
all unrelated settings were verified unchanged. Verify actual tool discovery
in the next turn; queue acceptance is not tool attachment. If new tools cannot attach
to this chat without disruptive restart, report that requirement for review.
A CLI install receipt alone is not proof of installed desktop use.

## Installed journey and browser route

Use the actual discovered tools in this same desktop conversation for connection
status, fresh workspace/source creation, preparation/start, bounded reasoning
and durable result readback. Then qualify declared input on the same run.
No Hermes or SDK/app-server model worker supplies replies. Wright retains every
execution, validation, review, gateway and recovery owner.

Windows rendering is a separate boundary. A Windows browser URL using localhost
5216 cannot be assumed to reach GB10. Observe a supported host-aware browser
route or prepare an explicitly reviewed loopback forward on Windows. The earlier
browser-open request had an uncertain outcome: do not automatically retry it.
No public listener, authentication removal or silent browser fallback is allowed.
Native conversation panels are documented, but no Wright-native panel is claimed.

After rendering is actually observed, enter via Workflows and preserve authoring
capabilities. Capture a clean desktop chat-and-Wright image. Browser open requests
or GB10 screenshots are not equivalent installed Windows proof.

## Rollback for this one new package

```bash
codex plugin remove wright-desktop-gb10-prototype@wright-desktop-gb10-prototype
codex plugin marketplace remove wright-desktop-gb10-prototype
```

Compare only affected entries and preserve concurrent user changes. Never restore
a whole old config or delete workflows/runs/evidence during rollback. The old
Windows-wrapper package/target and earlier chat pilot remain separate.
