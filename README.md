# psiu

> *psiu!* — that thing you do to get someone's attention.

Sound + toast + TTS notifications when [Claude Code](https://claude.com/claude-code) finishes a turn or needs your input. Cross-platform (macOS, Windows, Linux) with rich customization.

Never miss the moment Claude stops working again.

## Install

In Claude Code:

```
/plugin marketplace add Kaesene/claude-psiu
/plugin install psiu@claude-psiu
/reload-plugins
```

That's it. Out of the box you get:

- **Stop**: system sound + toast "Terminei a tarefa" + TTS speaking *"terminei"*
- **Notification**: alert sound + toast "Preciso de você" + TTS speaking *"preciso de você"*
- **StopFailure**: error sound + toast "Tarefa falhou" + TTS speaking *"deu ruim"*

## Test it

```
/psiu-test
```

Or with a custom phrase:

```
/psiu-test ola mundo
```

## Customize

Everything is configurable via environment variables in your `~/.claude/settings.json` `env` block. All optional — defaults are sensible.

### On / off

| Variable | Default | What it does |
|---|---|---|
| `NOTIFY_ENABLE_SOUND` | `1` | Play a sound |
| `NOTIFY_ENABLE_TOAST` | `1` | Show OS toast notification |
| `NOTIFY_ENABLE_TTS`   | `1` | Speak the phrase out loud |

Set any to `0` to disable that channel.

### Phrases

| Variable | Default |
|---|---|
| `NOTIFY_STOP_PHRASE` | `terminei` |
| `NOTIFY_STOP_FAILURE_PHRASE` | `deu ruim` |
| `NOTIFY_NOTIF_PHRASE` | `preciso de você` |

**Random phrase rotation** — set a pipe-separated list and one is picked at random:

```json
"NOTIFY_STOP_PHRASES": "terminei|acabou chefe|pronto|fim"
```

### Toast text

| Variable | Default |
|---|---|
| `NOTIFY_STOP_TOAST_TITLE` | `Claude Code` |
| `NOTIFY_STOP_TOAST_BODY` | `Terminei a tarefa` |
| `NOTIFY_STOP_FAILURE_TOAST_TITLE` | `Claude Code` |
| `NOTIFY_STOP_FAILURE_TOAST_BODY` | `Tarefa falhou` |
| `NOTIFY_NOTIF_TOAST_TITLE` | `Claude Code` |
| `NOTIFY_NOTIF_TOAST_BODY` | `Preciso de você` |

### Voice (TTS)

| Variable | Default | macOS | Windows | Linux |
|---|---|---|---|---|
| `NOTIFY_VOICE` | system | `Vitoria`, `Luciana`, `Joana`, `Daniel`, … | `Microsoft Maria Desktop`, … | locale code, e.g. `pt` |
| `NOTIFY_RATE` | system | words/min (e.g. `200`) | `-10` to `10` | speech-dispatcher rate |
| `NOTIFY_VOLUME` | system | — | `0` to `100` | — |

Mac: list available voices with `say -v '?'`. Windows: `Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices().VoiceInfo.Name`.

### Sound

System sound names or full file paths.

| Variable | Default Stop | Default Notification | Default StopFailure |
|---|---|---|---|
| `NOTIFY_STOP_SOUND` | macOS: `Glass` · Win: `Asterisk` | — | — |
| `NOTIFY_NOTIF_SOUND` | — | macOS: `Funk` · Win: `Exclamation` | — |
| `NOTIFY_STOP_FAILURE_SOUND` | — | — | macOS: `Sosumi` · Win: `Hand` |

- **macOS**: name from `/System/Library/Sounds/*.aiff` (`Basso`, `Blow`, `Bottle`, `Frog`, `Funk`, `Glass`, `Hero`, `Morse`, `Ping`, `Pop`, `Purr`, `Sosumi`, `Submarine`, `Tink`) or an absolute path
- **Windows**: `Asterisk`, `Beep`, `Exclamation`, `Hand`, `Question`, or absolute path to a `.wav` file
- **Linux**: absolute path to a sound file (`.oga`, `.wav`, `.ogg`)

### Smart behaviors

| Variable | Default | What it does |
|---|---|---|
| `NOTIFY_QUIET` | (off) | Range like `"22-7"` — silences notifications from 22:00 to 06:59. Wraps midnight. |
| `NOTIFY_INCLUDE_CWD` | `0` | Set to `1` to append project folder name to TTS phrase: *"terminei em binstash"* |

### Webhooks & logging

| Variable | Default | What it does |
|---|---|---|
| `NOTIFY_WEBHOOK_URL` | (off) | POST `{event, message, cwd}` JSON to this URL — pipe to ntfy.sh, Pushover, Telegram, Slack, etc. |
| `NOTIFY_LOG` | (off) | Path to a log file — appends every event with timestamp. Useful for debugging. |

## Example config

```jsonc
// ~/.claude/settings.json
{
  "env": {
    "NOTIFY_VOICE": "Vitoria",
    "NOTIFY_RATE": "220",
    "NOTIFY_STOP_PHRASES": "terminei|acabou chefe|pronto|fim",
    "NOTIFY_NOTIF_PHRASE": "ó eu aqui",
    "NOTIFY_QUIET": "23-7",
    "NOTIFY_INCLUDE_CWD": "1",
    "NOTIFY_WEBHOOK_URL": "https://ntfy.sh/your-topic"
  }
}
```

## Requirements

- **macOS**: works out of the box (uses native `afplay`, `say`, `osascript`).
- **Windows**: requires either [BurntToast](https://github.com/Windos/BurntToast) for toast notifications *or* Windows 10+ for the fallback WinRT toast API. To install BurntToast:
  ```powershell
  Install-Module -Name BurntToast -Scope CurrentUser -Force
  ```
  The plugin also requires `bash` on the PATH — Git for Windows ships it.
- **Linux**: requires `notify-send` (libnotify), `paplay` or `aplay`, and `spd-say` or `espeak`.

## Events supported

| Event | When it fires |
|---|---|
| `Stop` | Claude finishes a turn (also clear/resume/compact) |
| `StopFailure` | Stop hook itself failed, or Claude errored |
| `Notification` | Claude needs your input (permission prompt, question) |

## Troubleshooting

- **Nothing happens** — run `/psiu-test`. If that works, the issue is hooks not loading; try `/reload-plugins` or restart Claude Code.
- **Toast missing on Windows** — install BurntToast (see Requirements). The WinRT fallback works on Win10+ but may need PowerShell 5.1+.
- **Wrong voice** — verify the voice exists on your system (`say -v '?'` on macOS).
- **Webhook silently fails** — set `NOTIFY_LOG` to a file path and inspect.

## License

MIT — see [LICENSE](LICENSE).
