## Description

<!-- Provide a brief description of the changes introduced by this PR -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🧪 Tests / Refactoring / Code quality

## Architectural & Quality Invariants

- [ ] My code strictly follows the **Hexagonal (Ports & Adapters)** boundaries.
- [ ] No un-scoped file write permissions or arbitrary subprocess bypasses.
- [ ] In-memory AST Guard checks have been preserved.
- [ ] All new and existing tests pass locally (`uv run pytest tests/ -v`).
- [ ] Code is formatted and linted cleanly (`uv run ruff check .`).
- [ ] Relevant documentation has been added or updated in `docs/`.

## How Has This Been Tested?

<!-- Describe the tests that you ran to verify your changes -->

## Related Issues

<!-- Closes #IssueNumber or Fixes #IssueNumber -->
