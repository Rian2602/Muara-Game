# Product Definition

## Initial Concept

Muara is a CLI narrative game set in colonial-era Batavia (1899). The player takes on the role of Rasmi, a buruh pribumi (indigenous laborer) who keeps a private ledger of wages. The game explores themes of labor, identity, and resistance through interactive fiction with branching storylines driven by player choices.

The game is designed to be played via command-line interface, with text rendered using the Rich library for enhanced formatting. Content is authored as YAML chapter files, validated by Pydantic models, and executed through an engine that manages state, saves, and conditional text rendering based on player choices.

## Target Audience

**Primary:** Interactive fiction fans who enjoy narrative-heavy, choice-driven games. Players who appreciate rich prose, atmospheric world-building, and meaningful consequences for their decisions. Comparable experiences include Bandersnatch, 80 Days, and Choice of Games titles.

**Secondary:** Developers and writers interested in AI-assisted content creation tools, and people curious about Indonesian colonial history.

## Core Experience

**Balanced** — equal emphasis on story depth and mechanical depth. The game delivers:
- **Literary quality:** First-person present-tense reflective prose with sensory detail, short emphatic sentences, and precise administrative details contrasted with intangible emotions.
- **Meaningful choices:** Player decisions create real consequences that branch the narrative, affect available options in later chapters, and lead to multiple distinct endings.
- **Score/ending tracking:** Multiple endings determined by cumulative flag state, with an endings-achieved tracker for replay motivation.

## Content Scope

**Long-form (episodic):** 15+ chapters across multiple story arcs. The game is structured for multi-session play with save/load functionality. Chapters are organized into narrative phases:
- **Opening** — Introduction to Rasmi, the warehouse, and the initial anomaly.
- **Rising Action** — Branching paths based on player choices (report, conceal, investigate).
- **Climax** — Confrontation sequences with multiple outcomes based on accumulated evidence and trust.
- **Resolution** — Multiple endings determined by cumulative flag state (dipercaya, dicurigai, terlupakan, sekutu).

## Distribution

**Standalone binary** — distributed as a self-contained executable via PyInstaller or similar tooling. No Python installation required for end users. Development and testing use `uv run muara`.

## Design Principles

1. **Narrative-first:** Every engine decision serves the story. No mechanical systems that don't enhance narrative delivery.
2. **Branching with convergence:** Meaningful branches that feel distinct but converge at key narrative beats to maintain scope.
3. **Sensory before emotional:** Prose always leads with physical sensation (temperature, texture, sound) before emotional interpretation.
4. **No exposition dumps:** World details emerge through passing mention, never blocks of explanation.
5. **Cultural authenticity:** Indonesian language and cultural details woven naturally into English prose.

## Success Criteria

- Players can complete a full playthrough in 2-4 hours per path.
- At least 4 distinct endings with different narrative outcomes.
- All 138+ tests pass (content integrity, engine playthrough, model validation).
- Standalone binary runs on Linux, macOS, and Windows without dependencies.
