param([switch]$CpuTorch)
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
    # The installed torch must be the pinned build (CUDA unless -CpuTorch); GPU state is only shown.
    . (Join-Path $PSScriptRoot 'TorchPin.ps1')
    $torchVersion = if ($CpuTorch) { $TorchCpuVersion } else { $TorchCudaVersion }
    Invoke-PythonCheck @('-c', "import torch; v = torch.__version__; assert v == '$torchVersion', 'torch ' + v + ' is not the pinned $torchVersion; run scripts/Bootstrap.ps1'; print('torch', v, 'cuda_available', torch.cuda.is_available())")
    Invoke-PythonCheck @('-m', 'ruff', 'check', 'src', 'tests', 'scripts/smoke_rl.py', 'scripts/compare_eval.py', 'scripts/lua_perf.py')
    Invoke-PythonCheck @('-m', 'ruff', 'format', '--check', 'src', 'tests', 'scripts/smoke_rl.py', 'scripts/compare_eval.py', 'scripts/lua_perf.py')
    Invoke-PythonCheck @('-m', 'mypy')
    Invoke-PythonCheck @('-m', 'pytest', '-m', 'not game')
    Invoke-PythonCheck @('-m', 'pip', 'check')
    & (Join-Path $PSScriptRoot 'OpenSpec.ps1') validate --all --strict
    if ($LASTEXITCODE -ne 0) { throw 'OpenSpec strict validation failed.' }
    Write-Output 'Offline quality gates passed. No real-game integration was tested.'
} finally { Pop-Location }
