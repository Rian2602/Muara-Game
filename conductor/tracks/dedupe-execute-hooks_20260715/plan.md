# Implementation Plan: Deduplicate `_execute_hooks()`

## Phase 1: Parity Verification

- [x] Task: Read both `_execute_hooks()` implementations side-by-side
    - [x] Compare `chapter_runner.py:87-142` with `gui/app.py:98-140`
    - [x] Document any differences (expected: GUI silently ignores some errors)

- [x] Task: Write parity regression test
    - [x] Create test that builds identical `GameState` with same initial flags
    - [x] Run same hook list through both old implementations (before refactoring)
    - [x] Assert `state.flags` is identical after execution
    - [x] Test should PASS currently (implementations are functionally equivalent for valid hooks)

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Extract to GameState

- [x] Task: Add `execute_hooks()` method to `GameState` in `state.py`
    - [x] Copy logic from `chapter_runner.py` (more complete error handling)
    - [x] Add explicit type annotation: `value: bool | int | str`
    - [x] Raise errors for invalid `advance_clock()` arguments
    - [x] Raise errors for invalid `change_rep()` amounts

- [x] Task: Update `chapter_runner.py` callers
    - [x] Replace `self._execute_hooks(hooks)` with `self.state.execute_hooks(hooks)`
    - [x] Remove the private `_execute_hooks()` method from `ChapterRunner`
    - [x] Verify no other callers exist with `grep -rn "_execute_hooks" src/ tests/`

- [x] Task: Update `gui/app.py` callers
    - [x] Replace `self._execute_hooks(hooks)` with `self.state.execute_hooks(hooks)`
    - [x] Remove the private `_execute_hooks()` method from `GameScreen`
    - [x] Verify no other callers exist

- [x] Task: Run full test suite
    - [x] `uv run pytest tests/ -q` — all tests pass
    - [x] Parity test still passes

- [x] Task: Run static analysis
    - [x] `mypy src/muara --ignore-missing-imports` — not installed, documented
    - [x] `ruff check src/` — not installed, documented

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase: Review

- [x] Task: Apply review suggestions 88f3432
