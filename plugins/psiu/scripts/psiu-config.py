#!/usr/bin/env python3
"""psiu-config — CLI for the psiu Claude Code plugin.

Reads and writes ~/.claude/psiu.json without touching settings.json.
Also emits `export VAR=value` lines for the hook dispatcher.

Usage:
  psiu-config show
  psiu-config voice Vitoria
  psiu-config rate 220
  psiu-config volume 80
  psiu-config phrase stop "terminei"
  psiu-config phrase notification "preciso de voce"
  psiu-config phrases stop "terminei|pronto|acabou"
  psiu-config toast stop "Claude Code" "Terminei a tarefa"
  psiu-config sound stop Glass
  psiu-config quiet 22-7
  psiu-config on tts            # on|off + sound|toast|tts
  psiu-config off sound
  psiu-config cwd 1             # 0 or 1
  psiu-config webhook https://ntfy.sh/foo
  psiu-config log ~/.claude/psiu.log
  psiu-config unset <key.path>  # remove a single key, e.g. voice or phrases.stop
  psiu-config reset             # delete the whole config file
  psiu-config path              # print the config file path
  psiu-config edit              # open the config file in $EDITOR
  psiu-config voices            # list TTS voices on this OS
  psiu-config sounds            # list system sounds on this OS
  psiu-config --export          # emit `export VAR=value` lines (used by dispatcher)
"""
from __future__ import annotations

import json
import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout/stderr so accented chars (você, ó, ç…) survive on Windows
# (cp1252 console default mangles them and crashes on the → arrow).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CONFIG_PATH = Path(os.environ.get("PSIU_CONFIG_FILE", str(Path.home() / ".claude" / "psiu.json")))

DEFAULTS = {
    "channels": {"sound": True, "toast": True, "tts": True},
    "phrases": {
        "stop": "terminei",
        "stop_failure": "deu ruim",
        "notification": "preciso de você",
    },
    "phrases_random": {"stop": None, "notification": None},
    "toasts": {
        "stop": {"title": "Claude Code", "body": "Terminei a tarefa"},
        "stop_failure": {"title": "Claude Code", "body": "Tarefa falhou"},
        "notification": {"title": "Claude Code", "body": "Preciso de você"},
    },
    "sounds": {"stop": None, "stop_failure": None, "notification": None},
    "voice": None,
    "rate": None,
    "volume": None,
    "quiet": None,
    "include_cwd": False,
    "webhook_url": None,
    "log_file": None,
}

EVENTS = ("stop", "stop_failure", "notification")
CHANNELS = ("sound", "toast", "tts")


# ---- IO --------------------------------------------------------------------

def load() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"warning: {CONFIG_PATH} is not valid JSON ({e}); ignoring", file=sys.stderr)
        return {}


def save(d: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def deep_merge(base: dict, override: dict) -> dict:
    out = json.loads(json.dumps(base))  # deep copy
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def merged() -> dict:
    return deep_merge(DEFAULTS, load())


def set_path(d: dict, dotted: str, value) -> None:
    """Set d.a.b.c = value, creating intermediate dicts."""
    parts = dotted.split(".")
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def unset_path(d: dict, dotted: str) -> bool:
    """Remove d.a.b.c if present. Returns True if anything was removed."""
    parts = dotted.split(".")
    cur = d
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    if isinstance(cur, dict) and parts[-1] in cur:
        del cur[parts[-1]]
        return True
    return False


# ---- Commands --------------------------------------------------------------

def cmd_show(args):
    cfg = load()
    if not cfg:
        print("(empty — all defaults active)")
        print(f"config path: {CONFIG_PATH}")
        return
    print(f"config path: {CONFIG_PATH}\n")
    print(json.dumps(cfg, indent=2, ensure_ascii=False))


def cmd_path(args):
    print(CONFIG_PATH)


def cmd_export(args):
    """Emit shell `export VAR=value` lines from the merged config."""
    c = merged()
    out = []

    def emit(name, value):
        if value is None or value == "":
            return
        out.append(f"export {name}={shlex.quote(str(value))}")

    out.append(f"export NOTIFY_ENABLE_SOUND={'1' if c['channels']['sound'] else '0'}")
    out.append(f"export NOTIFY_ENABLE_TOAST={'1' if c['channels']['toast'] else '0'}")
    out.append(f"export NOTIFY_ENABLE_TTS={'1' if c['channels']['tts'] else '0'}")

    emit("NOTIFY_STOP_PHRASE", c["phrases"]["stop"])
    emit("NOTIFY_STOP_FAILURE_PHRASE", c["phrases"]["stop_failure"])
    emit("NOTIFY_NOTIF_PHRASE", c["phrases"]["notification"])
    emit("NOTIFY_STOP_PHRASES", c["phrases_random"]["stop"])
    emit("NOTIFY_NOTIF_PHRASES", c["phrases_random"]["notification"])

    emit("NOTIFY_STOP_TOAST_TITLE", c["toasts"]["stop"]["title"])
    emit("NOTIFY_STOP_TOAST_BODY", c["toasts"]["stop"]["body"])
    emit("NOTIFY_STOP_FAILURE_TOAST_TITLE", c["toasts"]["stop_failure"]["title"])
    emit("NOTIFY_STOP_FAILURE_TOAST_BODY", c["toasts"]["stop_failure"]["body"])
    emit("NOTIFY_NOTIF_TOAST_TITLE", c["toasts"]["notification"]["title"])
    emit("NOTIFY_NOTIF_TOAST_BODY", c["toasts"]["notification"]["body"])

    emit("NOTIFY_VOICE", c["voice"])
    emit("NOTIFY_RATE", c["rate"])
    emit("NOTIFY_VOLUME", c["volume"])

    emit("NOTIFY_STOP_SOUND", c["sounds"]["stop"])
    emit("NOTIFY_NOTIF_SOUND", c["sounds"]["notification"])
    emit("NOTIFY_STOP_FAILURE_SOUND", c["sounds"]["stop_failure"])

    emit("NOTIFY_QUIET", c["quiet"])
    out.append(f"export NOTIFY_INCLUDE_CWD={'1' if c['include_cwd'] else '0'}")
    emit("NOTIFY_WEBHOOK_URL", c["webhook_url"])
    emit("NOTIFY_LOG", c["log_file"])

    print("\n".join(out))


def _apply_and_report(dotted: str, new_value, label: str | None = None):
    cfg = load()
    old = merged()
    # navigate old value
    old_val = old
    for p in dotted.split("."):
        if isinstance(old_val, dict):
            old_val = old_val.get(p)
        else:
            old_val = None
            break
    set_path(cfg, dotted, new_value)
    save(cfg)
    print(f"{label or dotted}: {old_val!r}  →  {new_value!r}")
    print(f"config: {CONFIG_PATH}")


def cmd_voice(args):
    if not args:
        print(f"current voice: {merged()['voice']!r}\nusage: psiu-config voice <name>", file=sys.stderr)
        sys.exit(1)
    _apply_and_report("voice", args[0])


def cmd_rate(args):
    if not args:
        print(f"current rate: {merged()['rate']!r}\nusage: psiu-config rate <number>", file=sys.stderr)
        sys.exit(1)
    try:
        _apply_and_report("rate", int(args[0]))
    except ValueError:
        print("error: rate must be an integer", file=sys.stderr)
        sys.exit(1)


def cmd_volume(args):
    if not args:
        print(f"current volume: {merged()['volume']!r}\nusage: psiu-config volume <0-100>", file=sys.stderr)
        sys.exit(1)
    try:
        _apply_and_report("volume", int(args[0]))
    except ValueError:
        print("error: volume must be an integer", file=sys.stderr)
        sys.exit(1)


def cmd_phrase(args):
    if len(args) < 2:
        print("usage: psiu-config phrase <stop|stop_failure|notification> <text>", file=sys.stderr)
        sys.exit(1)
    event, text = args[0], " ".join(args[1:])
    if event not in EVENTS:
        print(f"error: event must be one of {EVENTS}", file=sys.stderr)
        sys.exit(1)
    _apply_and_report(f"phrases.{event}", text)


def cmd_phrases(args):
    if len(args) < 2:
        print("usage: psiu-config phrases <stop|notification> 'a|b|c'", file=sys.stderr)
        sys.exit(1)
    event, text = args[0], " ".join(args[1:])
    if event not in ("stop", "notification"):
        print("error: phrases rotation is only supported for stop and notification", file=sys.stderr)
        sys.exit(1)
    _apply_and_report(f"phrases_random.{event}", text)


def cmd_toast(args):
    if len(args) < 3:
        print('usage: psiu-config toast <stop|stop_failure|notification> "<title>" "<body>"', file=sys.stderr)
        sys.exit(1)
    event = args[0]
    if event not in EVENTS:
        print(f"error: event must be one of {EVENTS}", file=sys.stderr)
        sys.exit(1)
    title, body = args[1], " ".join(args[2:])
    cfg = load()
    set_path(cfg, f"toasts.{event}.title", title)
    set_path(cfg, f"toasts.{event}.body", body)
    save(cfg)
    print(f"toast {event}: title={title!r}  body={body!r}")
    print(f"config: {CONFIG_PATH}")


def cmd_sound(args):
    if len(args) < 2:
        print("usage: psiu-config sound <stop|stop_failure|notification> <name-or-path>", file=sys.stderr)
        sys.exit(1)
    event, name = args[0], " ".join(args[1:])
    if event not in EVENTS:
        print(f"error: event must be one of {EVENTS}", file=sys.stderr)
        sys.exit(1)
    _apply_and_report(f"sounds.{event}", name)


def cmd_quiet(args):
    if not args:
        cfg = load()
        cur = merged()["quiet"]
        print(f"current quiet hours: {cur!r}\nusage: psiu-config quiet <HH-HH>  (e.g. 22-7)", file=sys.stderr)
        sys.exit(1)
    _apply_and_report("quiet", args[0])


def cmd_on(args):
    if not args or args[0] not in CHANNELS:
        print(f"usage: psiu-config on <{'|'.join(CHANNELS)}>", file=sys.stderr)
        sys.exit(1)
    _apply_and_report(f"channels.{args[0]}", True)


def cmd_off(args):
    if not args or args[0] not in CHANNELS:
        print(f"usage: psiu-config off <{'|'.join(CHANNELS)}>", file=sys.stderr)
        sys.exit(1)
    _apply_and_report(f"channels.{args[0]}", False)


def cmd_cwd(args):
    if not args or args[0] not in ("0", "1", "true", "false", "on", "off"):
        print("usage: psiu-config cwd <0|1>", file=sys.stderr)
        sys.exit(1)
    val = args[0] in ("1", "true", "on")
    _apply_and_report("include_cwd", val)


def cmd_webhook(args):
    if not args:
        print("usage: psiu-config webhook <url>", file=sys.stderr)
        sys.exit(1)
    _apply_and_report("webhook_url", args[0])


def cmd_log(args):
    if not args:
        print("usage: psiu-config log <path>", file=sys.stderr)
        sys.exit(1)
    _apply_and_report("log_file", os.path.expanduser(args[0]))


def cmd_unset(args):
    if not args:
        print("usage: psiu-config unset <key.path>  (e.g. voice or phrases.stop)", file=sys.stderr)
        sys.exit(1)
    cfg = load()
    if unset_path(cfg, args[0]):
        save(cfg)
        print(f"unset {args[0]}")
    else:
        print(f"{args[0]} was not set", file=sys.stderr)


def cmd_reset(args):
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
        print(f"removed {CONFIG_PATH}")
    else:
        print("(already at defaults)")


def cmd_edit(args):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save(load() or {})  # creates the file as {}
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        editor = "notepad" if platform.system() == "Windows" else "nano"
    try:
        subprocess.run([editor, str(CONFIG_PATH)], check=False)
    except FileNotFoundError:
        print(f"editor not found: {editor}", file=sys.stderr)
        print(f"config file is at: {CONFIG_PATH}")
        sys.exit(1)


def cmd_voices(args):
    sys_name = platform.system()
    if sys_name == "Darwin":
        subprocess.run(["say", "-v", "?"], check=False)
    elif sys_name == "Windows":
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
            ".GetInstalledVoices().VoiceInfo | "
            "Select-Object Name,Culture | Format-Table -AutoSize"
        )
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], check=False)
    else:
        # Linux
        if subprocess.run(["which", "spd-say"], capture_output=True).returncode == 0:
            subprocess.run(["spd-say", "-L"], check=False)
        else:
            print("install speech-dispatcher (spd-say) for voice listing", file=sys.stderr)


def cmd_sounds(args):
    sys_name = platform.system()
    if sys_name == "Darwin":
        for p in sorted(Path("/System/Library/Sounds").glob("*.aiff")):
            print(p.stem)
    elif sys_name == "Windows":
        for s in ("Asterisk", "Beep", "Exclamation", "Hand", "Question"):
            print(s)
    else:
        for p in sorted(Path("/usr/share/sounds/freedesktop/stereo").glob("*.oga")):
            print(p.name)


HELP = """\
psiu-config — configure the psiu plugin

Usage:
  /psiu:psiu-config show                 Show current config
  /psiu:psiu-config voice <name>         Set TTS voice
  /psiu:psiu-config rate <number>        Set TTS rate
  /psiu:psiu-config volume <0-100>       Set TTS volume (Windows only)
  /psiu:psiu-config phrase <ev> <text>   Set TTS phrase for event (stop|stop_failure|notification)
  /psiu:psiu-config phrases <ev> "a|b|c" Set random rotation list (stop|notification)
  /psiu:psiu-config toast <ev> "<t>" "<b>"   Set toast title and body
  /psiu:psiu-config sound <ev> <name>    Set system sound for event
  /psiu:psiu-config quiet <HH-HH>        Silence between hours (e.g. 22-7)
  /psiu:psiu-config on <sound|toast|tts>     Enable a channel
  /psiu:psiu-config off <sound|toast|tts>    Disable a channel
  /psiu:psiu-config cwd <0|1>            Include project name in TTS phrase
  /psiu:psiu-config webhook <url>        POST JSON on each event
  /psiu:psiu-config log <path>           Append-log every event
  /psiu:psiu-config unset <key.path>     Remove a single key (e.g. voice, phrases.stop)
  /psiu:psiu-config reset                Delete the whole config file
  /psiu:psiu-config path                 Print the config file path
  /psiu:psiu-config edit                 Open config file in $EDITOR
  /psiu:psiu-config voices               List available TTS voices on this OS
  /psiu:psiu-config sounds               List available system sounds on this OS

Interactive menu (no Claude tokens — runs in your terminal):
  !python "<plugin>/scripts/psiu-config.py" menu
  (works only when invoked from a TTY, e.g. via Claude Code's `!` prefix)

Config file: ~/.claude/psiu.json (separate from settings.json)
"""


def cmd_help(args):
    print(HELP)


# ---- Interactive menu ------------------------------------------------------

def _prompt_str(label, current):
    cur = f" [{current}]" if current else " [default]"
    ans = input(f"  {label}{cur}\n  (Enter mantém · '-' apaga · ou digite novo): ").strip()
    if ans == "":
        return current, False  # keep
    if ans == "-":
        return None, True  # unset
    return ans, True


def _prompt_int(label, current, lo=None, hi=None):
    cur = f" [{current}]" if current is not None else " [default]"
    while True:
        ans = input(f"  {label}{cur}\n  (Enter mantém · '-' apaga · número novo): ").strip()
        if ans == "":
            return current, False
        if ans == "-":
            return None, True
        try:
            v = int(ans)
            if lo is not None and v < lo:
                print(f"  min {lo}")
                continue
            if hi is not None and v > hi:
                print(f"  max {hi}")
                continue
            return v, True
        except ValueError:
            print("  precisa ser número, tenta de novo")


def _apply_change(dotted, new_value, changed):
    if not changed:
        return
    cfg = load()
    if new_value is None:
        unset_path(cfg, dotted)
    else:
        set_path(cfg, dotted, new_value)
    save(cfg)
    print(f"  ✓ {dotted} → {new_value!r}")


def _menu_voice():
    while True:
        c = merged()
        print("\n--- Voz, velocidade, volume ---")
        print(f"  1) Voz       [{c['voice'] or 'default'}]")
        print(f"  2) Rate      [{c['rate'] if c['rate'] is not None else 'default'}]")
        print(f"  3) Volume    [{c['volume'] if c['volume'] is not None else 'default'}]   (só Windows)")
        print(f"  4) Listar vozes disponíveis no OS")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch == "1":
            val, changed = _prompt_str("Nome da voz", c["voice"])
            _apply_change("voice", val, changed)
        elif ch == "2":
            val, changed = _prompt_int("Rate (Mac: wpm tipo 200; Win: -10..10)", c["rate"])
            _apply_change("rate", val, changed)
        elif ch == "3":
            val, changed = _prompt_int("Volume 0-100 (só Windows)", c["volume"], 0, 100)
            _apply_change("volume", val, changed)
        elif ch == "4":
            print()
            cmd_voices([])
            input("\n  (Enter pra continuar)")


def _pick_event(allow=("stop", "stop_failure", "notification")):
    print("\n  Evento:")
    for i, ev in enumerate(allow, 1):
        print(f"    {i}) {ev}")
    print(f"    0) cancelar")
    ans = input("  > ").strip()
    if ans in ("", "0", "q"):
        return None
    if ans.isdigit():
        i = int(ans) - 1
        if 0 <= i < len(allow):
            return allow[i]
    return None


def _menu_phrases():
    while True:
        c = merged()
        print("\n--- Frases TTS ---")
        print(f"  1) Frase fixa por evento")
        print(f"     stop:          {c['phrases']['stop']!r}")
        print(f"     stop_failure:  {c['phrases']['stop_failure']!r}")
        print(f"     notification:  {c['phrases']['notification']!r}")
        print(f"  2) Rotação aleatória (lista de frases)")
        print(f"     stop:          {c['phrases_random']['stop'] or '(off)'}")
        print(f"     notification:  {c['phrases_random']['notification'] or '(off)'}")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch == "1":
            ev = _pick_event()
            if not ev:
                continue
            val, changed = _prompt_str(f"Frase pra {ev}", c["phrases"][ev])
            _apply_change(f"phrases.{ev}", val, changed)
        elif ch == "2":
            ev = _pick_event(allow=("stop", "notification"))
            if not ev:
                continue
            print("  Formato: 'frase 1|frase 2|frase 3'  (separado por |)")
            val, changed = _prompt_str(f"Rotação pra {ev}", c["phrases_random"][ev])
            _apply_change(f"phrases_random.{ev}", val, changed)


def _menu_toasts():
    while True:
        c = merged()
        print("\n--- Toast (popup) ---")
        for i, ev in enumerate(EVENTS, 1):
            t = c["toasts"][ev]
            print(f"  {i}) {ev}: '{t['title']}' / '{t['body']}'")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch.isdigit() and 1 <= int(ch) <= len(EVENTS):
            ev = EVENTS[int(ch) - 1]
            t = c["toasts"][ev]
            title, ch_t = _prompt_str("Título", t["title"])
            body, ch_b = _prompt_str("Corpo", t["body"])
            cfg = load()
            if ch_t:
                if title is None:
                    unset_path(cfg, f"toasts.{ev}.title")
                else:
                    set_path(cfg, f"toasts.{ev}.title", title)
            if ch_b:
                if body is None:
                    unset_path(cfg, f"toasts.{ev}.body")
                else:
                    set_path(cfg, f"toasts.{ev}.body", body)
            save(cfg)
            print(f"  ✓ toast {ev} atualizado")


def _menu_sounds():
    while True:
        c = merged()
        print("\n--- Sons do sistema ---")
        for i, ev in enumerate(EVENTS, 1):
            print(f"  {i}) {ev}: {c['sounds'][ev] or 'default'}")
        print(f"  {len(EVENTS)+1}) Listar sons disponíveis no OS")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch == str(len(EVENTS) + 1):
            print()
            cmd_sounds([])
            input("\n  (Enter pra continuar)")
            continue
        if ch.isdigit() and 1 <= int(ch) <= len(EVENTS):
            ev = EVENTS[int(ch) - 1]
            val, changed = _prompt_str(f"Som pra {ev}", c["sounds"][ev])
            _apply_change(f"sounds.{ev}", val, changed)


def _menu_channels():
    while True:
        c = merged()
        print("\n--- Canais on/off ---")
        for i, ch_name in enumerate(CHANNELS, 1):
            state = "ON " if c["channels"][ch_name] else "OFF"
            print(f"  {i}) {ch_name:<6}  [{state}]")
        print(f"  0) Voltar")
        ch = input("\n  Toggle qual? > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch.isdigit() and 1 <= int(ch) <= len(CHANNELS):
            name = CHANNELS[int(ch) - 1]
            new = not c["channels"][name]
            cfg = load()
            set_path(cfg, f"channels.{name}", new)
            save(cfg)
            print(f"  ✓ {name} → {'ON' if new else 'OFF'}")


def _menu_smart():
    while True:
        c = merged()
        print("\n--- Esperto ---")
        print(f"  1) Quiet hours       [{c['quiet'] or 'off'}]")
        print(f"  2) Incluir CWD no TTS [{'on' if c['include_cwd'] else 'off'}]")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch == "1":
            print("  Formato: HH-HH (ex: 22-7 silencia das 22h às 7h)")
            val, changed = _prompt_str("Quiet hours", c["quiet"])
            _apply_change("quiet", val, changed)
        elif ch == "2":
            cfg = load()
            set_path(cfg, "include_cwd", not c["include_cwd"])
            save(cfg)
            print(f"  ✓ include_cwd → {'on' if not c['include_cwd'] else 'off'}")


def _menu_webhook_log():
    while True:
        c = merged()
        print("\n--- Webhook + log ---")
        print(f"  1) Webhook URL  [{c['webhook_url'] or 'off'}]")
        print(f"  2) Log file     [{c['log_file'] or 'off'}]")
        print(f"  0) Voltar")
        ch = input("\n  > ").strip()
        if ch in ("", "0", "q"):
            return
        if ch == "1":
            val, changed = _prompt_str("URL (POST JSON on each event)", c["webhook_url"])
            _apply_change("webhook_url", val, changed)
        elif ch == "2":
            val, changed = _prompt_str("Path to log file", c["log_file"])
            _apply_change("log_file", val, changed)


def _menu_show():
    cmd_show([])
    input("\n(Enter pra continuar)")


def _menu_reset():
    print("\n--- Reset ---")
    ans = input("  Apagar TODA a config (volta tudo aos defaults)? [y/N]: ").strip().lower()
    if ans in ("y", "yes", "s", "sim"):
        cmd_reset([])
    else:
        print("  cancelado.")


def cmd_menu(args):
    if not sys.stdin.isatty():
        print("Menu mode precisa de terminal interativo.", file=sys.stderr)
        print(f"Roda no teu shell (ou via prefixo ! do Claude Code):", file=sys.stderr)
        print(f"  !python \"{__file__}\" menu", file=sys.stderr)
        sys.exit(1)

    while True:
        c = merged()
        ch_str = "  ".join(
            f"{name}={'ON' if c['channels'][name] else 'OFF'}" for name in CHANNELS
        )
        print("\n" + "=" * 46)
        print("  psiu config")
        print(f"  arquivo: {CONFIG_PATH}")
        print("=" * 46)
        print(f"  1) Voz, rate, volume        [{c['voice'] or 'default'} · rate {c['rate'] or 'default'}]")
        print(f"  2) Frases TTS               [stop: {c['phrases']['stop']!r}]")
        print(f"  3) Toasts (popup)")
        print(f"  4) Sons do sistema")
        print(f"  5) Canais on/off            [{ch_str}]")
        print(f"  6) Esperto (quiet/CWD)      [quiet {c['quiet'] or 'off'} · cwd {'on' if c['include_cwd'] else 'off'}]")
        print(f"  7) Webhook + log            [{'webhook on' if c['webhook_url'] else 'webhook off'} · {'log on' if c['log_file'] else 'log off'}]")
        print(f"  8) Mostrar config (JSON)")
        print(f"  9) Reset")
        print(f"  q) Sair")
        try:
            ch = input("\n  Escolha: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if ch in ("q", "0", ""):
            print("\n  bye!")
            return
        handlers = {
            "1": _menu_voice,
            "2": _menu_phrases,
            "3": _menu_toasts,
            "4": _menu_sounds,
            "5": _menu_channels,
            "6": _menu_smart,
            "7": _menu_webhook_log,
            "8": _menu_show,
            "9": _menu_reset,
        }
        h = handlers.get(ch)
        if h:
            try:
                h()
            except (EOFError, KeyboardInterrupt):
                print()
                return
        else:
            print(f"  opção inválida: {ch}")


COMMANDS = {
    "show": cmd_show,
    "path": cmd_path,
    "voice": cmd_voice,
    "rate": cmd_rate,
    "volume": cmd_volume,
    "phrase": cmd_phrase,
    "phrases": cmd_phrases,
    "toast": cmd_toast,
    "sound": cmd_sound,
    "quiet": cmd_quiet,
    "on": cmd_on,
    "off": cmd_off,
    "cwd": cmd_cwd,
    "webhook": cmd_webhook,
    "log": cmd_log,
    "unset": cmd_unset,
    "reset": cmd_reset,
    "edit": cmd_edit,
    "voices": cmd_voices,
    "sounds": cmd_sounds,
    "menu": cmd_menu,
    "help": cmd_help,
    "-h": cmd_help,
    "--help": cmd_help,
    "--export": cmd_export,
    "export": cmd_export,
}


def main():
    if len(sys.argv) < 2:
        cmd_show([])
        print("\n" + HELP)
        return
    cmd, rest = sys.argv[1], sys.argv[2:]
    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"unknown command: {cmd}\n", file=sys.stderr)
        print(HELP, file=sys.stderr)
        sys.exit(1)
    handler(rest)


if __name__ == "__main__":
    main()
