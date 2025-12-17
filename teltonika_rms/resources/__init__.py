"""Resource classes for Teltonika RMS API."""

from teltonika_rms.resources.base import BaseResource
from teltonika_rms.resources.companies import CompaniesResource
from teltonika_rms.resources.device_commands import DeviceCommandsResource
from teltonika_rms.resources.devices import DevicesResource
from teltonika_rms.resources.tags import TagsResource

__all__ = [
    "BaseResource",
    "CompaniesResource",
    "TagsResource",
    "DevicesResource",
    "DeviceCommandsResource",
]
