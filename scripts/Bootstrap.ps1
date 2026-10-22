param([string]$PythonExe)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Exe $Arguments" }
}
Push-Location $projectRoot
try {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Install Node.js 20.19+ first.' }
    Invoke-Checked node @('-e', 'const [a,b]=process.versions.node.split(".").map(Number);if(a<20||(a===20&&b<19))process.exit(1)')
    $venvPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        if (-not $PythonExe) {
            $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            if (Test-Path -LiteralPath $bundledPython) { $PythonExe = $bundledPython }
            elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = (Get-Command python).Source }
            else { throw 'Install CPython 3.12 x64 or pass -PythonExe <path>.' }
        }
        Invoke-Checked $PythonExe @('-c', 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 required"')
        Invoke-Checked $PythonExe @('-m', 'venv', '.venv')
    }
    Invoke-Checked $venvPython @('-c', 'import sys; assert sys.version_info[:2] == (3,12)')
    Invoke-Checked $venvPython @('-m', 'pip', '--version')
    # Keep the CPU wheel source explicit; do not add it as an extra PyPI index.
    Invoke-Checked $venvPython @('-m', 'pip', 'install', 'torch==2.14.1+cpu', '--index-url', 'https://download.pytorch.org/whl/cpu', '--cache-dir', '.cache/pip')
    if (Test-Path -LiteralPath 'requirements-lock.txt') {
        Invoke-Checked $venvPython @('-m', 'pip', 'install', '-r', 'requirements-lock.txt', '--cache-dir', '.cache/pip')
        Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', '.[dev]', '--no-deps', '--cache-dir', '.cache/pip')
    } else {
        Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', '.[dev]', '--cache-dir', '.cache/pip')
    }
    $pnpmCommand = Get-Command pnpm -ErrorAction SilentlyContinue
    $bundledPnpm = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd'
    if ($pnpmCommand) { Invoke-Checked $pnpmCommand.Source @('install', '--frozen-lockfile', '--store-dir', '.pnpm-store') }
    elseif (Test-Path -LiteralPath $bundledPnpm) { Invoke-Checked $bundledPnpm @('install', '--frozen-lockfile', '--store-dir', '.pnpm-store') }
    elseif (Get-Command npm -ErrorAction SilentlyContinue) {
        # Exact top-level OpenSpec pin; pnpm is the canonical transitive lock.
        Invoke-Checked npm @('install', '--package-lock=false', '--ignore-scripts')
    } else { throw 'npm or pnpm is required to install OpenSpec.' }
    Invoke-Checked $venvPython @('-m', 'pip', 'check')
    Write-Output 'Dependencies installed. Run scripts/Check.ps1.'
} finally { Pop-Location }
