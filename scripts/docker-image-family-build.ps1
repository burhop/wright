param(
  [ValidateSet("standard", "linux-amd64", "linux-arm64", "windows-amd64")]
  [string]$Profile = "windows-amd64"
)

$ErrorActionPreference = "Stop"

$dockerSecretArgs = @()

function Use-GitHubSecret {
  if ($env:GITHUB_TOKEN) {
    $script:dockerSecretArgs = @("--secret", "id=github_token,env=GITHUB_TOKEN")
    return
  }
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    try {
      $token = gh auth token 2>$null
      if ($token) {
        $env:GITHUB_TOKEN = $token.Trim()
        $script:dockerSecretArgs = @("--secret", "id=github_token,env=GITHUB_TOKEN")
      }
    } catch {
      $script:dockerSecretArgs = @()
    }
  }
}

Use-GitHubSecret

switch ($Profile) {
  "standard" {
    $platform = $env:WRIGHT_DOCKER_PLATFORM
    if (-not $platform) { $platform = "linux/amd64" }
    $image = $env:WRIGHT_STANDARD_IMAGE
    if (-not $image) { $image = "wright:standard-linux-amd64" }
    docker build --platform $platform -t $image -f docker/Dockerfile .
  }
  "linux-amd64" {
    $platform = $env:WRIGHT_MCP_DOCKER_PLATFORM
    if (-not $platform) { $platform = "linux/amd64" }
    $baseImage = $env:WRIGHT_BASE_IMAGE
    if (-not $baseImage) { $baseImage = "wright:standard-linux-amd64" }
    $mcpImage = $env:WRIGHT_MCP_IMAGE
    if (-not $mcpImage) { $mcpImage = "wright:engineering-tools-linux-amd64" }
    $solidEdgeUrl = $env:WRIGHT_SOLIDEDGE_MCP_GIT_URL
    if (-not $solidEdgeUrl) { $solidEdgeUrl = "https://github.com/burhop/SolidEdgeMCP.git" }
    $solidEdgeRef = $env:WRIGHT_SOLIDEDGE_MCP_GIT_REF
    if (-not $solidEdgeRef) { $solidEdgeRef = "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330" }
    docker build --platform $platform -t $baseImage -f docker/Dockerfile .
    docker build @dockerSecretArgs --platform $platform -t $mcpImage -f docker/Dockerfile.mcp `
      --build-arg "WRIGHT_BASE_IMAGE=$baseImage" `
      --build-arg "WRIGHT_MCP_BUNDLE_FILE=mcp-bundle.yaml" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=$solidEdgeUrl" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=$solidEdgeRef" `
      .
  }
  "linux-arm64" {
    $platform = $env:WRIGHT_MCP_DOCKER_PLATFORM
    if (-not $platform) { $platform = "linux/arm64" }
    $baseImage = $env:WRIGHT_BASE_IMAGE
    if (-not $baseImage) { $baseImage = "wright:standard-linux-arm64" }
    $mcpImage = $env:WRIGHT_MCP_IMAGE
    if (-not $mcpImage) { $mcpImage = "wright:engineering-tools-linux-arm64" }
    $solidEdgeUrl = $env:WRIGHT_SOLIDEDGE_MCP_GIT_URL
    if (-not $solidEdgeUrl) { $solidEdgeUrl = "https://github.com/burhop/SolidEdgeMCP.git" }
    $solidEdgeRef = $env:WRIGHT_SOLIDEDGE_MCP_GIT_REF
    if (-not $solidEdgeRef) { $solidEdgeRef = "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330" }
    docker build --platform $platform -t $baseImage -f docker/Dockerfile .
    docker build @dockerSecretArgs --platform $platform -t $mcpImage -f docker/Dockerfile.mcp `
      --build-arg "WRIGHT_BASE_IMAGE=$baseImage" `
      --build-arg "WRIGHT_MCP_BUNDLE_FILE=mcp-bundle.linux-arm64.yaml" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=$solidEdgeUrl" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=$solidEdgeRef" `
      .
  }
  "windows-amd64" {
    $image = $env:WRIGHT_MCP_WINDOWS_IMAGE
    if (-not $image) { $image = "wright:engineering-tools-windows-amd64" }
    $solidEdgeUrl = $env:WRIGHT_SOLIDEDGE_MCP_GIT_URL
    if (-not $solidEdgeUrl) { $solidEdgeUrl = "https://github.com/burhop/SolidEdgeMCP.git" }
    $solidEdgeRef = $env:WRIGHT_SOLIDEDGE_MCP_GIT_REF
    if (-not $solidEdgeRef) { $solidEdgeRef = "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330" }
    $solidEdgeArchiveUrl = $env:WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL
    if (-not $solidEdgeArchiveUrl) {
      $archiveBase = $solidEdgeUrl
      if ($archiveBase.EndsWith(".git")) {
        $archiveBase = $archiveBase.Substring(0, $archiveBase.Length - 4)
      }
      if ($archiveBase -notmatch "^https://github\.com/[^/]+/[^/]+$") {
        throw "Set WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL for non-GitHub SolidEdgeMCP sources."
      }
      $solidEdgeArchiveUrl = "$archiveBase/archive/$solidEdgeRef.zip"
    }
    docker build --isolation=process -t $image -f docker/Dockerfile.windows.mcp `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=$solidEdgeUrl" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=$solidEdgeRef" `
      --build-arg "WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL=$solidEdgeArchiveUrl" `
      .
  }
}
