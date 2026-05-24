---
description: Configure psiu — direct CLI. Run with no args to see help, or pass a subcommand (show, voice, phrase, sound, on/off, quiet, reset, edit, voices, etc.)
allowed-tools: Bash
---

Run the psiu-config CLI with whatever arguments the user passed. The CLI handles all read/write to `~/.claude/psiu.json` directly — no AI loop, single tool call, fast.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/psiu-config.sh" $ARGUMENTS
```

If `$ARGUMENTS` is empty, the CLI shows the current config plus a help summary. Common usages:

- `/psiu:psiu-config show`
- `/psiu:psiu-config voice Vitoria`
- `/psiu:psiu-config phrase stop "acabou chefe"`
- `/psiu:psiu-config off tts`
- `/psiu:psiu-config quiet 22-7`
- `/psiu:psiu-config reset`
- `/psiu:psiu-config edit`  ← opens the JSON in your $EDITOR
- `/psiu:psiu-config voices` / `sounds` ← list options on the current OS
