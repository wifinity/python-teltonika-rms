"""Authentication handling for Teltonika RMS API."""

import logging
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from httpx import Headers

logger = logging.getLogger(__name__)


class BearerAuth:
    """Bearer token authentication handler."""

    def __init__(self, token: str) -> None:
        """Initialize bearer authentication.

        Args:
            token: Bearer token for authentication
        """
        if not token:
            raise ValueError("Token cannot be empty")
        self.token = token
        logger.debug("BearerAuth initialized")

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers.

        Returns:
            Dictionary with Authorization header
        """
        return {"Authorization": f"Bearer {self.token}"}

    def apply_to_headers(self, headers: "Headers") -> None:
        """Apply authentication to existing headers.

        Args:
            headers: Headers to modify
        """
        headers["Authorization"] = f"Bearer {self.token}"
