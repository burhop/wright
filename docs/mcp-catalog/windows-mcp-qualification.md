# Native Windows MCP Qualification

This workflow answers several different questions separately. A package may
install and speak MCP correctly even when its commercial engineering host is
not installed, signed in, licensed, or safe to modify. Wright must never reduce
those facts to one ambiguous `Compatible` or `Incompatible` label.

## Scope and allowlist

The native runner accepts exactly these identities, in this order:

1. `brep-mcp`
2. `solid-edge-mcp-burhop`
3. `aps-mcp-server-nodejs`
4. `autodesk-product-help-mcp`
5. `autodesk-fusion-desktop-mcp`
6. `autodesk-fusion-data-mcp`
7. `onshape-labs-featurescript-mcp`

Adding another identity requires a new reviewed recipe and a code change. The
CLI has no arbitrary command, package, repository, endpoint, environment, or
extra-server input.

## What the eight results mean

| Result group | Question answered |
|---|---|
| Source | Is this the reviewed publisher/source identity and revision? |
| Package or registration | Did the local package install, host bridge build, or remote endpoint registration complete? |
| Startup | Did the MCP process or service become available? |
| Protocol | Did MCP initialize and list tools? |
| Host app or backend | Did the approved read-only/disposable probe pass, or is a separate commercial host/account still needed? |
| Wright setup | Did Wright register the exact reviewed launch/endpoint locally? |
| Wright gateway | Could the same MCP be reached through the Wright/Hermes gateway? |
| Cleanup | Were qualification-owned processes and disposable files removed? |

Only current evidence with passed package/registration, startup, protocol,
Wright setup, and cleanup may carry the claim **Installs on Windows with no
problems**. A missing CAD host is reported independently as **MCP server
installed; host app needed**.

## Safe operator workflow

Normal tests use local fixtures only. They do not download or contact any MCP.

```powershell
uv run pytest packages/tool_registry/tests/test_windows_qualification_models.py packages/tool_registry/tests/test_windows_qualification_recipes.py packages/tool_registry/tests/test_windows_qualification_executor.py packages/tool_registry/tests/test_windows_qualification_service.py packages/tool_registry/tests/test_windows_qualification_writer.py packages/tool_registry/tests/test_windows_qualification_cli.py
```

For an approved native run, first preview the exact recipe:

```powershell
uv run python -m tool_registry.windows_qualification_cli preview brep-mcp --evidence-dir docs/mcp-catalog/evidence/windows-qualification-2026-08-13
```

Then supply a safety decision bound to the current recipe digest and use only a
dedicated ignored root:

```powershell
uv run python -m tool_registry.windows_qualification_cli qualify brep-mcp --evidence-dir docs/mcp-catalog/evidence/windows-qualification-2026-08-13 --work-root .local-run/windows-mcp-qualification --safety-decision .local-run/windows-mcp-qualification/decisions/brep-mcp.json
```

`qualify-all` accepts no server identity and follows the fixed order. Factual
partial, blocked, obsolete, and unavailable results are successful checkpoints;
only harness, safety-binding, schema, or cleanup failures produce an
infrastructure failure.

## Safety and evidence rules

- Perform the recorded safety review before any package installation, source
  build, server launch, endpoint connection, Wright registration, or tool call.
- Never request credentials, begin OAuth, accept publisher terms, install or
  upgrade commercial hosts, or modify a real engineering document.
- BREP is the sole exception to read-only probing, and only the reviewed
  deterministic program may write inside its disposable root.
- Use exact source revisions, package versions, artifact integrity, and network
  destinations from the recipe bundle.
- Do not pass ambient secrets to child processes. Raw commands, environment,
  output, tool arguments, private paths, and response content are not evidence.
- Save only bounded digests, counts, public identities, classifications,
  limitations, and recovery guidance. JSON is schema-validated and limited to
  1 MiB; Markdown is generated from the same redacted payload.
- Always attempt process-tree shutdown and isolated-root cleanup, even after a
  timeout or failed stage. `.local-run/` and downloaded source/build output stay
  ignored.

## Interpreting boundaries

- `passed`: the stated group was directly established on this Windows machine.
- `partial`: some evidence passed, but a separately named boundary remains.
- `failed`: an attempted bounded operation failed.
- `safety_blocked`: Wright deliberately did not cross a risk, terms, account,
  credential, or mutation boundary.
- `obsolete_or_unavailable`: the exact source is archived, absent, not yet
  released, or unavailable on this machine.
- `not_applicable`: the group does not apply to this server type.
- `not_tested`: no current evidence exists; this is not a failed install.

Evidence becomes stale when its recipe, source revision, package, tool schema,
machine binding, credential binding, or maximum age changes. Re-run the
qualification rather than carrying a historical pass forward.

