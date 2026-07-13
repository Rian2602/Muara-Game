# Implementation Plan: Narrative Expansion

## Phase 1: Planning and Design

- [x] Task: Analyze existing chapter structure and flag system
    - [x] Review all 11 existing chapters for branch points
    - [x] Document current flag usage and dependencies
    - [x] Identify gaps in narrative progression
- [x] Task: Design new chapter outlines
    - [x] Create 4-5 chapter summaries with key scenes
    - [x] Define major branch points and consequences
    - [x] Map new flags and their effects
- [x] Task: Design new endings
    - [x] Define 1-2 new ending scenarios
    - [x] Map flag combinations to each ending
    - [x] Ensure all endings are reachable
- [x] Task: Conductor - User Manual Verification 'Planning' (Protocol in workflow.md)

## Phase 2: Test Infrastructure

- [x] Task: Write tests for new chapter validation
    - [x] Test chapter ID naming conventions
    - [x] Test scene ID uniqueness
    - [x] Test choice option references
- [x] Task: Write tests for new flag system
    - [x] Test new flag types (if any)
    - [x] Test flag evaluation with new combinations
    - [x] Test flag persistence across chapters
- [x] Task: Write playthrough tests for new branches
    - [x] Test happy path through new chapters
    - [x] Test failure state branch
    - [x] Test all new endings
- [x] Task: Conductor - User Manual Verification 'Test Infrastructure' (Protocol in workflow.md)

## Phase 3: Content Creation

- [x] Task: Create chapter 07 (first new chapter)
    - [x] Write YAML content with scenes and choices
    - [x] Ensure all scenes have unique IDs
    - [x] Add appropriate flags and text variants
    - [x] Verify content passes validation tests
- [x] Task: Create chapter 08 (branching chapter)
    - [x] Write YAML content with major branch point
    - [x] Implement failure state branch
    - [x] Add text variants based on flag conditions
    - [x] Verify content passes validation tests
- [x] Task: Create chapter 09 (consequence chapter)
    - [x] Write YAML content showing consequences of previous choices
    - [x] Add conditional text based on accumulated flags
    - [x] Set up for final chapters
    - [x] Verify content passes validation tests
- [x] Task: Create chapter 10 (climax chapter)
    - [x] Write YAML content for climactic confrontation
    - [x] Implement multiple paths based on flag state
    - [x] Add emotional intensity through prose
    - [x] Verify content passes validation tests
- [x] Task: Create chapter 11 (resolution chapter)
    - [x] Write YAML content leading to endings
    - [x] Implement ending determination logic
    - [x] Add closure for character arcs
    - [x] Verify content passes validation tests
- [x] Task: Conductor - User Manual Verification 'Content Creation' (Protocol in workflow.md)

## Phase 4: Integration and Testing

- [x] Task: Update manifest.yaml
    - [x] Add new chapter IDs in correct sequence
    - [x] Verify chapter order makes narrative sense
    - [x] Test manifest loading
- [x] Task: Run full test suite
    - [x] Execute all 190 tests
    - [x] Verify no regressions
    - [ ] Check code coverage ≥ 80%
- [ ] Task: Manual playthrough testing
    - [ ] Play through all new branches
    - [ ] Verify flag state consistency
    - [ ] Check save/load functionality
    - [ ] Test ending determination
- [ ] Task: Conductor - User Manual Verification 'Integration' (Protocol in workflow.md)

## Phase 5: Documentation and Cleanup

- [ ] Task: Update documentation
    - [ ] Update AGENTS.md with new chapter conventions
    - [ ] Document new flag types and their effects
    - [ ] Update project structure documentation
- [ ] Task: Code review
    - [ ] Self-review all changes
    - [ ] Check for security issues
    - [ ] Verify code style compliance
- [ ] Task: Final commit
    - [ ] Stage all changes
    - [ ] Write descriptive commit message
    - [ ] Include test results
- [ ] Task: Conductor - User Manual Verification 'Documentation' (Protocol in workflow.md)

## Success Metrics

- [ ] All existing tests pass
- [ ] New content passes validation tests
- [ ] All new chapters are playable
- [ ] All new endings are reachable
- [ ] Code coverage ≥ 80%
- [ ] No dead-end branches
- [ ] Prose follows World Bible §6 style
- [ ] Content is primarily in Bahasa Indonesia
