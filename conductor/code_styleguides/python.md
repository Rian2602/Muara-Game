# Python Code Style Guide

## General Principles

- Follow PEP 8 for all Python code
- Write clear, readable code that speaks for itself
- Prefer explicit over implicit
- Keep functions focused and small
- Use meaningful variable and function names

## Formatting

- **Line length:** 88 characters (Black default)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings, single quotes for dictionary keys
- **Trailing commas:** Always use trailing commas in multi-line collections

## Type Hints

- Use type hints for all function signatures
- Use `from __future__ import annotations` for modern type hint syntax
- Prefer `str | None` over `Optional[str]` (Python 3.10+)
- Use `list[str]` over `List[str]` (Python 3.9+)

```python
def process_chapter(chapter_id: str, state: GameState) -> Scene | None:
    """Process a chapter and return the next scene."""
    ...
```

## Imports

- Group imports: stdlib → third-party → local
- Use absolute imports for local modules
- One import per line

```python
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, field_validator

from muara.models.chapter import Chapter
```

## Error Handling

- Use specific exception types, not bare `except`
- Wrap library errors in custom exceptions
- Never silently swallow exceptions
- Use context managers for resource cleanup

```python
class ChapterLoadError(Exception):
    """Raised when a chapter fails to load or validate."""
    pass

try:
    chapter = load_chapter(path)
except yaml.YAMLError as e:
    raise ChapterLoadError(f"Invalid YAML in {path}: {e}") from e
```

## Docstrings

- Use Google-style docstrings for public functions
- Include type information in docstrings when not obvious
- Keep docstrings concise but informative

```python
def evaluate_condition(condition: str, flags: dict[str, bool | str | int]) -> bool:
    """Evaluate a condition string against game state flags.
    
    Args:
        condition: Condition string like "flag == true"
        flags: Dictionary of flag names to values
        
    Returns:
        True if condition is met, False otherwise
    """
    ...
```

## Naming Conventions

- **Functions:** `snake_case` — verbs or verb phrases
- **Variables:** `snake_case` — nouns or noun phrases
- **Classes:** `PascalCase` — nouns
- **Constants:** `UPPER_SNAKE_CASE` — descriptive names
- **Private:** Prefix with underscore `_private_method`

## Testing

- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- One assertion per test (prefer multiple focused tests)
- Use fixtures for shared setup
- Name test files `test_<module>.py`

```python
def test_load_chapter_with_valid_yaml():
    """Test that a valid YAML chapter loads successfully."""
    # Arrange
    yaml_content = {"id": "test", "scenes": [...]}
    
    # Act
    chapter = load_chapter_from_dict(yaml_content)
    
    # Assert
    assert chapter.id == "test"
    assert len(chapter.scenes) == 1
```
