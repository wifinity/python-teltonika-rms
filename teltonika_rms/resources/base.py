"""Base resource class for API resources."""

import logging
from typing import Any, cast

from teltonika_rms.exceptions import RMSNotFoundError

logger = logging.getLogger(__name__)


class BaseResource:
    """Base class for API resources providing common CRUD operations."""

    def __init__(self, client: Any, path: str) -> None:
        """Initialize the resource.

        Args:
            client: RMSClient instance
            path: Base API path for this resource (e.g., "/companies")
        """
        self.client = client
        self.path = path.rstrip("/")
        logger.debug(f"Initialized {self.__class__.__name__} with path {self.path}")

    def all(self) -> list[dict[str, Any]]:
        """Get all items, automatically handling pagination.

        Returns:
            List of all items across all pages
        """
        all_items: list[dict[str, Any]] = []
        offset = 0
        limit = 100  # Default page size

        while True:
            params = {"limit": limit, "offset": offset}
            response = self.client.get(self.path, params=params)

            if not response:
                break

            items = response.get("data", [])
            if not items:
                break

            all_items.extend(items)

            # Check if we've fetched all items
            # If no meta/total info, stop when we get fewer items than requested
            meta = response.get("meta", {})
            total = meta.get("total")

            if total is not None:
                # We have total count, check if we've fetched all
                if len(all_items) >= total:
                    break
            elif len(items) < limit:
                # No more items available
                break

            offset += limit

        logger.debug(f"Fetched {len(all_items)} items from {self.path}")
        return all_items

    def get(self, id: int | str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Get a single item by ID or by filter parameters.

        Args:
            id: Item ID (optional if using filter parameters)
            **kwargs: Filter parameters to search by (e.g., name="Wifinity")

        Returns:
            Item data

        Raises:
            RMSNotFoundError: If item not found
            ValueError: If multiple items found or invalid parameters
        """
        # If ID is provided, use direct lookup
        if id is not None:
            response = self.client.get(f"{self.path}/{id}")
            if not response:
                raise RMSNotFoundError(f"Item with id {id} not found")
            return cast(dict[str, Any], response)

        # If filter parameters are provided, use filter and return single result
        if kwargs:
            response = self.client.get(self.path, params=kwargs)
            if not response:
                raise RMSNotFoundError("No items found matching the criteria")

            items = response.get("data", [])
            if len(items) == 0:
                raise RMSNotFoundError("No items found matching the criteria")
            if len(items) > 1:
                raise ValueError(
                    f"Multiple items found ({len(items)}). Use filter() to get all results or be more specific."
                )

            return cast(dict[str, Any], items[0])

        # Neither ID nor filter parameters provided
        raise ValueError("Either 'id' or filter parameters must be provided")

    def filter(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get filtered list of items.

        Args:
            **kwargs: Filter parameters to pass as query parameters

        Returns:
            List of filtered items
        """
        response = self.client.get(self.path, params=kwargs)
        if not response:
            return []
        data = response.get("data", [])
        return cast(list[dict[str, Any]], data)

    def create(self, **kwargs: Any) -> dict[str, Any]:
        """Create a new item.

        Args:
            **kwargs: Item data to create

        Returns:
            Created item data
        """
        response = self.client.post(self.path, json=kwargs)
        if not response:
            raise ValueError("Failed to create item")
        return cast(dict[str, Any], response)

    def update(self, id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing item.

        Args:
            id: Item ID
            data: Data to update

        Returns:
            Updated item data
        """
        response = self.client.put(f"{self.path}/{id}", json=data)
        if not response:
            raise ValueError(f"Failed to update item with id {id}")
        return cast(dict[str, Any], response)

    def delete(self, id: int | str) -> dict[str, Any] | None:
        """Delete an item.

        Args:
            id: Item ID

        Returns:
            Response data or None
        """
        result = self.client.delete(f"{self.path}/{id}")
        return cast(dict[str, Any] | None, result)

    def _filter_items_client_side(
        self, items: list[dict[str, Any]], **filters: Any
    ) -> list[dict[str, Any]]:
        """Filter items client-side based on provided criteria.

        Args:
            items: List of items to filter
            **filters: Filter criteria (field=value pairs)

        Returns:
            Filtered list of items matching all criteria
        """
        if not filters:
            return items

        filtered = []
        for item in items:
            match = True
            for key, value in filters.items():
                item_value = item.get(key)
                # Handle case-insensitive string comparison
                if isinstance(value, str) and isinstance(item_value, str):
                    if item_value.lower() != value.lower():
                        match = False
                        break
                elif item_value != value:
                    match = False
                    break
            if match:
                filtered.append(item)

        return filtered
