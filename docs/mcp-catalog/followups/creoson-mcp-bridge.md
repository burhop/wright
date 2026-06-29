# CREOSON MCP Bridge Follow-Up

Catalog ID: `creoson-mcp-bridge`

Status: `blocked`

Source: https://github.com/SimplifiedLogic/creoson

## Validation Summary

CREOSON is a valid Creo Parametric JSON/JLINK micro-server, but it is not an MCP protocol server.

Container evidence:

- Source cloned at commit `1939a585a1fcc94b6c05586af92c2da00adebdb0`.
- Release `v3.0.1` asset `CreosonServer-3.0.1-win64.zip` downloaded successfully.
- Source build instructions require a Creo installation with JLINK `text/java/pfcasync.jar`, CreosonSetup ZIPs, Commons Codec, and Jackson jars.
- Release ZIP includes `CreosonServer-3.0.0.jar`, support JARs, `creoson_run.bat`, and `jshellnative.dll`.
- `java -jar CreosonServer-3.0.0.jar` returned `no main manifest attribute`.
- Calling `com.simplifiedlogic.nitro.jshell.MainServer` with the release JARs returned `NoClassDefFoundError: com/ptc/cipjava/jxthrowable`.
- No MCP `initialize` or `tools/list` calls could be made because CREOSON does not implement MCP stdio/SSE.

## Required Follow-Up

1. Decide whether CREOSON should remain in the MCP catalog as a blocked capability alias or move to a backend dependency catalog.
2. If Wright needs direct CREOSON MCP support, implement or find an MCP wrapper that exposes MCP stdio/SSE and calls the CREOSON HTTP JSON endpoint.
3. Validate the wrapper against a controlled Windows host with Creo, JLINK, and CREOSON running.
4. Keep machine-control approval gates enabled for all write/regeneration/import operations.

## Expected Classification After Follow-Up

If a real wrapper is added and can initialize, list tools, and perform a safe read against CREOSON, reclassify the wrapper entry as `might_work` or `tested` depending on whether a real Creo backend operation succeeds.

CREOSON itself should remain a backend dependency, not a standalone MCP server.
