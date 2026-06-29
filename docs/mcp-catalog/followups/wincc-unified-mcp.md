# WinCC Unified MCP Follow-Up

Catalog ID: `wincc-unified-mcp`

Status: `blocked`

Source: https://support.industry.siemens.com/cs/document/110002407

## Validation Summary

Clean Intel Ubuntu validation could not obtain a public installable artifact for the official Siemens WinCC Unified PC Runtime MCP Server.

Evidence:

- Public search results confirm Siemens Support Entry ID `110002407`, titled `Integration of MCP Server with WinCC Unified PC Runtime`.
- Search results show a login-required artifact named `110002407_MCPServerPCRuntime_READMEOSS.zip`.
- Direct requests to the support page and PDF attachment returned HTTP 403 from Akamai.
- `npm view wincc-unified-mcp` returned npm 404.
- `npm view @siemens/wincc-unified-mcp` returned npm 404.
- `pip index versions wincc-unified-mcp` found no matching distribution.
- `pip index versions wincc_unified_mcp` found no matching distribution.
- `wincc-unified-mcp.exe --help` failed with `command not found` in Linux.
- Guessed Siemens GitHub repository URLs did not resolve publicly without authentication.

## Required Follow-Up

1. Use a Siemens Support account with access to Entry ID `110002407`.
2. Download the official MCP Server package and README/OSS zip.
3. Record the exact artifact filename, version, checksum, license notes, and install commands.
4. Validate on Windows with WinCC Unified PC Runtime installed.
5. Run MCP stdio probes: `initialize`, `notifications/initialized`, `tools/list`, a safe/status tool, and one backend-touching read operation against a non-production runtime.
6. Keep write/alarm/reset tools disabled or gated until a safety review defines acceptable test conditions.

## Expected Classification After Follow-Up

If the official artifact installs, starts, lists tools, and returns a clear diagnostic without a configured WinCC runtime, reclassify as `might_work` / `dependency_missing`.

Only classify as `tested` / `passed` after a meaningful backend read operation succeeds against a controlled WinCC Unified PC Runtime environment.
