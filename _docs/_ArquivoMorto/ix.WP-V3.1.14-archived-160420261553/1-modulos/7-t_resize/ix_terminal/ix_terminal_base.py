#!/usr/bin/env python3
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ ix_terminal_base – V1.5.5                                  │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | ix.WP                                     │║
# ║ ██ ▀ ████████ │ commit:HEAD                                                │║
# ║ ██ ● ██▀██▀██ │ Última modificação: 2026-03-15 - 09:45                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ 1-dev/1-modulos/7-t_resize/ix_terminal/                    │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * Classes base reutilizáveis para TUI ix_terminal.         │║
# ║               │ * IxTerminalApp, SplashScreen, ActionScreen, BrandSidebar. │║
# ║               │ * NÃO contém lógica de projeto — só estrutura visual.      │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝
"""
Classes base reutilizáveis para ix_terminal TUI.

Cada projeto importa estas classes e fornece:
  - PROJECT_NAME, PROJECT_SUBTITLE, PROJECT_EMOJI
  - MENU_SECTIONS: lista de (seção, [(tecla, label, descrição), ...])
  - ACTION_MAP: dict {action_name: "emoji Título"}
  - action handlers (subclasse de ActionScreen)

Uso mínimo:
    from ix_terminal_base import IxTerminalApp, ActionScreen
    class MyApp(IxTerminalApp): ...
    MyApp().run()
"""

from __future__ import annotations

import asyncio
from typing import Callable, Sequence

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Label, RichLog, Static


# ═══════════════════════════════════════════════════════════════
# MARCA — Obrigatória (fonte: iHead_iFooter_MarcaANSII.md)
# ═══════════════════════════════════════════════════════════════

BRAND_STD = """\
[bold green]     ▄██▄
  ▄███▀▀███▄
▄██▀      ▀██▄
██          ██
██          ██
███▄      ▄███
██████▄▄██████
██████████████
██ ▀ █████████
██ ● ███▀██▀██
██    ██ ██ ██
      ██    ██
      ██[/]

[dim]© 2026 Ir.On
ironix.com.br[/]"""

BRAND_COMPACT = """\
[bold green]  ▄███▄
▄█▀   ▀█▄
█       █
██▄   ▄██
█████████
█ █ █ █ █
█ ● █ ▀ █
▀   █   ▀
    ▀[/]
[dim]© Ir.On[/]"""

# Frames para animação splash (marca constrói linha por linha, sobe da base)
BRAND_ANIM_FRAMES = [
    "[bold green]     ▄██▄[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄\n██          ██\n██          ██[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄\n██          ██\n██          ██\n███▄      ▄███[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄\n██          ██\n██          ██\n███▄      ▄███\n██████▄▄██████\n██████████████[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄\n██          ██\n██          ██\n███▄      ▄███\n██████▄▄██████\n██████████████\n██ ▀ █████████\n██ ● ███▀██▀██[/]",
    "[bold green]     ▄██▄\n  ▄███▀▀███▄\n▄██▀      ▀██▄\n██          ██\n██          ██\n███▄      ▄███\n██████▄▄██████\n██████████████\n██ ▀ █████████\n██ ● ███▀██▀██\n██    ██ ██ ██\n      ██    ██\n      ██[/]",
]


# ═══════════════════════════════════════════════════════════════
# WIDGETS
# ═══════════════════════════════════════════════════════════════

class BrandSidebar(Static):
    """Sidebar com marca compacta Ir.On."""
    pass


class MenuOption(Static):
    """Item de menu clicável."""

    def __init__(self, key: str, label: str, desc: str, **kw):
        super().__init__(**kw)
        self._key = key
        self._label = label
        self._desc = desc

    def on_mount(self) -> None:
        self.update(
            f"  [bold red]{self._key.upper()}[/])  "
            f"[bold cyan]▸ {self._label}[/]  "
            f"[dim]{self._desc}[/]"
        )

    def on_click(self) -> None:
        self.app.handle_menu_key(self._key)  # type: ignore[attr-defined]


class SectionLabel(Static):
    """Rótulo de seção no menu."""
    pass


# ═══════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════

class SplashScreen(Screen):
    """Tela de abertura com animação da marca (set_timer — OBRIGATÓRIO)."""

    CSS = """
    SplashScreen {
        align: center bottom;
        background: $background;
    }
    #splash-box { width: auto; height: auto; padding: 0 4 2 4; }
    #splash-brand { width: auto; }
    #splash-info { text-align: center; margin-top: 1; }
    #splash-dots { text-align: center; margin-top: 1; }
    """

    def __init__(self, project_name: str, project_subtitle: str, project_emoji: str):
        super().__init__()
        self._project_name = project_name
        self._project_subtitle = project_subtitle
        self._project_emoji = project_emoji

    def compose(self) -> ComposeResult:
        with Vertical(id="splash-box"):
            yield Static("", id="splash-brand")
            yield Static("", id="splash-info")
            yield Static("", id="splash-dots")

    def on_mount(self) -> None:
        self._phase = 0
        self._dot_count = 0
        self._num_brand_frames = len(BRAND_ANIM_FRAMES)
        self.set_timer(0.1, self._tick)

    def _tick(self) -> None:
        brand = self.query_one("#splash-brand", Static)
        info = self.query_one("#splash-info", Static)
        dots = self.query_one("#splash-dots", Static)
        p = self._phase
        n = self._num_brand_frames

        if p < n:
            brand.update(BRAND_ANIM_FRAMES[p])
            self._phase += 1
            self.set_timer(0.09, self._tick)
        elif p == n:
            brand.update(BRAND_STD)
            self._phase += 1
            self.set_timer(0.3, self._tick)
        elif p == n + 1:
            info.update(
                f"[bold]{self._project_emoji}  {self._project_name}[/]  "
                f"[dim]{self._project_subtitle}[/]"
            )
            self._phase += 1
            self._dot_count = 0
            self.set_timer(0.3, self._tick)
        elif p == n + 2:
            if self._dot_count < 6:
                dots.update(
                    f"[bold green]{'●' * (self._dot_count + 1)}"
                    f"{'○' * (5 - self._dot_count)}[/]"
                )
                self._dot_count += 1
                self.set_timer(0.15, self._tick)
            else:
                self._phase += 1
                self.set_timer(0.2, self._tick)
        else:
            self.app.pop_screen()


# ═══════════════════════════════════════════════════════════════
# ACTION SCREEN (sub-páginas com log scrollável)
# ═══════════════════════════════════════════════════════════════

class ActionScreen(Screen):
    """Screen genérica com RichLog scrollável.

    Subclasses override ``_run_action`` para implementar a lógica.
    O default chama ``self.actions_registry[action_name](log)`` se
    o app principal registrou handlers via ``register_action``.
    """

    BINDINGS = [
        Binding("escape", "go_back", "← Voltar"),
        Binding("q", "quit_app", "Sair"),
    ]

    CSS = """
    ActionScreen { layout: horizontal; }
    ActionScreen BrandSidebar {
        width: 14; padding: 1 1;
        content-align: center middle;
        border-right: solid $secondary;
    }
    ActionScreen #ar { width: 1fr; layout: vertical; }
    ActionScreen #at {
        height: 3; content-align: center middle;
        text-style: bold; border-bottom: solid $secondary;
    }
    ActionScreen #al {
        height: 1fr; padding: 0 1;
        scrollbar-color: $secondary;
    }
    ActionScreen #af {
        height: 1; border-top: solid $secondary;
        content-align: center middle;
    }
    """

    def __init__(self, title: str, action_name: str):
        super().__init__()
        self._title = title
        self._action = action_name

    def compose(self) -> ComposeResult:
        yield BrandSidebar(BRAND_COMPACT)
        with Vertical(id="ar"):
            yield Static(f"[bold]{self._title}[/]", id="at")
            yield RichLog(id="al", highlight=True, markup=True)
            yield Static("[dim]ESC)Voltar  ↑↓)Scroll  Q)Sair[/]", id="af")

    def on_mount(self) -> None:
        asyncio.create_task(self._run_action())

    async def _run_action(self) -> None:
        """Override ou registre handlers no app."""
        log = self.query_one("#al", RichLog)
        handler = getattr(self.app, f"action_handler_{self._action}", None)
        if handler:
            await handler(log)
        else:
            log.write(f"[dim]Ação '{self._action}' sem handler registrado.[/]")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()


# ═══════════════════════════════════════════════════════════════
# APP PRINCIPAL (classe base)
# ═══════════════════════════════════════════════════════════════

class IxTerminalApp(App):
    """Classe base para TUI ix_terminal.

    Subclasses devem definir:
      - PROJECT_NAME, PROJECT_SUBTITLE, PROJECT_EMOJI (class vars)
      - MENU_SECTIONS: list[(section_name, list[(key, label, desc)])]
      - ACTION_MAP: dict[action_name, "emoji Título"]
      - action_handler_<name>(self, log: RichLog) — async handlers
    """

    PROJECT_NAME: str = "ix.Project"
    PROJECT_SUBTITLE: str = ""
    PROJECT_EMOJI: str = "⚡"

    MENU_SECTIONS: Sequence[tuple[str, Sequence[tuple[str, str, str]]]] = []
    ACTION_MAP: dict[str, str] = {}

    theme: str = "tokyo-night"  # type: ignore[assignment]

    CSS = """
    Screen { layout: horizontal; }
    BrandSidebar {
        width: 14; padding: 1 1;
        content-align: center middle;
        border-right: solid $secondary;
    }
    #rp { width: 1fr; layout: vertical; }
    #title-bar {
        height: 3; content-align: center middle;
        text-style: bold; border-bottom: solid $secondary;
    }
    #menu { height: 1fr; padding: 1 2; }
    SectionLabel { margin-top: 1; color: $warning; text-style: bold; }
    MenuOption { height: 1; margin-left: 1; }
    MenuOption:hover { background: $boost; }
    #foot {
        height: 1; border-top: solid $secondary;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield BrandSidebar(BRAND_COMPACT)
        with Vertical(id="rp"):
            yield Static(
                f"[bold]{self.PROJECT_EMOJI}  {self.PROJECT_NAME}[/]  "
                f"[dim]{self.PROJECT_SUBTITLE}[/]",
                id="title-bar",
            )
            with VerticalScroll(id="menu"):
                for sect, items in self.MENU_SECTIONS:
                    yield SectionLabel(f"▶ {sect}")
                    for key, label, desc in items:
                        yield MenuOption(key=key, label=label, desc=desc)
            # Footer com atalhos
            shortcuts = "  ".join(
                f"{k.upper()}){lab}"
                for _sect, items in self.MENU_SECTIONS
                for k, lab, _d in items
            )
            yield Static(f"[dim]{shortcuts}  Q)Sair[/]", id="foot")
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen(SplashScreen(
            self.PROJECT_NAME,
            self.PROJECT_SUBTITLE,
            self.PROJECT_EMOJI,
        ))

    def handle_menu_key(self, key: str) -> None:
        """Chamado por MenuOption.on_click."""
        action = self._key_to_action().get(key)
        if action and action in self.ACTION_MAP:
            self.push_screen(ActionScreen(self.ACTION_MAP[action], action))

    def action_go(self, action: str) -> None:
        """Chamado por Binding("x", "go('action')")."""
        if action in self.ACTION_MAP:
            self.push_screen(ActionScreen(self.ACTION_MAP[action], action))

    def _key_to_action(self) -> dict[str, str]:
        """Mapa tecla → action_name derivado de MENU_SECTIONS + ACTION_MAP."""
        result: dict[str, str] = {}
        action_names = list(self.ACTION_MAP.keys())
        idx = 0
        for _sect, items in self.MENU_SECTIONS:
            for key, _label, _desc in items:
                if idx < len(action_names):
                    result[key] = action_names[idx]
                    idx += 1
        return result


"""
  ▗▅▅▖
▄▛▘‾‾▝▜▄
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀
    ▀
"""
