# Specification: Narrative Expansion

## Overview

This track expands the Muara game's narrative by adding 4-5 new chapters that deepen player choice consequences, create more meaningful branching paths, and introduce additional story arcs while maintaining the existing quality standards.

## Background

The current game has 11 chapters with branching structure, but playtesting revealed:
- Choices lack real consequences — branches converge too quickly
- Player never feels failure or meaningful loss
- Protagonist is too passive — decisions don't feel impactful
- Conflict doesn't escalate through the narrative
- Ending feels abrupt and unsatisfying

## Functional Requirements

### 1. New Chapter Content
- Add 4-5 new chapters to the existing 11-chapter structure
- Each chapter must have 3-6 scenes with meaningful choices
- All chapters must follow World Bible §6 prose style
- All content must be in Bahasa Indonesia

### 2. Branching Path Enhancement
- Create at least 3 distinct narrative branches that remain meaningfully different for 2+ chapters
- Introduce at least 1 "failure state" branch where the player experiences negative consequences
- Ensure no branch is a dead end — all paths must lead to a valid ending

### 3. Choice Consequence System
- Each major choice must set flags that affect text in subsequent chapters
- Use existing text_variants system for conditional text
- Ensure flag state is properly saved and loaded
- Create at least 2 new flag types (beyond existing 12)

### 4. Ending Expansion
- Add 1-2 new endings based on new flag combinations
- Ensure all new endings are reachable from the new branches
- Maintain existing ending determination logic

## Non-Functional Requirements

### 1. Quality Gates
- All 138+ existing tests must continue to pass
- New content must pass test_content_integrity.py validation
- New chapters must be playable through test_engine.py playthrough helpers
- Code coverage must remain ≥ 80%

### 2. Performance
- No performance degradation with additional content
- Flag evaluation must handle 1000+ flags efficiently
- Chapter loading must remain fast (<100ms per chapter)

### 3. Compatibility
- New content must work with existing save files
- Backward compatible with existing flag system
- No breaking changes to existing APIs

## Acceptance Criteria

### Content Criteria
- [ ] 4-5 new YAML chapter files created
- [ ] All new chapters follow naming convention (NN nama_singkat.yaml)
- [ ] Chapter IDs match filenames
- [ ] All scenes have unique IDs within their chapters
- [ ] All choice options reference valid scene IDs
- [ ] Prose follows World Bible §6 style
- [ ] Content is primarily in Bahasa Indonesia

### Technical Criteria
- [ ] All existing tests pass (uv run pytest tests/ -v)
- [ ] New content passes test_content_integrity.py
- [ ] New chapters are playable via test_engine.py
- [ ] Code coverage ≥ 80%
- [ ] No hardcoded secrets or credentials
- [ ] All public APIs documented

### Narrative Criteria
- [ ] At least 3 distinct narrative branches
- [ ] At least 1 failure state branch
- [ ] Each major choice affects subsequent text
- [ ] At least 2 new flag types introduced
- [ ] 1-2 new endings added
- [ ] All new endings reachable from new branches
- [ ] No dead-end branches

## Out of Scope

- Engine architecture changes
- UI/UX modifications
- Distribution/packaging changes
- Performance optimization beyond maintaining current levels
- New test infrastructure
- Documentation updates beyond API docs

## Dependencies

- Existing engine (chapter_loader, chapter_runner, renderer, state, save_manager)
- Existing models (Chapter, Scene, Choice, TextVariant, SaveState)
- Existing content (01-06 chapters with branching structure)
- World Bible and Character Plot Brief documentation

## Risks

1. **Scope creep** — 4-5 chapters may expand beyond estimates
   - Mitigation: Strict adherence to spec, regular check-ins

2. **Flag complexity** — New flags may create unexpected interactions
   - Mitigation: Comprehensive flag documentation, integration testing

3. **Content quality** — New prose may not match existing quality
   - Mitigation: Style guide adherence, review process

4. **Test coverage** — New content may require additional tests
   - Mitigation: TDD approach, coverage monitoring
