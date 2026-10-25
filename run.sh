#!/usr/bin/env sh
# Data Explorer: start the app on this computer (macOS, Linux). Usage: ./run.sh
# Installs uv if needed (no admin rights), which fetches Python and the libraries on first run.
set -e
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    if [ ! -x "$HOME/.local/bin/uv" ]; then
        echo "Installing uv, first run only..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    PATH="$HOME/.local/bin:$PATH"
fi

echo "Preparing Data Explorer, the first run downloads the libraries (a few minutes)..."
exec uv run --project backend --frozen --no-dev python backend/launch.py "$@"
