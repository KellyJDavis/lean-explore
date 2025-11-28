# tests/lean_explore/http/test_server.py

"""Tests for the Lean Explore HTTP server.

This module verifies that the HTTP server correctly implements the API endpoints,
handles both 'api' and 'local' backends, and properly manages backend initialization.
"""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from lean_explore.http.server import (
    app,
    initialize_backend,
)
from lean_explore.shared.models.api import (
    APICitationsResponse,
    APIPrimaryDeclarationInfo,
    APISearchResponse,
    APISearchResultItem,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def reset_backend_state():
    """Reset the backend state before and after each test."""
    # Save original state
    from lean_explore.http import server as server_module

    original_backend_type = getattr(server_module, "_backend_type", None)
    original_api_client = getattr(server_module, "_api_client", None)
    original_local_service = getattr(server_module, "_local_service", None)

    # Reset state
    server_module._backend_type = None
    server_module._api_client = None
    server_module._local_service = None

    yield

    # Restore original state
    server_module._backend_type = original_backend_type
    server_module._api_client = original_api_client
    server_module._local_service = original_local_service


class TestBackendInitialization:
    """Tests for backend initialization."""

    def test_initialize_backend_api_success(self, reset_backend_state):
        """Test successful initialization of API backend."""
        mock_api_key = "test-api-key"
        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            initialize_backend("api", mock_api_key)

            mock_client_class.assert_called_once_with(api_key=mock_api_key)
            from lean_explore.http import server as server_module

            assert server_module._backend_type == "api"
            assert server_module._api_client is mock_client
            assert server_module._local_service is None

    def test_initialize_backend_api_missing_key(self, reset_backend_state):
        """Test that API backend initialization fails without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            initialize_backend("api", None)

    def test_initialize_backend_local_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test successful initialization of local backend."""
        mock_service = MagicMock()
        with patch("lean_explore.http.server.LocalService") as mock_service_class:
            mock_service_class.return_value = mock_service

            initialize_backend("local", None)

            mock_service_class.assert_called_once()
            from lean_explore.http import server as server_module

            assert server_module._backend_type == "local"
            assert server_module._local_service is mock_service
            assert server_module._api_client is None

    def test_initialize_backend_local_failure(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test that local backend initialization fails when Service raises error."""
        error_msg = "Database file not found"
        with patch("lean_explore.http.server.LocalService") as mock_service_class:
            mock_service_class.side_effect = FileNotFoundError(error_msg)

            with pytest.raises(RuntimeError, match="Failed to initialize local backend"):
                initialize_backend("local", None)

    def test_initialize_backend_invalid(self, reset_backend_state):
        """Test that invalid backend raises ValueError."""
        with pytest.raises(ValueError, match="Invalid backend"):
            initialize_backend("invalid", None)


class TestSearchEndpoint:
    """Tests for the /api/v1/search endpoint."""

    def test_search_api_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test search endpoint with API backend."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_response = APISearchResponse(
            query="test query",
            packages_applied=None,
            results=[],
            count=0,
            total_candidates_considered=0,
            processing_time_ms=10,
        )

        mock_api_client.search = AsyncMock(return_value=mock_response)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/search", params={"q": "test query"})

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            assert data["count"] == 0
            mock_api_client.search.assert_called_once_with(
                query="test query", package_filters=None
            )

    def test_search_api_backend_with_packages(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test search endpoint with API backend and package filters."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_response = APISearchResponse(
            query="test query",
            packages_applied=["Mathlib"],
            results=[],
            count=0,
            total_candidates_considered=0,
            processing_time_ms=10,
        )

        mock_api_client.search = AsyncMock(return_value=mock_response)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get(
                "/api/v1/search", params={"q": "test query", "pkg": ["Mathlib"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["packages_applied"] == ["Mathlib"]
            mock_api_client.search.assert_called_once_with(
                query="test query", package_filters=["Mathlib"]
            )

    def test_search_local_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test search endpoint with local backend."""
        mock_local_service = MagicMock()
        mock_response = APISearchResponse(
            query="test query",
            packages_applied=None,
            results=[],
            count=0,
            total_candidates_considered=0,
            processing_time_ms=10,
        )

        mock_local_service.search.return_value = mock_response

        with patch("lean_explore.http.server.LocalService") as mock_service_class:
            mock_service_class.return_value = mock_local_service
            initialize_backend("local", None)

            client = TestClient(app)
            response = client.get("/api/v1/search", params={"q": "test query"})

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            mock_local_service.search.assert_called_once_with(
                query="test query", package_filters=None
            )

    def test_search_backend_not_initialized(self, reset_backend_state):
        """Test search endpoint fails when backend is not initialized."""
        client = TestClient(app)
        response = client.get("/api/v1/search", params={"q": "test query"})

        assert response.status_code == 500
        assert "Backend not initialized or invalid" in response.json()["detail"]

    def test_search_api_backend_http_error(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test search endpoint handles HTTP errors from API backend."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()

        # Simulate HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        http_error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_api_client.search = AsyncMock(side_effect=http_error)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/search", params={"q": "test query"})

            assert response.status_code == 401

    def test_search_missing_query_parameter(self, reset_backend_state):
        """Test search endpoint requires query parameter."""
        with patch("lean_explore.http.server.LocalService"):
            initialize_backend("local", None)

            client = TestClient(app)
            response = client.get("/api/v1/search")

            assert response.status_code == 422  # FastAPI validation error


class TestGetStatementGroupEndpoint:
    """Tests for the /api/v1/statement_groups/{group_id} endpoint."""

    def test_get_statement_group_api_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get statement group endpoint with API backend."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_item = APISearchResultItem(
            id=123,
            primary_declaration=APIPrimaryDeclarationInfo(lean_name="Test.name"),
            source_file="Test.lean",
            range_start_line=10,
            statement_text="def test := 1",
            display_statement_text="def test := 1",
            docstring=None,
            informal_description=None,
        )

        mock_api_client.get_by_id = AsyncMock(return_value=mock_item)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 123
            assert data["primary_declaration"]["lean_name"] == "Test.name"
            mock_api_client.get_by_id.assert_called_once_with(123)

    def test_get_statement_group_not_found(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get statement group endpoint returns 404 when not found."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_api_client.get_by_id = AsyncMock(return_value=None)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_statement_group_local_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get statement group endpoint with local backend."""
        mock_local_service = MagicMock()
        mock_item = APISearchResultItem(
            id=456,
            primary_declaration=APIPrimaryDeclarationInfo(lean_name="Local.name"),
            source_file="Local.lean",
            range_start_line=20,
            statement_text="theorem local := True",
            display_statement_text="theorem local := True",
            docstring="A local theorem",
            informal_description=None,
        )

        mock_local_service.get_by_id.return_value = mock_item

        with patch("lean_explore.http.server.LocalService") as mock_service_class:
            mock_service_class.return_value = mock_local_service
            initialize_backend("local", None)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/456")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 456
            assert data["docstring"] == "A local theorem"
            mock_local_service.get_by_id.assert_called_once_with(456)


class TestGetDependenciesEndpoint:
    """Tests for the /api/v1/statement_groups/{group_id}/dependencies endpoint."""

    def test_get_dependencies_api_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get dependencies endpoint with API backend."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_citation = APISearchResultItem(
            id=789,
            primary_declaration=APIPrimaryDeclarationInfo(lean_name="Dep.name"),
            source_file="Dep.lean",
            range_start_line=30,
            statement_text="def dep := 2",
            display_statement_text="def dep := 2",
            docstring=None,
            informal_description=None,
        )
        mock_response = APICitationsResponse(
            source_group_id=123, citations=[mock_citation], count=1
        )

        mock_api_client.get_dependencies = AsyncMock(return_value=mock_response)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/123/dependencies")

            assert response.status_code == 200
            data = response.json()
            assert data["source_group_id"] == 123
            assert data["count"] == 1
            assert len(data["citations"]) == 1
            assert data["citations"][0]["id"] == 789
            mock_api_client.get_dependencies.assert_called_once_with(123)

    def test_get_dependencies_not_found(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get dependencies endpoint returns 404 when group not found."""
        mock_api_key = "test-api-key"
        mock_api_client = MagicMock()
        mock_api_client.get_dependencies = AsyncMock(return_value=None)

        with patch("lean_explore.http.server.APIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            initialize_backend("api", mock_api_key)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/999/dependencies")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_dependencies_local_backend_success(
        self, reset_backend_state, mocker: "MockerFixture"
    ):
        """Test get dependencies endpoint with local backend."""
        mock_local_service = MagicMock()
        mock_citation = APISearchResultItem(
            id=111,
            primary_declaration=APIPrimaryDeclarationInfo(lean_name="LocalDep.name"),
            source_file="LocalDep.lean",
            range_start_line=40,
            statement_text="def local_dep := 3",
            display_statement_text="def local_dep := 3",
            docstring=None,
            informal_description=None,
        )
        mock_response = APICitationsResponse(
            source_group_id=456, citations=[mock_citation], count=1
        )

        mock_local_service.get_dependencies.return_value = mock_response

        with patch("lean_explore.http.server.LocalService") as mock_service_class:
            mock_service_class.return_value = mock_local_service
            initialize_backend("local", None)

            client = TestClient(app)
            response = client.get("/api/v1/statement_groups/456/dependencies")

            assert response.status_code == 200
            data = response.json()
            assert data["source_group_id"] == 456
            assert data["count"] == 1
            mock_local_service.get_dependencies.assert_called_once_with(456)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_not_initialized(self, reset_backend_state):
        """Test health endpoint when backend is not initialized."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["backend"] == "not initialized"

    def test_health_check_initialized(self, reset_backend_state):
        """Test health endpoint when backend is initialized."""
        with patch("lean_explore.http.server.LocalService"):
            initialize_backend("local", None)

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["backend"] == "local"

