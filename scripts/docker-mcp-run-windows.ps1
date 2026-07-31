param(
  [string]$Image = $(if ($env:WRIGHT_MCP_WINDOWS_IMAGE) { $env:WRIGHT_MCP_WINDOWS_IMAGE } else { "wright:engineering-tools-windows-amd64" }),
  [string]$Name = $(if ($env:WRIGHT_MCP_WINDOWS_CONTAINER) { $env:WRIGHT_MCP_WINDOWS_CONTAINER } else { "wright_mcp_windows_amd64" })
)

$ErrorActionPreference = "Stop"

docker run -d `
  --name $Name `
  --isolation=process `
  -v wright_mcp_windows_data:C:\wright\data `
  -v wright_mcp_windows_workspace:C:\wright\workspace `
  -v wright_mcp_windows_config:C:\wright\config `
  -v wright_mcp_windows_hermes:C:\wright\hermes `
  -v wright_mcp_windows_logs:C:\wright\logs `
  $Image

Write-Host "Started $Image as $Name"
