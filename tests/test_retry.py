"""Tests for retry logic."""

import time
from unittest.mock import patch

import pytest

from teltonika_rms.exceptions import RMSConnectionError
from teltonika_rms.retry import retry_with_backoff


def test_retry_success():
    """Test retry decorator with successful call."""
    call_count = 0

    @retry_with_backoff(max_retries=3)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_then_success():
    """Test retry decorator that succeeds after retries."""
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RMSConnectionError("Connection failed")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 2


def test_retry_exhausted():
    """Test retry decorator when all retries are exhausted."""
    call_count = 0

    @retry_with_backoff(max_retries=2, initial_delay=0.01)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise RMSConnectionError("Connection failed")

    with pytest.raises(RMSConnectionError, match="Connection failed"):
        always_fails()

    assert call_count == 3  # Initial + 2 retries


def test_retry_non_retryable_exception():
    """Test retry decorator with non-retryable exception."""
    call_count = 0

    @retry_with_backoff(max_retries=3)
    def raises_value_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Not retryable")

    with pytest.raises(ValueError, match="Not retryable"):
        raises_value_error()

    assert call_count == 1  # Should not retry


def test_retry_exponential_backoff():
    """Test that retry uses exponential backoff."""
    call_count = 0
    delays = []

    original_sleep = time.sleep

    def mock_sleep(seconds):
        delays.append(seconds)
        original_sleep(0)  # Don't actually wait

    @retry_with_backoff(max_retries=3, initial_delay=0.1, exponential_base=2.0)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RMSConnectionError("Connection failed")
        return "success"

    with patch("time.sleep", side_effect=mock_sleep):
        result = flaky_function()

    assert result == "success"
    assert len(delays) == 2  # Two retries
    # Check exponential backoff (approximately)
    assert delays[0] == pytest.approx(0.1, rel=0.1)
    assert delays[1] == pytest.approx(0.2, rel=0.1)  # 0.1 * 2
