param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$scriptDir = $PSScriptRoot
$workspaceDir = Join-Path $scriptDir "workspace"
$remoteWsPath = "/d/files/Contracted projects/IdeaProjects/orchestrator-ai-agent/workspace"

if (-not (Test-Path $workspaceDir)) {
    New-Item -ItemType Directory -Path $workspaceDir | Out-Null
}

$envFile = Join-Path $scriptDir ".env"
$volumeArg = "${remoteWsPath}:/workspace/orchestrator-ai-agent/workspace"

$isTty = [Environment]::UserInteractive -and (-not [Console]::IsInputRedirected)
$ttyFlag = if ($isTty) { "-it" } else { "-i" }

try {
    if ($Arguments.Count -eq 0) {
        docker run --rm $ttyFlag -v "$volumeArg" --env-file "$envFile" oragai:dev --check-config
    } else {
        docker run --rm $ttyFlag -v "$volumeArg" --env-file "$envFile" oragai:dev @Arguments
    }
} finally {
    if ($Arguments.Count -gt 0 -and -not ($Arguments -contains "--check-config")) {
        Write-Host "`n[Syncing files to Windows workspace...]" -ForegroundColor Cyan
        try {
            ssh -o BatchMode=yes crowz-debian@192.168.85.129 "tar -czf /tmp/oragai_ws_sync.tar.gz -C '$remoteWsPath' ."
            if ($LASTEXITCODE -eq 0) {
                $tarGz = Join-Path $scriptDir "oragai_ws_sync.tar.gz"
                scp -o BatchMode=yes crowz-debian@192.168.85.129:/tmp/oragai_ws_sync.tar.gz "$tarGz" 2>$null
                if (Test-Path $tarGz) {
                    tar -xzf "$tarGz" -C "$workspaceDir"
                    Remove-Item "$tarGz" -Force
                    ssh -o BatchMode=yes crowz-debian@192.168.85.129 "rm -f /tmp/oragai_ws_sync.tar.gz" 2>$null
                    Write-Host "[OK] Workspace synced to $workspaceDir" -ForegroundColor Green
                }
            }
        } catch {
        }
    }
}
