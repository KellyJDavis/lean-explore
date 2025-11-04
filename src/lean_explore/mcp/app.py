# src/lean_explore/mcp/app.py

"""Initializes the FastMCP application and its lifespan context.

This module creates the main FastMCP application instance and defines
a lifespan context manager. The lifespan manager is responsible for
making the configured backend service (API client or local service)
available to MCP tools via the request context. The initialization parameters
will be set by the server startup script before running the app.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional, Union

from mcp.server.fastmcp import FastMCP

# Import your backend service types for type hinting
from lean_explore.api.client import Client as APIClient
from lean_explore.local.service import Service as LocalService

logger = logging.getLogger(__name__)

# Define a type for the backend service to be used by tools
BackendServiceType = Union[APIClient, LocalService, None]


@dataclass
class AppContext:
    """Dataclass to hold application-level context for MCP tools.

    Attributes:
        backend_service: The initialized backend service (either APIClient or
                         LocalService) that tools will use to perform actions.
                         This will be None initially and populated asynchronously.
        _backend_future: An asyncio Future that will contain the backend service
                        once initialization completes. Tools should await this
                        instead of accessing backend_service directly.
    """

    backend_service: Optional[BackendServiceType] = None
    _backend_future: Optional[asyncio.Future[BackendServiceType]] = field(
        default=None, init=False
    )


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Asynchronous context manager for the MCP application's lifespan.

    This function is called by FastMCP when the server starts and stops.
    It initializes the backend service instance based on parameters set by
    the server script and makes it available in the AppContext.

    Args:
        server: The FastMCP application instance.

    Yields:
        AppContext: The application context containing the backend service.

    Raises:
        RuntimeError: If the backend initialization parameters have not been
                      set on an attribute of the `server` instance prior to
                      the app running.
    """
    logger.info("MCP application lifespan starting...")

    # The main server script (mcp/server.py) is expected to set initialization
    # parameters as attributes on the mcp_app instance before mcp_app.run() is called.
    # This allows the server to respond to initialize requests quickly, and then
    # we load the heavy backend service asynchronously.
    backend_type: Optional[str] = getattr(server, "_lean_explore_backend_type", None)
    backend_api_key: Optional[str] = getattr(
        server, "_lean_explore_backend_api_key", None
    )

    if backend_type is None:
        logger.error(
            "Backend type not found on the FastMCP app instance. "
            "The MCP server script must set '_lean_explore_backend_type' "
            "before running the app."
        )
        raise RuntimeError(
            "Backend type not set for MCP app. "
            "Ensure the server script correctly sets the backend type attribute "
            "on the FastMCP app instance."
        )

    # Create a future that will be resolved when backend initialization completes
    backend_future: asyncio.Future[BackendServiceType] = asyncio.Future()

    # Create app context with the future - yield immediately so server can respond
    app_context = AppContext()
    app_context._backend_future = backend_future

    # Start backend initialization in background task
    async def initialize_backend():
        """Initialize the backend service asynchronously."""
        try:
            logger.info(
                f"Starting backend service initialization ({backend_type})..."
            )
            backend_service_instance: BackendServiceType = None

            if backend_type == "local":
                # Run in executor to avoid blocking the event loop
                # This allows the MCP server to respond to initialize requests
                # while heavy model loading happens in the background
                loop = asyncio.get_event_loop()
                from lean_explore.local.service import Service

                backend_service_instance = await loop.run_in_executor(
                    None, lambda: Service()
                )
                logger.info("Local backend service initialized successfully.")
            elif backend_type == "api":
                if not backend_api_key:
                    raise RuntimeError(
                        "API key is required when using the 'api' backend."
                    )
                from lean_explore.api.client import Client

                backend_service_instance = Client(api_key=backend_api_key)
                logger.info("API client backend initialized successfully.")
            else:
                raise RuntimeError(f"Invalid backend type: {backend_type}")

            if backend_service_instance is None:
                raise RuntimeError(
                    "Backend service instance was not created during initialization."
                )

            # Update the context and resolve the future
            app_context.backend_service = backend_service_instance
            backend_future.set_result(backend_service_instance)
        except Exception as e:
            logger.error(
                f"Failed to initialize backend service ({backend_type}): {e}",
                exc_info=True,
            )
            backend_future.set_exception(e)
            raise

    # Start initialization in background
    init_task = asyncio.create_task(initialize_backend())

    try:
        # Yield immediately - server can now respond to initialize requests
        # Backend initialization happens in background
        yield app_context
    finally:
        logger.info("MCP application lifespan shutting down...")
        # Cancel initialization if it's still running
        if not init_task.done():
            init_task.cancel()
            try:
                await init_task
            except asyncio.CancelledError:
                pass


# Create the FastMCP application instance
# The lifespan manager will be associated with this app.
mcp_app = FastMCP(
    "LeanExploreMCPServer",
    version="0.1.0",
    description=(
        "MCP Server for Lean Explore, providing tools to search and query Lean"
        " mathematical data."
    ),
    lifespan=app_lifespan,
)

mcp_app.lifespan = app_lifespan
