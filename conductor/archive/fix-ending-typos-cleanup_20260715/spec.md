# Specification: Fix Ending Typos & Dead Code Cleanup

## Overview

Two low-risk issues in `src/muara/engine/` need to be resolved:
1. A typo in the `dipercaya` ending text header
2. A dead code file (`renderer.py`) that has zero callers

## Functional Requirements

### FR-1: Fix Ending Typo

- **File:** `src/muara/engine/ending.py`
- **Line 31:** Current text `"— TAMAT: DIPERCAI —"` is missing the second 'A'
- **Fix:** Change to `"— TAMAT: DIPERCAIA —"` to match the key `"dipercaya"`
- **No other ending texts should change**

### FR-2: Remove Dead Code `renderer.py`

- **File:** `src/muara/engine/renderer.py`
- **Status:** 21 statements, 0% test coverage, zero callers confirmed via `grep`
- **Action:** Delete the file entirely
- **Verify:** No broken imports anywhere in the codebase

### FR-3: Add Ending Text Validation Tests

- **Location:** New file `tests/test_ending_texts.py`
- **Tests required:**
  - For every key in `ENDING_TEXTS`, assert the uppercase version of the key appears in the header text
  - Assert no ending has empty text
  - Assert all 6 expected keys exist: `pembebasan`, `kehancuran`, `dipercaya`, `dicurigai`, `terlupakan`, `sekutu`
  - Assert the total number of ending keys is exactly 6

## Non-Functional Requirements

- No changes to `content/chapters/*.yaml`
- No changes to `SaveState` schema
- No changes to `Renderer` protocol
- Full test suite must pass after changes

## Acceptance Criteria

- [ ] Typo "DIPERCAI" → "DIPERCAIA" fixed in `ending.py:31`
- [ ] `renderer.py` deleted, no broken imports
- [ ] New test file validates all 6 ending text headers
- [ ] Full suite passes: `uv run pytest tests/ -q`
- [ ] No changes to any other file except `ending.py` and deletion of `renderer.py`

## Out of Scope

- Modifying ending logic (`determine_ending()`)
- Adding new endings
- Refactoring `ENDING_TEXTS` structure
