"""Tests for RMS client."""

import pytest
import respx
from respx import MockResponse as resp

from teltonika_rms.client import RMSClient
from teltonika_rms.exceptions import (
    RMSAPIError,
    RMSAuthenticationError,
    RMSNotFoundError,
    RMSPermissionError,
    RMSValidationError,
)


def test_client_init(client: RMSClient):
    """Test client initialization."""
    assert client.base_url == "https://rms.teltonika-networks.com/api"
    assert client.timeout == 30.0
    assert client.max_retries == 3
    assert client.enable_retry is False


def test_client_context_manager(token: str, base_url: str):
    """Test client as context manager."""
    with RMSClient(token=token, base_url=base_url) as client:
        assert client is not None
    # Client should be closed after context exit
    assert client._client.is_closed


@respx.mock
def test_client_get_success(client: RMSClient):
    """Test successful GET request."""
    respx.get("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(
            status_code=200, json={"data": [{"id": 1, "name": "Company 1"}]}
        )
    )

    result = client.get("/companies")
    assert result == {"data": [{"id": 1, "name": "Company 1"}]}


@respx.mock
def test_client_get_with_params(client: RMSClient):
    """Test GET request with query parameters."""
    respx.get("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(status_code=200, json={"data": []})
    )

    result = client.get("/companies", params={"limit": 10, "offset": 0})
    assert result == {"data": []}


@respx.mock
def test_client_post_success(client: RMSClient):
    """Test successful POST request."""
    respx.post("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(status_code=201, json={"id": 1, "name": "New Company"})
    )

    result = client.post("/companies", json={"name": "New Company", "parent_id": 1})
    assert result == {"id": 1, "name": "New Company"}


@respx.mock
def test_client_put_success(client: RMSClient):
    """Test successful PUT request."""
    respx.put("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=200, json={"id": 1, "name": "Updated Company"})
    )

    result = client.put("/companies/1", json={"name": "Updated Company"})
    assert result == {"id": 1, "name": "Updated Company"}


@respx.mock
def test_client_delete_success(client: RMSClient):
    """Test successful DELETE request."""
    respx.delete("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.delete("/companies/1")
    assert result == {"success": True}


@respx.mock
def test_client_authentication_error(client: RMSClient):
    """Test authentication error handling."""
    respx.get("https://rms.teltonika-networks.com/api/user").mock(
        return_value=resp(status_code=401, json={"message": "Unauthorized"})
    )

    with pytest.raises(RMSAuthenticationError) as exc_info:
        client.get("/user")

    assert exc_info.value.status_code == 401
    assert "Unauthorized" in str(exc_info.value)


@respx.mock
def test_client_permission_error(client: RMSClient):
    """Test permission error handling."""
    respx.delete("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=403, json={"message": "Forbidden"})
    )

    with pytest.raises(RMSPermissionError) as exc_info:
        client.delete("/companies/1")

    assert exc_info.value.status_code == 403


@respx.mock
def test_client_not_found_error(client: RMSClient):
    """Test not found error handling."""
    respx.get("https://rms.teltonika-networks.com/api/companies/999").mock(
        return_value=resp(status_code=404, json={"message": "Not found"})
    )

    with pytest.raises(RMSNotFoundError) as exc_info:
        client.get("/companies/999")

    assert exc_info.value.status_code == 404


@respx.mock
def test_client_validation_error(client: RMSClient):
    """Test validation error handling."""
    respx.post("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(
            status_code=422,
            json={
                "message": "Validation failed",
                "errors": [{"field": "name", "message": "Required"}],
            },
        )
    )

    with pytest.raises(RMSValidationError) as exc_info:
        client.post("/companies", json={})

    assert exc_info.value.status_code == 422
    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0]["field"] == "name"


@respx.mock
def test_client_generic_error(client: RMSClient):
    """Test generic API error handling."""
    respx.get("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(status_code=500, json={"message": "Internal server error"})
    )

    with pytest.raises(RMSAPIError) as exc_info:
        client.get("/companies")

    assert exc_info.value.status_code == 500


@respx.mock
def test_client_get_user(client: RMSClient):
    """Test get_user method."""
    respx.get("https://rms.teltonika-networks.com/api/user").mock(
        return_value=resp(status_code=200, json={"id": 1, "email": "user@example.com"})
    )

    result = client.get_user()
    assert result == {"id": 1, "email": "user@example.com"}


@respx.mock
def test_client_resources_initialized(client: RMSClient):
    """Test that resources are properly initialized."""
    assert client.companies is not None
    assert client.tags is not None
    assert client.devices is not None
    assert client.device_commands is not None
