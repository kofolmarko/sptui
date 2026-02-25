$ErrorActionPreference = "Stop"

$REPO = if ($env:SPTUI_REPO) { $env:SPTUI_REPO } else { "git+https://github.com/kofolmarko/sptui.git" }

# ── Find Python 3.10+ ─────────────────────────────────────────────────────────
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        try {
            $ok = & $cmd -c "import sys; print('ok' if sys.version_info >= (3,10) else 'no')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $ok -eq "ok") { $python = $cmd; break }
        } catch {}
    }
}

if (-not $python) {
    Write-Error "Python 3.10+ is required. Download from https://python.org"
    exit 1
}

Write-Host "Using $(& $python --version)"

# ── Ensure pipx is available ──────────────────────────────────────────────────
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pipx..."
    & $python -m pip install --user pipx --quiet
    & $python -m pipx ensurepath
    # Reload user PATH for this session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
}

# ── Install sptui ─────────────────────────────────────────────────────────────
Write-Host "Installing sptui..."
& $python -m pipx install $REPO --force

Write-Host ""
Write-Host "✓ Done. Run: sptui"
Write-Host "  (If the command is not found, restart your terminal)"
