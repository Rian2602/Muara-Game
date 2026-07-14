# Contributing to Muara

Thank you for your interest in contributing to Muara! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Content Guidelines](#content-guidelines)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Muara-Game.git
   cd Muara-Game
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Rian2602/Muara-Game.git
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Installation

```bash
# Sync dependencies
uv sync

# Run tests to verify setup
uv run pytest tests/ -v
```

### Development Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_models.py -v
uv run pytest tests/test_engine.py -v
uv run pytest tests/test_gui.py -v

# Run tests with coverage
uv run pytest tests/ --cov=src/muara

# Play the game (CLI)
uv run muara

# Play the game (GUI)
uv run muara-gui
```

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS

### Suggesting Features

1. Check existing issues/discussions
2. Create a new issue with:
   - Feature description
   - Use case
   - How it fits the game's vision

### Submitting Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation if needed

3. **Run tests**:
   ```bash
   uv run pytest tests/ -v
   ```

4. **Commit your changes**:
   ```bash
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Pull Request Process

1. **Title**: Use conventional commit format (`feat:`, `fix:`, `docs:`, `test:`, etc.)
2. **Description**: Explain what the PR does and why
3. **Tests**: Ensure all tests pass
4. **Documentation**: Update relevant docs (README, AGENTS.md, etc.)
5. **Review**: Wait for maintainer review

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**
```
feat(chapters): add chapter 12 with new branching path
fix(engine): handle edge case in flag evaluation
docs: update README with new CLI options
test: add tests for multi-slot save system
```

## Content Guidelines

### Writing New Chapters

1. **Read the World Bible** (`docs/00_WORLD_BIBLE.md`) — this is canon
2. **Read Character Brief** (`docs/01_CHARACTER_PLOT_BRIEF.md`) — character constraints
3. **Follow the YAML schema** (see `AGENTS.md` for format)
4. **Use proper flag naming**: `snake_case`, Indonesian, past tense actions
5. **Ensure all scene references resolve** — no dead ends

### Chapter Structure

```yaml
id: "NN_nama_bab"           # Must match filename (without .yaml)
title: "CHAPTER TITLE"      # English, uppercase style
location: "Location, City"
date: "DD Month YYYY"
time: "HH.MM"
scenes:
  - id: "scene_1"
    text: |
      [First-person narrative, present tense.]
    choice:
      prompt: "What do you do?"
      options:
        - id: "option_a"
          label: "Option A"
          next: "scene_2a"
          set_flags:
            - "flag_name: true"
```

### Flag Naming Conventions

- Use `snake_case`: `melihat_anomali`, `menyimpan_bukti`
- Describe actions, not outcomes: `melapor_ke_mandor`, not `laporan_diterima`
- Boolean for binary choices: `melapor: true` / `melapor: false`
- Integer for counts: `teknanan_meningkat: 3`

### Testing Content

```bash
# Validate chapter schema
uv run pytest tests/test_content_integrity.py -v

# Validate narrative graph (no orphans, no dead ends)
uv run pytest tests/test_narrative_graph.py -v

# Run all tests
uv run pytest tests/ -v
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Use Pydantic models with `extra="forbid"`
- Prefer `snake_case` for functions/variables
- Use `PascalCase` for classes

### Engine Conventions

- **Input injection**: Never call `input()` directly in engine code
- **Renderer purity**: Renderers only print, never read input
- **Error handling**: Use custom exceptions (`ChapterLoadError`, `SaveLoadError`, `ChapterRunError`)
- **Timezone**: Always use `datetime.now(timezone.utc)`

### File Organization

```
src/muara/
├── models/         # Pydantic data models
├── engine/         # Core game logic
├── gui/            # Textual GUI
├── main.py         # CLI entry point
└── gui_cli.py      # GUI entry point
```

## Testing

### Test Requirements

- All new features must include tests
- All tests must pass before submitting PR
- Aim for good coverage of edge cases

### Test Patterns

```python
# Unit test
def test_feature_works():
    result = my_function()
    assert result == expected

# Integration test
def test_playthrough():
    state = GameState.new_playthrough("test", "chapter_1", "")
    # ... test game flow
```

### Running Specific Tests

```bash
# Single test file
uv run pytest tests/test_models.py -v

# Single test function
uv run pytest tests/test_models.py::TestChapterModel::test_valid_chapter -v

# With coverage
uv run pytest tests/ --cov=src/muara --cov-report=term-missing
```

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Check existing documentation in `docs/`
- Review `AGENTS.md` for detailed conventions

Thank you for contributing to Muara! 🎮
