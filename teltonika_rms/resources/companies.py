"""Companies resource."""

import logging
from typing import Any, cast

from teltonika_rms.exceptions import RMSNotFoundError
from teltonika_rms.resources.base import BaseResource

logger = logging.getLogger(__name__)


class CompaniesResource(BaseResource):
    """Resource for managing companies."""

    def __init__(self, client: Any) -> None:
        """Initialize companies resource."""
        super().__init__(client, "/companies")

    def create(self, name: str, parent_id: int, **kwargs: Any) -> dict[str, Any]:
        """Create a new company.

        Args:
            name: Company name
            parent_id: Parent company ID
            **kwargs: Additional company data

        Returns:
            Created company data
        """
        data = {"name": name, "parent_id": parent_id, **kwargs}
        return cast(dict[str, Any], super().create(**data))

    def filter(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get filtered list of companies using client-side filtering.

        Note: This method fetches all companies and filters them client-side
        since the API only supports q= search parameter. For better performance
        with name searches, consider using get() with name parameter.

        Args:
            **kwargs: Filter parameters (name, parent_id, etc.)

        Returns:
            List of filtered companies
        """
        # If only 'name' is provided, use q= parameter for API search
        if len(kwargs) == 1 and "name" in kwargs:
            response = self.client.get(self.path, params={"q": kwargs["name"]})
            if not response:
                return []
            items = response.get("data", [])
            # Still filter client-side for exact match
            filtered = self._filter_items_client_side(items, **kwargs)
            return cast(list[dict[str, Any]], filtered)

        # For other filters or multiple filters, fetch all and filter client-side
        all_companies = self.all()
        filtered = self._filter_items_client_side(all_companies, **kwargs)
        return cast(list[dict[str, Any]], filtered)

    def _get_by_id(self, id: int | str) -> dict[str, Any]:
        """Get a company by ID.

        Args:
            id: Company ID

        Returns:
            Company data

        Raises:
            RMSNotFoundError: If company not found
        """
        response = self.client.get(f"{self.path}/{id}")
        if not response:
            raise RMSNotFoundError(f"Company with id {id} not found")
        # Handle wrapped response structure (some endpoints return {"success": True, "data": {...}})
        if isinstance(response, dict):
            if "data" in response:
                data = response["data"]
                # If data is a dict (single object), return it; if list, return first item
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
                elif isinstance(data, list) and len(data) > 0:
                    return cast(dict[str, Any], data[0])
        return cast(dict[str, Any], response)

    def _get_by_filters(self, **kwargs: Any) -> dict[str, Any]:
        """Get a company by filter parameters using client-side filtering.

        Args:
            **kwargs: Filter parameters to search by

        Returns:
            Company data

        Raises:
            RMSNotFoundError: If company not found
            ValueError: If multiple companies found
        """
        # If only 'name' is provided, use q= parameter for API search first
        if len(kwargs) == 1 and "name" in kwargs:
            response = self.client.get(self.path, params={"q": kwargs["name"]})
            if not response:
                raise RMSNotFoundError("No companies found matching the criteria")
            items = response.get("data", [])
        else:
            # Fetch all and filter client-side
            items = self.all()

        # Filter client-side for exact matches
        exact_matches = self._filter_items_client_side(items, **kwargs)

        if len(exact_matches) == 0:
            raise RMSNotFoundError(
                f"No companies found with exact match for {kwargs}. "
                f"API returned {len(items)} partial matches."
            )
        if len(exact_matches) > 1:
            raise ValueError(
                f"Multiple companies found ({len(exact_matches)}) with exact match for {kwargs}. "
                "Use filter() to get all results or be more specific."
            )

        return cast(dict[str, Any], exact_matches[0])

    def get(self, id: int | str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Get a single company by ID or by filter parameters.

        Args:
            id: Company ID (optional if using filter parameters)
            **kwargs: Filter parameters to search by (e.g., name="Engineering Department")

        Returns:
            Company data

        Raises:
            RMSNotFoundError: If company not found
            ValueError: If multiple companies found or invalid parameters
        """
        if id is not None:
            return self._get_by_id(id)

        if kwargs:
            return self._get_by_filters(**kwargs)

        # Neither ID nor filter parameters provided
        raise ValueError("Either 'id' or filter parameters must be provided")
