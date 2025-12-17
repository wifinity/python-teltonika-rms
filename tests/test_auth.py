"""Tests for authentication module."""

import pytest

from teltonika_rms.auth import BearerAuth


def test_bearer_auth_init():
    """Test BearerAuth initialization."""
    auth = BearerAuth("test_token")
    assert auth.token == "test_token"


def test_bearer_auth_empty_token():
    """Test BearerAuth with empty token raises error."""
    with pytest.raises(ValueError, match="Token cannot be empty"):
        BearerAuth("")


def test_bearer_auth_get_headers():
    """Test BearerAuth get_headers."""
    auth = BearerAuth("test_token_123")
    headers = auth.get_headers()
    assert headers == {"Authorization": "Bearer test_token_123"}


def test_bearer_auth_apply_to_headers():
    """Test BearerAuth apply_to_headers."""
    from httpx import Headers

    auth = BearerAuth("test_token_456")
    headers = Headers()
    auth.apply_to_headers(headers)
    assert headers["Authorization"] == "Bearer test_token_456"
