# Implementation Plan: Fix Ending Typos & Dead Code Cleanup

## Phase 1: Fix Ending Typo

- [ ] Task: Write failing test for ending text validation
    - [ ] Create `tests/test_ending_texts.py`
    - [ ] Test all 6 ENDING_TEXTS keys exist with correct count
    - [ ] Test each key's uppercase version appears in its header text
    - [ ] Test no ending text is empty
    - [ ] Run test → confirm FAIL on "DIPERCAI" assertion

- [ ] Task: Fix typo in `ending.py:31`
    - [ ] Change `"— TAMAT: DIPERCAI —"` to `"— TAMAT: DIPERCAIA —"`
    - [ ] Run new test → confirm PASS
    - [ ] Run full suite → confirm 0 regressions

- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Dead Code Removal

- [ ] Task: Confirm no callers for `renderer.py`
    - [ ] Run `grep -rn "from muara.engine.renderer import\|engine\.renderer\." src/ tests/`
    - [ ] Confirm zero results outside the file itself

- [ ] Task: Check documentation references
    - [ ] Search README.md for `renderer.py` mentions
    - [ ] Search AGENTS.md for `renderer.py` mentions
    - [ ] Search pyproject.toml for entry point references
    - [ ] Update any documentation that references the file

- [ ] Task: Delete `src/muara/engine/renderer.py`
    - [ ] Delete the file
    - [ ] Run full suite → confirm same pass count
    - [ ] Run `python -c "import muara.main; import muara.gui.app; print('OK')"` → confirm clean imports

- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase: Review Fixes

- [x] Task: Apply review suggestions — removed unused `determine_ending` import from test_ending_texts.py
