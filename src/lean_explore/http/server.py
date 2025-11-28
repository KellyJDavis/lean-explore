# src/lean_explore/http/server.py

"""HTTP server implementation for Lean Explore.

This module provides a FastAPI-based HTTP server that exposes the same
API endpoints as the remote Lean Explore API. It supports both 'api'
(proxy) and 'local' backends.
"""

import logging
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query

from lean_explore.api.client import Client as APIClient
from lean_explore.local.service import Service as LocalService
from lean_explore.shared.models.api import (
    APICitationsResponse,
    APISearchResponse,
    APISearchResultItem,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lean Explore HTTP Server",
    description="Local HTTP server providing Lean search functionalities",
    version="1.0.0",
)

# Global backend state
_backend_type: Optional[str] = None
_api_client: Optional[APIClient] = None
_local_service: Optional[LocalService] = None


def initialize_backend(backend: str, api_key: Optional[str] = None) -> None:
    """Initialize the backend service based on the specified backend type.

    Args:
        backend: The backend type ('api' or 'local').
        api_key: Optional API key for 'api' backend.

    Raises:
        ValueError: If backend is invalid or API key is missing for 'api' backend.
        RuntimeError: If local backend initialization fails.
    """
    global _backend_type, _api_client, _local_service

    _backend_type = backend.lower()

    if _backend_type == "api":
        if not api_key:
            raise ValueError("API key is required for 'api' backend.")
        _api_client = APIClient(api_key=api_key)
        logger.info("Initialized API backend with provided API key.")
    elif _backend_type == "local":
        try:
            _local_service = LocalService()
            logger.info("Initialized local backend successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize local backend: {e}", exc_info=True)
            raise RuntimeError(
                f"Failed to initialize local backend: {e}. "
                "Please ensure local data is available by running "
                "'leanexplore data fetch'."
            ) from e
    else:
        raise ValueError(f"Invalid backend: '{backend}'. Must be 'api' or 'local'.")


@app.get("/api/v1/search", response_model=APISearchResponse)
async def search(
    q: str = Query(..., description="The natural language search query string."),
    pkg: Optional[List[str]] = Query(
        None, description="Package names to filter by. Can be specified multiple times."
    ),
) -> APISearchResponse:
    """Search for Lean statement groups.

    Args:
        q: The search query string.
        pkg: Optional list of package names to filter by.

    Returns:
        APISearchResponse containing search results.

    Raises:
        HTTPException: If backend is not initialized or request fails.
    """
    if _backend_type == "api":
        if not _api_client:
            raise HTTPException(
                status_code=500, detail="API backend not properly initialized."
            )
        try:
            response = await _api_client.search(query=q, package_filters=pkg)
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text or "API request failed.",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    elif _backend_type == "local":
        if not _local_service:
            raise HTTPException(
                status_code=500, detail="Local backend not properly initialized."
            )
        try:
            response = _local_service.search(query=q, package_filters=pkg)
            return response
        except Exception as e:
            logger.error(f"Local search failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    else:
        raise HTTPException(
            status_code=500, detail="Backend not initialized or invalid."
        )


@app.get("/api/v1/statement_groups/{group_id}", response_model=APISearchResultItem)
async def get_statement_group(group_id: int) -> APISearchResultItem:
    """Get a statement group by its ID.

    Args:
        group_id: The unique identifier of the statement group.

    Returns:
        APISearchResultItem containing the statement group details.

    Raises:
        HTTPException: If backend is not initialized, group not found, or request fails.
    """
    if _backend_type == "api":
        if not _api_client:
            raise HTTPException(
                status_code=500, detail="API backend not properly initialized."
            )
        try:
            item = await _api_client.get_by_id(group_id)
            if item is None:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            return item
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e}")
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text or "API request failed.",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    elif _backend_type == "local":
        if not _local_service:
            raise HTTPException(
                status_code=500, detail="Local backend not properly initialized."
            )
        try:
            item = _local_service.get_by_id(group_id)
            if item is None:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            return item
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local get_by_id failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    else:
        raise HTTPException(
            status_code=500, detail="Backend not initialized or invalid."
        )


@app.get(
    "/api/v1/statement_groups/{group_id}/dependencies",
    response_model=APICitationsResponse,
)
async def get_dependencies(group_id: int) -> APICitationsResponse:
    """Get dependencies (citations) for a statement group.

    Args:
        group_id: The unique identifier of the source statement group.

    Returns:
        APICitationsResponse containing the list of dependencies.

    Raises:
        HTTPException: If backend is not initialized, group not found, or request fails.
    """
    if _backend_type == "api":
        if not _api_client:
            raise HTTPException(
                status_code=500, detail="API backend not properly initialized."
            )
        try:
            response = await _api_client.get_dependencies(group_id)
            if response is None:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            return response
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e}")
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text or "API request failed.",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    elif _backend_type == "local":
        if not _local_service:
            raise HTTPException(
                status_code=500, detail="Local backend not properly initialized."
            )
        try:
            response = _local_service.get_dependencies(group_id)
            if response is None:
                raise HTTPException(
                    status_code=404, detail="Statement group not found."
                )
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local get_dependencies failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    else:
        raise HTTPException(
            status_code=500, detail="Backend not initialized or invalid."
        )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        A dictionary indicating server status.
    """
    return {
        "status": "healthy",
        "backend": _backend_type or "not initialized",
    }

