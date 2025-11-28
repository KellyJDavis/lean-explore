# Configuration

Learn how to configure Lean Explore for your needs.

## CLI Configuration

### API Key

Set your API key for the remote API:

```bash
leanexplore configure api-key YOUR_API_KEY
```

The API key is stored in your user configuration directory and will be used for all API requests.

### View Current Configuration

```bash
leanexplore configure show
```

### Reset Configuration

```bash
leanexplore configure reset
```

## Environment Variables

You can also configure Lean Explore using environment variables:

### API Key

```bash
export LEAN_EXPLORE_API_KEY=your-api-key
```

### Base URL

For local servers or custom endpoints:

```bash
export LEAN_EXPLORE_BASE_URL=http://localhost:8000
```

## Python Configuration

### Using Environment Variables

```python
import os
from lean_explore.api.client import Client

# Read from environment
api_key = os.getenv("LEAN_EXPLORE_API_KEY")
base_url = os.getenv("LEAN_EXPLORE_BASE_URL", "https://www.leanexplore.com/api/v1")

client = Client(api_key=api_key, base_url=base_url)
```

### Direct Configuration

```python
from lean_explore.api.client import Client

# Configure directly
client = Client(
    api_key="your-api-key",
    base_url="https://www.leanexplore.com/api/v1",
    timeout=30.0  # Custom timeout
)
```

## Local Backend Configuration

### Data Directory

By default, local data is stored in `~/.leanexplore/data`. You can configure this:

```python
from lean_explore.local.service import Service
from lean_explore import defaults

# Custom data directory
service = Service(data_dir="/path/to/custom/data")
```

### Database URL

For local backend, you can specify a custom database URL:

```python
from lean_explore.local.service import Service

service = Service(
    db_url="sqlite:///path/to/custom/database.db"
)
```

## HTTP Server Configuration

### Backend Selection

```bash
# Use remote API backend
leanexplore http start --backend api --api-key YOUR_API_KEY

# Use local backend
leanexplore http start --backend local
```

### Port and Host

```bash
# Custom port
leanexplore http start --backend local --port 8080

# Custom host
leanexplore http start --backend local --host 0.0.0.0
```

## MCP Server Configuration

```bash
# API backend
leanexplore mcp start --backend api --api-key YOUR_API_KEY

# Local backend
leanexplore mcp start --backend local
```

## Configuration Files

Configuration is stored in:
- **macOS/Linux**: `~/.config/leanexplore/config.toml`
- **Windows**: `%APPDATA%\leanexplore\config.toml`

The configuration file uses TOML format:

```toml
[api]
api_key = "your-api-key"
base_url = "https://www.leanexplore.com/api/v1"
```

