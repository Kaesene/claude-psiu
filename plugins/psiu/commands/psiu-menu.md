---
description: Open the psiu config menu in a NEW terminal window — interactive TUI, zero Claude tokens
allowed-tools: Bash
---

Launches the psiu interactive menu in a brand-new terminal window. Once it's open, navigate by number; every change saves to `~/.claude/psiu.json` immediately. Close the window when done.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/psiu-menu.sh"
```

Cross-platform:
- **macOS** opens Terminal.app
- **Windows** opens a new cmd window
- **Linux** picks the first available terminal emulator (gnome-terminal, konsole, xfce4-terminal, alacritty, kitty, xterm, …)

If your distro's terminal isn't on that list, fall back to running the menu manually in any terminal:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/psiu-config.py" menu
```
