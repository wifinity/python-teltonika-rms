"""Devices resource."""

import logging
from typing import Any, cast

from teltonika_rms.exceptions import RMSNotFoundError
from teltonika_rms.resources.base import BaseResource

logger = logging.getLogger(__name__)

# Allowed filter parameters for devices API
ALLOWED_DEVICE_FILTERS = {"status", "mac", "model", "company_id"}


class DevicesResource(BaseResource):
    """Resource for managing devices."""

    def __init__(self, client: Any) -> None:
        """Initialize devices resource."""
        super().__init__(client, "/devices")

    def _validate_filter_params(self, **kwargs: Any) -> None:
        """Validate that only allowed filter parameters are used.

        Args:
            **kwargs: Filter parameters to validate

        Raises:
            ValueError: If invalid parameters are provided
        """
        invalid_params = set(kwargs.keys()) - ALLOWED_DEVICE_FILTERS
        if invalid_params:
            raise ValueError(
                f"Invalid filter parameters: {', '.join(sorted(invalid_params))}. "
                f"Allowed parameters are: {', '.join(sorted(ALLOWED_DEVICE_FILTERS))}"
            )

    def _validate_create_params(self, **kwargs: Any) -> None:
        """Validate required fields for device creation.

        Args:
            **kwargs: Device creation parameters

        Raises:
            ValueError: If required fields are missing
        """
        # Always required fields
        required_fields = {
            "company_id": "Company ID",
            "device_series": "Device series",
            "serial": "Serial number",
            "password_confirmation": "Password confirmation",
        }

        missing_fields = []
        for field, label in required_fields.items():
            if field not in kwargs or kwargs[field] is None:
                missing_fields.append(label)

        # Conditional requirements based on device_series
        device_series = kwargs.get("device_series")
        if device_series:
            device_series_lower = str(device_series).lower()
            if device_series_lower in ["rut", "tcr"]:
                if "mac" not in kwargs or kwargs["mac"] is None:
                    missing_fields.append("MAC address (required for RUT/TCR devices)")
            elif device_series_lower == "trb":
                if "imei" not in kwargs or kwargs["imei"] is None:
                    missing_fields.append("IMEI (required for TRB devices)")

        if missing_fields:
            raise ValueError(
                f"Missing required fields for device creation: {', '.join(missing_fields)}"
            )

    def filter(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get filtered list of devices using API filtering.

        Only the following filter parameters are supported by the API:
        - status: Device status (online, offline, not_activated)
        - mac: Device MAC address
        - model: Device model
        - company_id: Company ID

        Args:
            **kwargs: Filter parameters (only status, mac, model, company_id allowed)

        Returns:
            List of filtered devices

        Raises:
            ValueError: If invalid filter parameters are provided
        """
        self._validate_filter_params(**kwargs)
        # Use parent filter method which passes params to API
        return cast(list[dict[str, Any]], super().filter(**kwargs))

    def _get_by_id(self, id: int | str) -> dict[str, Any]:
        """Get a device by ID.

        Args:
            id: Device ID

        Returns:
            Device data

        Raises:
            RMSNotFoundError: If device not found
        """
        response = self.client.get(f"{self.path}/{id}")
        if not response:
            raise RMSNotFoundError(f"Device with id {id} not found")
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
        """Get a device by filter parameters using API filtering.

        Args:
            **kwargs: Filter parameters (only status, mac, model, company_id allowed)

        Returns:
            Device data

        Raises:
            RMSNotFoundError: If device not found
            ValueError: If multiple devices found or invalid parameters
        """
        self._validate_filter_params(**kwargs)
        response = self.client.get(self.path, params=kwargs)
        if not response:
            raise RMSNotFoundError("No devices found matching the criteria")

        items = response.get("data", [])
        if len(items) == 0:
            raise RMSNotFoundError("No devices found matching the criteria")
        if len(items) > 1:
            raise ValueError(
                f"Multiple devices found ({len(items)}). Use filter() to get all results or be more specific."
            )

        return cast(dict[str, Any], items[0])

    def get(self, id: int | str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Get a single device by ID or by filter parameters.

        Only the following filter parameters are supported:
        - status: Device status (online, offline, not_activated)
        - mac: Device MAC address
        - model: Device model
        - company_id: Company ID

        Args:
            id: Device ID (optional if using filter parameters)
            **kwargs: Filter parameters (only status, mac, model, company_id allowed)

        Returns:
            Device data

        Raises:
            RMSNotFoundError: If device not found
            ValueError: If multiple devices found or invalid parameters
        """
        if id is not None:
            return self._get_by_id(id)

        if kwargs:
            return self._get_by_filters(**kwargs)

        # Neither ID nor filter parameters provided
        raise ValueError("Either 'id' or filter parameters must be provided")

    def create(self, **kwargs: Any) -> dict[str, Any]:
        """Create a new device.

        Required fields:
        - company_id: Company ID that device belongs to
        - device_series: Device series type (rut, trb, tcr, tap, otd, swm)
        - serial: Device serial number
        - password_confirmation: Device password

        Conditional requirements:
        - mac: Required if device_series is "rut" or "tcr"
        - imei: Required if device_series is "trb"

        Args:
            **kwargs: Device data to create

        Returns:
            Created device data

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        self._validate_create_params(**kwargs)

        # Wrap device data in data array as expected by API
        wrapped_data = {"data": [kwargs]}

        # Call parent create with wrapped data
        response = self.client.post(self.path, json=wrapped_data)
        if not response:
            raise ValueError("Failed to create device")
        return cast(dict[str, Any], response)

    def _normalize_device_ids(self, device_ids: int | list[int]) -> list[int]:
        """Normalize device IDs to a list and validate.

        Args:
            device_ids: Single device ID or list of device IDs

        Returns:
            List of device IDs

        Raises:
            ValueError: If device IDs are invalid (must be >= 1)
        """
        # Normalize to list
        if isinstance(device_ids, int):
            device_ids_list = [device_ids]
        elif isinstance(device_ids, list):
            device_ids_list = device_ids
        else:
            raise ValueError(
                f"device_ids must be int or list[int], got {type(device_ids).__name__}"
            )

        # Validate all IDs are >= 1
        invalid_ids = [
            did for did in device_ids_list if not isinstance(did, int) or did < 1
        ]
        if invalid_ids:
            raise ValueError(
                f"Invalid device IDs: {invalid_ids}. Device IDs must be integers >= 1"
            )

        return device_ids_list

    def enable_monitoring(self, device_ids: int | list[int]) -> dict[str, Any]:
        """Enable monitoring on one or more devices.

        Args:
            device_ids: Single device ID or list of device IDs

        Returns:
            API response

        Raises:
            ValueError: If device IDs are invalid
        """
        return self.set_monitoring(device_ids, enabled=True)

    def disable_monitoring(self, device_ids: int | list[int]) -> dict[str, Any]:
        """Disable monitoring on one or more devices.

        Args:
            device_ids: Single device ID or list of device IDs

        Returns:
            API response

        Raises:
            ValueError: If device IDs are invalid
        """
        return self.set_monitoring(device_ids, enabled=False)

    def set_monitoring(
        self, device_ids: int | list[int], enabled: bool
    ) -> dict[str, Any]:
        """Set monitoring status on one or more devices.

        Args:
            device_ids: Single device ID or list of device IDs
            enabled: True to enable monitoring, False to disable

        Returns:
            API response

        Raises:
            ValueError: If device IDs are invalid
        """
        # Normalize and validate device IDs
        device_ids_list = self._normalize_device_ids(device_ids)

        # Prepare data array with monitoring status (1 for enabled, 0 for disabled)
        monitoring_data = {
            "data": [
                {
                    "device_id": device_id,
                    "monitoring_enabled": 1 if enabled else 0,
                }
                for device_id in device_ids_list
            ]
        }

        # Call PUT /devices/monitoring
        response = self.client.put(f"{self.path}/monitoring", json=monitoring_data)
        if not response:
            raise ValueError("Failed to set device monitoring")
        return cast(dict[str, Any], response)
