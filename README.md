# Muara

CLI narrative game set in colonial-era Batavia, 1899. You play as Rasmi, a buruh pribumi who keeps a private ledger of wages.

## Quick Start

```bash
uv run muara
```

## Development

```bash
uv run pytest tests/ -v          # run all tests
uv run pytest -x -v              # stop on first failure
```

## Adding Chapters

1. Create a YAML file in `content/chapters/` (e.g. `05_bab_baru.yaml`)
2. Follow the schema in `AGENTS.md` → YAML Chapter Format
3. Add the chapter ID to `content/manifest.yaml`
4. Run `uv run pytest tests/test_content_integrity.py -v` to validate

## Project Structure

```
src/muara/
├── constants.py           # END_OF_STORY_MARKER
├── main.py              # CLI entry point
├── models/              # Pydantic schemas (Chapter, Scene, SaveState)
└── engine/              # Runtime (runner, renderer, state, saves)

content/
├── manifest.yaml        # Chapter sequence
└── chapters/            # YAML chapter files

tests/                   # pytest suite
```
