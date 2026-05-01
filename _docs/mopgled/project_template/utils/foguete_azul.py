# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Foguete Azul – V1.1.3                                      │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║
# ║ ██ ▀ ████████ │ commit:f563b5b                                             │║
# ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ _docs/mopgled/project_template/utils/foguete_azul.py       │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * V1.1.3 - [sem detalhes]                                  │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝


#!/usr/bin/env python3
import sys, time, random, os, threading, platform, shutil, argparse
from typing import TextIO

def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")

def rocket_rise(
    lines: int | None = None,
    right_step: int = 2,
    delay: float = 0.1,
    stream: TextIO = sys.stderr,
    sound_file: str | None = None,
    force: bool = False,
):
    """
    Animação do foguete com:
      • Forçar animação sem TTY (--force)
      • Seleção de stream (--use-stdout)
      • Som opcional (afplay/play) com pre-roll
    """
    # altura base
    if lines is None:
        total = shutil.get_terminal_size().lines if (sys.stdout.isatty() or sys.stderr.isatty()) else 24
        lines = max(3, total - 9)

    interactive = (stream.isatty() or force)
    is_ci = _truthy(os.getenv("CI")) or _truthy(os.getenv("RENDER"))

    # modo compacto em CI real ou quando não interativo (e sem force)
    if (not interactive) or is_ci:
        if sound_file and platform.system() in {"Darwin", "Linux"} and interactive:
            player = "afplay" if platform.system() == "Darwin" else "play"
            threading.Thread(target=lambda: os.system(f"{player} '{sound_file}'"), daemon=True).start()
        stream.write("...LANÇADO!🚀\n")
        stream.flush()
        return

    size = shutil.get_terminal_size()
    width = max(40, size.columns)

    # limpar tela
    stream.write("\033[2J\033[H")
    stream.flush()

    moon = [
        "       _..._      ",
        "    .:::::::.     ",
        "   :::::::::::    ",
        "   :::::::::::    ",
        "    ':::::::'     ",
        "      '::'      "
    ]

    # dispara o som 1s antes
    if sound_file and platform.system() in {"Darwin","Linux"}:
        player = 'afplay' if platform.system()=='Darwin' else 'play'
        threading.Thread(target=lambda: os.system(f"{player} '{sound_file}'"), daemon=True).start()
        time.sleep(1)

    for step in range(1, lines + 1):
        bg_code = 46 if step < lines/2 else 44
        bg = f"\033[{bg_code}m"
        total_h = len(moon) + lines

        stream.write("\033[H")
        for _ in range(total_h):
            stream.write(bg + " " * width + "\033[0m\n")
        stream.flush()

        for i, line in enumerate(moon, start=1):
            x = max(1, width - len(line) - 1)
            stream.write(f"\033[{i};{x}H{bg}{line}\033[0m")
        stream.flush()

        for row in range(lines):
            if row == lines - step:
                offset = min(width - 2, step * right_step)
                content = " " * offset + "🚀" + " " * max(0, width - offset - 1)
            else:
                density = 0.002 + 0.005 * (step / lines)
                content = "".join("*" if random.random() < density else " " for _ in range(width))
            stream.write(bg + content + "\033[0m\n")

        stream.flush()
        time.sleep(delay)

    final_bg = "\033[44m"
    stream.write("\033[H\033[2J")
    stream.write(final_bg + " " * width + "\033[0m\n")
    stream.write(final_bg + " " * width + "\033[0m\n")
    stream.write(f"\033[{right_step*lines}C\033[44;97m...LANÇADO!🚀\033[0m\n")
    stream.flush()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Animação de foguete")
    p.add_argument("--lines", type=int, help="número de linhas de altura")
    p.add_argument("--right-step", type=int, dest="right_step", default=2, help="passo horizontal")
    p.add_argument("--delay", type=float, default=0.08, help="delay entre frames")
    p.add_argument("--sound-file", dest="sound_file", default="static/sounds/foguete.wav",
                   help="caminho para .wav do som de lançamento")
    p.add_argument("--force", action="store_true", help="força animação mesmo sem TTY")
    p.add_argument("--use-stdout", action="store_true", help="imprime no stdout (não no stderr)")
    args = p.parse_args()

    out = sys.stdout if args.use_stdout else sys.stderr
    rocket_rise(
        lines=args.lines,
        right_step=args.right_step,
        delay=args.delay,
        stream=out,
        sound_file=args.sound_file,
        force=args.force,
    )

'''
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
'''
