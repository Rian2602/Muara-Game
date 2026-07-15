# Specification: Deduplicate `_execute_hooks()`

## Overview

The `_execute_hooks()` method is copy-pasted identically between two files:
- `src/muara/engine/chapter_runner.py` (lines 87-142)
- `src/muara/gui/app.py` (lines 98-140)

This duplication creates a maintenance risk: any future hook format change must be applied to both files, and divergence would go undetected by tests.

## Functional Requirements

### FR-1: Extract Shared Logic to `GameState`

- **Target:** New method `GameState.execute_hooks()` in `src/muara/engine/state.py`
- **Signature:** `def execute_hooks(self, hooks: list[str]) -> None`
- **Responsibility:** Parse and execute all hook formats (flag assignment, increment, add_to_set, advance_clock, change_rep)
- **Explicit type annotation:** `value: bool | int | str` at first assignment to fix mypy false-positives

### FR-2: Standardize Error Handling

The GUI version silently swallows errors that the CLI version raises:
- `advance_clock()` with invalid argument: CLI raises `ChapterRunError`, GUI silently ignores
- `change_rep()` with non-numeric amount: CLI raises `ChapterRunError`, GUI silently passes

**Decision:** The shared implementation should match the CLI behavior (raise errors), because silent failures hide bugs. The GUI caller should catch and handle errors appropriately.

### FR-3: Update Callers

- `chapter_runner.py`: Replace `_execute_hooks(hooks)` calls with `self.state.execute_hooks(hooks)`
- `gui/app.py`: Replace `_execute_hooks(hooks)` calls with `self.state.execute_hooks(hooks)`
- Preserve any wrapper methods if they exist for backward compatibility (check with grep first)

### FR-4: Add Parity Regression Test

- **Location:** `tests/test_new_features.py` or new file
- **Purpose:** Verify that hook execution produces identical `state.flags` regardless of which code path invokes it
- **Method:** Create identical `GameState`, run same hook strings through `ChapterRunner._execute_hooks` and `GameScreen._execute_hooks` (or both through the new shared method), assert flags match

## Non-Functional Requirements

- mypy error count should decrease (from baseline ~40, at least 4 fewer due to type annotation fix)
- No changes to hook format or semantics
- No changes to `content/chapters/*.yaml`
- Full test suite must pass

## Acceptance Criteria

- [ ] Only ONE implementation of hook parsing logic exists in the entire codebase (`grep -c "elif hook.startswith"` in `src/` returns 1 hit)
- [ ] `GameState.execute_hooks()` method exists in `state.py` with explicit type annotation
- [ ] CLI parity test passes
- [ ] All existing 304 tests pass with zero regressions
- [ ] mypy error count documented (before vs after)

## Out of Scope

- Adding new hook types
- Unifying `FlagCondition` (models) with `evaluate_condition()` (runtime) — separate architectural decision
- Changing the `Renderer` protocol
