# Start, stop or inspect pure-profile training (runs\pure-v4) without typing the game paths.
# Called by Train-Start.cmd, Train-Stop.cmd and Train-Status.cmd in the project root.
# Record-Demo.cmd calls -Action Record: it only checks that training is stopped.
param(
    [Parameter(Mandatory = $true)][ValidateSet('Start', 'Stop', 'Status', 'Record')][string]$Action,
    [switch]$Initialize,
    [int]$WaitMinutes = 15
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Defaults are the paths of this PC; ISAAC_GAME and ISAAC_LOG override them.
$game = if ($env:ISAAC_GAME) { $env:ISAAC_GAME } else {
    'C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth'
}
$log = if ($env:ISAAC_LOG) { $env:ISAAC_LOG } else {
    Join-Path $env:USERPROFILE 'Documents\My Games\Binding of Isaac Repentance+\log.txt'
}
$runRoot = Join-Path $root 'runs\pure-v4'
$supervisor = Join-Path $runRoot 'supervisor'
$stopFile = Join-Path $supervisor 'stop.forever'
$python = Join-Path $root '.venv\Scripts\python.exe'

function Get-Trainers {
    # The forever supervisor of this project; the training worker is its child.
    @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -like '*isaac_threrisaifuture.session_runner*--forever*' })
}

function Show-Status {
    $trainers = Get-Trainers
    if ($trainers.Count -gt 0) {
        Write-Host "Training: RUNNING (supervisor PID $($trainers.ProcessId -join ', '))"
    } else {
        Write-Host 'Training: not running'
    }
    Write-Host "Stop file: $(if (Test-Path $stopFile) { 'present' } else { 'absent' })"
    $latest = Join-Path $runRoot 'seed-1\checkpoints\latest.txt'
    if (Test-Path $latest) { Write-Host "Latest checkpoint: $((Get-Content $latest -Raw).Trim())" }
    $episodes = Join-Path $runRoot 'metrics\episodes.csv'
    if (Test-Path $episodes) {
        $count = (Get-Content $episodes | Measure-Object -Line).Lines - 1
        Write-Host "Episodes: $count"
    }
    $forever = Join-Path $supervisor 'forever.json'
    if (Test-Path $forever) {
        $summary = Get-Content $forever -Raw | ConvertFrom-Json
        Write-Host "Last supervisor stop reason: $($summary.stop_reason)"
    }
    $session = Get-ChildItem $supervisor -Directory -Filter 'session-*' -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($session -and (Test-Path (Join-Path $session.FullName 'status.json'))) {
        $status = Get-Content (Join-Path $session.FullName 'status.json') -Raw | ConvertFrom-Json
        Write-Host "Session $($session.Name): $($status.state); fault: $($status.fault)"
    }
}

switch ($Action) {
    'Status' { Show-Status }

    'Start' {
        if ((Get-Trainers).Count -gt 0) {
            Write-Host 'Training is already running; nothing started.'
            Show-Status
            exit 1
        }
        foreach ($path in @($python, $game, $log)) {
            if (-not (Test-Path $path)) { Write-Host "Missing: $path"; exit 2 }
        }
        if (Test-Path $stopFile) {
            Remove-Item $stopFile
            Write-Host 'Removed the stop file from the last stop.'
        }
        $arguments = @('-m', 'isaac_threrisaifuture.session_runner', '--forever',
            '--game', $game, '--game-log', $log, '--run-root', 'runs\pure-v4')
        if ($Initialize) { $arguments += '--initialize' }
        Write-Host "Starting pure training$(if ($Initialize) { ' (fresh lineage, --initialize)' })."
        Write-Host 'Stop it with Train-Stop.cmd (or Ctrl+C in this window).'
        & $python @arguments
        exit $LASTEXITCODE
    }

    'Record' {
        # The demo recorder listens on the training port, so training must be stopped.
        if ((Get-Trainers).Count -gt 0) {
            Write-Host 'Training is running and holds the observer port; stop it first with Train-Stop.cmd.'
            exit 1
        }
        if (-not (Test-Path $python)) { Write-Host "Missing: $python"; exit 2 }
    }

    'Stop' {
        if (-not (Test-Path $supervisor)) { New-Item -ItemType Directory $supervisor | Out-Null }
        if (-not (Test-Path $stopFile)) { New-Item -ItemType File $stopFile | Out-Null }
        Write-Host 'Stop requested: the current session releases input, closes the game and exits.'
        $deadline = (Get-Date).AddMinutes($WaitMinutes)
        while ((Get-Trainers).Count -gt 0) {
            if ((Get-Date) -gt $deadline) {
                Write-Host "Still running after $WaitMinutes minutes; check the session status."
                Show-Status
                exit 1
            }
            Start-Sleep -Seconds 5
        }
        Write-Host 'Training stopped.'
        Show-Status
    }
}
