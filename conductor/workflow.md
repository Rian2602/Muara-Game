# Development Workflow

## Overview

This workflow defines the development process for the Muara project, ensuring consistent quality and maintainability.

## Development Cycle

### 1. Task Planning
- Break work into discrete, completable tasks
- Each task should be independently testable
- Estimate complexity (simple/moderate/complex)

### 2. Test-Driven Development
- **Write tests first** for all new functionality
- Tests should cover happy path, edge cases, and error conditions
- Minimum 80% code coverage for new code
- All tests must pass before proceeding

### 3. Implementation
- Write clean, focused code that passes all tests
- Follow code style guides (Python, Pydantic)
- Keep functions small and single-purpose
- Use meaningful variable names

### 4. Code Review
- Self-review before committing
- Check for security issues (no hardcoded secrets)
- Verify documentation is complete
- Ensure all tests still pass

### 5. Commit
- Commit after each completed task
- Use descriptive commit messages
- Include test results in commit message body
- Reference issue numbers when applicable

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**
```
feat(engine): Add text_variants support

- Implement TextVariant model for conditional text
- Add evaluate_condition() method to GameState
- Update chapter_runner to resolve text variants

Tests: 138 passed, 0 failed
```

## Quality Gates

### Before Any Commit
- [ ] All existing tests pass (`uv run pytest tests/ -v`)
- [ ] New tests added for new functionality
- [ ] Code follows style guides
- [ ] No hardcoded secrets or credentials

### Before Merging to Main
- [ ] All tests pass
- [ ] Code coverage ≥ 80%
- [ ] Documentation updated
- [ ] No TODO comments left in code

## Branch Strategy

- `main` — production-ready code
- `develop` — integration branch
- `feature/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation changes

## Testing Strategy

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution (< 1 second per test)

### Integration Tests
- Test module interactions
- Use real dependencies where possible
- Verify data flows correctly

### Playthrough Tests
- Test complete game paths
- Verify all scenes are reachable
- Check flag state consistency

## Documentation

- Update README.md for user-facing changes
- Update AGENTS.md for development process changes
- Keep docstrings current with code changes
- Document all public APIs

## Performance

- Profile before optimizing
- Benchmark critical paths
- Memory usage monitoring for large content files
- Cache expensive computations

## Security

- Never commit secrets or API keys
- Validate all external input
- Use parameterized queries (N/A for this project)
- Regular dependency updates
