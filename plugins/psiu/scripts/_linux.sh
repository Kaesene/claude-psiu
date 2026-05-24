#!/usr/bin/env bash
# Linux implementation (best-effort).
# Requires: notify-send (libnotify), paplay or aplay (PulseAudio/ALSA), spd-say (speech-dispatcher).
set -u

# ---- Sound -----------------------------------------------------------------
if [ "$NOTIFY_ENABLE_SOUND" = "1" ]; then
  default_sound="/usr/share/sounds/freedesktop/stereo/complete.oga"
  case "$NOTIFY_EVENT" in
    stop_failure) default_sound="/usr/share/sounds/freedesktop/stereo/dialog-error.oga" ;;
    notification) default_sound="/usr/share/sounds/freedesktop/stereo/message.oga" ;;
  esac
  s="${SOUND:-$default_sound}"
  if [ -f "$s" ]; then
    if command -v paplay >/dev/null 2>&1; then
      paplay "$s" >/dev/null 2>&1 &
    elif command -v aplay >/dev/null 2>&1; then
      aplay -q "$s" >/dev/null 2>&1 &
    fi
  fi
fi

# ---- Toast -----------------------------------------------------------------
if [ "$NOTIFY_ENABLE_TOAST" = "1" ] && command -v notify-send >/dev/null 2>&1; then
  notify-send "$TOAST_TITLE" "$TOAST_BODY" >/dev/null 2>&1 &
fi

# ---- TTS -------------------------------------------------------------------
if [ "$NOTIFY_ENABLE_TTS" = "1" ] && [ -n "$PHRASE" ]; then
  if command -v spd-say >/dev/null 2>&1; then
    args=()
    [ -n "${NOTIFY_VOICE:-}" ] && args+=(-l "$NOTIFY_VOICE")
    [ -n "${NOTIFY_RATE:-}" ]  && args+=(-r "$NOTIFY_RATE")
    spd-say ${args[@]+"${args[@]}"} "$PHRASE" >/dev/null 2>&1 &
  elif command -v espeak >/dev/null 2>&1; then
    espeak "$PHRASE" >/dev/null 2>&1 &
  fi
fi

wait
exit 0
