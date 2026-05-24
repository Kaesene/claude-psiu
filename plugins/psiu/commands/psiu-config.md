---
description: Open an interactive menu to configure the psiu plugin (voices, phrases, sounds, quiet hours, channels)
allowed-tools: Read, Edit, Write, AskUserQuestion, Bash, PowerShell
---

Open an interactive configuration menu for the psiu plugin.

## Steps

1. **Read current config** — Read `~/.claude/settings.json` and extract any keys starting with `NOTIFY_` from the `env` block. Show a brief summary of current overrides (or "tudo no default" if empty).

2. **Open main menu via AskUserQuestion** — present these options:
   - **Voz** — voice, rate, volume (TTS)
   - **Frases** — what to say on Stop / StopFailure / Notification (single phrase or random rotation)
   - **Sons** — which system sound per event
   - **Toasts** — title + body text per event
   - **Canais** — turn sound / toast / TTS on or off independently
   - **Esperto** — quiet hours, include CWD project name in TTS
   - **Webhook & log** — POST URL and log file path
   - **Listar vozes** — read-only: show available TTS voices on this OS
   - **Mostrar config** — read-only: full table of current values vs defaults
   - **Reset** — remove all `NOTIFY_*` from settings.json (restores defaults)

3. **Drill into selection** — for each branch, ask follow-up via AskUserQuestion or accept a text answer. Then patch `~/.claude/settings.json` via the Edit tool.

4. **Show before → after** for the changed keys.

5. **Remind** — env vars in settings.json apply on next Claude Code session (or `/reload-plugins` for hooks).

## Reference: env vars and defaults

| Variable | Default | Type | What |
|---|---|---|---|
| `NOTIFY_ENABLE_SOUND` | `1` | bool (0/1) | Play sound |
| `NOTIFY_ENABLE_TOAST` | `1` | bool | Show toast |
| `NOTIFY_ENABLE_TTS` | `1` | bool | Speak phrase |
| `NOTIFY_STOP_PHRASE` | `terminei` | text | TTS on Stop |
| `NOTIFY_STOP_FAILURE_PHRASE` | `deu ruim` | text | TTS on StopFailure |
| `NOTIFY_NOTIF_PHRASE` | `preciso de você` | text | TTS on Notification |
| `NOTIFY_STOP_PHRASES` | (off) | text, pipe-separated | Random rotation, e.g. `a\|b\|c` |
| `NOTIFY_NOTIF_PHRASES` | (off) | text, pipe-separated | Random rotation |
| `NOTIFY_STOP_TOAST_TITLE` | `Claude Code` | text | |
| `NOTIFY_STOP_TOAST_BODY` | `Terminei a tarefa` | text | |
| `NOTIFY_STOP_FAILURE_TOAST_TITLE` | `Claude Code` | text | |
| `NOTIFY_STOP_FAILURE_TOAST_BODY` | `Tarefa falhou` | text | |
| `NOTIFY_NOTIF_TOAST_TITLE` | `Claude Code` | text | |
| `NOTIFY_NOTIF_TOAST_BODY` | `Preciso de você` | text | |
| `NOTIFY_VOICE` | system | text | TTS voice name |
| `NOTIFY_RATE` | system | number | TTS speed |
| `NOTIFY_VOLUME` | system | number 0-100 (Win) | TTS volume |
| `NOTIFY_STOP_SOUND` | Glass / Asterisk | text | Sound on Stop |
| `NOTIFY_NOTIF_SOUND` | Funk / Exclamation | text | Sound on Notification |
| `NOTIFY_STOP_FAILURE_SOUND` | Sosumi / Hand | text | Sound on StopFailure |
| `NOTIFY_QUIET` | (off) | text `HH-HH` | Quiet hours, e.g. `22-7` |
| `NOTIFY_INCLUDE_CWD` | `0` | bool | Append project name to TTS |
| `NOTIFY_WEBHOOK_URL` | (off) | url | POST JSON on each event |
| `NOTIFY_LOG` | (off) | path | Append-log per event |

## How to list available voices

- **macOS:** `say -v '?'`
- **Windows:** `powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices().VoiceInfo | Select-Object Name,Culture | Format-Table"`
- **Linux:** `spd-say -L`

## How to list available sounds

- **macOS:** `ls /System/Library/Sounds/*.aiff` (use the basename without extension)
- **Windows:** fixed set — `Asterisk`, `Beep`, `Exclamation`, `Hand`, `Question`

## How to patch settings.json

- If the `env` block doesn't exist, add it.
- To **set** a var: add/update the key in `env`.
- To **unset** (restore default): remove the key from `env`.
- After editing, **always validate the JSON** (try parsing it) — a broken settings.json silently disables ALL settings from that file.
- Preserve all keys you didn't touch — never replace the whole file.

## After applying

Tell the user:
- What changed (before → after)
- That env vars apply on the next session restart (or `/reload-plugins` if they want a quick check)
- They can run `/psiu-test` to hear the new config immediately
