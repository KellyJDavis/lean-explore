# Quick Start

Get up and running with Lean Explore in minutes.

## Using the CLI

### Basic Search

Search for Lean declarations using natural language:

```bash
leanexplore search "natural numbers"
```

### Configure API Key

To use the remote API, you'll need an API key:

```bash
leanexplore configure api-key YOUR_API_KEY
```

### Search with Package Filters

Filter results to specific packages:

```bash
leanexplore search "monoid" --pkg Mathlib --pkg Batteries
```

## Using Python API

### Basic Example

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    # Initialize client with API key
    client = Client(api_key="your-api-key")
    
    # Perform a search
    results = await client.search("natural numbers")
    
    # Print results
    for item in results.items[:5]:  # Top 5 results
        print(f"{item.primary_declaration.lean_name}: {item.informal_name}")

asyncio.run(main())
```

### Search Multiple Queries

```python
async def main():
    client = Client(api_key="your-api-key")
    
    # Search multiple queries at once
    results = await client.search([
        "natural numbers",
        "group theory",
        "topology"
    ])
    
    for result in results:
        print(f"Query: {result.query}")
        print(f"Found {len(result.items)} results\n")

asyncio.run(main())
```

## Using Local Backend

### Start Local HTTP Server

```bash
# First, fetch local data
leanexplore data fetch

# Start the server
leanexplore http start --backend local
```

The server will be available at `http://localhost:8000`.

### Query the Local Server

```bash
curl "http://localhost:8000/api/v1/search?q=natural+numbers"
```

Or use the Python client with a custom base URL:

```python
client = Client(base_url="http://localhost:8000")
results = await client.search("natural numbers")
```

## Using MCP Server

The MCP (Model Context Protocol) server allows AI agents to interact with Lean Explore:

```bash
leanexplore mcp start --backend api --api-key YOUR_API_KEY
```

## Next Steps

- [CLI Usage](../user-guide/cli.md) - Detailed CLI documentation
- [API Client](../user-guide/api-client.md) - Python API guide
- [Configuration](configuration.md) - Advanced configuration options

