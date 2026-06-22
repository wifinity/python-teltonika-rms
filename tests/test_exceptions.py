"""Tests for exception classes."""

import pytest

from teltonika_rms.exceptions import (
    RMSAPIError,
    RMSAuthenticationError,
    RMSPermissionError,
    RMSNotFoundError,
    RMSValidationError,
)


def test_rms_api_error():
    """Test RMSAPIError."""
    error = RMSAPIError("Test error", status_code=500, response_data={"key": "value"})
    assert str(error) == "Test error"
    assert error.status_code == 500
    assert error.response_data == {"key": "value"}


def test_rms_authentication_error():
    """Test RMSAuthenticationError."""
    error = RMSAuthenticationError(
        "Auth failed", response_data={"error": "invalid_token"}
    )
    assert str(error) == "Auth failed"
    assert error.status_code == 401
    assert error.response_data == {"error": "invalid_token"}


def test_rms_permission_error():
    """Test RMSPermissionError."""
    error = RMSPermissionError("Permission denied")
    assert str(error) == "Permission denied"
    assert error.status_code == 403


def test_rms_not_found_error():
    """Test RMSNotFoundError."""
    error = RMSNotFoundError("Not found")
    assert str(error) == "Not found"
    assert error.status_code == 404


def test_rms_validation_error():
    """Test RMSValidationError."""
    errors = [{"field": "name", "message": "Required"}]
    error = RMSValidationError("Validation failed", errors=errors)
    assert str(error) == "Validation failed"
    assert error.status_code == 422
    assert error.errors == errors


def test_rms_api_error_headers():
    """RMSAPIError carries response headers (used to honour Retry-After)."""
    error = RMSAPIError("Rate limited", status_code=429, headers={"Retry-After": "7"})
    assert error.headers == {"Retry-After": "7"}


def test_rms_api_error_headers_default_none():
    """Headers default to None when not provided."""
    error = RMSAPIError("Boom", status_code=500)
    assert error.headers is None
