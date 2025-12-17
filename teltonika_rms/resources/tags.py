"""Tags resource."""

from typing import Any

from teltonika_rms.resources.base import BaseResource


class TagsResource(BaseResource):
    """Resource for managing tags."""

    def __init__(self, client: Any) -> None:
        """Initialize tags resource."""
        super().__init__(client, "/tags")
