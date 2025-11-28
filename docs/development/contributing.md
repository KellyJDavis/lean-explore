# Contributing

Thank you for your interest in contributing to Lean Explore!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install in development mode:

```bash
pip install -e ".[dev]"
```

4. Run tests:

```bash
make test
```

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- (Optional) Local Lean 4 installation for extractor scripts

### Installation

```bash
# Clone repository
git clone https://github.com/KellyJDavis/lean-explore.git
cd lean-explore

# Install in development mode
pip install -e ".[dev]"

# Run tests
make test
```

## Code Style

We use:
- **Ruff** for linting and formatting
- **Google-style** docstrings
- **Type hints** for all functions

### Formatting

```bash
# Format code
ruff format .

# Check linting
ruff check .
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/lean_explore/api/test_client.py
```

## Documentation

Documentation is built with MkDocs:

```bash
# Install docs dependencies
pip install mkdocs-material mkdocstrings[python]

# Serve locally
mkdocs serve

# Build
mkdocs build
```

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## Code of Conduct

Be respectful and inclusive in all interactions.

## Questions?

Open an issue or start a discussion on GitHub.

