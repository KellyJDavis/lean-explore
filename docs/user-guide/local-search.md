# Local Search

Use Lean Explore with a local backend for offline access and faster queries.

## Setup

### Fetch Local Data

First, download the necessary data files:

```bash
leanexplore data fetch
```

This downloads:
- SQLite database with declarations
- FAISS index for semantic search
- Embedding model files
- ID mapping files

### Verify Data

Check that data is available:

```bash
leanexplore data status
```

## Using Local Backend

### CLI

```bash
# Search using local backend
leanexplore search "natural numbers" --backend local
```

### Python API

```python
from lean_explore.local.service import Service

# Initialize local service
service = Service()

# Search
results = await service.search("natural numbers")

# Process results
for item in results.items:
    print(item.primary_declaration.lean_name)
```

### HTTP Server

```bash
# Start server with local backend
leanexplore http start --backend local
```

Then query via HTTP:

```bash
curl "http://localhost:8000/api/v1/search?q=natural+numbers"
```

## Configuration

### Custom Data Directory

```python
from lean_explore.local.service import Service

service = Service(data_dir="/path/to/custom/data")
```

### Custom Database URL

```python
from lean_explore.local.service import Service

service = Service(
    db_url="sqlite:///path/to/database.db"
)
```

## Advantages of Local Backend

- **Offline Access**: No internet connection required
- **Faster Queries**: No network latency
- **Privacy**: Data stays on your machine
- **No API Key**: No authentication needed
- **Customizable**: Full control over data and configuration

## Data Updates

To update your local data:

```bash
leanexplore data fetch
```

This will download the latest data files.

## Storage Location

By default, data is stored in:
- **macOS/Linux**: `~/.leanexplore/data`
- **Windows**: `%APPDATA%\leanexplore\data`

## Next Steps

- [CLI Usage](cli.md) - Command-line interface
- [API Client](api-client.md) - Python API client
- [HTTP Server](http-server.md) - HTTP API server

