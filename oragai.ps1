param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$scriptDir = $PSScriptRoot
$workspaceDir = Join-Path $scriptDir "workspace"

if (-not (Test-Path $workspaceDir)) {
    New-Item -ItemType Directory -Path $workspaceDir | Out-Null
}

$envFile = Join-Path $scriptDir ".env"
# Convert Windows path (e.g. C:\path or D:\path) to Docker-compatible volume path (/c/path or /d/path)
$normalizedWs = $workspaceDir.Replace("\", "/")
if ($normalizedWs -match '^([a-zA-Z]):(.*)$') {
    $drive = $matches[1].ToLower()
    $normalizedWs = "/$drive" + $matches[2]
}
$volumeArg = "${normalizedWs}:/workspace/orchestrator-ai-agent/workspace"

$isTty = [Environment]::UserInteractive -and (-not [Console]::IsInputRedirected)
$ttyFlag = if ($isTty) { "-it" } else { "-i" }

if ($Arguments.Count -eq 0) {
    docker run --rm $ttyFlag -v "$volumeArg" --env-file "$envFile" oragai:dev --check-config
} else {
    docker run --rm $ttyFlag -v "$volumeArg" --env-file "$envFile" oragai:dev @Arguments
}
