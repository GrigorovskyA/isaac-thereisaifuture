$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & (Join-Path $projectRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'smoke_rl.py')
    if ($LASTEXITCODE -ne 0) { throw 'RL stack smoke test failed.' }
} finally { Pop-Location }
