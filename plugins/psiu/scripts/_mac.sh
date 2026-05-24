#!/usr/bin/env bash
# macOS implementation. Variables exported by notify.sh:
#   PHRASE, TOAST_TITLE, TOAST_BODY, SOUND, NOTIFY_EVENT
#   NOTIFY_ENABLE_SOUND, NOTIFY_ENABLE_TOAST, NOTIFY_ENABLE_TTS
#   NOTIFY_VOICE, NOTIFY_RATE, NOTIFY_VOLUME
set -u

resolve_sound() {
  # Returns the .aiff path for a name like "Glass" or passes through a full path.
  local s="$1"
  [ -z "$s" ] && { echo ""; return; }
  if [ -f "$s" ]; then
    echo "$s"
  elif [ -f "/System/Library/Sounds/${s}.aiff" ]; then
    echo "/System/Library/Sounds/${s}.aiff"
  else
    echo ""
  fi
}

# ---- Sound -----------------------------------------------------------------
if [ "$NOTIFY_ENABLE_SOUND" = "1" ]; then
  default_sound="Glass"
  case "$NOTIFY_EVENT" in
    stop_failure) default_sound="Sosumi" ;;
    notification) default_sound="Funk" ;;
  esac
  s="$(resolve_sound "${SOUND:-$default_sound}")"
  [ -z "$s" ] && s="$(resolve_sound "$default_sound")"
  if [ -n "$s" ]; then
    afplay "$s" >/dev/null 2>&1 &
  fi
fi

# ---- Toast (native macOS notification center) -----------------------------
if [ "$NOTIFY_ENABLE_TOAST" = "1" ]; then
  # Escape double quotes in title/body for AppleScript
  esc_title="${TOAST_TITLE//\"/\\\"}"
  esc_body="${TOAST_BODY//\"/\\\"}"
  osascript -e "display notification \"$esc_body\" with title \"$esc_title\"" >/dev/null 2>&1 &
fi

# ---- TTS -------------------------------------------------------------------
if [ "$NOTIFY_ENABLE_TTS" = "1" ] && [ -n "$PHRASE" ]; then
  args=()
  [ -n "${NOTIFY_VOICE:-}" ] && args+=(-v "$NOTIFY_VOICE")
  [ -n "${NOTIFY_RATE:-}" ] && args+=(-r "$NOTIFY_RATE")
  say "${args[@]}" "$PHRASE" >/dev/null 2>&1 &
fi

wait
exit 0
