# Pydantic Code Style Guide

## Core Principles

- Use Pydantic for all data validation
- Leverage type hints for automatic validation
- Prefer validators over complex logic in models
- Use `extra="forbid"` to catch typos

## Model Definition

```python
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator


class Chapter(BaseModel):
    """Represents a game chapter with scenes and metadata."""
    
    model_config = {"extra": "forbid"}
    
    id: str
    title: str
    scenes: list[Scene]
    
    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure chapter ID matches filename convention."""
        if not v.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            raise ValueError("Chapter ID must start with a number")
        return v
```

## Validators

- Use `@field_validator` for single-field validation
- Use `@model_validator` for cross-field validation
- Always use `@classmethod` decorator
- Raise `ValueError` with descriptive messages

```python
@field_validator("scenes")
@classmethod
def validate_scenes(cls, v: list[Scene]) -> list[Scene]:
    """Ensure at least one scene exists."""
    if len(v) < 1:
        raise ValueError("Chapter must have at least one scene")
    return v

@model_validator(mode="after")
def validate_scene_ids_unique(self) -> Chapter:
    """Ensure all scene IDs are unique."""
    scene_ids = [s.id for s in self.scenes]
    if len(scene_ids) != len(set(scene_ids)):
        raise ValueError("Scene IDs must be unique")
    return self
```

## Field Configuration

```python
from pydantic import Field


class Scene(BaseModel):
    """Represents a single scene within a chapter."""
    
    model_config = {"extra": "forbid"}
    
    id: str
    text: str = Field(..., min_length=1)
    choice: Choice | None = None
    next_chapter: str | None = None
    text_variants: list[TextVariant] | None = None
```

## Mutually Exclusive Fields

Use `@model_validator` to enforce mutual exclusivity:

```python
@model_validator(mode="after")
def validate_terminal_fields(self) -> Scene:
    """Ensure choice and next_chapter are mutually exclusive."""
    if self.choice is not None and self.next_chapter is not None:
        raise ValueError("Scene cannot have both 'choice' and 'next_chapter'")
    if self.choice is None and self.next_chapter is None:
        raise ValueError("Scene must have either 'choice' or 'next_chapter'")
    return self
```

## Custom Types

Use `Literal` for constrained choices:

```python
from typing import Literal


class FlagAssignment(BaseModel):
    """Represents a flag to be set based on player choice."""
    
    model_config = {"extra": "forbid"}
    
    key: str
    value: bool | str | int
    
    @classmethod
    def from_raw_string(cls, raw: str) -> FlagAssignment:
        """Parse a raw string like 'flag: true' into a FlagAssignment."""
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()
        
        if value.lower() == "true":
            return cls(key=key, value=True)
        elif value.lower() == "false":
            return cls(key=key, value=False)
        elif value.lstrip("-").isdigit():
            return cls(key=key, value=int(value))
        else:
            return cls(key=key, value=value)
```

## Serialization

```python
# Model to dict
chapter_dict = chapter.model_dump()

# Model to JSON
chapter_json = chapter.model_dump_json()

# Dict to model
chapter = Chapter.model_validate(chapter_dict)

# JSON to model
chapter = Chapter.model_validate_json(chapter_json)
```

## Error Handling

```python
from pydantic import ValidationError

try:
    chapter = Chapter.model_validate(yaml_data)
except ValidationError as e:
    print(f"Validation error: {e}")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

## Best Practices

1. **Always use `extra="forbid"`** — catches typos and unexpected fields
2. **Use `Field(...)` for required fields** — makes intent explicit
3. **Use `field_validator` over `__init__`** — cleaner, more testable
4. **Prefer `model_validator` for cross-field logic** — keeps models coherent
5. **Use `from __future__ import annotations`** — modern type syntax
6. **Keep models focused** — one model per data structure
7. **Use inheritance for variants** — not optional fields
