# Product Guidelines

## Prose Style

遵循 World Bible §6 specifications:
- **POV:** Orang pertama (first-person), present-tense reflektif
- **Sensory first:** Always lead with physical sensation (suhu, tekstur, bau, bunyi) before emotional interpretation
- **Sentence structure:** Short repetitive sentences for emphasis
- **Detail contrast:** Precise administrative details contrasted with intangible emotions
- **No exposition dumps:** World details emerge through passing mention only

## Language

**Primarily Indonesian** — all narrative prose, chapter titles, and scene text in Bahasa Indonesia. English used only for:
- Technical identifiers (chapter IDs, flag keys)
- UI prompts where clarity requires it

Indonesian loanwords and cultural terms woven naturally into prose without italicization or footnotes.

## CLI Visual Aesthetic

**Rich/formatted** using the Rich library:
- Colored chapter headers with location, date, time
- Panel-formatted narrative text for readability
- Decorative separators between scenes
- Clean, readable typography optimized for terminal display

## UX Principles

1. **Aggressive auto-save:** Autosave after every chapter completion. Manual save available at any point via menu. No progress loss on unexpected exit.
2. **Narrative immersion:** UI elements serve the story, never break immersion. No stat displays, score counters, or mechanical indicators visible during play.
3. **Pacing control:** Player advances text with Enter/Return. No timed sequences. Player controls reading speed entirely.
4. **Clear choices:** Menu options clearly labeled with consequences hinted but not revealed. No hidden or ambiguous choices.
5. **Save metadata:** Save slots show chapter title, elapsed time, and play date for easy identification.

## Content Standards

1. **Cultural authenticity:** Indonesian names, places, and cultural concepts used accurately and respectfully.
2. **Historical groundedness:** Colonial-era Batavia details drawn from documented history, not fantasy.
3. **Emotional depth:** Every scene must evoke at least one specific emotional response from the player.
4. **Branching integrity:** Every choice must lead to meaningfully different outcomes — no false choices.
5. **Canon compliance:** Follow AGENTS.md and World Bible constraints for all content creation.

## Quality Gates

- All content passes `test_content_integrity.py` validation
- All prose follows World Bible §6 style
- All 138+ tests pass before any commit
- No broken scene references or unreachable paths
