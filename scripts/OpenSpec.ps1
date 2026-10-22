# Pass CLI arguments through without PowerShell treating --flags as script parameters.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $projectRoot 'node_modules/@fission-ai/openspec/bin/openspec.js'
if (-not (Test-Path -LiteralPath $cli)) { throw 'OpenSpec is missing. Run scripts/Bootstrap.ps1.' }
$oldConfigRoot = $env:XDG_CONFIG_HOME
$oldTelemetry = $env:OPENSPEC_TELEMETRY
$result = 1
Push-Location $projectRoot
try {
    $env:XDG_CONFIG_HOME = Join-Path $projectRoot '.tooling'
    $env:OPENSPEC_TELEMETRY = '0'
    & node $cli @args
    $result = $LASTEXITCODE
} finally {
    $env:XDG_CONFIG_HOME = $oldConfigRoot
    $env:OPENSPEC_TELEMETRY = $oldTelemetry
    Pop-Location
}
exit $result
