# MCP Server

The Model Context Protocol (MCP) server allows AI agents to interact with Lean Explore.

## Overview

MCP is a protocol that enables AI assistants to access external tools and data sources. The Lean Explore MCP server provides tools for searching Lean declarations and exploring their relationships.

## Starting the Server

### Using API Backend

```bash
leanexplore mcp serve --backend api --api-key YOUR_API_KEY
```

### Using Local Backend

```bash
# First, fetch local data
leanexplore data fetch

# Start MCP server
leanexplore mcp serve --backend local
```

### Custom Logging

```bash
leanexplore mcp serve --backend local
```

## Available Tools

The MCP server provides the following tools:

### Search

Search for Lean declarations using natural language queries.

**Parameters:**
- `query` (string, required): The search query
- `package_filters` (array of strings, optional): Package names to filter by

**Example:**

```json
{
  "name": "search",
  "arguments": {
    "query": "natural numbers",
    "package_filters": ["Mathlib"],
    "limit": 10
  }
}
```

### Get Statement Group

Retrieve detailed information about a specific statement group.

**Parameters:**
- `group_id` (integer or list of integers, required): The ID(s) of the statement group(s)

**Example:**

```json
{
  "name": "get_by_id",
  "arguments": {
    "group_id": 123
  }
}
```

### Get Dependencies

Get dependencies (citations) for a specific statement group.

**Parameters:**
- `group_id` (integer or list of integers, required): The ID(s) of the statement group(s)

**Example:**

```json
{
  "name": "get_dependencies",
  "arguments": {
    "group_id": 123
  }
}
```

## Integration

### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "lean-explore": {
      "command": "leanexplore",
      "args": ["mcp", "serve", "--backend", "api", "--api-key", "YOUR_API_KEY"]
    }
  }
}
```

### With Other MCP Clients

The server communicates via stdio using the MCP protocol. Any MCP-compatible client can connect to it.

## Use Cases

- **AI Code Assistants**: Help AI assistants understand and search Lean code
- **Documentation Generation**: Automatically generate documentation from Lean code
- **Code Exploration**: Enable AI agents to explore Lean codebases
- **Research Tools**: Assist in mathematical research by finding relevant theorems

## Next Steps

- [CLI Usage](cli.md) - Command-line interface
- [API Client](api-client.md) - Python API client
- [HTTP Server](http-server.md) - HTTP API server

