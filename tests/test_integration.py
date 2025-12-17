"""Integration tests for API endpoints."""

import pytest
import respx
from respx import MockResponse as resp

from teltonika_rms.client import RMSClient
from teltonika_rms.exceptions import RMSAPIError


class TestIntegration:
    """Integration tests using mocked API responses."""

    @respx.mock
    def test_companies_workflow(self, client: RMSClient):
        """Test complete companies workflow using resource API."""
        # List all companies
        respx.get(
            "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
        ).mock(
            return_value=resp(
                status_code=200,
                json={"data": [{"id": 1, "name": "Company 1"}], "meta": {"total": 1}},
            )
        )

        companies = client.companies.all()
        assert len(companies) == 1
        assert companies[0]["name"] == "Company 1"

        # Create company
        respx.post("https://rms.teltonika-networks.com/api/companies").mock(
            return_value=resp(
                status_code=201, json={"id": 2, "name": "New Company", "parent_id": 1}
            )
        )

        new_company = client.companies.create(name="New Company", parent_id=1)
        assert new_company["id"] == 2

        # Get single company
        respx.get("https://rms.teltonika-networks.com/api/companies/2").mock(
            return_value=resp(status_code=200, json={"id": 2, "name": "New Company"})
        )

        company = client.companies.get(2)
        assert company["id"] == 2

        # Update company
        respx.put("https://rms.teltonika-networks.com/api/companies/2").mock(
            return_value=resp(
                status_code=200, json={"id": 2, "name": "Updated Company"}
            )
        )

        updated = client.companies.update(2, {"name": "Updated Company"})
        assert updated["name"] == "Updated Company"

        # Delete company
        respx.delete("https://rms.teltonika-networks.com/api/companies/2").mock(
            return_value=resp(status_code=200, json={"success": True})
        )

        result = client.companies.delete(2)
        assert result["success"] is True

    @respx.mock
    def test_devices_workflow(self, client: RMSClient):
        """Test devices workflow using resource API."""
        # List all devices
        respx.get(
            "https://rms.teltonika-networks.com/api/devices?limit=100&offset=0"
        ).mock(
            return_value=resp(
                status_code=200,
                json={"data": [{"id": 1, "name": "Device 1"}], "meta": {"total": 1}},
            )
        )

        devices = client.devices.all()
        assert len(devices) == 1
        assert devices[0]["name"] == "Device 1"

        # Get single device
        respx.get("https://rms.teltonika-networks.com/api/devices/1").mock(
            return_value=resp(
                status_code=200,
                json={"id": 1, "name": "Device 1", "serial": "12345"},
            )
        )

        device = client.devices.get(1)
        assert device["id"] == 1
        assert device["serial"] == "12345"

        # Filter devices
        respx.get(
            "https://rms.teltonika-networks.com/api/devices?mac=00:11:22:33:44:55"
        ).mock(
            return_value=resp(
                status_code=200,
                json={
                    "data": [{"id": 1, "mac": "00:11:22:33:44:55", "serial": "12345"}]
                },
            )
        )

        filtered = client.devices.filter(mac="00:11:22:33:44:55")
        assert len(filtered) == 1

    @respx.mock
    def test_error_handling_workflow(self, client: RMSClient):
        """Test error handling in various scenarios."""
        # Test 401 error
        respx.get("https://rms.teltonika-networks.com/api/user").mock(
            return_value=resp(status_code=401, json={"message": "Unauthorized"})
        )

        with pytest.raises(RMSAPIError) as exc_info:
            client.get_user()
        assert exc_info.value.status_code == 401

        # Test 404 error
        respx.get("https://rms.teltonika-networks.com/api/companies/999").mock(
            return_value=resp(status_code=404, json={"message": "Not found"})
        )

        with pytest.raises(RMSAPIError) as exc_info:
            client.get("/companies/999")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_pagination(self, client: RMSClient):
        """Test pagination with all method."""
        # Mock the first page call that all() makes
        respx.get(
            "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
        ).mock(
            return_value=resp(
                status_code=200, json={"data": [], "meta": {"total": 100}}
            )
        )

        result = client.companies.all()
        assert isinstance(result, list)
