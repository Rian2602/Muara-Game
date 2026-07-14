# Muara

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-230%20passed-brightgreen)]()

> *Angka-angka tidak akan berhenti karena aku berhenti mencatat.*

**Muara** is a CLI/GUI narrative game set in colonial-era Batavia, 1899. You play as **Rasmi**, a buruh pribumi at the municipal warehouses who discovers systematic wage discrepancies. You keep a private ledger — and must decide what to do with what you find.

## Install

Requires [Python 3.11+](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/Rian2602/Muara-Game.git
cd Muara-Game
uv sync
```

## Play

**CLI mode** (Rich terminal):

```bash
uv run muara
```

**GUI mode** (Textual TUI):

```bash
uv run muara-gui
```

## Development

```bash
uv run pytest tests/ -v          # run all tests (230 tests)
uv run pytest -x -v              # stop on first failure
uv run pytest tests/test_models.py -v   # model validation only
```

## Adding Chapters

1. Create a YAML file in `content/chapters/` (e.g. `12_bab_baru.yaml`)
2. Follow the schema in `AGENTS.md` (YAML Chapter Format section)
3. Add the chapter ID to `content/manifest.yaml`
4. Run `uv run pytest tests/test_content_integrity.py -v` to validate
5. Run `uv run pytest tests/ -v` — all tests must pass

See `docs/00_WORLD_BIBLE.md` for world canon and `docs/01_CHARACTER_PLOT_BRIEF.md` for character guidelines.

## Project Structure

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
tests/                     # pytest suite (230 tests)
```

## Architecture

Muara supports two frontends sharing the same engine:

| Mode | Command | Frontend | Engine |
|------|---------|----------|--------|
| CLI | `uv run muara` | Rich terminal | `ChapterRunner` |
| GUI | `uv run muara-gui` | Textual TUI | `GameScreen` |

Both use the same `engine/` (state, saves, chapter loading) and `content/` (YAML chapters).

## Story

16 chapters. 6 endings. Your choices shape Rasmi's fate — and the truth about the numbers.

**Endings:** Pembebasan | Kehancuran | Sekutu | Dipercaya | Dicurigai | Terlupakan

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`uv run pytest tests/ -v`)
4. Submit a pull request

See `AGENTS.md` for coding conventions and content guidelines.

## License

[MIT](LICENSE) - 2026 Rian2602
