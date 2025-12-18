"""Devices resource."""

import logging
from typing import Any, cast

from teltonika_rms.exceptions import RMSNotFoundError
from teltonika_rms.resources.base import BaseResource

logger = logging.getLogger(__name__)

# Allowed filter parameters for devices API
ALLOWED_DEVICE_FILTERS = {"status", "mac", "model", "company_id"}

# Allowed device series values
ALLOWED_DEVICE_SERIES = {"rut", "trb", "tcr", "tap", "otd", "swm"}


class DevicesResource(BaseResource):
    """Resource for managing devices."""

    def __init__(self, client: Any) -> None:
        """Initialize devices resource."""
        super().__init__(client, "/devices")

    def _cast_to_int(self, value: int | str, field_name: str = "value") -> int:
        """Cast a value to integer, accepting strings containing numbers.

        Args:
            value: Integer or string containing a number
            field_name: Name of field for error messages

        Returns:
            Integer value

        Raises:
            ValueError: If value cannot be converted to integer
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(
                    f"{field_name} must be an integer or string containing a number, got {value!r}"
                )
        raise ValueError(
            f"{field_name} must be an integer or string containing a number, got {type(value).__name__}"
        )

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
        # Cast company_id if present
        if "company_id" in kwargs:
            kwargs["company_id"] = self._cast_to_int(kwargs["company_id"], "company_id")
        # Use parent filter method which passes params to API
        return cast(list[dict[str, Any]], super().filter(**kwargs))

    def _get_by_id(self, id: int | str) -> dict[str, Any]:
        """Get a device by ID.

        Args:
            id: Device ID (can be string or int)

        Returns:
            Device data

        Raises:
            RMSNotFoundError: If device not found
        """
        # Cast ID to integer
        device_id = self._cast_to_int(id, "id")
        response = self.client.get(f"{self.path}/{device_id}")
        if not response:
            raise RMSNotFoundError(f"Device with id {device_id} not found")
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
        # Cast company_id if present
        if "company_id" in kwargs:
            kwargs["company_id"] = self._cast_to_int(kwargs["company_id"], "company_id")
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
            **kwargs: Device data to create (IDs and serials can be strings or ints)

        Returns:
            Created device data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Cast ID fields to integers (serial should remain as string)
        if "company_id" in kwargs:
            kwargs["company_id"] = self._cast_to_int(kwargs["company_id"], "company_id")
        # Ensure serial is a string (convert int to str if needed, but keep as string)
        if "serial" in kwargs and kwargs["serial"] is not None:
            kwargs["serial"] = str(kwargs["serial"])
        if "firmware_file_id" in kwargs and kwargs["firmware_file_id"] is not None:
            kwargs["firmware_file_id"] = self._cast_to_int(
                kwargs["firmware_file_id"], "firmware_file_id"
            )
        if "config_file_id" in kwargs and kwargs["config_file_id"] is not None:
            kwargs["config_file_id"] = self._cast_to_int(
                kwargs["config_file_id"], "config_file_id"
            )

        # Validate required fields
        self._validate_create_params(**kwargs)

        # Wrap device data in data array as expected by API
        wrapped_data = {"data": [kwargs]}

        # Call parent create with wrapped data
        response = self.client.post(self.path, json=wrapped_data)
        if not response:
            raise ValueError("Failed to create device")
        return cast(dict[str, Any], response)

    def update(self, id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing device.

        Args:
            id: Device ID (can be string or int)
            data: Data to update

        Returns:
            Updated device data
        """
        # Cast ID to integer
        device_id = self._cast_to_int(id, "id")
        response = self.client.put(f"{self.path}/{device_id}", json=data)
        if not response:
            raise ValueError(f"Failed to update device with id {device_id}")
        return cast(dict[str, Any], response)

    def _normalize_device_ids(
        self, device_ids: int | str | list[int | str]
    ) -> list[int]:
        """Normalize device IDs to a list and validate.

        Args:
            device_ids: Single device ID or list of device IDs (can be strings or ints)

        Returns:
            List of device IDs as integers

        Raises:
            ValueError: If device IDs are invalid (must be >= 1)
        """
        # Normalize to list
        if isinstance(device_ids, (int, str)):
            device_ids_list = [device_ids]
        elif isinstance(device_ids, list):
            device_ids_list = device_ids
        else:
            raise ValueError(
                f"device_ids must be int, str, or list of int/str, got {type(device_ids).__name__}"
            )

        # Cast all IDs to integers
        casted_ids = [self._cast_to_int(did, "device_id") for did in device_ids_list]

        # Validate all IDs are >= 1
        invalid_ids = [did for did in casted_ids if did < 1]
        if invalid_ids:
            raise ValueError(
                f"Invalid device IDs: {invalid_ids}. Device IDs must be >= 1"
            )

        return casted_ids

    def enable_monitoring(
        self, device_ids: int | str | list[int | str]
    ) -> dict[str, Any]:
        """Enable monitoring on one or more devices.

        Args:
            device_ids: Single device ID or list of device IDs

        Returns:
            API response

        Raises:
            ValueError: If device IDs are invalid
        """
        return self.set_monitoring(device_ids, enabled=True)

    def disable_monitoring(
        self, device_ids: int | str | list[int | str]
    ) -> dict[str, Any]:
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
        self, device_ids: int | str | list[int | str], enabled: bool
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

    def delete(
        self, id: int | str | list[int | str] | None = None
    ) -> dict[str, Any] | None:
        """Delete one or more devices.

        Device deletion requires sending device IDs in the request body,
        not as URL parameters.

        Args:
            id: Single device ID or list of device IDs

        Returns:
            Response data or None

        Raises:
            ValueError: If no ID provided or IDs are invalid
        """
        if id is None:
            raise ValueError("Device ID(s) must be provided")

        # Normalize to list
        if isinstance(id, (int, str)):
            device_ids = [id]
        elif isinstance(id, list):
            device_ids = id
        else:
            raise ValueError(
                f"id must be int, str, or list of int/str, got {type(id).__name__}"
            )

        # Cast all IDs to integers
        casted_ids = [
            self._cast_to_int(device_id, "device_id") for device_id in device_ids
        ]

        # Validate all IDs are >= 1
        invalid_ids = [did for did in casted_ids if did < 1]
        if invalid_ids:
            raise ValueError(
                f"Invalid device IDs: {invalid_ids}. Device IDs must be >= 1"
            )

        # Send DELETE request with device_id array in body
        response = self.client.delete(self.path, json={"device_id": casted_ids})
        return cast(dict[str, Any] | None, response)

    def move(
        self,
        device_id: int | str | list[int | str],
        company_id: int | str,
    ) -> dict[str, Any]:
        """Move one or more devices to a different company.

        Args:
            device_id: Single device ID or list of device IDs (can be strings or ints)
            company_id: Target company ID (can be string or int)

        Returns:
            API response

        Raises:
            ValueError: If device IDs or company_id are invalid
        """
        # Normalize and validate device IDs
        device_ids_list = self._normalize_device_ids(device_id)

        # Cast company_id to integer
        target_company_id = self._cast_to_int(company_id, "company_id")

        # Validate company_id is > 0
        if target_company_id <= 0:
            raise ValueError("company_id must be a positive integer")

        # Prepare request body
        move_data = {
            "device_id": device_ids_list,
            "company_id": target_company_id,
        }

        # Call POST /devices/move/
        response = self.client.post(f"{self.path}/move/", json=move_data)
        if not response:
            raise ValueError("Failed to move devices")
        return cast(dict[str, Any], response)

    def assign_tags(
        self,
        device_id: int | str,
        tag_ids: int | str | list[int | str],
    ) -> dict[str, Any]:
        """Assign one or more tags to a device.

        Args:
            device_id: Device ID (can be string or int)
            tag_ids: Single tag ID or list of tag IDs (can be strings or ints)

        Returns:
            API response

        Raises:
            ValueError: If device_id or tag_ids are invalid
        """
        # Cast device_id to integer
        casted_device_id = self._cast_to_int(device_id, "device_id")
        if casted_device_id < 1:
            raise ValueError("device_id must be >= 1")

        # Normalize tag_ids to list
        if isinstance(tag_ids, (int, str)):
            tag_ids_list = [tag_ids]
        elif isinstance(tag_ids, list):
            tag_ids_list = tag_ids
        else:
            raise ValueError(
                f"tag_ids must be int, str, or list of int/str, got {type(tag_ids).__name__}"
            )

        # Cast all tag IDs to integers
        casted_tag_ids = [
            self._cast_to_int(tag_id, "tag_id") for tag_id in tag_ids_list
        ]

        # Validate all tag IDs are >= 1
        invalid_tag_ids = [tid for tid in casted_tag_ids if tid < 1]
        if invalid_tag_ids:
            raise ValueError(
                f"Invalid tag IDs: {invalid_tag_ids}. Tag IDs must be >= 1"
            )

        # Prepare request body (wrapped in data array)
        assign_data = {
            "data": [
                {
                    "device_id": casted_device_id,
                    "tag_id": casted_tag_ids,
                }
            ]
        }

        # Call PUT /devices/tags/assign
        response = self.client.put(f"{self.path}/tags/assign", json=assign_data)
        if not response:
            raise ValueError("Failed to assign tags to device")
        return cast(dict[str, Any], response)
