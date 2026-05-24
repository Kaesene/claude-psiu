#!/usr/bin/env bash
# Open the psiu config menu in a brand-new terminal window.
# Cross-platform: macOS (Terminal.app), Windows (cmd), Linux (first available emulator).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/psiu-config.py"

# Pick a python interpreter
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "psiu: python is required (install python3 and try again)" >&2
  exit 1
fi

case "$(uname -s)" in
  Darwin*)
    # macOS Terminal.app via AppleScript. `do script` opens a new window.
    osascript \
      -e "tell application \"Terminal\" to do script \"$PY '$PY_SCRIPT' menu\"" \
      -e 'tell application "Terminal" to activate' >/dev/null 2>&1
    ;;

  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    # Windows: convert path to native form so cmd can read it.
    WIN_PATH="$PY_SCRIPT"
    if command -v cygpath >/dev/null 2>&1; then
      WIN_PATH="$(cygpath -w "$PY_SCRIPT")"
    fi
    # Use PowerShell Start-Process — reliably opens a new console window
    # regardless of parent shell. `cmd /k` keeps the new window open after
    # the python script exits so the user can read final state.
    # Single-quoted PS literal avoids $expansion conflicts; the path is
    # interpolated by bash before PS sees it.
    powershell.exe -NoProfile -Command \
      "Start-Process cmd -ArgumentList '/k python \"$WIN_PATH\" menu'"
    ;;

  Linux*)
    cmd_in_term="$PY '$PY_SCRIPT' menu; echo; read -n1 -r -p 'Press any key to close...'"
    for term in gnome-terminal konsole xfce4-terminal alacritty kitty tilix terminator xterm; do
      if command -v "$term" >/dev/null 2>&1; then
        case "$term" in
          gnome-terminal|tilix|terminator)
            "$term" -- bash -c "$cmd_in_term"
            ;;
          konsole|xfce4-terminal)
            "$term" -e "bash -c \"$cmd_in_term\""
            ;;
          alacritty|kitty)
            "$term" -e bash -c "$cmd_in_term"
            ;;
          xterm)
            xterm -e "bash -c \"$cmd_in_term\""
            ;;
        esac
        exit 0
      fi
    done
    echo "psiu: no supported terminal emulator found." >&2
    echo "Run this manually in your shell:" >&2
    echo "  $PY '$PY_SCRIPT' menu" >&2
    exit 1
    ;;

  *)
    echo "psiu: unsupported OS for auto-open. Run this manually:" >&2
    echo "  $PY '$PY_SCRIPT' menu" >&2
    exit 1
    ;;
esac
