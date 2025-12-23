"""Tags resource."""

from typing import Any, Dict, List, Optional, Union, cast

from teltonika_rms.exceptions import RMSNotFoundError
from teltonika_rms.resources.base import BaseResource


class TagsResource(BaseResource):
    """Resource for managing tags."""

    def __init__(self, client: Any) -> None:
        """Initialize tags resource."""
        super().__init__(client, "/tags")

    def filter(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get filtered list of tags using client-side filtering.

        Note: This method fetches all tags and filters them client-side
        since the API only supports q= search parameter. For better performance
        with name searches, consider using get() with name parameter.

        Args:
            **kwargs: Filter parameters (name, company_id, etc.)

        Returns:
            List of filtered tags
        """
        # If only 'name' is provided, use q= parameter for API search
        if len(kwargs) == 1 and "name" in kwargs:
            response = self.client.get(self.path, params={"q": kwargs["name"]})
            if not response:
                return []
            items = response.get("data", [])
            # Still filter client-side for exact match
            filtered = self._filter_items_client_side(items, **kwargs)
            return cast(List[Dict[str, Any]], filtered)

        # For other filters or multiple filters, fetch all and filter client-side
        all_tags = self.all()
        filtered = self._filter_items_client_side(all_tags, **kwargs)
        return cast(List[Dict[str, Any]], filtered)

    def _get_by_id(self, id: Union[int, str]) -> Dict[str, Any]:
        """Get a tag by ID.

        Args:
            id: Tag ID

        Returns:
            Tag data

        Raises:
            RMSNotFoundError: If tag not found
        """
        response = self.client.get(f"{self.path}/{id}")
        if not response:
            raise RMSNotFoundError(f"Tag with id {id} not found")
        # Handle wrapped response structure (some endpoints return {"success": True, "data": {...}})
        if isinstance(response, dict):
            if "data" in response:
                data = response["data"]
                # If data is a dict (single object), return it; if list, return first item
                if isinstance(data, dict):
                    return cast(Dict[str, Any], data)
                elif isinstance(data, list) and len(data) > 0:
                    return cast(Dict[str, Any], data[0])
        return cast(Dict[str, Any], response)

    def _get_by_filters(self, **kwargs: Any) -> Dict[str, Any]:
        """Get a tag by filter parameters using client-side filtering.

        Args:
            **kwargs: Filter parameters to search by

        Returns:
            Tag data

        Raises:
            RMSNotFoundError: If tag not found
            ValueError: If multiple tags found
        """
        # If only 'name' is provided, use q= parameter for API search first
        if len(kwargs) == 1 and "name" in kwargs:
            response = self.client.get(self.path, params={"q": kwargs["name"]})
            if not response:
                raise RMSNotFoundError("No tags found matching the criteria")
            items = response.get("data", [])
        else:
            # Fetch all and filter client-side
            items = self.all()

        # Filter client-side for exact matches
        exact_matches = self._filter_items_client_side(items, **kwargs)

        if len(exact_matches) == 0:
            raise RMSNotFoundError(
                f"No tags found with exact match for {kwargs}. "
                f"API returned {len(items)} partial matches."
            )
        if len(exact_matches) > 1:
            raise ValueError(
                f"Multiple tags found ({len(exact_matches)}) with exact match for {kwargs}. "
                "Use filter() to get all results or be more specific."
            )

        return cast(Dict[str, Any], exact_matches[0])

    def get(
        self, id: Optional[Union[int, str]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Get a single tag by ID or by filter parameters.

        Args:
            id: Tag ID (optional if using filter parameters)
            **kwargs: Filter parameters to search by (e.g., name="DEPLOYED")

        Returns:
            Tag data

        Raises:
            RMSNotFoundError: If tag not found
            ValueError: If multiple tags found or invalid parameters
        """
        if id is not None:
            return self._get_by_id(id)

        if kwargs:
            return self._get_by_filters(**kwargs)

        # Neither ID nor filter parameters provided
        raise ValueError("Either 'id' or filter parameters must be provided")
