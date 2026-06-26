# Wright with Hermes Desktop

This guide covers the browser-based Wright integration for Hermes Desktop.
Hermes Desktop can load the Wright slash command plugin, and `/wright start`
then starts the Wright API and opens the Wright UI in the default browser.

## Requirements

- Hermes Desktop installed and logged in.
- Wright available on disk.
- `uv`, Python, Node.js, and npm available to the user running Hermes Desktop.
- A reachable LLM endpoint if you want the Wright LLM status light to be green.

## Important: Hermes API Server

Installing Hermes Desktop is not enough for Wright to show as connected to
Hermes. Wright talks to the Hermes API Server, which is exposed by Hermes when
the API server feature is enabled.

Set these environment values for the same Windows user that runs Hermes Desktop:

```powershell
setx API_SERVER_ENABLED true
setx API_SERVER_HOST 127.0.0.1
setx API_SERVER_PORT 8642
setx API_SERVER_KEY wright-local-dev
setx HERMES_API_BASE_URL http://127.0.0.1:8642
setx HERMES_API_KEY wright-local-dev
```

Hermes Desktop reads the local app data env file during backend startup:

```text
%LOCALAPPDATA%\hermes\.env
```

For compatibility with CLI/profile launches, the VM image scripts also write:

```text
%USERPROFILE%\.hermes\.env
```

Then fully quit Hermes Desktop from the system tray and start it again. If the
gateway is not already running, start it from a Hermes-enabled terminal:

```powershell
hermes gateway run
```

For repeatable Windows test images, install the gateway auto-start task instead:

```powershell
hermes gateway install
```

A healthy Hermes API connection should make Wright's Hermes status endpoint
return `connected`:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/agent/health
```

Expected response shape:

```json
{"state":"connected","baseUrl":"http://127.0.0.1:8642"}
```

## Plugin Load Paths on Windows

Hermes Desktop may load plugins from its bundled agent directory, not only from
the profile plugin directory. During Windows VM validation, the active Wright
plugin path was:

```text
%LOCALAPPDATA%\hermes\hermes-agent\plugins\wright
```

The profile agent path is also useful:

```text
%USERPROFILE%\.hermes\hermes-agent\plugins\wright
```

Avoid installing a stale duplicate at:

```text
%USERPROFILE%\.hermes\plugins\wright
```

After replacing plugin files, fully quit Hermes Desktop from the system tray
before restarting it. Hermes can cache loaded plugin modules in memory.

## LLM Status Light

The Wright LLM status light checks Wright's configured LLM URL, not the Hermes
API Server. Configure it in Wright setup or set:

```powershell
setx LLM_API_URL http://192.168.1.165:8000/v1
```

For OpenAI-compatible vLLM servers, Wright derives the health check from the
base URL by using `/health`, for example:

```text
http://192.168.1.165:8000/health
```

## Fresh Install Hygiene

Fresh VM/user installs should not copy Wright runtime state from a development
checkout. Do not copy these files into a user's install:

```text
apps/api/state.db
apps/api/state.db-wal
apps/api/state.db-shm
apps/api/state.db-journal
*.log
*.pid
tmp/
```

The Windows VM scripts exclude these files and clear VM-side Wright runtime
state before seeding only the intended clean settings.

## Troubleshooting

If `/wright` is not recognized:

```powershell
hermes plugins list
hermes plugins enable wright
```

If Wright opens but the Hermes light is red:

```powershell
Invoke-WebRequest http://127.0.0.1:8642/health -Headers @{ Authorization = "Bearer wright-local-dev" }
Invoke-WebRequest http://127.0.0.1:8000/api/agent/health
```

If `8642` does not respond, the fix is to write the API settings to
`%LOCALAPPDATA%\hermes\.env` and run `hermes gateway run` or
`hermes gateway install`. The Wright plugin's `/wright start` command now does
a best-effort repair by writing the env files and starting Gateway in the
background.

If Wright opens but the LLM light is red:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/setup/status
Invoke-WebRequest http://127.0.0.1:8000/api/inference/health
```

If a plugin change appears to do nothing, quit Hermes Desktop from the system
tray and restart it.
