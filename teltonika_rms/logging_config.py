"""Logging configuration and utilities for Teltonika RMS client."""

import json
import logging
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

# Sensitive header names that should be masked in logs
SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie"}

# Maximum length for response body in logs (truncate if longer)
MAX_LOG_BODY_LENGTH = 1000


def _normalize_log_level(level: str | int) -> int:
    """Normalize log level to integer.

    Args:
        level: Log level as string or integer

    Returns:
        Log level as integer
    """
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    return level


def _configure_main_logger(logger: logging.Logger, level: int) -> None:
    """Configure the main teltonika_rms logger.

    Args:
        logger: The main logger instance
        level: Log level to set
    """
    logger.setLevel(level)
    logger.propagate = True

    # If no handler exists, add a StreamHandler
    if not logger.handlers:
        handler: logging.Handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    # Set level on all handlers
    for handler in logger.handlers:
        handler.setLevel(level)


def _configure_child_loggers(level: int) -> None:
    """Configure all existing teltonika_rms child loggers.

    Args:
        level: Log level to set
    """
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith("teltonika_rms"):
            child_logger = logging.getLogger(name)
            child_logger.setLevel(level)
            # Set level on all handlers for this child logger
            for child_handler in child_logger.handlers:
                child_handler.setLevel(level)
            # Ensure child loggers propagate to parent
            child_logger.propagate = True
            # Remove any handlers from child loggers - let them use parent's handler
            # This prevents duplicate log messages
            for handler in list(child_logger.handlers):
                child_logger.removeHandler(handler)


def _configure_httpx_logger(level: int) -> None:
    """Configure httpx and httpcore loggers to be completely silenced.

    httpx and httpcore log HTTP requests at INFO level. We completely disable
    these loggers to prevent any HTTP request logs from appearing.

    Args:
        level: Current teltonika_rms log level (unused, kept for API consistency)
    """
    # Completely disable httpx and httpcore loggers to silence all HTTP request logs
    logging.getLogger("httpx").disabled = True
    logging.getLogger("httpcore").disabled = True


def set_log_level(level: str | int) -> None:
    """Set the log level for the teltonika_rms logger.

    Args:
        level: Log level as string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
               or integer (logging.DEBUG, logging.INFO, etc.)
    """
    level_int = _normalize_log_level(level)
    logger = logging.getLogger("teltonika_rms")

    _configure_main_logger(logger, level_int)
    _configure_child_loggers(level_int)
    _configure_httpx_logger(level_int)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with consistent configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def mask_sensitive_headers(headers: dict[str, str] | Any) -> dict[str, str]:
    """Mask sensitive headers in a dictionary.

    Args:
        headers: Headers dictionary or httpx.Headers object

    Returns:
        Dictionary with sensitive headers masked
    """
    if httpx and isinstance(headers, httpx.Headers):
        # httpx.Headers object
        headers_dict = dict(headers.items())
    elif hasattr(headers, "items"):
        # Dict-like object
        headers_dict = dict(headers.items())
    else:
        # Regular dict
        headers_dict = dict(headers)

    masked = {}
    for key, value in headers_dict.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            if (
                key_lower == "authorization"
                and isinstance(value, str)
                and value.startswith("Bearer ")
            ):
                masked[key] = "Bearer ***"
            else:
                masked[key] = "***"
        else:
            masked[key] = value

    return masked


def format_request_body(body: Any) -> str:
    """Format request body for logging.

    Args:
        body: Request body (dict, str, bytes, etc.)

    Returns:
        Formatted string representation
    """
    if body is None:
        return "None"

    if isinstance(body, (dict, list)):
        try:
            return json.dumps(body, indent=2)
        except (TypeError, ValueError):
            return str(body)

    if isinstance(body, bytes):
        try:
            # Try to decode as JSON
            decoded = body.decode("utf-8")
            try:
                parsed = json.loads(decoded)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, ValueError):
                return f"<bytes: {len(body)} bytes>"
        except UnicodeDecodeError:
            return f"<bytes: {len(body)} bytes>"

    return str(body)


def format_response_body(body: Any) -> str:
    """Format response body for logging, truncating if too long.

    Args:
        body: Response body (dict, str, etc.)

    Returns:
        Formatted string representation (truncated if too long)
    """
    if body is None:
        return "None"

    if isinstance(body, dict):
        try:
            formatted = json.dumps(body, indent=2)
        except (TypeError, ValueError):
            formatted = str(body)
    elif isinstance(body, str):
        # Try to parse as JSON for pretty printing
        try:
            parsed = json.loads(body)
            formatted = json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, ValueError):
            formatted = body
    else:
        formatted = str(body)

    # Truncate if too long
    if len(formatted) > MAX_LOG_BODY_LENGTH:
        truncated = formatted[:MAX_LOG_BODY_LENGTH]
        return f"{truncated}... (truncated, {len(formatted)} chars total)"

    return formatted
