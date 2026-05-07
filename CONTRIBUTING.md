# Contributing to agno-docs-mcp

Thanks for your interest in contributing! This document explains how to set up your environment and submit changes.

## Development Setup

```bash
git clone https://github.com/gonzalorrecalde/agno-docs-mcp.git
cd agno-docs-mcp
pip install -e ".[dev]"
```

## Quality Gates

All contributions must pass these checks before merge:

| Gate | Command | Target |
|------|---------|--------|
| Tests | `pytest` | 0 failures |
| Coverage | `pytest --cov=src/mcp_agno_docs --cov-fail-under=80` | ≥80% |
| Lint | `ruff check src/` | 0 violations |
| Type check | `mypy src/ --strict` | 0 errors |

## Pull Request Process

1. **Fork the repo** and create a feature branch from `main`.
2. **Write tests first** (TDD). The project enforces strict TDD — no production code without a preceding failing test.
3. **Keep files under 250 lines**. Split larger modules into smaller ones.
4. **Use Google-style docstrings** on all public functions and classes.
5. **Run all quality gates** before opening a PR.
6. **Update CHANGELOG.md** with your changes under `[Unreleased]`.

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add semantic search support
fix: resolve FTS5 tokenizer issue with hyphenated terms
test: add integration tests for navigation parser
docs: update README with Claude Desktop config
chore: upgrade pydantic to v2.14
```

## Architecture

The project follows **hexagonal architecture** with two abstract ports:

- **`DocSource`** — loads and parses documentation pages
- **`SearchEngine`** — indexes and searches content

Adding a new adapter (e.g., `RemoteDocSource`, `VectorSearchEngine`) requires implementing the port interface only — no changes to tool handlers or the server.

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
