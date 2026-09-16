# Solid Edge native MCP required-null result serialization

The feature-081 campaign's native `cad.get_status` failed Python MCP SDK output
validation when no document was open. Its advertised schema requires nullable
`activeDocument`, but the server omitted it. Before application startup it also
omitted required nullable `version`. These were real protocol failures.

The registered Solid Edge 2026 executable is
`D:/Program Files/Siemens/Solid Edge 2026/Program/Edge.exe`. The earlier MCP
`cad.connect(startIfNeeded=true,visible=false)` timed out. An explicit hidden
`Edge.exe /automation` launch subsequently worked: the native status response
reported `isAvailable=true`, `isConnected=true`, version `226.00.01.04`.
No document was opened or modified by these prerequisite probes.

The installed MCP SDK 1.4.0 documents `WhenWritingNull` in its default serializer
options. The server declares required nullable result fields, so its tool
registration must retain nulls. `scripts/prepare-solid-edge-campaign-host.py`
copies only build inputs from the selected local checkout, hashes every copied
file, and replaces `WithToolsFromAssembly()` with the same registration using
cloned SDK options and `DefaultIgnoreCondition=Never`. It does not insert missing
values into responses or relax output schemas.

The local upstream checkout contains substantial existing uncommitted work.
Its base commit is `f58a783d2bfad4cff97c818bb63d42c1485d305a`; the selected source
identity is the entire recorded working-tree snapshot, not that commit alone.
The original checkout and installed binary were preserved.

Reproduction from the Wright root:

```powershell
.venv/Scripts/python.exe scripts/prepare-solid-edge-campaign-host.py --source D:/repos/SolidEdgeMCP --destination .local-run/feature-081-live/sources/solid-edge-campaign-001
dotnet build .local-run/feature-081-live/sources/solid-edge-campaign-001/src/SolidEdgeMcpServer/SolidEdgeMcpServer.csproj -c Release --nologo -v quiet
```

Use a fresh snapshot suffix when the target already exists. Native build passed
with zero warnings/errors. A fresh Python MCP client accepted the repaired
status response. Full-mode direct protocol/discovery and Wright GatewayService
status probes passed with 59 tools. Evidence:

- `.local-run/feature-081-live/solid-edge-native-start.json`
- `.local-run/feature-081-live/solid-edge-started-status-probe.json` (original failure)
- `.local-run/feature-081-live/sources/solid-edge-campaign-001/snapshot-manifest.json`
- `.local-run/feature-081-live/solid-edge-repaired-status-probe.json`
- `.local-run/feature-081-live/solid-edge-repaired-native-gateway-qualification.json`

The older `solid-edge-repaired-gateway-qualification.json` is superseded: the
generic helper initially hardcoded Linux/container metadata despite its native
invocation. The helper now accepts explicit platform/environment/workspace
arguments; the replacement evidence above is a fresh Windows native run.

This is a native prerequisite repair, not a clean Linux container qualification
or a complete sheet-metal engineering run. No public qualification fields were
promoted. The demo launcher prefers the isolated build directory on its own
PATH; another running API must restart before using that selection. Fresh tool
discovery and policy enrollment are required before campaign execution.

Proposed upstream follow-up: adopt the registration serializer change and add
connected/no-document and disconnected structured-output contract regressions.
No upstream files, branch, pull request or push were changed for this repair.
