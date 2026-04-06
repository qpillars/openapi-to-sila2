# Contributing to openapi-to-sila2

## Development Setup

```bash
git clone https://github.com/qpillars/openapi-to-sila2.git
cd openapi-to-sila2
just install
```

Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

## Commands

```bash
just test      # Run tests
just lint      # Check formatting, linting, and types
just format    # Auto-format code
just build     # Build distribution
```

## Submitting Changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `just lint` and `just test` - both must pass
4. Open a pull request with a clear description

## Code Style

- Formatted with [ruff](https://docs.astral.sh/ruff/) (line length 120)
- Lint rules: E, F, I, UP, W
- Type hints on all public functions
- Type checking with [ty](https://github.com/astral-sh/ty)
- Tests for new functionality (pytest)

## Project Structure

```
src/openapi_to_sila2/     # Library code (published to PyPI)
tests/                     # Tests and fixtures
examples/                  # Working proxy server/client demos
docs/                      # Additional documentation
```

## Questions

Open an issue on [GitHub](https://github.com/qpillars/openapi-to-sila2/issues).
