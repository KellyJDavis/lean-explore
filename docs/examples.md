# Examples

Collection of example code demonstrating Lean Explore usage.

## Basic Search

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    client = Client(api_key="your-api-key")
    results = await client.search("natural numbers")
    
    for item in results.items[:5]:
        print(f"{item.primary_declaration.lean_name}")
        print(f"  {item.informal_name}")
        print()

asyncio.run(main())
```

## Search with Filters

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    client = Client(api_key="your-api-key")
    
    results = await client.search(
        "monoid",
        package_filters=["Mathlib", "Batteries"]
    )
    
    print(f"Found {len(results.items)} results in Mathlib and Batteries")
    for item in results.items:
        print(f"- {item.primary_declaration.lean_name}")

asyncio.run(main())
```

## Multiple Queries

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    client = Client(api_key="your-api-key")
    
    queries = [
        "natural numbers",
        "group theory",
        "topology"
    ]
    
    results = await client.search(queries)
    
    for result in results:
        print(f"\nQuery: {result.query}")
        print(f"Results: {len(result.items)}")
        for item in result.items[:3]:
            print(f"  - {item.primary_declaration.lean_name}")

asyncio.run(main())
```

## Get Citations

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    client = Client(api_key="your-api-key")
    
    # Search first
    search_results = await client.search("Nat")
    if search_results.items:
        first_result = search_results.items[0]
        
        # Get citations
        citations = await client.get_citations(first_result.id)
        
        print(f"Citations for {first_result.primary_declaration.lean_name}:")
        for citation in citations.citations:
            print(f"  - {citation.lean_name}")

asyncio.run(main())
```

## Local Backend

```python
import asyncio
from lean_explore.local.service import Service

async def main():
    # Initialize local service
    service = Service()
    
    # Search
    results = await service.search("natural numbers")
    
    print(f"Found {len(results.items)} results")
    for item in results.items[:5]:
        print(f"- {item.primary_declaration.lean_name}")

asyncio.run(main())
```

## HTTP Server Client

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    # Connect to local server
    client = Client(base_url="http://localhost:8000")
    
    # Use as normal
    results = await client.search("natural numbers")
    
    for item in results.items:
        print(item.primary_declaration.lean_name)

asyncio.run(main())
```

## Error Handling

```python
import asyncio
import httpx
from lean_explore.api.client import Client

async def main():
    client = Client(api_key="your-api-key")
    
    try:
        results = await client.search("natural numbers")
        print(f"Found {len(results.items)} results")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(main())
```

## Custom Configuration

```python
import asyncio
from lean_explore.api.client import Client

async def main():
    client = Client(
        api_key="your-api-key",
        base_url="https://custom-api.example.com/api/v1",
        timeout=30.0
    )
    
    results = await client.search("natural numbers")
    print(f"Found {len(results.items)} results")

asyncio.run(main())
```

