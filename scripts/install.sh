#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-python3.12}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python3
fi
cd "$ROOT"
"$PY" -m venv .venv
.venv/bin/pip install -U pip wheel
.venv/bin/pip install -e ".[dev]"
echo "Installed chirpctl. Add to PATH:"
echo "  export PATH=\"$ROOT/.venv/bin:\$PATH\""
.venv/bin/chirpctl skill install || true
.venv/bin/chirpctl doctor
