---
description: Test the psiu plugin — fires sound + toast + TTS now so you can confirm config
allowed-tools: Bash
---

Run the psiu script directly to test the current configuration. This fires sound, toast, and TTS as if a Stop event just happened.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/psiu.sh" test "$ARGUMENTS"
```

If `$ARGUMENTS` is provided, the TTS will speak it. Otherwise it says "teste de notificação".

Examples:
- `/psiu:psiu-test` — default test phrase
- `/psiu:psiu-test ola mundo` — custom phrase
