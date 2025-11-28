# CLI Usage

The Lean Explore command-line interface provides easy access to search functionality and server management.

## Overview

The CLI is accessed via the `leanexplore` command:

```bash
leanexplore [OPTIONS] COMMAND [ARGS]...
```

## Commands

### Search

Search for Lean declarations:

```bash
leanexplore search QUERY [OPTIONS]
```

**Options:**
- `--pkg, -p`: Filter by package name (can be specified multiple times)
- `--limit, -n`: Maximum number of results (default: 10)

**Examples:**

```bash
# Basic search
leanexplore search "natural numbers"

# Search with package filter
leanexplore search "monoid" --pkg Mathlib

# Multiple package filters
leanexplore search "group" --pkg Mathlib --pkg Batteries

# Limit results
leanexplore search "topology" --limit 5
```

### Configure

Manage CLI configuration:

```bash
leanexplore configure COMMAND
```

**Subcommands:**

- `api-key KEY`: Set API key for remote API
- `show`: Display current configuration
- `reset`: Reset configuration to defaults

**Examples:**

```bash
# Set API key
leanexplore configure api-key YOUR_API_KEY

# View configuration
leanexplore configure show

# Reset configuration
leanexplore configure reset
```

### HTTP Server

Start a local HTTP server:

```bash
leanexplore http start [OPTIONS]
```

**Options:**
- `--backend`: Backend type (`api` or `local`)
- `--api-key`: API key (required for `api` backend)
- `--host`: Host to bind to (default: `127.0.0.1`)
- `--port`: Port to bind to (default: `8000`)

**Examples:**

```bash
# Start with API backend
leanexplore http start --backend api --api-key YOUR_API_KEY

# Start with local backend
leanexplore http start --backend local

# Custom host and port
leanexplore http start --backend local --host 0.0.0.0 --port 8080
```

### MCP Server

Start the Model Context Protocol server:

```bash
leanexplore mcp start [OPTIONS]
```

**Options:**
- `--backend`: Backend type (`api` or `local`)
- `--api-key`: API key (required for `api` backend)
- `--log-level`: Logging level (default: `INFO`)

**Examples:**

```bash
# Start with API backend
leanexplore mcp start --backend api --api-key YOUR_API_KEY

# Start with local backend
leanexplore mcp start --backend local
```

### Data Management

Manage local data:

```bash
leanexplore data COMMAND
```

**Subcommands:**

- `fetch`: Download local data files
- `list`: List available data toolchains
- `status`: Check data status

**Examples:**

```bash
# Fetch local data
leanexplore data fetch

# List available toolchains
leanexplore data list

# Check data status
leanexplore data status
```

### Chat

Interact with an AI agent using Lean Explore tools:

```bash
leanexplore chat [OPTIONS]
```

**Options:**
- `--model`: Model to use (default: `gpt-4`)
- `--backend`: Backend type (`api` or `local`)
- `--api-key`: API key (required for `api` backend)

**Examples:**

```bash
# Start chat session
leanexplore chat

# Use specific model
leanexplore chat --model gpt-4-turbo

# Use local backend
leanexplore chat --backend local
```

## Global Options

- `--help, -h`: Show help message
- `--version`: Show version information

## Examples

### Complete Workflow

```bash
# 1. Configure API key
leanexplore configure api-key YOUR_API_KEY

# 2. Search for declarations
leanexplore search "natural numbers"

# 3. Start local server
leanexplore data fetch
leanexplore http start --backend local

# 4. Query the server
curl "http://localhost:8000/api/v1/search?q=natural+numbers"
```

## Next Steps

- [API Client](api-client.md) - Use the Python API
- [HTTP Server](http-server.md) - Run a local HTTP server
- [MCP Server](mcp-server.md) - Integrate with AI agents

