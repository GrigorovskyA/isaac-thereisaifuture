$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
function Invoke-PythonCheck {
    param([string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Check failed ($LASTEXITCODE): python $Arguments" }
}
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/Bootstrap.ps1 first.' }
    Invoke-PythonCheck @('-m', 'ruff', 'check', 'src', 'tests', 'scripts/smoke_rl.py')
    Invoke-PythonCheck @('-m', 'ruff', 'format', '--check', 'src', 'tests', 'scripts/smoke_rl.py')
    Invoke-PythonCheck @('-m', 'mypy')
    Invoke-PythonCheck @('-m', 'pytest', '-m', 'not game')
    Invoke-PythonCheck @('-m', 'pip', 'check')
    & (Join-Path $PSScriptRoot 'OpenSpec.ps1') validate --all --strict
    if ($LASTEXITCODE -ne 0) { throw 'OpenSpec strict validation failed.' }
    Write-Output 'Offline quality gates passed. No real-game integration was tested.'
} finally { Pop-Location }
