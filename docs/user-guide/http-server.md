# HTTP Server

Run a local HTTP server that provides the same API as the remote Lean Explore service.

## Starting the Server

### Using API Backend

```bash
leanexplore http serve --backend api --api-key YOUR_API_KEY
```

This starts a server that proxies requests to the remote API.

### Using Local Backend

```bash
# First, fetch local data
leanexplore data fetch

# Start server with local backend
leanexplore http serve --backend local
```

### Custom Configuration

```bash
# Custom host and port
leanexplore http serve --backend local --host 0.0.0.0 --port 8080
```

## API Endpoints

The server provides the same endpoints as the remote API:

### Search

```bash
GET /api/v1/search?q=QUERY&pkg=PACKAGE
```

**Parameters:**
- `q` (required): Search query string
- `pkg` (optional): Package filter (can be specified multiple times)

**Example:**

```bash
curl "http://localhost:8001/api/v1/search?q=natural+numbers"
```

**Response:**

```json
{
  "query": "natural numbers",
  "results": [
    {
      "id": 123,
      "primary_declaration": {
        "lean_name": "Nat"
      },
      "informal_description": "..."
    }
  ]
}
```

### Get Dependencies

```bash
GET /api/v1/statement_groups/{group_id}/dependencies
```

**Example:**

```bash
curl "http://localhost:8001/api/v1/statement_groups/123/dependencies"
```

**Response:**

```json
{
  "source_group_id": 123,
  "citations": [
    {
      "id": 456,
      "primary_declaration": {
        "lean_name": "Nat.add"
      }
    }
  ],
  "count": 1
}
```

## Using with Python Client

You can use the Python client with a local server:

```python
from lean_explore.api.client import Client

# Connect to local server
client = Client(base_url="http://localhost:8001")

# Use as normal
results = await client.search("natural numbers")
```

## OpenAPI Documentation

The server provides OpenAPI documentation at:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`
- OpenAPI JSON: `http://localhost:8001/openapi.json`

## Backend Comparison

### API Backend

- **Pros**: No local data required, always up-to-date
- **Cons**: Requires API key, network access needed

### Local Backend

- **Pros**: No API key needed, works offline, faster for repeated queries
- **Cons**: Requires local data download, may be out of date

## Next Steps

- [CLI Usage](cli.md) - Command-line interface
- [API Client](api-client.md) - Python API client
- [MCP Server](mcp-server.md) - Model Context Protocol server

