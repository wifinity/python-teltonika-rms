"""Tests for logging functionality."""

import logging
from io import StringIO

import pytest
import respx
from respx import MockResponse as resp

from teltonika_rms.client import RMSClient
from teltonika_rms.logging_config import (
    format_request_body,
    format_response_body,
    mask_sensitive_headers,
    set_log_level,
)


def test_set_log_level():
    """Test setting log level."""
    # Set log level
    set_log_level("DEBUG")
    logger = logging.getLogger("teltonika_rms")
    assert logger.level == logging.DEBUG

    # Set to INFO
    set_log_level("INFO")
    assert logger.level == logging.INFO

    # Set using integer
    set_log_level(logging.WARNING)
    assert logger.level == logging.WARNING


def test_mask_sensitive_headers():
    """Test masking sensitive headers."""
    headers = {
        "Authorization": "Bearer abc123token",
        "Content-Type": "application/json",
        "X-API-Key": "secret-key",
    }

    masked = mask_sensitive_headers(headers)
    assert masked["Authorization"] == "Bearer ***"
    assert masked["X-API-Key"] == "***"
    assert masked["Content-Type"] == "application/json"


def test_format_request_body_dict():
    """Test formatting request body as dict."""
    body = {"name": "Test", "id": 123}
    formatted = format_request_body(body)
    assert "Test" in formatted
    assert "123" in formatted


def test_format_request_body_string():
    """Test formatting request body as string."""
    body = '{"name": "Test"}'
    formatted = format_request_body(body)
    assert "Test" in formatted


def test_format_response_body_truncation():
    """Test response body truncation for long content."""
    # Create a long response body
    long_body = {"data": ["x" * 2000]}
    formatted = format_response_body(long_body)
    assert "truncated" in formatted
    assert "2000" in formatted or "chars total" in formatted


def test_client_log_level_parameter():
    """Test client accepts log_level parameter."""
    client = RMSClient(token="test", log_level="DEBUG")
    assert client.log_level == "DEBUG"


@respx.mock
def test_debug_logging_output(caplog):
    """Test that debug logging produces expected output."""
    # Set up logging capture
    with caplog.at_level(logging.DEBUG):
        respx.get("https://rms.teltonika-networks.com/api/companies").mock(
            return_value=resp(
                status_code=200, json={"data": [{"id": 1, "name": "Company 1"}]}
            )
        )

        client = RMSClient(token="test_token", log_level="DEBUG")
        client.get("/companies")

        # Check that debug logs were generated
        log_messages = [record.message for record in caplog.records]

        # Should have request method/URL
        assert any("GET" in msg and "companies" in msg for msg in log_messages)

        # Should have response status
        assert any("Response status: 200" in msg for msg in log_messages)


@respx.mock
def test_sensitive_data_masking_in_logs(caplog):
    """Test that sensitive data is masked in logs."""
    with caplog.at_level(logging.DEBUG):
        respx.get("https://rms.teltonika-networks.com/api/user").mock(
            return_value=resp(status_code=200, json={"id": 1})
        )

        client = RMSClient(token="secret_token_123", log_level="DEBUG")
        client.get("/user")

        # Check that Authorization header is masked
        log_text = "\n".join([record.message for record in caplog.records])
        assert "Bearer ***" in log_text or "***" in log_text
        # Should NOT contain the actual token
        assert "secret_token_123" not in log_text


@respx.mock
def test_request_body_logging(caplog):
    """Test that request body is logged."""
    with caplog.at_level(logging.DEBUG):
        respx.post("https://rms.teltonika-networks.com/api/companies").mock(
            return_value=resp(status_code=201, json={"id": 1})
        )

        client = RMSClient(token="test", log_level="DEBUG")
        client.post("/companies", json={"name": "New Company", "parent_id": 1})

        log_text = "\n".join([record.message for record in caplog.records])
        assert "Request body" in log_text
        assert "New Company" in log_text


@respx.mock
def test_response_body_logging(caplog):
    """Test that response body is logged."""
    with caplog.at_level(logging.DEBUG):
        respx.get("https://rms.teltonika-networks.com/api/companies/1").mock(
            return_value=resp(status_code=200, json={"id": 1, "name": "Company 1"})
        )

        client = RMSClient(token="test", log_level="DEBUG")
        client.get("/companies/1")

        log_text = "\n".join([record.message for record in caplog.records])
        assert "Response body" in log_text
        assert "Company 1" in log_text
