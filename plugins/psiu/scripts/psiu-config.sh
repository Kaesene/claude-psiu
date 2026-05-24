#!/usr/bin/env bash
# Wrapper around psiu-config.py that picks python3 or python.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "psiu: python is required for /psiu-config (install python3 and try again)" >&2
  exit 1
fi
exec "$PY" "$SCRIPT_DIR/psiu-config.py" "$@"
