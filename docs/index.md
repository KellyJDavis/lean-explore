# Lean Explore

**A search engine for Lean 4 declarations**

Lean Explore is a powerful search engine designed to help you discover and explore declarations in the Lean 4 ecosystem. It provides semantic search capabilities across multiple Lean projects including Mathlib, Batteries, Std, and more.

## Features

- 🔍 **Semantic Search**: Find Lean declarations using natural language queries
- 📚 **Multi-Project Support**: Search across Mathlib, Batteries, Std, PhysLean, Init, and Lean
- 🚀 **Multiple Interfaces**: Use via CLI, Python API, HTTP server, or MCP server
- 🏠 **Local Backend**: Run searches locally with your own data
- 🔗 **Dependency Tracking**: Explore relationships between declarations
- 📊 **Ranked Results**: Results are ranked using semantic similarity, PageRank, and lexical matching

## Quick Links

- [Installation](getting-started/installation.md) - Get started with Lean Explore
- [Quick Start Guide](getting-started/quickstart.md) - Learn the basics in minutes
- [CLI Usage](user-guide/cli.md) - Command-line interface documentation
- [API Reference](api-reference/api-client.md) - Python API documentation

## Current Indexed Projects

The following Lean projects are currently indexed:

- **Batteries** - Extended standard library for Lean 4
- **Lean** - Core Lean 4 library
- **Init** - Initialization and basic types
- **Mathlib** - Mathematics library for Lean 4
- **PhysLean** - Physics library for Lean 4
- **Std** - Standard library for Lean 4

## Installation

```bash
pip install lean-xplore
```

For more details, see the [Installation Guide](getting-started/installation.md).

## Basic Usage

### CLI

```bash
# Search for declarations
leanexplore search "natural numbers"

# Configure API key
leanexplore configure api-key YOUR_API_KEY

# Start local HTTP server
leanexplore http start --backend local
```

### Python API

```python
from lean_explore.api.client import Client

client = Client(api_key="your-api-key")
results = await client.search("natural numbers")
```

### HTTP Server

```bash
# Start server
leanexplore http start --backend local

# Query via HTTP
curl "http://localhost:8000/api/v1/search?q=natural+numbers"
```

## Documentation Structure

- **[Getting Started](getting-started/installation.md)**: Installation and setup
- **[User Guide](user-guide/cli.md)**: How to use different interfaces
- **[API Reference](api-reference/api-client.md)**: Complete API documentation
- **[Development](development/scripts.md)**: Contributing and development guides

## Citation

If you use Lean Explore in your research or work, please cite it:

```bibtex
@software{Asher_LeanExplore_2025,
  author = {Asher, Justin},
  title = {{LeanExplore: A search engine for Lean 4 declarations}},
  year = {2025},
  url = {http://www.leanexplore.com},
  note = {GitHub repository: https://github.com/justincasher/lean-explore}
}
```

## License

This project is distributed under the Apache License 2.0. See [LICENSE](https://github.com/KellyJDavis/lean-explore/blob/main/LICENSE) for details.

