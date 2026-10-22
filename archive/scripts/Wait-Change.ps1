# Block (without an LLM) until a shared coordination file changes, then exit.
# Usage: ./scripts/Wait-Change.ps1 -Path agent-status.json [-TimeoutSeconds 3600]
#        [-States 'ready_for_review|needs_input|blocked']
# Exit 0 = changed (prints new hash), 2 = timeout. The last seen hash is kept
# locally, so a change made while the caller was busy is reported at once.
param(
    [Parameter(Mandatory)][string]$Path,
    [int]$TimeoutSeconds = 3600,
    [string]$States = ''
)
$ErrorActionPreference = 'Stop'
$seenDir = Join-Path $env:LOCALAPPDATA 'isaac-bus'
New-Item -ItemType Directory -Force -Path $seenDir | Out-Null
$seen = Join-Path $seenDir ((Split-Path $Path -Leaf) + '.sha')

function Get-Digest {
    try { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower() } catch { 'missing' }
}
function Test-State {
    if (-not $States) { return $true }
    try { (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json).state -match "^($States)$" } catch { $false }
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    $now = Get-Digest
    $last = if (Test-Path $seen) { (Get-Content -Raw $seen).Trim() } else { '' }
    if ($now -ne $last) {
        Start-Sleep -Seconds 2  # let a non-atomic writer finish
        if ((Get-Digest) -eq $now -and (Test-State)) {
            Set-Content -Path $seen -Value $now
            "changed $Path $now"; exit 0
        }
    }
    Start-Sleep -Seconds 5
}
"timeout $Path"; exit 2
