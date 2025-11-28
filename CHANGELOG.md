# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

N/A

## [0.4.1] - 2025-11-28

### Fixed
- **Version Detection**: Fixed version detection to work in both development and installed environments. The `_get_project_version()` function now falls back to reading from package metadata when `pyproject.toml` is not available (e.g., when installed from PyPI), preventing `RuntimeError` when running commands like `leanexplore --help` after installation.

## [0.4.0] - 2025-11-28

### Added
- **HTTP Server**: Added new `leanexplore serve` command that provides a FastAPI-based HTTP server for local API access, enabling programmatic access to search functionality without requiring the full CLI.
- **Documentation Site**: Comprehensive documentation site built with MkDocs, including user guides, API references, development documentation, and examples.
- **API Client Enhancements**: The API Client (`lean_explore.api.client`) now supports optional API keys and custom base URLs, making it more flexible for different deployment scenarios.
- **GitHub Releases Integration**: Updated manifest generation to use GitHub releases with dynamic versioning, improving the reliability of version information.
- **CI/CD Pipeline**: Added automated PyPI publishing workflow for streamlined releases.
- **Development Tools**: Added Ruff linting configuration and included Ruff in dev dependencies for improved code quality.
- **Makefile**: Added Makefile with common development tasks for easier project maintenance.
- **Documentation**: Added comprehensive READMEs for extractors and scripts directories to help users understand the data pipeline.

### Changed
- **Package Name**: Changed package name from `lean-explore` to `lean-xplore` on PyPI.
- **Lean Toolchain**: Reverted Lean toolchain from version 4.19 to 4.15 for better compatibility.

### Fixed
- **MCP Server**: Resolved timeout issues and improved error handling in the MCP server.
- **MCP Server API Key**: Fixed MCP server to use stored API key when `--api-key` flag is not provided.
- **Code Quality**: Resolved all Ruff linting errors across the codebase.
- **Tests**: Fixed test alignment with lifespan initialization logic and allowed empty test runs for integration and external markers.

## [0.3.0] - 2025-06-09

### Added
- Implemented batch processing for `search`, `get_by_id`, and `get_dependencies` methods across the stack, allowing them to accept lists of requests for greater efficiency.
- The **API Client** (`lean_explore.api.client`) now sends batch requests concurrently using `asyncio.gather` to reduce network latency.
- The **Local Service** (`lean_explore.local.service`) was updated to process lists of requests serially against the local database and FAISS index.
- The **MCP Tools** (`lean_explore.mcp.tools`) now expose this batch functionality and provide list-based responses.
- The **AI Agent** instructions (`lean_explore.cli.agent`) were updated to explicitly guide the model to use batch calls for more efficient tool use.

## [0.2.2] - 2025-06-06

### Changed
- Updated minimum Python requirement to `>=3.10`.
