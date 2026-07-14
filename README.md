# Muara

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-268%20passed-brightgreen)]()
[![Code style: pydantic](https://img.shields.io/badge/code%20style-pydantic-3d6ef7.svg)](https://pydantic-docs.readthedocs.io/)

> *Angka-angka tidak akan berhenti karena aku berhenti mencatat.*

**Muara** is a CLI/GUI narrative game set in colonial-era Batavia, 1899. You play as **Rasmi**, a buruh pribumi at the municipal warehouses who discovers systematic wage discrepancies. You keep a private ledger — and must decide what to do with what you find.

## Quick Start

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager)

### Installation

```bash
git clone https://github.com/Rian2602/Muara-Game.git
cd Muara-Game
uv sync
```

### Play

**CLI mode** (Rich terminal):

```bash
uv run muara
```

**GUI mode** (Textual TUI):

```bash
uv run muara-gui
```

### CLI Options

```bash
uv run muara --typewriter                    # Enable typewriter effect
uv run muara --typewriter --typewriter-delay 0.05  # Custom delay (seconds)
```

## Features

- **16 chapters** with branching paths (chapters 01-04 have a/b/c/d variants)
- **6 endings** based on your choices and discovered evidence
- **Dual mode**: CLI (Rich) + GUI (Textual) sharing the same engine
- **Multi-slot saves**: Save and load multiple game progressions
- **Typewriter effect**: Character-by-character text animation (optional)
- **Scene hooks**: Dynamic flag changes on scene entry/exit
- **Structured conditions**: Advanced flag-based branching with `requires` and `visible_if`

## Architecture

```
src/muara/
├── main.py                # CLI entry point
├── gui_cli.py             # GUI entry point
├── constants.py           # Shared constants
├── engine/
│   ├── chapter_loader.py  # YAML loading
│   ├── chapter_runner.py  # CLI game loop
│   ├── ending.py          # Ending logic (shared CLI/GUI)
│   ├── render_protocol.py # Renderer interface
│   ├── render_cli.py      # Rich terminal renderer
│   ├── renderer.py        # Legacy wrapper
│   ├── save_manager.py    # JSON save/load
│   └── state.py           # Flag store + condition eval
├── gui/
│   ├── app.py             # Textual GUI (MuaraApp + GameScreen)
│   └── muara.tcss         # GUI stylesheet
└── models/
    ├── chapter.py         # Chapter, Scene, Choice models
    └── save_state.py      # Save state model

content/
├── manifest.yaml          # Chapter sequence
└── chapters/              # 16 YAML chapter files

docs/                      # Design documents
tests/                     # pytest suite (268 tests)
```

### Dual Mode

| Mode | Command | Frontend | Engine |
|------|---------|----------|--------|
| CLI | `uv run muara` | Rich terminal | `ChapterRunner` |
| GUI | `uv run muara-gui` | Textual TUI | `GameScreen` |

Both use the same `engine/` (state, saves, chapter loading) and `content/` (YAML chapters).

## Development

### Running Tests

```bash
uv run pytest tests/ -v                    # Run all tests (268 tests)
uv run pytest -x -v                        # Stop on first failure
uv run pytest tests/test_models.py -v      # Model validation only
uv run pytest tests/test_engine.py -v      # Engine tests only
uv run pytest tests/test_gui.py -v         # GUI tests only
```

### Adding Chapters

1. Create a YAML file in `content/chapters/` (e.g. `12_bab_baru.yaml`)
2. Follow the schema in `AGENTS.md` (YAML Chapter Format section)
3. Add the chapter ID to `content/manifest.yaml`
4. Run `uv run pytest tests/test_content_integrity.py -v` to validate
5. Run `uv run pytest tests/ -v` — all tests must pass

See `docs/00_WORLD_BIBLE.md` for world canon and `docs/01_CHARACTER_PLOT_BRIEF.md` for character guidelines.

### Chapter YAML Structure

```yaml
id: "12_bab_baru"
title: "CHAPTER TITLE"
location: "Location, City"
date: "DD Month YYYY"
time: "HH.MM"
scenes:
  - id: "scene_1"
    text: |
      [First-person narrative, present tense.]
    on_enter:
      - "flag_name: true"
    choice:
      prompt: "What do you do?"
      options:
        - id: "option_a"
          label: "Option A"
          next: "scene_2a"
          set_flags:
            - "chose_option_a: true"
        - id: "option_b"
          label: "Option B"
          next: "scene_2b"
          visible_if:
            - flag: "some_flag"
              operator: "=="
              value: true
  - id: "scene_2a"
    text: |
      [Consequence of option A.]
    next_chapter: "13_next_chapter"
```

## Story

16 chapters. 6 endings. Your choices shape Rasmi's fate — and the truth about the numbers.

**Endings:** Pembebasan | Kehancuran | Sekutu | Dipercaya | Dicurigai | Terlupakan

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) - 2026 Rian2602
