<#
.SYNOPSIS
Request Steam startup, enter declared file2 mode and wait for bridge readiness.
.DESCRIPTION
Local menu-only keys, no screenshots, training or terminal pause. A fresh native
file2 run marker and one validated snapshot are required. New Run requires missing
saved-game evidence and an active Isaac snapshot; default remains Continue.
#>
[CmdletBinding()]
param(
    [ValidateRange(5, 600)]
    [int]$TimeoutSeconds = 180,
    [string]$GameDirectory,
    [string]$GameLog,
    [ValidateSet('continue', 'new-run')]
    [string]$EntryMode = 'continue',
    [switch]$PreflightOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    Write-Error 'Project Python is missing; run the documented project setup.'
    exit 2
}
$launchArguments = @(
    '-m', 'isaac_threrisaifuture.launcher',
    '--samples', '1', '--reconnects', '0',
    '--entry-mode', $EntryMode,
    '--duration', "$TimeoutSeconds", '--connection-timeout', "$TimeoutSeconds"
)
if ($GameDirectory) { $launchArguments += @('--game-directory', $GameDirectory) }
if ($GameLog) { $launchArguments += @('--game-log', $GameLog) }
if ($PreflightOnly) { $launchArguments += '--preflight-only' }
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath @launchArguments
    $launchExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $launchExitCode
