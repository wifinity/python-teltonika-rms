"""Device commands resource."""

import logging
import time
from typing import Any, Dict, List, Optional, cast

from teltonika_rms.exceptions import RMSAPIError

logger = logging.getLogger(__name__)


class DeviceCommandsActions:
    """Nested resource for device actions."""

    def __init__(self, client: Any) -> None:
        """Initialize device actions resource."""
        self.client = client

    def execute(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Execute device action for a device list.

        Args:
            **kwargs: Action data (device_action schema)

        Returns:
            Response data
        """
        result = self.client.post("/devices/actions", json=kwargs)
        return cast(Optional[Dict[str, Any]], result)

    def cancel(self, device_ids: List[int]) -> Optional[Dict[str, Any]]:
        """Cancel device action for given devices.

        Args:
            device_ids: List of device IDs

        Returns:
            Response data
        """
        result = self.client.post(
            "/devices/actions/cancel", json={"devices": device_ids}
        )
        return cast(Optional[Dict[str, Any]], result)

    def logs(
        self,
        device_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get device action logs.

        Args:
            device_id: Filter by device ID (required if tag_id not provided)
            tag_id: Filter by tag ID (required if device_id not provided)
            limit: Maximum number of results to return
            offset: Offset number of results to return
            **kwargs: Additional query parameters

        Returns:
            Action logs data
        """
        params: Dict[str, Any] = {}
        if device_id is not None:
            params["device_id"] = device_id
        if tag_id is not None:
            params["tag_id"] = tag_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        params.update(kwargs)
        result = self.client.get("/devices/actions/logs", params=params)
        return cast(Optional[Dict[str, Any]], result)


class DeviceCommandsResource:
    """Resource for managing device commands and actions."""

    def __init__(self, client: Any) -> None:
        """Initialize device commands resource."""
        self.client = client
        self.actions = DeviceCommandsActions(client)
        logger.debug("Initialized DeviceCommandsResource")

    def execute(
        self, device_id: int, command_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute command for a device.

        Args:
            device_id: Device ID
            command_data: Command data (execute_command schema)

        Returns:
            Response data including meta.channel for polling the result
        """
        result = self.client.post(f"/devices/{device_id}/command", json=command_data)
        return cast(Optional[Dict[str, Any]], result)

    def run(
        self,
        device_id: int,
        command_data: Dict[str, Any],
        poll_interval: float = 5.0,
        timeout: float = 120.0,
    ) -> Optional[Dict[str, Any]]:
        """Execute a command and wait for the result.

        Fires the command via execute(), then polls the Status API until the
        command completes or errors, or until timeout is exceeded.

        Args:
            device_id: Device ID
            command_data: Command data (e.g. {"command": "speedtest -s"})
            poll_interval: Seconds between status polls
            timeout: Maximum seconds to wait for a result

        Returns:
            Final status event dict (contains value, status, type keys)

        Raises:
            RMSAPIError: If timeout is exceeded before a result is received
        """
        result = self.execute(device_id, command_data)
        channel = (result or {}).get("meta", {}).get("channel")
        if not channel:
            raise RMSAPIError("No status channel returned by execute()")

        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.client.poll_status(channel)
            events = (status or {}).get("data", {}).get(str(device_id), [])
            if events and events[-1]["status"] in ("completed", "error"):
                return cast(Optional[Dict[str, Any]], events[-1])
            time.sleep(poll_interval)

        raise RMSAPIError(
            f"Command did not complete within {timeout}s (device_id={device_id})"
        )
