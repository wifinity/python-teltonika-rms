"""Teltonika RMS API Python Client Library."""

__version__ = "0.1.0"

from teltonika_rms.client import RMSClient
from teltonika_rms.exceptions import (
    RMSAPIError,
    RMSAuthenticationError,
    RMSNotFoundError,
    RMSPermissionError,
    RMSValidationError,
)
from teltonika_rms.logging_config import set_log_level
from teltonika_rms.resources import (
    BaseResource,
    CompaniesResource,
    DeviceCommandsResource,
    DevicesResource,
    TagsResource,
)

__all__ = [
    "RMSClient",
    "RMSAPIError",
    "RMSAuthenticationError",
    "RMSNotFoundError",
    "RMSPermissionError",
    "RMSValidationError",
    "BaseResource",
    "CompaniesResource",
    "TagsResource",
    "DevicesResource",
    "DeviceCommandsResource",
    "set_log_level",
]
