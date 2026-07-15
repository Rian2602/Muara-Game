# Implementation Plan: Write Tests for `main.py`

## Phase 1: Fix Bug & Unit Tests

- [x] Task: Fix type hint bug in `_format_elapsed()`
    - [x] Read current implementation at `main.py:35-43`
    - [x] Add `from datetime import datetime` at top-level import section
    - [x] Change parameter type hint from `"datetime"` to `datetime`
    - [x] Remove unused local import `from datetime import datetime as _dt` (line 36)
    - [x] Verify `ruff check src/muara/main.py` — no new errors

- [x] Task: Write unit tests for `_format_elapsed()`
    - [x] Create `tests/test_main.py`
    - [x] Test hours=0 case → `"MM:SS"` format
    - [x] Test hours>0 case → `"HH:MM:SS"` format
    - [x] Test zero duration → `"00:00"`
    - [x] Test large duration → correct HH:MM:SS

- [x] Task: Write unit tests for `_prompt_save_slot_selection()`
    - [x] Create helper to write fake save files in `tmp_path`
    - [x] Test case (a): no saves → `("new", None)`
    - [x] Test case (b): valid selection → `("continue", GameState)`
    - [x] Test case (c): user types "b" → `("new", None)`
    - [x] Test case (d): out-of-range input → loops
    - [x] Test case (e): corrupted save → catches error, loops

- [x] Task: Write unit tests for `_resolve_chapter_sequence()`
    - [x] Test normal manifest → returns list of IDs
    - [x] Test empty manifest fallback → scans directory
    - [x] Test empty directory → calls `sys.exit(1)` (use `pytest.raises(SystemExit)`)

- [x] Task: Write unit tests for `_find_chapter_path_by_id()`
    - [x] Test convention path found
    - [x] Test fallback scan found
    - [x] Test not found → calls `sys.exit(1)`

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Integration Tests

- [x] Task: Create minimal test chapter fixtures
    - [x] Write 2-3 simple YAML chapter files in `tmp_path` with linear flow
    - [x] Include one chapter with a choice for branching test
    - [x] Include `manifest.yaml` pointing to test chapters

- [x] Task: Write end-to-end tests for `run()`
    - [x] Test linear flow: single chapter → ending → save file written
    - [x] Test branching flow: choice affects which ending is reached
    - [x] Assert: `save_state.completed == True`, `endings_achieved` populated, file exists on disk

- [x] Task: Verify coverage target
    - [x] Run `uv run python -m pytest tests/test_main.py -v --cov=src/muara/main --cov-report=term-missing`
    - [x] Confirm ≥ 80% coverage on `main.py`
    - [x] Document any intentionally uncovered lines (e.g., `sys.exit()` branches, frozen app paths)

- [x] Task: Run full regression suite
    - [x] `uv run pytest tests/ -q` — all tests pass
    - [x] Document final test count (should be 304 + N new tests)

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
