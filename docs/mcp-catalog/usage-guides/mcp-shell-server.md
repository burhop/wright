# Generic file transfer through mcp-shell-server

Observed 12 October 2026: independent provider
<https://github.com/tumf/mcp-shell-server>, version 1.1.12, source commit
`b71b694b463883fae4ae12dfb111d28a72c405da`. Provider source is unmodified.
This is a supporting file capability; CAD creation, measurement, mesh export
and rendering remain owned by their engineering providers.

## Verified boundary and setup

The native Windows Wright gateway initialized, listed and proxied the actual
`shell_execute` tool in a fresh minimal Linux container. A jq backend probe
returned 42. A durable connected-input canary passed in 3.440 seconds. This is
not a full clean-Linux-Wright catalog qualification or a production release.
See `artifacts/stevecad-demonstrations/qualification/generic-transfer-001/` and
`qualification/transfer-privacy-canary-002/` for exact arguments and receipts.

Selected image `wright-stevecad-transfer-clean:001`, image SHA-256
`963478d283a142f63b7cb377865a74eded05760b5d0ecfa80f685c80196ffbcc`, contains
Python 3.12, MCP SDK 1.30.0, h11 0.16.0, curl and jq. The container runs as UID
10001, with a read-only root, bounded tmpfs, no capabilities, no privilege
escalation, resource limits and only one fresh workspace output directory
mounted writable. No credentials or Docker socket are mounted. Entry point:
`python -c "from mcp_shell_server import main; main()"`. There is no `__main__`
module. Allow only the needed executable names: `curl,jq,sha256sum`.

The provider explicitly documents trusted execution: its command allowlist
does not constrain what allowed programs can do. OS isolation supplies those
boundaries. The selected internal network has no direct external DNS/route;
the explicit proxy allows HTTPS CONNECT only to `stevecad.studio:443`.
The disallowed-domain probe returned 403; direct external access failed.
The proxy has no published host port and does not log transfer requests.

## Successful calling conventions

`shell_execute` takes `command` as an argv array, optional `stdin`, optional
`directory`, and bounded integer `timeout`. Tool output is MCP text content. Wright's ordinary document output
port carries the MCP envelope; decode `.content[0].text | fromjson` when the
next jq operation needs JSON produced by a previous jq call. Output format and
output-port kind are separate declarations. Compile and inspect bindings before
dispatch; use `mcp_argument_ports` and actual item connections.

Use separate jq and curl tasks connected by a **text** output port. A literal
`"|"` argv entry selects the provider pipeline path, which ignores supplied
stdin in version 1.1.12 (verified in source and failed attempt 004). Do not use
a pipeline to carry a transfer credential. The validator also rejects literal
newlines in argv: keep jq programs on one line and encode embedded newlines as
JSON escapes. Semicolons are forbidden; for fixed-string substitution use
`split(marker) | join(value)` instead of a two-argument function with semicolon.
These are qualified calling constraints, not changes to provider source.

Native Blender safe mode rejects `bpy.data.texts.load`. Keep it enabled. A jq
step can read a declared nonsecret metadata artifact and return ordinary native
tool arguments from a fixed template with validated literals. Connect these
through `mcp_arguments_source: connection`; never add eval, exec, unrestricted
file reading or raw add-on socket calls.

**Observed limitation:** a program can exit nonzero and return stderr without
the provider setting MCP `isError`. A completed Wright run is therefore not
proof that the intended shell computation passed. Check exact output content,
fresh required artifacts and the downstream engineering producer's validation.
The first canary (`445963e66443498bb63a37ecf120eedf`) preserves this observation.
The corrected source unwraps the envelope; its exact output asserts that the
unredacted synthetic value was received, without returning that value.

## Transfer and privacy

Do not execute a returned shell command. In the accepted workflow, parse only
the documented HTTPS URL and header, check the pinned resource/revision/build,
and pass a curl configuration through stdin. Keep the one-use header out of
argv, source, prompts and saved outputs. The original export-instruction step
must not save its response. Use the exact scoped output destination, no redirect,
bounded transfer time/size, `--fail` and `--remove-on-error`. Downstream use must
depend on the freshly hashed actual file, not a written success claim.

Before real credentials, repeat the retained synthetic canary against any
changed persistence boundary. It proved current-run in-memory usability,
redacted run/event/API evidence, and no raw value in 265 scanned files including
runtime logs/database. This is a scoped observation, not a general secret-store
guarantee. Credential-bearing durable human-interaction continuations fail
closed; arrange expiring transfers within an uninterrupted declared section.

One-use transfers must not be replayed after an uncertain outcome. Inspect the
existing run, destination and provider response first. Do not stop an active
renderer or rebuild CAD because an observation request timed out. A new ticket,
fresh destination or source revision must be deliberate and identifiable.

## Remaining work

The actual SteveCAD export-to-three-view proof **passed in 62.007 seconds** in
run `646d7a74c124431e8979c3acea4b01de`, retained under
`qualification/automatic-native-render-chain-007/`. HTTP 200, exact STEP/GLB/PNG
hashes, native mesh validation and all 110 instance matches are verified. No
credential-bearing intermediate artifact is saved. Attempts 001–006 remain as
failure/recovery evidence, including pending native work observed to completion.
The generic per-design bindings subsequently completed inside main block v16,
including exact private STEP download, mesh validation and three native images.
See `prompt-to-reviewed-cad/block-native-003/native-run-audit.json`. Its final
review rejected the renderer's fallback appearance, so passing transfer is not
overall engineering acceptance. Full catalog clean-container qualification,
assembly main-process reuse, broader shell operations and physical actions remain
unverified. Changed-prompt block reuse now has actual same-source v19 evidence:
`block-native-006` and `six-hole-native-001` both complete exact private transfer,
mesh matching and six-image production. The latter retains an unrelated generated
intermediate-stock requirement as UNVERIFIED. See
`qualification/generic-render-binding-001/v19-reuse-audit.json` for source,
input, model-routing and producer-order checks.
No provider bug has been submitted. Investigate documented behavior and a small
reproduction before treating the nonzero-exit observation as a provider defect.
