from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from rich.text import Text

from muara.models.chapter import ChoiceOption


class CLIRenderer:
    """Rich-based CLI renderer implementing the Renderer protocol."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def render_chapter_header(
        self,
        title: str,
        location: str,
        date: str,
        time: str,
        chapter_index: int = 0,
        total_chapters: int = 0,
    ) -> None:
        header_text = Text()
        if total_chapters > 0:
            header_text.append(f"[Bab {chapter_index}/{total_chapters}]", style="dim")
            header_text.append("\n")
        header_text.append(title, style="bold")
        header_text.append("\n")
        header_text.append(location, style="bold italic")
        header_text.append("\n")
        header_text.append(f"{date}, {time}", style="bold italic")

        self.console.print()
        self.console.print(Panel(header_text, expand=False, border_style="dim"))
        self.console.print()

    def render_scene_text(self, text: str) -> None:
        self.console.print(Padding(text.strip(), (0, 2)))
        self.console.print()

    def render_choice_prompt(
        self, prompt: str, options: list[ChoiceOption]
    ) -> None:
        self.console.print(Padding(Text(prompt, style="bold"), (0, 2)))
        self.console.print()
        for index, option in enumerate(options, 1):
            self.console.print(
                Padding(f"[cyan]{index}.[/cyan] {option.label}", (0, 4))
            )
        self.console.print()

    def render_continue_prompt(self) -> None:
        self.console.print(
            Padding(
                Text("(tekan Enter untuk lanjut)", style="dim italic"), (0, 2)
            )
        )

    def render_error(self, message: str) -> None:
        self.console.print(
            Panel(Text(message, style="bold red"), border_style="red")
        )

    def render_line(self, text: str = "") -> None:
        self.console.print(text)
