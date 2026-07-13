# Technology Stack

## Core Runtime

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.11+ | Primary runtime |
| Package Manager | uv | latest | Dependency management and virtual environments |
| Build System | Hatchling | latest | Package building and distribution |

## Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| Rich | 15.0+ | CLI rendering (colors, panels, formatting) |
| Pydantic | 2.13+ | Data validation (chapter schemas, save state) |
| PyYAML | 6.0+ | YAML parsing for chapter content files |

## Testing

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 9.1+ | Test framework |
| pytest-coverage | - | Code coverage measurement |

## Distribution

| Tool | Purpose |
|------|---------|
| PyInstaller | Standalone binary packaging |
| GitHub Releases | Binary distribution channels |

## Development Tools

| Tool | Purpose |
|------|---------|
| js-yaml (Node) | Content validation tooling |
| Git | Version control |

## Architecture

**Monolith Python package** with clear module separation:
- `src/muara/` — Main package
- `src/muara/engine/` — Runtime logic (chapter loading, execution, rendering, state)
- `src/muara/models/` — Pydantic data models
- `content/chapters/` — YAML content files
- `tests/` — pytest test suite

## Dependency Management

- **Production:** pydantic, pyyaml, rich
- **Development:** pytest
- **Node.js (optional):** js-yaml for content validation scripts

All dependencies managed via `pyproject.toml` with `uv` as the package manager.
