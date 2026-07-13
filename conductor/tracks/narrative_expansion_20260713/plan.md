# Implementation Plan: Narrative Expansion

## Phase 1: Planning and Design

- [ ] Task: Analyze existing chapter structure and flag system
    - [ ] Review all 11 existing chapters for branch points
    - [ ] Document current flag usage and dependencies
    - [ ] Identify gaps in narrative progression
- [ ] Task: Design new chapter outlines
    - [ ] Create 4-5 chapter summaries with key scenes
    - [ ] Define major branch points and consequences
    - [ ] Map new flags and their effects
- [ ] Task: Design new endings
    - [ ] Define 1-2 new ending scenarios
    - [ ] Map flag combinations to each ending
    - [ ] Ensure all endings are reachable
- [ ] Task: Conductor - User Manual Verification 'Planning' (Protocol in workflow.md)

## Phase 2: Test Infrastructure

- [ ] Task: Write tests for new chapter validation
    - [ ] Test chapter ID naming conventions
    - [ ] Test scene ID uniqueness
    - [ ] Test choice option references
- [ ] Task: Write tests for new flag system
    - [ ] Test new flag types (if any)
    - [ ] Test flag evaluation with new combinations
    - [ ] Test flag persistence across chapters
- [ ] Task: Write playthrough tests for new branches
    - [ ] Test happy path through new chapters
    - [ ] Test failure state branch
    - [ ] Test all new endings
- [ ] Task: Conductor - User Manual Verification 'Test Infrastructure' (Protocol in workflow.md)

## Phase 3: Content Creation

- [ ] Task: Create chapter 07 (first new chapter)
    - [ ] Write YAML content with scenes and choices
    - [ ] Ensure all scenes have unique IDs
    - [ ] Add appropriate flags and text variants
    - [ ] Verify content passes validation tests
- [ ] Task: Create chapter 08 (branching chapter)
    - [ ] Write YAML content with major branch point
    - [ ] Implement failure state branch
    - [ ] Add text variants based on flag conditions
    - [ ] Verify content passes validation tests
- [ ] Task: Create chapter 09 (consequence chapter)
    - [ ] Write YAML content showing consequences of previous choices
    - [ ] Add conditional text based on accumulated flags
    - [ ] Set up for final chapters
    - [ ] Verify content passes validation tests
- [ ] Task: Create chapter 10 (climax chapter)
    - [ ] Write YAML content for climactic confrontation
    - [ ] Implement multiple paths based on flag state
    - [ ] Add emotional intensity through prose
    - [ ] Verify content passes validation tests
- [ ] Task: Create chapter 11 (resolution chapter)
    - [ ] Write YAML content leading to endings
    - [ ] Implement ending determination logic
    - [ ] Add closure for character arcs
    - [ ] Verify content passes validation tests
- [ ] Task: Conductor - User Manual Verification 'Content Creation' (Protocol in workflow.md)

## Phase 4: Integration and Testing

- [ ] Task: Update manifest.yaml
    - [ ] Add new chapter IDs in correct sequence
    - [ ] Verify chapter order makes narrative sense
    - [ ] Test manifest loading
- [ ] Task: Run full test suite
    - [ ] Execute all 138+ tests
    - [ ] Verify no regressions
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
