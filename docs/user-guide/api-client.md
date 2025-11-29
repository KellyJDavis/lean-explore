# API Client

The Python API client provides programmatic access to Lean Explore search functionality.

## Basic Usage

### Initialization

```python
from lean_explore.api.client import Client

# With API key
client = Client(api_key="your-api-key")

# With custom base URL (for local servers)
client = Client(base_url="http://localhost:8001")

# Both API key and custom URL
client = Client(
    api_key="your-api-key",
    base_url="https://custom-api.example.com/api/v1"
)
```

### Single Search

```python
import asyncio

async def main():
    client = Client(api_key="your-api-key")
    results = await client.search("natural numbers")
    
    print(f"Found {len(results.results)} results")
    for item in results.results:
        print(f"- {item.primary_declaration.lean_name}")

asyncio.run(main())
```

### Multiple Searches

```python
async def main():
    client = Client(api_key="your-api-key")
    
    queries = ["natural numbers", "group theory", "topology"]
    results = await client.search(queries)
    
    for result in results:
        print(f"Query: {result.query}")
        print(f"Results: {len(result.results)}\n")

asyncio.run(main())
```

## Advanced Usage

### Package Filtering

```python
async def main():
    client = Client(api_key="your-api-key")
    
    # Filter by package
    results = await client.search(
        "monoid",
        package_filters=["Mathlib", "Batteries"]
    )
    
    for item in results.results:
        print(f"{item.primary_declaration.lean_name}")

asyncio.run(main())
```

### Getting Citations

```python
async def main():
    client = Client(api_key="your-api-key")
    
    # Search first
    search_results = await client.search("natural numbers")
    if search_results.results:
        first_result = search_results.results[0]
        
        # Get dependencies (citations) for a result
        dependencies = await client.get_dependencies(first_result.id)
        
        if dependencies:
            print(f"Dependencies for {first_result.primary_declaration.lean_name}:")
            for citation in dependencies.citations:
                print(f"- {citation.primary_declaration.lean_name}")

asyncio.run(main())
```

### Error Handling

```python
import httpx

async def main():
    client = Client(api_key="your-api-key")
    
    try:
        results = await client.search("natural numbers")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")

asyncio.run(main())
```

## Response Models

### APISearchResponse

```python
from lean_explore.shared.models.api import APISearchResponse

results: APISearchResponse = await client.search("query")

# Access properties
results.query  # The search query
results.results  # List of APISearchResultItem
```

### APISearchResultItem

```python
item = results.results[0]

# Primary declaration
item.primary_declaration.lean_name

# Informal description
item.informal_description

# Statement group ID
item.id

```

### APICitationsResponse

```python
dependencies = await client.get_dependencies(item_id)

# List of dependencies (citations)
if dependencies:
    for citation in dependencies.citations:
        print(citation.primary_declaration.lean_name)
```

## Configuration

### Timeout

```python
client = Client(
    api_key="your-api-key",
    timeout=30.0  # 30 second timeout
)
```

### Environment Variables

```python
import os
from lean_explore.api.client import Client

api_key = os.getenv("LEAN_EXPLORE_API_KEY")
base_url = os.getenv("LEAN_EXPLORE_BASE_URL")

client = Client(api_key=api_key, base_url=base_url)
```

## Next Steps

- [API Reference](../api-reference/api-client.md) - Complete API documentation
- [HTTP Server](http-server.md) - Run a local HTTP server
- [Local Search](local-search.md) - Use local backend

