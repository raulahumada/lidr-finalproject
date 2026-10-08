# Sync course ai-engineering reference into .reference/ai-engineering
# Windows / PowerShell only. On macOS/Linux use the bash sibling:
#   bash .cursor/skills/openspec-prespec/scripts/sync-reference.sh
#
# Usage (from repo root):
#   powershell -NoProfile -File .cursor/skills/openspec-prespec/scripts/sync-reference.ps1
#   powershell -NoProfile -File .cursor/skills/openspec-prespec/scripts/sync-reference.ps1 -Branch session_16 -SparsePath ai-service

param(
    [string]$Branch = "session_16",
    [string]$SparsePath = "ai-service",
    [string]$RepoUrl = "https://github.com/LIDR-academy/ai-engineering.git",
    [string]$TargetDir = ".reference/ai-engineering"
)

$ErrorActionPreference = "Stop"

$repoRoot = Get-Location
$target = Join-Path $repoRoot $TargetDir

Write-Host "Course reference sync"
Write-Host "  repo:   $RepoUrl"
Write-Host "  branch: $Branch"
Write-Host "  sparse: $SparsePath"
Write-Host "  target: $target"

function Assert-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "git is required but was not found on PATH."
    }
}

Assert-Git

if (-not (Test-Path (Join-Path $target ".git"))) {
    $parent = Split-Path -Parent $target
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
    }

    Write-Host "Cloning (blobless, sparse)..."
    git clone --filter=blob:none --sparse --branch $Branch --single-branch $RepoUrl $target
    if ($LASTEXITCODE -ne 0) { throw "git clone failed (exit $LASTEXITCODE)" }

    Push-Location $target
    try {
        git sparse-checkout set $SparsePath
        if ($LASTEXITCODE -ne 0) { throw "git sparse-checkout failed (exit $LASTEXITCODE)" }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Updating existing cache..."
    Push-Location $target
    try {
        git remote set-url origin $RepoUrl
        git fetch --depth 1 origin $Branch
        if ($LASTEXITCODE -ne 0) { throw "git fetch failed (exit $LASTEXITCODE)" }

        git checkout $Branch
        if ($LASTEXITCODE -ne 0) {
            git checkout -B $Branch "origin/$Branch"
            if ($LASTEXITCODE -ne 0) { throw "git checkout failed (exit $LASTEXITCODE)" }
        }

        git reset --hard "origin/$Branch"
        if ($LASTEXITCODE -ne 0) { throw "git reset failed (exit $LASTEXITCODE)" }

        git sparse-checkout set $SparsePath
        if ($LASTEXITCODE -ne 0) { throw "git sparse-checkout failed (exit $LASTEXITCODE)" }
    }
    finally {
        Pop-Location
    }
}

$head = git -C $target rev-parse --short HEAD
$sparseRoot = Join-Path $target $SparsePath
Write-Host "OK @ $head"
if (Test-Path $sparseRoot) {
    Write-Host "Sparse tree ready: $sparseRoot"
    Get-ChildItem $sparseRoot -Name | Select-Object -First 20 | ForEach-Object { Write-Host "  - $_" }
}
else {
    Write-Warning "Sparse path not found after sync: $sparseRoot"
}
