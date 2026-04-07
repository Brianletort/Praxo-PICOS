# Contributing to Praxo-PICOS

Thanks for your interest in contributing. Here's how to get started.

## Setup

```bash
git clone https://github.com/praxo/picos.git
cd picos
make bootstrap
```

## Development Workflow

1. Create a branch from `main`
2. Make your changes (small, focused diffs preferred)
3. Add or update tests for any behavior changes
4. Run the test suite: `make test`
5. Run linting and type checks: `make lint && make typecheck`
6. Open a pull request with a clear description

## Code Standards

- **Python**: type hints on public functions, `ruff` for formatting, `mypy` for type checking
- **TypeScript**: strict mode, ESLint, Vitest for tests
- **Tests**: unit tests for pure logic, integration tests for IO boundaries, Playwright for E2E
- **Security**: never commit secrets, API keys, or real user data

## Architecture

See the [README](README.md) for architecture diagrams and repo layout. Key directories:

- `services/api/` — FastAPI backend
- `services/workers/` — data extractors and indexing
- `apps/web/` — Next.js dashboard
- `apps/desktop/` — Electron shell
- `tests/` — full test suite

## Pull Request Guidelines

- Reference any relevant issues
- Include "How tested" in your PR description
- Keep diffs small and reviewable
- Follow existing patterns in the codebase

## Questions?

Open an issue or start a discussion. We're happy to help.
