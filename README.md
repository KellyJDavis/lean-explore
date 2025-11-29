<h1 align="center">
  LeanExplore
</h1>

<h3 align="center">
  A search engine for Lean 4 declarations
</h3>

<p align="center">
  <a href="https://pypi.org/project/lean-explore/">
    <img src="https://img.shields.io/pypi/v/lean-explore.svg" alt="PyPI version" />
  </a>
  <a href="https://github.com/justincasher/lean-explore/blob/main/LeanExplore.pdf">
    <img src="https://img.shields.io/badge/Paper-PDF-blue.svg" alt="Read the Paper" />
  </a>
  <a href="https://github.com/justincasher/lean-explore/commits/main">
    <img src="https://img.shields.io/github/last-commit/justincasher/lean-explore" alt="last update" />
  </a>
  <a href="https://github.com/justincasher/lean-explore/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/justincasher/lean-explore.svg" alt="license" />
  </a>
</p>

A search engine for Lean 4 declarations. This project provides tools and resources for exploring the Lean 4 ecosystem. Lean Explore enables semantic search across multiple Lean projects including Mathlib, Batteries, Std, PhysLean, Init, and Lean, helping you discover relevant theorems, definitions, and other declarations using natural language queries.

## Features

- 🔍 **Semantic Search**: Find Lean declarations using natural language queries
- 📚 **Multi-Project Support**: Search across Mathlib, Batteries, Std, PhysLean, Init, and Lean
- 🚀 **Multiple Interfaces**: Use via CLI, Python API, HTTP server, or MCP server
- 🏠 **Local Backend**: Run searches locally with your own data (no API key required)
- 🔗 **Dependency Tracking**: Explore relationships between declarations
- 📊 **Ranked Results**: Results are ranked using semantic similarity, PageRank, and lexical matching

## Installation

Install from PyPI:

```bash
pip install lean-xplore
```

### Requirements

- Python 3.10 or higher
- pip (Python package installer)

## Quick Start

### Getting an API Key

To use the remote API, you'll need an API key. API keys can be obtained from [https://www.leanexplore.com](https://www.leanexplore.com). Once you have your API key, configure it using:

```bash
leanexplore configure api-key --api-key YOUR_API_KEY
```

Alternatively, you can run `leanexplore configure api-key` without arguments and it will prompt you for the key, or use the local backend without an API key (see [Local Backend](#local-backend) below).

### Command Line

Search for Lean declarations:

```bash
# Basic search
leanexplore search "natural numbers"

# Search with package filters (limit results to specific packages)
leanexplore search "monoid" --package Mathlib --package Batteries

# Limit the number of results
leanexplore search "topology" --limit 5
```

The CLI will automatically use your configured API key. Note: The search command does not support a `--backend` flag. To use the local backend, you need to run a local HTTP server (see [Local Backend](#local-backend) below) and configure the client to use it.

### Python API

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    # Initialize client with API key
    client = Client(api_key="your-api-key")
    
    # Perform a search
    results = await client.search("natural numbers")
    
    # Display results
    print(f"Found {len(results.results)} results")
    for item in results.results[:5]:
        lean_name = item.primary_declaration.lean_name if item.primary_declaration else "N/A"
        print(f"{lean_name}")
        if item.informal_description:
            print(f"  {item.informal_description[:100]}...")

asyncio.run(main())
```

You can also search multiple queries at once:

```python
async def main():
    client = Client(api_key="your-api-key")
    
    # Search multiple queries
    results = await client.search([
        "natural numbers",
        "group theory",
        "topology"
    ])
    
    for result in results:
        print(f"\nQuery: {result.query}")
        print(f"Results: {len(result.results)}")

asyncio.run(main())
```

### Local Backend

Run searches locally without an API key. This is useful for offline access, faster queries, or when you want full control over the data.

```bash
# Download local data (database, embeddings, and search index)
leanexplore data fetch

# Start local HTTP server
leanexplore http serve --backend local
```

The server will be available at `http://localhost:8001/api/v1` (default port is 8001). You can query it via HTTP or use the Python client:

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    # Connect to local server
    client = Client(base_url="http://localhost:8001/api/v1")
    
    # Use as normal (no API key needed)
    results = await client.search("natural numbers")
    print(f"Found {len(results.results)} results")

asyncio.run(main())
```

### Additional Features

- **MCP Server**: Integrate with AI agents using the Model Context Protocol

  ```bash
  leanexplore mcp serve --backend api --api-key YOUR_API_KEY
  ```

- **HTTP Server**: Run your own API server

  ```bash
  leanexplore http serve --backend local
  ```

- **AI Chat**: Interact with an AI agent that can search Lean code

  ```bash
  leanexplore chat --backend api --lean-api-key YOUR_API_KEY
  ```

## Documentation

For detailed documentation, API reference, configuration options, and more examples, visit **[https://kellyjdavis.github.io/lean-explore](https://kellyjdavis.github.io/lean-explore)**.

The documentation includes:

- Complete installation and setup guides
- Detailed CLI usage and options
- Python API reference with examples
- HTTP server configuration
- MCP server integration
- Local backend setup and data management
- Development guides and contributing information

This code is distributed under an Apache License (see [LICENSE](LICENSE)).

### Cite

If you use LeanExplore in your research or work, please cite it as follows:

**General Citation:**

Justin Asher. (2025). *LeanExplore: A search engine for Lean 4 declarations*. LeanExplore.com. (GitHub: [https://github.com/justincasher/lean-explore](https://github.com/justincasher/lean-explore)).

**BibTeX Entry:**

```bibtex
@software{Asher_LeanExplore_2025,
  author = {Asher, Justin},
  title = {{LeanExplore: A search engine for Lean 4 declarations}},
  year = {2025},
  url = {http://www.leanexplore.com},
  note = {GitHub repository: https://github.com/justincasher/lean-explore}
}
```
