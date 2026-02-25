#!/usr/bin/env bash
set -e

REPO="${SPTUI_REPO:-git+https://github.com/kofolmarko/sptui.git}"

# ── Find Python 3.10+ ─────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null \
       && "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.10+ is required."
    echo "Install from https://python.org"
    exit 1
fi

echo "Using $($PYTHON --version)"

# ── Ensure pipx is available ──────────────────────────────────────────────────
if ! command -v pipx &>/dev/null; then
    echo "Installing pipx..."
    "$PYTHON" -m pip install --user pipx --quiet
    export PATH="$HOME/.local/bin:$PATH"
    "$PYTHON" -m pipx ensurepath --quiet 2>/dev/null || true
fi

# ── Install sptui ─────────────────────────────────────────────────────────────
echo "Installing sptui..."
"$PYTHON" -m pipx install "$REPO" --force

echo ""
echo "✓ Done. Run: sptui"
echo "  (If the command is not found, restart your terminal)"
