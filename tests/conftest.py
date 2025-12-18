"""Pytest configuration and fixtures."""

import logging

import pytest
import respx

from teltonika_rms.client import RMSClient
from teltonika_rms.logging_config import set_log_level

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
# Set teltonika_rms logger to INFO (httpx/httpcore will be disabled by set_log_level)
set_log_level(logging.INFO)


@pytest.fixture
def base_url() -> str:
    """Base URL for API."""
    return "https://rms.teltonika-networks.com/api"


@pytest.fixture
def token() -> str:
    """Test bearer token."""
    return "test_token_12345"


@pytest.fixture
def client(token: str, base_url: str) -> RMSClient:
    """Create a test client instance."""
    return RMSClient(token=token, base_url=base_url, enable_retry=False)


@pytest.fixture
def client_with_retry(token: str, base_url: str) -> RMSClient:
    """Create a test client instance with retry enabled."""
    return RMSClient(token=token, base_url=base_url, enable_retry=True, max_retries=2)


@pytest.fixture
def mocked_api(respx_mock: respx.MockRouter) -> respx.MockRouter:
    """Fixture for mocking HTTP API calls."""
    return respx_mock
