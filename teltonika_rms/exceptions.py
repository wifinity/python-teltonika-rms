"""Custom exceptions for Teltonika RMS API client."""


class RMSAPIError(Exception):
    """Base exception for all RMS API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code if available
            response_data: Response data if available
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class RMSAuthenticationError(RMSAPIError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        response_data: dict | None = None,
    ) -> None:
        """Initialize authentication error."""
        super().__init__(message, status_code=401, response_data=response_data)


class RMSPermissionError(RMSAPIError):
    """Raised when user lacks permission (403)."""

    def __init__(
        self,
        message: str = "Permission denied",
        response_data: dict | None = None,
    ) -> None:
        """Initialize permission error."""
        super().__init__(message, status_code=403, response_data=response_data)


class RMSNotFoundError(RMSAPIError):
    """Raised when resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        response_data: dict | None = None,
    ) -> None:
        """Initialize not found error."""
        super().__init__(message, status_code=404, response_data=response_data)


class RMSValidationError(RMSAPIError):
    """Raised when request validation fails (422)."""

    def __init__(
        self,
        message: str = "Validation error",
        response_data: dict | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            response_data: Response data if available
            errors: List of validation errors
        """
        super().__init__(message, status_code=422, response_data=response_data)
        self.errors = errors or []


class RMSConnectionError(RMSAPIError):
    """Raised when connection to API fails."""

    def __init__(
        self,
        message: str = "Connection error",
        original_error: Exception | None = None,
    ) -> None:
        """Initialize connection error.

        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error
