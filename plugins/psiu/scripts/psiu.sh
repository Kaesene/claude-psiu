#!/usr/bin/env bash
# Cross-platform dispatcher for Claude Code notify plugin.
# Receives event name as $1: stop | stop_failure | notification
# Receives JSON payload on stdin (cwd, session_id, etc.)
set -u

EVENT="${1:-stop}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read stdin (Claude Code passes JSON payload here)
PAYLOAD=""
if [ ! -t 0 ]; then
  PAYLOAD="$(cat)"
fi

# ---- Defaults --------------------------------------------------------------
: "${NOTIFY_ENABLE_SOUND:=1}"
: "${NOTIFY_ENABLE_TOAST:=1}"
: "${NOTIFY_ENABLE_TTS:=1}"

: "${NOTIFY_STOP_PHRASE:=terminei}"
: "${NOTIFY_STOP_TOAST_TITLE:=Claude Code}"
: "${NOTIFY_STOP_TOAST_BODY:=Terminei a tarefa}"

: "${NOTIFY_STOP_FAILURE_PHRASE:=deu ruim}"
: "${NOTIFY_STOP_FAILURE_TOAST_TITLE:=Claude Code}"
: "${NOTIFY_STOP_FAILURE_TOAST_BODY:=Tarefa falhou}"

: "${NOTIFY_NOTIF_PHRASE:=preciso de você}"
: "${NOTIFY_NOTIF_TOAST_TITLE:=Claude Code}"
: "${NOTIFY_NOTIF_TOAST_BODY:=Preciso de você}"

: "${NOTIFY_VOICE:=}"
: "${NOTIFY_RATE:=}"
: "${NOTIFY_VOLUME:=}"

: "${NOTIFY_STOP_SOUND:=}"
: "${NOTIFY_STOP_FAILURE_SOUND:=}"
: "${NOTIFY_NOTIF_SOUND:=}"

: "${NOTIFY_QUIET:=}"
: "${NOTIFY_INCLUDE_CWD:=0}"
: "${NOTIFY_STOP_PHRASES:=}"
: "${NOTIFY_NOTIF_PHRASES:=}"

: "${NOTIFY_WEBHOOK_URL:=}"
: "${NOTIFY_LOG:=}"

# ---- Logging ---------------------------------------------------------------
log() {
  [ -z "$NOTIFY_LOG" ] && return 0
  local dir
  dir="$(dirname "$NOTIFY_LOG")"
  [ -d "$dir" ] || mkdir -p "$dir" 2>/dev/null || true
  printf '[%s] %s | %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$EVENT" "$*" >> "$NOTIFY_LOG" 2>/dev/null || true
}

# ---- Quiet hours -----------------------------------------------------------
# NOTIFY_QUIET="22-7" silences from 22:00 to 06:59
in_quiet_hours() {
  [ -z "$NOTIFY_QUIET" ] && return 1
  local range="$NOTIFY_QUIET"
  local start end now
  start="${range%-*}"
  end="${range#*-}"
  now="$(date +%-H 2>/dev/null || date +%H | sed 's/^0//')"
  [ -z "$now" ] && now=0
  if [ "$start" -le "$end" ]; then
    [ "$now" -ge "$start" ] && [ "$now" -lt "$end" ]
  else
    [ "$now" -ge "$start" ] || [ "$now" -lt "$end" ]
  fi
}

if in_quiet_hours; then
  log "skipped (quiet hours $NOTIFY_QUIET, now $(date +%H:%M))"
  exit 0
fi

# ---- Per-event resolution --------------------------------------------------
case "$EVENT" in
  stop)
    PHRASE="$NOTIFY_STOP_PHRASE"
    TOAST_TITLE="$NOTIFY_STOP_TOAST_TITLE"
    TOAST_BODY="$NOTIFY_STOP_TOAST_BODY"
    SOUND="$NOTIFY_STOP_SOUND"
    PHRASES="$NOTIFY_STOP_PHRASES"
    ;;
  stop_failure)
    PHRASE="$NOTIFY_STOP_FAILURE_PHRASE"
    TOAST_TITLE="$NOTIFY_STOP_FAILURE_TOAST_TITLE"
    TOAST_BODY="$NOTIFY_STOP_FAILURE_TOAST_BODY"
    SOUND="$NOTIFY_STOP_FAILURE_SOUND"
    PHRASES=""
    ;;
  notification)
    PHRASE="$NOTIFY_NOTIF_PHRASE"
    TOAST_TITLE="$NOTIFY_NOTIF_TOAST_TITLE"
    TOAST_BODY="$NOTIFY_NOTIF_TOAST_BODY"
    SOUND="$NOTIFY_NOTIF_SOUND"
    PHRASES="$NOTIFY_NOTIF_PHRASES"
    ;;
  test)
    PHRASE="${2:-teste de notificação}"
    TOAST_TITLE="Claude Code"
    TOAST_BODY="Teste do plugin notify"
    SOUND=""
    PHRASES=""
    ;;
  *)
    log "unknown event"
    exit 0
    ;;
esac

# ---- Random phrase rotation ------------------------------------------------
# NOTIFY_STOP_PHRASES="terminei|pronto|acabou chefe" picks one at random
if [ -n "$PHRASES" ]; then
  IFS='|' read -r -a opts <<< "$PHRASES"
  if [ "${#opts[@]}" -gt 0 ]; then
    idx=$(( RANDOM % ${#opts[@]} ))
    PHRASE="${opts[$idx]}"
  fi
fi

# ---- Include CWD project name in TTS ---------------------------------------
if [ "$NOTIFY_INCLUDE_CWD" = "1" ]; then
  CWD=""
  if [ -n "$PAYLOAD" ] && command -v jq >/dev/null 2>&1; then
    CWD="$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty' 2>/dev/null)"
  fi
  [ -z "$CWD" ] && CWD="$PWD"
  if [ -n "$CWD" ]; then
    PROJECT="$(basename "$CWD")"
    PHRASE="$PHRASE em $PROJECT"
    TOAST_BODY="$TOAST_BODY ($PROJECT)"
  fi
fi

log "phrase='$PHRASE' toast='$TOAST_BODY' sound='$SOUND'"

# ---- Webhook ---------------------------------------------------------------
if [ -n "$NOTIFY_WEBHOOK_URL" ] && command -v curl >/dev/null 2>&1; then
  CWD_JSON=""
  if [ -n "$PAYLOAD" ] && command -v jq >/dev/null 2>&1; then
    CWD_JSON="$(printf '%s' "$PAYLOAD" | jq -r '.cwd // ""' 2>/dev/null)"
  fi
  body=$(printf '{"event":"%s","message":"%s","cwd":"%s"}' \
    "$EVENT" "${TOAST_BODY//\"/\\\"}" "${CWD_JSON//\"/\\\"}")
  curl -s -m 5 -X POST -H 'Content-Type: application/json' \
    -d "$body" "$NOTIFY_WEBHOOK_URL" >/dev/null 2>&1 || true
fi

# ---- Export for child processes -------------------------------------------
export NOTIFY_ENABLE_SOUND NOTIFY_ENABLE_TOAST NOTIFY_ENABLE_TTS
export NOTIFY_VOICE NOTIFY_RATE NOTIFY_VOLUME
export PHRASE TOAST_TITLE TOAST_BODY SOUND
export NOTIFY_EVENT="$EVENT"

# ---- OS dispatch -----------------------------------------------------------
case "$(uname -s)" in
  Darwin*)
    bash "$SCRIPT_DIR/_mac.sh"
    ;;
  Linux*)
    bash "$SCRIPT_DIR/_linux.sh" 2>/dev/null || true
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    # Translate script path to Windows form so powershell.exe can read it
    PS1="$SCRIPT_DIR/_win.ps1"
    if command -v cygpath >/dev/null 2>&1; then
      PS1="$(cygpath -w "$PS1")"
    fi
    powershell.exe -NoProfile -File "$PS1" 2>/dev/null || true
    ;;
  *)
    log "unsupported OS: $(uname -s)"
    exit 0
    ;;
esac
