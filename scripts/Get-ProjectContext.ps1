param(
    [ValidateSet('text', 'json')]
    [string]$Format = 'text'
)

# Read-only handoff: no game, checkpoint, approval, network or dependency access.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statusPath = Join-Path $projectRoot 'docs/STATUS.md'
$status = [System.IO.File]::ReadAllText($statusPath)
if ([System.Text.Encoding]::UTF8.GetByteCount($status) -gt 12000) {
    throw 'STATUS exceeds 12 KB. Consolidate current state and link dated evidence.'
}

$revision = & git -C $projectRoot rev-parse --short HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot read the Git revision.' }
$changes = @(& git -C $projectRoot status --short --untracked-files=normal)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Git status.' }

# Cap noisy worktrees while retaining the actual count. Paths only, never diffs.
$context = [ordered]@{
    schema_version = 1
    project_root = $projectRoot
    revision = [string]$revision
    changed_entries = $changes.Count
    git_status = @($changes | Select-Object -First 30)
    git_status_truncated = ($changes.Count -gt 30)
    status_path = $statusPath
    status = $status.TrimEnd()
    routing = 'AGENTS.md; load only the guide/spec/evidence required for the task.'
    authority = 'Context only: does not authorize runtime, resume, New Run or acceptance.'
}

if ($Format -eq 'json') {
    $context | ConvertTo-Json -Depth 3
} else {
    "Project: $projectRoot; revision: $revision"
    "Git changed entries: $($changes.Count) (showing up to 30)"
    $context.git_status
    $context.status
    $context.authority
}
