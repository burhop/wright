param(
    [ValidateRange(10, 300)]
    [int]$WaitSeconds = 90,
    [switch]$SkipDocker,
    [switch]$ServicesOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runRoot = Join-Path $repoRoot ".local-run\feature-081-live"
$dataRoot = Join-Path $runRoot "data"
$logRoot = Join-Path $runRoot "logs"
$workspaceRoot = Join-Path $env:USERPROFILE "wright-feature-081"
$workspaceName = "Engineering Workflow Demos"
$workspacePath = Join-Path $workspaceRoot "engineering-workflow-demos"
$hermesWorkRoot = Join-Path $workspaceRoot "hermes-agent-runtime"
$apiBase = "http://127.0.0.1:8000"
$webBase = "http://127.0.0.1:5173"
$hermesBase = "http://127.0.0.1:8642"

$null = New-Item -ItemType Directory -Force -Path $dataRoot, $logRoot, $workspaceRoot, $workspacePath, $hermesWorkRoot

function Test-HttpEndpoint {
    param([Parameter(Mandatory)][string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 3
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Wait-HttpEndpoint {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Uri
    )

    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    do {
        if (Test-HttpEndpoint -Uri $Uri) {
            return
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "$Name did not become ready at $Uri within $WaitSeconds seconds."
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory)][string]$HostName,
        [Parameter(Mandatory)][int]$Port,
        [int]$TimeoutMilliseconds = 750
    )

    $client = [Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.ConnectAsync($HostName, $Port)
        return $pending.Wait($TimeoutMilliseconds) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Wait-TcpPort {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$HostName,
        [Parameter(Mandatory)][int]$Port
    )

    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    do {
        if (Test-TcpPort -HostName $HostName -Port $Port) {
            return
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "$Name did not become ready at ${HostName}:$Port within $WaitSeconds seconds."
}

function Start-HiddenProcess {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory
    )

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "$Name.out.log") `
        -RedirectStandardError (Join-Path $logRoot "$Name.err.log") `
        -PassThru
    Set-Content -LiteralPath (Join-Path $runRoot "$Name.pid") -Value $process.Id
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory)][ValidateSet("Get", "Post", "Put", "Patch")][string]$Method,
        [Parameter(Mandatory)][string]$Uri,
        [object]$Body
    )

    $parameters = @{
        Method = $Method
        Uri = $Uri
        UseBasicParsing = $true
    }
    if ($null -ne $Body) {
        $parameters.ContentType = "application/json"
        $parameters.Body = $Body | ConvertTo-Json -Depth 12 -Compress
    }
    return Invoke-RestMethod @parameters
}

# Keep all feature data separate from an existing Wright installation.
$env:WRIGHT_DATA_ROOT = $dataRoot
$env:WRIGHT_WORKSPACES_DIR = $workspaceRoot
$env:WRIGHT_WORKSPACE_ROOT = $workspaceRoot
$env:HERMES_API_BASE_URL = $hermesBase
$env:WRIGHT_AUTH_MODE = "compat"
$env:WRIGHT_RIVET_WORKFLOWS_ENABLED = "1"
$env:WRIGHT_RIVET_EDITOR_ENABLED = "1"
$env:WRIGHT_RIVET_AI_ENABLED = "1"
$env:WRIGHT_RIVET_RUNNER_ENABLED = "1"
$env:WRIGHT_RIVET_REAL_EXECUTION_ENABLED = "1"
$env:WRIGHT_WORKFLOW_INTEGRATION_TESTS = "1"
$env:WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED = "1"
$env:WRIGHT_RIVET_MCP_GATEWAY_ENABLED = "1"
$env:WRIGHT_API_MCP_AUTOSTART = "0"
$env:WRIGHT_SURFACES_ENABLED = "1"
$env:WRIGHT_SURFACES_LIVE_APPS_ENABLED = "1"
$env:VITE_WRIGHT_PROCESS_DEFINITION_VIEW = "1"
$env:VITE_WRIGHT_WORKFLOW_COMPOSER = "1"
$env:VITE_WRIGHT_WORKFLOW_RECOVERY = "1"

# Reuse the existing local Hermes gateway key in memory so Wright can list
# models and create sessions. Never print or copy the credential into the repo.
$hermesEnvCandidates = @(
    (Join-Path $env:LOCALAPPDATA "hermes\.env"),
    (Join-Path $env:USERPROFILE ".hermes\.env")
)
foreach ($candidate in $hermesEnvCandidates) {
    if (-not (Test-Path -LiteralPath $candidate)) {
        continue
    }
    foreach ($line in Get-Content -LiteralPath $candidate) {
        if ($line -notmatch '^\s*(HERMES_API_KEY|API_SERVER_KEY)\s*=\s*(.+?)\s*$') {
            continue
        }
        $value = $Matches[2].Trim().Trim('"').Trim("'")
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $env:HERMES_API_KEY = $value
            break
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($env:HERMES_API_KEY)) {
        break
    }
}

$toolDirectories = @(
    (Join-Path $runRoot "tools\bambu-studio-2.8.2.61"),
    (Join-Path $runRoot "tools\blender-4.5.10\blender-4.5.10-windows-x64"),
    (Join-Path $runRoot "tools\prusaslicer-2.9.6\PrusaSlicer-2.9.6"),
    (Join-Path $runRoot "sources\solid-edge-campaign-001\src\SolidEdgeMcpServer\bin\Release\net10.0-windows"),
    "D:\repos\SolidEdgeMCP\src\SolidEdgeMcpServer\bin\Release\net10.0-windows"
) | Where-Object { Test-Path -LiteralPath $_ }
if ($toolDirectories.Count -gt 0) {
    $env:PATH = (($toolDirectories -join [IO.Path]::PathSeparator) + [IO.Path]::PathSeparator + $env:PATH)
}
$bambuStudio = Join-Path $runRoot "tools\bambu-studio-2.8.2.61\bambu-studio.exe"
if (Test-Path -LiteralPath $bambuStudio) {
    $env:BAMBU_SLICER = $bambuStudio
}
$bambuProfiles = Join-Path $runRoot "tools\bambu-studio-2.8.2.61\resources\profiles\BBL"
$bambuMachine = Join-Path $bambuProfiles "machine\Bambu Lab P1S 0.4 nozzle.json"
$bambuProcess = Join-Path $bambuProfiles "process\0.20mm Standard @BBL X1C.json"
$bambuFilament = Join-Path $bambuProfiles "filament\Bambu PLA Basic @BBL P1S 0.4 nozzle.json"
if (Test-Path -LiteralPath $bambuMachine) { $env:BAMBU_MACHINE_JSON = $bambuMachine }
if (Test-Path -LiteralPath $bambuProcess) { $env:BAMBU_PROCESS_JSON = $bambuProcess }
if (Test-Path -LiteralPath $bambuFilament) { $env:BAMBU_FILAMENT_JSON = $bambuFilament }
$env:BLENDER_USER_SCRIPTS = Join-Path $runRoot "tools\blender-user\scripts"
$env:BLENDER_USER_CONFIG = Join-Path $runRoot "tools\blender-user\config"
$null = New-Item -ItemType Directory -Force -Path $env:BLENDER_USER_CONFIG
$env:BLENDER_MCP_DISABLE_TELEMETRY = "true"
$env:BLENDER_MCP_SAFE_MODE = "true"
$env:WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS = "540"
$env:WRIGHT_MCP_MAX_TIMEOUT = "600"

if (-not (Test-HttpEndpoint -Uri "$hermesBase/health")) {
    $hermes = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\hermes.exe"
    if (-not (Test-Path -LiteralPath $hermes)) {
        throw "Hermes is not installed at $hermes."
    }
    # Hermes's OpenAI-compatible API server is a decision service for Wright.
    # Keep its process cwd outside the repository so an accidentally enabled
    # Hermes host tool cannot create untracked files in the source checkout.
    Start-HiddenProcess -Name "hermes-gateway" -FilePath $hermes -ArgumentList @("gateway", "run") -WorkingDirectory $hermesWorkRoot
}
Wait-HttpEndpoint -Name "Hermes gateway" -Uri "$hermesBase/health"

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Wright Python environment is missing at $python."
}
# The normal snapshot authority intentionally preserves a previously activated
# catalog across restarts. This source-tree demo launcher also reconciles the
# current checked-out catalog so newly authored candidates are available for
# local qualification without activating an unsigned update channel.
& $python -c "from api.config import DATABASE_PATH; from tool_registry.catalog_reconcile import reconcile_engineering_catalog; reconcile_engineering_catalog(DATABASE_PATH)"
if ($LASTEXITCODE -ne 0) {
    throw "The checked-out engineering MCP catalog could not be reconciled."
}
$demoApiStarted = $false
if (-not (Test-HttpEndpoint -Uri "$apiBase/api/health")) {
    Start-HiddenProcess -Name "wright-api" -FilePath $python -ArgumentList @(
        "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"
    ) -WorkingDirectory $repoRoot
    $demoApiStarted = $true
}

$node = Get-Command node.exe -ErrorAction SilentlyContinue
$vite = Join-Path $repoRoot "node_modules\vite\bin\vite.js"
if (-not (Test-HttpEndpoint -Uri "$webBase/")) {
    if ($null -eq $node -or -not (Test-Path -LiteralPath $vite)) {
        throw "Node or the installed Vite dependency is missing."
    }
    Start-HiddenProcess -Name "wright-web" -FilePath $node.Source -ArgumentList @(
        $vite, "--host", "127.0.0.1", "--port", "5173", "--strictPort"
    ) -WorkingDirectory (Join-Path $repoRoot "apps\web")
}
Wait-HttpEndpoint -Name "Wright API" -Uri "$apiBase/api/health"
Wait-HttpEndpoint -Name "Wright web UI" -Uri "$webBase/"

# Both the launcher and API startup synchronize catalog defaults. Restore the
# explicitly installed bootstrap only after the API's synchronization finishes.
$demoBootstrapJson = & $python (Join-Path $repoRoot "scripts/configure-agentcad-demo-bootstrap.py") --run-root $runRoot --database (Join-Path $dataRoot "wright.db")
if ($LASTEXITCODE -ne 0) {
    throw "The installed demo AgentCAD bootstrap could not be verified."
}
$demoBootstrap = $demoBootstrapJson | ConvertFrom-Json
if ($demoApiStarted -and $demoBootstrap.configured -and $demoBootstrap.changed) {
    # Retire only a freshly autostarted host before this launcher enables it
    # below. Reusing a running API must not interrupt an existing native call.
    $null = Invoke-JsonRequest -Method Patch -Uri "$apiBase/api/mcp/servers/agentcad" -Body @{ is_active = $false }
}

if ($ServicesOnly) {
    [pscustomobject]@{
        mode = "services_only"
        wright_api_health = "$apiBase/api/health"
        hermes_health = "$hermesBase/health"
        workspace_url = $webBase
        agentcad_bootstrap = $demoBootstrap
        native_application_start_requested = $false
    } | ConvertTo-Json
    return
}

$blender = Join-Path $runRoot "tools\blender-4.5.10\blender-4.5.10-windows-x64\blender.exe"
$blenderAddonSource = Join-Path $runRoot "sources\blender-mcp\addon.py"
$blenderAddonDirectory = Join-Path $env:BLENDER_USER_SCRIPTS "addons"
if ((Test-Path -LiteralPath $blender) -and (Test-Path -LiteralPath $blenderAddonSource)) {
    $null = New-Item -ItemType Directory -Force -Path $blenderAddonDirectory
    Copy-Item -LiteralPath $blenderAddonSource -Destination (Join-Path $blenderAddonDirectory "blender_mcp.py") -Force
    if (-not (Test-TcpPort -HostName "127.0.0.1" -Port 9876)) {
        Start-HiddenProcess -Name "blender-mcp-host" -FilePath $blender -ArgumentList @(
            "--python", (Join-Path $repoRoot "scripts\windows\blender-mcp-host.py")
        ) -WorkingDirectory $workspacePath
    }
    Wait-TcpPort -Name "Blender MCP add-on" -HostName "127.0.0.1" -Port 9876
}

$workspaceList = Invoke-JsonRequest -Method Get -Uri "$apiBase/api/workspace/list"
$workspace = $workspaceList.workspaces | Where-Object { $_.workspace_name -eq $workspaceName } | Select-Object -First 1
if ($null -eq $workspace) {
    $workspace = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/workspace/create" -Body @{
        name = $workspaceName
        local_path = $workspacePath
    }
}

$serverList = Invoke-JsonRequest -Method Get -Uri "$apiBase/api/mcp/servers"
$solidEdge = $serverList.servers | Where-Object { $_.server_id -eq "solid-edge-mcp-burhop" } | Select-Object -First 1
if ($null -ne $solidEdge) {
    $null = Invoke-JsonRequest -Method Put -Uri "$apiBase/api/mcp/servers/solid-edge-mcp-burhop/credentials" -Body @{
        credentials = @{
            CADMCP_SOLID_EDGE_ALLOWED_ROOTS = $workspace.local_path
        }
    }
}

$workspaceServers = @(
    "rivet-workflows",
    "agentcad",
    "blender-mcp-ahujasid",
    "solid-edge-mcp-burhop"
)
foreach ($serverId in @("agentcad", "blender-mcp-ahujasid", "solid-edge-mcp-burhop")) {
    $server = $serverList.servers | Where-Object { $_.server_id -eq $serverId } | Select-Object -First 1
    if ($null -eq $server) {
        continue
    }
    if (-not $server.is_installed) {
        $null = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/mcp/servers/$serverId/install?session_id=$([uri]::EscapeDataString($workspace.session_id))"
    }
    $null = Invoke-RestMethod -Method Patch -ContentType "application/json" -Uri "$apiBase/api/mcp/servers/$serverId" -Body '{"is_active":true}'
}
foreach ($serverId in $workspaceServers) {
    $null = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/workspace/by-id/$($workspace.workspace_id)/tools/toggle" -Body @{
        server_id = $serverId
        is_enabled = $true
    }
}

$templatePaths = @{
    "printed-replacement-part" = "workflows/printed-replacement-part.workflow.wflow"
    "raspberry-pi-enclosure" = "workflows/raspberry-pi-enclosure.workflow.wflow"
    "sheet-metal-supplier-handoff" = "workflows/sheet-metal-supplier-handoff.workflow.wflow"
}
$catalog = Invoke-JsonRequest -Method Get -Uri "$apiBase/api/workspace/workflow-source-templates"
foreach ($templateId in $templatePaths.Keys) {
    $relativePath = $templatePaths[$templateId]
    $absolutePath = Join-Path $workspace.local_path ($relativePath -replace "/", "\")
    if (Test-Path -LiteralPath $absolutePath) {
        continue
    }
    $template = $catalog.templates | Where-Object { $_.template_id -eq $templateId } | Select-Object -First 1
    if ($null -eq $template) {
        throw "Engineering template $templateId is missing from the served catalog."
    }
    $requestId = "demo-bootstrap-$([guid]::NewGuid().ToString('N'))"
    $null = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/workspace/workflow-source-templates/$templateId/instances" -Body @{
        session_id = $workspace.session_id
        template_version = $template.version
        expected_source_digest = $template.source_digest
        workflow_path = $relativePath
        request_id = $requestId
    }
}

if (-not $SkipDocker -and (Get-Command docker.exe -ErrorAction SilentlyContinue)) {
    try {
        $foamScratch = Join-Path $runRoot "foam-agent-workspace"
        $null = New-Item -ItemType Directory -Force -Path $foamScratch
        $imageId = docker image inspect leoyue123/foamagent:latest --format "{{.Id}}" 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($imageId)) {
            $containerState = docker inspect wright-foam-agent --format "{{.State.Running}}" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $null = docker run --detach --name wright-foam-agent --env FOAMAGENT_SKIP_UPDATE=1 --env FOAMAGENT_MODEL_PROVIDER=openai --env OPENAI_API_KEY=WRIGHT_PROTOCOL_ONLY_DUMMY --publish 127.0.0.1:7860:7860 --volume "${foamScratch}:/workspace" leoyue123/foamagent:latest python -m src.mcp.cli --transport http --host 0.0.0.0 --port 7860
            }
            elseif ($containerState -ne "true") {
                $null = docker start wright-foam-agent
            }
        }
    }
    catch {
        Write-Warning "Foam-Agent was not started: $($_.Exception.Message)"
    }
}

$foamAgentReady = Test-TcpPort -HostName "127.0.0.1" -Port 7860
if ($foamAgentReady) {
    $serverList = Invoke-JsonRequest -Method Get -Uri "$apiBase/api/mcp/servers"
    $foamAgent = $serverList.servers | Where-Object { $_.server_id -eq "foam-agent-csml-rpi" } | Select-Object -First 1
    if ($null -ne $foamAgent) {
        if (-not $foamAgent.is_installed) {
            $null = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/mcp/servers/foam-agent-csml-rpi/install?session_id=$([uri]::EscapeDataString($workspace.session_id))"
        }
        $null = Invoke-RestMethod -Method Patch -ContentType "application/json" -Uri "$apiBase/api/mcp/servers/foam-agent-csml-rpi" -Body '{"is_active":true}'
        $null = Invoke-JsonRequest -Method Post -Uri "$apiBase/api/workspace/by-id/$($workspace.workspace_id)/tools/toggle" -Body @{
            server_id = "foam-agent-csml-rpi"
            is_enabled = $true
        }
    }
}

$workspaceUrl = "$webBase/workspace/$($workspace.workspace_id)"
[pscustomobject]@{
    workspace_url = $workspaceUrl
    workspace_id = $workspace.workspace_id
    session_id = $workspace.session_id
    workspace_path = $workspace.local_path
    hermes_health = "$hermesBase/health"
    wright_api_health = "$apiBase/api/health"
    foam_agent_mcp = "http://127.0.0.1:7860/mcp"
    foam_agent_ready = $foamAgentReady
} | ConvertTo-Json -Depth 4
