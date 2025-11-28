# Installation

This guide will help you install Lean Explore and set up your environment.

## Requirements

- Python 3.10 or higher
- pip (Python package installer)

## Install from PyPI

The easiest way to install Lean Explore is using pip:

```bash
pip install lean-xplore
```

## Install from Source

If you want to install from the source code:

```bash
# Clone the repository
git clone https://github.com/KellyJDavis/lean-explore.git
cd lean-explore

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Verify Installation

After installation, verify that the CLI is available:

```bash
leanexplore --help
```

You should see the help output for the Lean Explore CLI.

## Optional: Local Backend Setup

If you want to use the local backend (instead of the remote API), you'll need to download the data:

```bash
# Fetch local data
leanexplore data fetch
```

This will download the necessary database, embeddings, and index files to enable local search.

## Next Steps

- [Quick Start Guide](quickstart.md) - Learn how to use Lean Explore
- [Configuration](configuration.md) - Configure API keys and settings

