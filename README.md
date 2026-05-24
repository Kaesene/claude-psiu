# psiu

> *psiu!* — that thing you do to get someone's attention.

Sound + toast + TTS notifications when [Claude Code](https://claude.com/claude-code) finishes a turn or needs your input. Cross-platform (macOS, Windows, Linux).

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
/psiu:psiu-test
```

Or with a custom phrase:

```
/psiu:psiu-test ola mundo
```

## Configure

All config lives in `~/.claude/psiu.json` — **separate from your `settings.json`**, so the plugin never touches Claude Code's harness config. Use the `/psiu:psiu-config` slash command (direct CLI, no AI loop, single tool call):

```
/psiu:psiu-config show                            # show current config
/psiu:psiu-config voice Vitoria                   # set TTS voice
/psiu:psiu-config rate 220                        # words per minute (macOS) / -10..10 (Win)
/psiu:psiu-config phrase stop "acabou chefe"      # change phrase per event
/psiu:psiu-config phrases stop "a|b|c|d"          # random rotation per event
/psiu:psiu-config toast stop "Title" "Body"       # change toast text
/psiu:psiu-config sound stop Glass                # change sound per event
/psiu:psiu-config quiet 22-7                      # silence between 22:00 and 06:59
/psiu:psiu-config on tts | off tts                # toggle channels
/psiu:psiu-config cwd 1                           # include project name in TTS
/psiu:psiu-config webhook https://ntfy.sh/foo     # POST JSON on every event
/psiu:psiu-config log ~/.claude/psiu.log          # append-log every event
/psiu:psiu-config unset voice                     # remove a single key
/psiu:psiu-config reset                           # delete config file (restores defaults)
/psiu:psiu-config edit                            # open the JSON in $EDITOR
/psiu:psiu-config voices                          # list TTS voices on this OS
/psiu:psiu-config sounds                          # list system sounds on this OS
/psiu:psiu-config path                            # print config file path
```

Events: `stop`, `stop_failure`, `notification`. Channels: `sound`, `toast`, `tts`.

You can also edit `~/.claude/psiu.json` by hand — it's just JSON. Missing keys fall back to defaults; only what you explicitly set overrides.

### Interactive menu (no Claude tokens)

For browsing without remembering subcommand syntax, run the menu mode **in your own terminal** (or via Claude Code's `!` prefix which gives you a real shell):

```
!python "~/.claude/plugins/cache/claude-psiu/psiu/<version>/scripts/psiu-config.py" menu
```

This launches a numbered TUI that walks you through every option, shows the current value inline, and writes to `~/.claude/psiu.json` directly. Zero AI involvement — no tokens, no latency.

## Example psiu.json

```json
{
  "voice": "Vitoria",
  "rate": 220,
  "phrases_random": {
    "stop": "terminei|acabou chefe|pronto|fim"
  },
  "phrases": {
    "notification": "ó eu aqui"
  },
  "quiet": "23-7",
  "include_cwd": true,
  "webhook_url": "https://ntfy.sh/your-topic",
  "channels": { "tts": true, "toast": true, "sound": true }
}
```

## Defaults reference

| Event | Phrase (TTS) | Toast title | Toast body | Sound (Mac) | Sound (Win) |
|---|---|---|---|---|---|
| `Stop` | terminei | Claude Code | Terminei a tarefa | Glass | Asterisk |
| `StopFailure` | deu ruim | Claude Code | Tarefa falhou | Sosumi | Hand |
| `Notification` | preciso de você | Claude Code | Preciso de você | Funk | Exclamation |

Voice / rate / volume default to the system TTS voice. All three channels (sound, toast, TTS) are on by default.

## Sound names

- **macOS**: file basename from `/System/Library/Sounds/*.aiff` — `Basso`, `Blow`, `Bottle`, `Frog`, `Funk`, `Glass`, `Hero`, `Morse`, `Ping`, `Pop`, `Purr`, `Sosumi`, `Submarine`, `Tink`. Or an absolute path.
- **Windows**: one of `Asterisk`, `Beep`, `Exclamation`, `Hand`, `Question`. Or absolute path to a `.wav` file.
- **Linux**: absolute path to a sound file (`.oga`, `.wav`, `.ogg`).

Use `/psiu:psiu-config sounds` to list them on your current OS.

## Voice names

- **macOS**: `say -v '?'` shows all installed voices. Brazilian Portuguese: `Vitoria`, `Luciana`. Portuguese (Portugal): `Joana`, `Daniel`.
- **Windows**: `Microsoft Maria Desktop`, `Microsoft Daniel Desktop`, and any others installed via Settings → Time & language → Speech → Add voices.
- **Linux**: locale code passed to `spd-say`, e.g. `pt`, `pt-BR`.

Use `/psiu:psiu-config voices` to list them on your current OS.

## Requirements

- **macOS**: nothing extra — uses native `afplay`, `say`, `osascript`. Python 3 is preinstalled.
- **Windows**: needs `bash` (Git for Windows ships it) + Python 3 (for the config CLI). Toast notifications use [BurntToast](https://github.com/Windos/BurntToast) if installed, otherwise fall back to the WinRT API (Windows 10+). To install BurntToast:
  ```powershell
  Install-Module -Name BurntToast -Scope CurrentUser -Force
  ```
- **Linux**: needs `notify-send` (libnotify), `paplay` or `aplay`, and `spd-say` or `espeak`.

## Events supported

| Event | When it fires |
|---|---|
| `Stop` | Claude finishes a turn (also `/clear`, `/resume`, compaction) |
| `StopFailure` | Stop hook itself failed, or Claude errored out |
| `Notification` | Claude needs your input (permission prompt, question) |

## Troubleshooting

- **Nothing happens** — run `/psiu:psiu-test`. If that works, the hook isn't firing; try `/reload-plugins` or restart Claude Code.
- **Toast missing on Windows** — install BurntToast (see Requirements). The WinRT fallback works on Win10+ but may need PowerShell 5.1+.
- **Wrong voice** — run `/psiu:psiu-config voices` to see what's installed and pick the exact name.
- **Webhook silently fails** — set `/psiu:psiu-config log ~/.claude/psiu.log` and inspect.

## How it works

Plugin scripts read `~/.claude/psiu.json` via Python on every hook fire and translate the structured config into `NOTIFY_*` environment variables for the platform-specific scripts (`_mac.sh`, `_win.ps1`, `_linux.sh`). Nothing is ever written to `settings.json`.

## License

MIT — see [LICENSE](LICENSE).
