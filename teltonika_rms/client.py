"""Main client for Teltonika RMS API."""

import json as json_module
import logging
import time
from json import JSONDecodeError
from typing import Any

import httpx

from teltonika_rms.auth import BearerAuth
from teltonika_rms.exceptions import (
    RMSAPIError,
    RMSAuthenticationError,
    RMSConnectionError,
    RMSNotFoundError,
    RMSPermissionError,
    RMSValidationError,
)
from teltonika_rms.logging_config import (
    format_request_body,
    format_response_body,
    mask_sensitive_headers,
    set_log_level,
)
from teltonika_rms.resources import (
    CompaniesResource,
    DeviceCommandsResource,
    DevicesResource,
    TagsResource,
)

logger = logging.getLogger(__name__)


class RMSClient:
    """Client for interacting with Teltonika RMS API."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://rms.teltonika-networks.com/api",
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_retry: bool = True,
        log_level: str | int | None = None,
    ) -> None:
        """Initialize the RMS client.

        Args:
            token: Bearer token for authentication
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_retry: Whether to enable automatic retries
            log_level: Log level for the client (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                       or None to use default/global setting
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_retry = enable_retry
        self.log_level = log_level
        self.auth = BearerAuth(token)

        # Configure logging if log_level is provided
        if log_level is not None:
            set_log_level(log_level)

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self.auth.get_headers(),
        )

        # Initialize resources
        self.companies = CompaniesResource(self)
        self.tags = TagsResource(self)
        self.devices = DevicesResource(self)
        self.device_commands = DeviceCommandsResource(self)

        logger.debug(f"RMSClient initialized with base_url={self.base_url}")

    def __enter__(self) -> "RMSClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
        logger.debug("HTTP client closed")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any] | None:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Response data as dictionary, or None if no content

        Raises:
            RMSAuthenticationError: For 401 errors
            RMSPermissionError: For 403 errors
            RMSNotFoundError: For 404 errors
            RMSValidationError: For 422 errors
            RMSAPIError: For other API errors
        """
        status_code = response.status_code

        # Try to parse JSON response
        try:
            response_data = response.json() if response.content else None
        except Exception:
            response_data = {"text": response.text} if response.text else None

        # Handle error status codes
        if status_code == 401:
            error_msg = (
                response_data.get("message", "Authentication failed")
                if isinstance(response_data, dict)
                else "Authentication failed"
            )
            raise RMSAuthenticationError(error_msg, response_data=response_data)

        if status_code == 403:
            error_msg = (
                response_data.get("message", "Permission denied")
                if isinstance(response_data, dict)
                else "Permission denied"
            )
            raise RMSPermissionError(error_msg, response_data=response_data)

        if status_code == 404:
            error_msg = (
                response_data.get("message", "Resource not found")
                if isinstance(response_data, dict)
                else "Resource not found"
            )
            raise RMSNotFoundError(error_msg, response_data=response_data)

        if status_code == 422:
            error_msg = (
                response_data.get("message", "Validation error")
                if isinstance(response_data, dict)
                else "Validation error"
            )
            errors = (
                response_data.get("errors", [])
                if isinstance(response_data, dict)
                else []
            )
            raise RMSValidationError(
                error_msg, response_data=response_data, errors=errors
            )

        if status_code >= 400:
            error_msg = (
                response_data.get("message", f"API error: {status_code}")
                if isinstance(response_data, dict)
                else f"API error: {status_code}"
            )
            raise RMSAPIError(
                error_msg, status_code=status_code, response_data=response_data
            )

        # Return response data for successful requests
        return response_data

    def _log_response_body(self, response: httpx.Response) -> None:
        """Log response body for debugging.

        Args:
            response: HTTP response object
        """
        # Log response body (httpx caches response content, so this is safe)
        try:
            if response.content:
                # Read content once for logging (httpx will cache it)
                content_bytes = response.content
                if content_bytes:
                    # Try to parse as JSON first
                    try:
                        response_data = json_module.loads(content_bytes.decode("utf-8"))
                        logger.debug(
                            f"Response body: {format_response_body(response_data)}"
                        )
                    except (ValueError, JSONDecodeError, UnicodeDecodeError):
                        # Not JSON, log as text (truncated)
                        response_text = content_bytes.decode("utf-8", errors="replace")[
                            :1000
                        ]
                        if len(content_bytes) > 1000:
                            response_text += (
                                f"... (truncated, {len(content_bytes)} bytes total)"
                            )
                        logger.debug(f"Response body: {response_text}")
                else:
                    logger.debug("Response body: <empty>")
            else:
                logger.debug("Response body: <empty>")
        except Exception as e:
            # Fallback if anything goes wrong (don't break the request)
            logger.debug(f"Response body: <error reading response: {e}>")

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: Any = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path (relative to base_url)
            params: Query parameters
            json: JSON body data
            data: Form data
            files: Files to upload

        Returns:
            Response data as dictionary, or None if no content

        Raises:
            RMSConnectionError: For connection errors
            RMSAPIError: For API errors
        """
        url = f"{self.base_url}{path}" if not path.startswith("http") else path

        # Log request details
        logger.debug(f"{method} {url}")

        # Build request body for logging
        request_body = json if json is not None else data
        if request_body:
            logger.debug(f"Request body: {format_request_body(request_body)}")

        # Log request headers (with sensitive data masked)
        request_headers = self._client.headers.copy()
        if params:
            logger.debug(f"Query parameters: {params}")
        logger.debug(f"Request headers: {mask_sensitive_headers(request_headers)}")

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
            )

            # Log response details
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(
                f"Response headers: {mask_sensitive_headers(response.headers)}"
            )

            # Log response body
            self._log_response_body(response)

            return self._handle_response(response)
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise RMSConnectionError(f"Connection error: {e}", original_error=e) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            # This should be handled by _handle_response, but just in case
            raise RMSAPIError(
                f"HTTP error: {e}", status_code=e.response.status_code
            ) from e

    def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: Any = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body data
            data: Form data
            files: Files to upload

        Returns:
            Response data
        """
        if not self.enable_retry:
            return self._request(
                method, path, params=params, json=json, data=data, files=files
            )

        # Apply retry logic manually
        delay = 1.0
        max_delay = 60.0
        exponential_base = 2.0
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._request(
                    method, path, params=params, json=json, data=data, files=files
                )
            except RMSConnectionError as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. Giving up."
                    )
            except Exception:
                # Non-retryable exception, re-raise immediately
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a GET request.

        Args:
            path: API path
            params: Query parameters

        Returns:
            Response data
        """
        return self._request_with_retry("GET", path, params=params)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: Any = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a POST request.

        Args:
            path: API path
            json: JSON body data
            data: Form data
            files: Files to upload
            params: Query parameters

        Returns:
            Response data
        """
        return self._request_with_retry(
            "POST", path, json=json, data=data, files=files, params=params
        )

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a PUT request.

        Args:
            path: API path
            json: JSON body data
            data: Form data
            params: Query parameters

        Returns:
            Response data
        """
        return self._request_with_retry(
            "PUT", path, json=json, data=data, params=params
        )

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a DELETE request.

        Args:
            path: API path
            params: Query parameters
            json: JSON body data

        Returns:
            Response data
        """
        return self._request_with_retry("DELETE", path, params=params, json=json)

    def get_user(self) -> dict[str, Any] | None:
        """Get authenticated user info.

        Returns:
            User information
        """
        return self.get("/user")
