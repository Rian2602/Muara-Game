# Specification: Write Tests for `main.py`

## Overview

`src/muara/main.py` is the orchestration entry point for the entire CLI game. It contains 176 statements with **0% test coverage** — the most critical gap in the codebase. This file handles save slot selection, chapter resolution, chapter path lookup, the main game loop, and ending display. Without tests, any regression in core game flow goes undetected.

This is NOT a refactor. This is writing tests for code that already exists and works (behavior validated manually through use). The only code change allowed is fixing bugs discovered by the new tests.

## Functional Requirements

### FR-1: Fix Type Hint Bug in `_format_elapsed()`

- **Line 35:** Parameter type hint is `"datetime"` (string forward reference) but `datetime` is not imported at module level
- **Line 36:** Local import `from datetime import datetime as _dt` exists but `_dt` is never used in the function body
- **Fix options (pick one, be consistent):**
  - Option A: Add `import datetime` at top-level, use `datetime.datetime` in type hint, remove `_dt` alias
  - Option B: Import `datetime` at top-level (`from datetime import datetime`), remove local import, use `datetime` directly
- **Recommended:** Option B — cleaner, matches conventions in other files (`state.py` already does `from datetime import datetime, timezone`)

### FR-2: Unit Tests for `_format_elapsed()`

- **File:** New test file `tests/test_main.py`
- **Test cases:**
  - `hours=0, minutes=5, seconds=30` → `"05:30"`
  - `hours=2, minutes=15, seconds=45` → `"02:15:45"`
  - `hours=0, minutes=0, seconds=0` → `"00:00"`
  - `hours=10, minutes=0, seconds=0` → `"10:00:00"`

### FR-3: Unit Tests for `_prompt_save_slot_selection()`

- **File:** `tests/test_main.py`
- **Fixture:** Use `tmp_path` for saves directory, mock `Renderer`, inject `input_fn`
- **Test cases:**
  - (a) No saves exist → returns `("new", None)`
  - (b) 1+ saves exist, user picks valid number → loads and returns `("continue", GameState)`
  - (c) User types `"b"` / `"baru"` / `"new"` → returns `("new", None)`
  - (d) User types number out of range → loops, asks again
  - (e) Save file is corrupted → catches `SaveLoadError`, loops, asks again

### FR-4: Unit Tests for `_resolve_chapter_sequence()`

- **File:** `tests/test_main.py`
- **Test cases:**
  - Normal manifest with chapters → returns chapter ID list
  - Empty manifest (fallback path) → loads all YAML files in `content/chapters/`
  - Empty chapters directory → calls `sys.exit(1)`

### FR-5: Unit Tests for `_find_chapter_path_by_id()`

- **File:** `tests/test_main.py`
- **Test cases:**
  - Chapter found by convention path (`{id}.yaml`)
  - Chapter found by fallback scan
  - Chapter not found → calls `sys.exit(1)`

### FR-6: Integration Tests for `run()`

- **File:** `tests/test_main.py`
- **Method:** Create minimal chapter YAML files in `tmp_path`, mock `input_fn` with scripted choices
- **Test cases:**
  - Single chapter, linear flow → reaches ending, save file written, `completed=True`
  - Two chapters with branching → correct ending based on choices
  - Verify `endings_achieved` is populated correctly

## Non-Functional Requirements

- All tests must use `tmp_path` fixture for isolation (no test pollution)
- Tests must NOT modify `content/chapters/*.yaml` (use synthetic test chapters)
- Tests must use `input_fn` parameter for input injection (never mock `builtins.input`)
- Full test suite must pass after changes
- Coverage `main.py` must reach ≥ 80%

## Acceptance Criteria

- [ ] `main.py` coverage: 0% → ≥ 80%
- [ ] Type hint bug in `_format_elapsed()` fixed
- [ ] Unit tests for all 4 private functions
- [ ] Integration tests for `run()` (minimum 2 end-to-end scenarios)
- [ ] All existing 304 tests pass with zero regressions
- [ ] No changes to existing production logic except the type hint fix
- [ ] All test behavior matches current production behavior (tests document what IS, not what SHOULD BE)

## Out of Scope

- Changing game logic or ending conditions
- Refactoring `main.py` functions to be more testable (they're already testable via `input_fn`)
- Testing `argparse` argument parsing (covered implicitly by `run()` tests)
- Testing frozen/bundle paths (lines 19-24, branch for PyInstaller)
