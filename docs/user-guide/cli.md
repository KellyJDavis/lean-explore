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
- `--package, -p`: Filter by package name (can be specified multiple times)
- `--limit, -n`: Maximum number of results (default: 5)

**Examples:**

```bash
# Basic search
leanexplore search "natural numbers"

# Search with package filter
leanexplore search "monoid" --package Mathlib

# Multiple package filters
leanexplore search "group" --package Mathlib --package Batteries

# Limit results
leanexplore search "topology" --limit 5
```

### Configure

Manage CLI configuration:

```bash
leanexplore configure COMMAND
```

**Subcommands:**

- `api-key`: Set API key for remote API (prompts if not provided)
- `openai-key`: Set OpenAI API key for chat functionality (prompts if not provided)

**Examples:**

```bash
# Set API key (will prompt if not provided)
leanexplore configure api-key YOUR_API_KEY

# Set OpenAI API key (will prompt if not provided)
leanexplore configure openai-key YOUR_OPENAI_API_KEY
```

### HTTP Server

Start a local HTTP server:

```bash
leanexplore http serve [OPTIONS]
```

**Options:**
- `--backend, -b`: Backend type (`api` or `local`, default: `local`)
- `--api-key`: API key (required for `api` backend)
- `--host`: Host to bind to (default: `localhost`)
- `--port`: Port to bind to (default: `8001`)

**Examples:**

```bash
# Start with API backend
leanexplore http serve --backend api --api-key YOUR_API_KEY

# Start with local backend
leanexplore http serve --backend local

# Custom host and port
leanexplore http serve --backend local --host 0.0.0.0 --port 8080
```

### MCP Server

Start the Model Context Protocol server:

```bash
leanexplore mcp serve [OPTIONS]
```

**Options:**
- `--backend, -b`: Backend type (`api` or `local`, default: `api`)
- `--api-key`: API key (required for `api` backend)

**Examples:**

```bash
# Start with API backend
leanexplore mcp serve --backend api --api-key YOUR_API_KEY

# Start with local backend
leanexplore mcp serve --backend local
```

### Data Management

Manage local data:

```bash
leanexplore data COMMAND
```

**Subcommands:**

- `fetch`: Download local data files
- `clean`: Remove all downloaded local data toolchains

**Examples:**

```bash
# Fetch local data
leanexplore data fetch

# Clean all downloaded data
leanexplore data clean
```

### Chat

Interact with an AI agent using Lean Explore tools:

```bash
leanexplore chat [OPTIONS]
```

**Options:**
- `--backend, -lb`: Backend type (`api` or `local`, default: `api`)
- `--lean-api-key`: API key for Lean Explore (if `api` backend, overrides env var/config)
- `--debug`: Enable detailed debug logging

**Examples:**

```bash
# Start chat session (uses API backend by default)
leanexplore chat

# Use local backend
leanexplore chat --backend local

# Use API backend with explicit API key
leanexplore chat --backend api --lean-api-key YOUR_API_KEY

# Enable debug logging
leanexplore chat --debug
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
leanexplore http serve --backend local

# 4. Query the server
curl "http://localhost:8001/api/v1/search?q=natural+numbers"
```

## Next Steps

- [API Client](api-client.md) - Use the Python API
- [HTTP Server](http-server.md) - Run a local HTTP server
- [MCP Server](mcp-server.md) - Integrate with AI agents

