"""Tests for resource classes."""

import pytest
import respx
from respx import MockResponse as resp

from teltonika_rms.client import RMSClient


@respx.mock
def test_companies_all(client: RMSClient):
    """Test companies.all() with pagination."""
    # First page
    respx.get(
        "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
    ).mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "name": "Company 1"}], "meta": {"total": 2}},
        )
    )
    # Second page
    respx.get(
        "https://rms.teltonika-networks.com/api/companies?limit=100&offset=100"
    ).mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 2, "name": "Company 2"}], "meta": {"total": 2}},
        )
    )

    companies = client.companies.all()
    assert len(companies) == 2
    assert companies[0]["id"] == 1
    assert companies[1]["id"] == 2


@respx.mock
def test_companies_get_by_id(client: RMSClient):
    """Test companies.get(id)."""
    respx.get("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=200, json={"id": 1, "name": "Company 1"})
    )

    company = client.companies.get(1)
    assert company["id"] == 1
    assert company["name"] == "Company 1"


@respx.mock
def test_companies_get_by_name(client: RMSClient):
    """Test companies.get() with name parameter (uses q= then client-side exact match)."""
    respx.get("https://rms.teltonika-networks.com/api/companies?q=Wifinity").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Wifinity"},
                    {"id": 2, "name": "Wifinity Department"},
                ]
            },
        )
    )

    company = client.companies.get(name="Wifinity")
    assert company["id"] == 1
    assert company["name"] == "Wifinity"


@respx.mock
def test_companies_get_by_multiple_params(client: RMSClient):
    """Test companies.get() with multiple filter parameters (client-side filtering)."""
    # Mock all() call
    respx.get(
        "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
    ).mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Test", "parent_id": 1},
                    {"id": 2, "name": "Test", "parent_id": 2},
                ],
                "meta": {"total": 2},
            },
        )
    )

    company = client.companies.get(name="Test", parent_id=1)
    assert company["id"] == 1
    assert company["parent_id"] == 1


@respx.mock
def test_companies_get_multiple_results(client: RMSClient):
    """Test companies.get() raises error when multiple results found."""
    # Mock the all() call that _get_by_filters() makes internally
    respx.get(
        "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
    ).mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Company 1", "parent_id": 1},
                    {"id": 2, "name": "Company 2", "parent_id": 1},
                ],
                "meta": {"total": 2},
            },
        )
    )

    with pytest.raises(ValueError, match="Multiple companies found"):
        client.companies.get(parent_id=1)


@respx.mock
def test_companies_get_no_results(client: RMSClient):
    """Test companies.get() raises error when no results found."""
    from teltonika_rms.exceptions import RMSNotFoundError

    respx.get("https://rms.teltonika-networks.com/api/companies?q=Nonexistent").mock(
        return_value=resp(status_code=200, json={"data": []})
    )

    with pytest.raises(RMSNotFoundError, match="No companies found"):
        client.companies.get(name="Nonexistent")


@respx.mock
def test_companies_filter_name_only(client: RMSClient):
    """Test companies.filter() with name only (uses q= parameter)."""
    respx.get("https://rms.teltonika-networks.com/api/companies?q=Test").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Test"},
                    {"id": 2, "name": "Test Company"},
                    {"id": 3, "name": "Test Department"},
                ]
            },
        )
    )

    companies = client.companies.filter(name="Test")
    # Should return exact matches after client-side filtering
    assert len(companies) == 1
    assert companies[0]["name"] == "Test"


@respx.mock
def test_companies_filter_multiple_params(client: RMSClient):
    """Test companies.filter() with multiple params (client-side filtering)."""
    # First call to all() - page 1
    respx.get(
        "https://rms.teltonika-networks.com/api/companies?limit=100&offset=0"
    ).mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Test", "parent_id": 1},
                    {"id": 2, "name": "Other", "parent_id": 2},
                ],
                "meta": {"total": 2},
            },
        )
    )

    companies = client.companies.filter(name="Test", parent_id=1)
    assert len(companies) == 1
    assert companies[0]["name"] == "Test"
    assert companies[0]["parent_id"] == 1


@respx.mock
def test_companies_create(client: RMSClient):
    """Test companies.create()."""
    respx.post("https://rms.teltonika-networks.com/api/companies").mock(
        return_value=resp(
            status_code=201, json={"id": 1, "name": "New Company", "parent_id": 1}
        )
    )

    company = client.companies.create(name="New Company", parent_id=1)
    assert company["id"] == 1
    assert company["name"] == "New Company"


@respx.mock
def test_companies_update(client: RMSClient):
    """Test companies.update()."""
    respx.put("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=200, json={"id": 1, "name": "Updated Company"})
    )

    company = client.companies.update(1, {"name": "Updated Company"})
    assert company["name"] == "Updated Company"


@respx.mock
def test_companies_delete(client: RMSClient):
    """Test companies.delete()."""
    respx.delete("https://rms.teltonika-networks.com/api/companies/1").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.companies.delete(1)
    assert result["success"] is True


@respx.mock
def test_tags_all(client: RMSClient):
    """Test tags.all()."""
    respx.get("https://rms.teltonika-networks.com/api/tags?limit=100&offset=0").mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "name": "Tag 1"}], "meta": {"total": 1}},
        )
    )

    tags = client.tags.all()
    assert len(tags) == 1
    assert tags[0]["name"] == "Tag 1"


@respx.mock
def test_tags_get_by_id(client: RMSClient):
    """Test tags.get(id)."""
    respx.get("https://rms.teltonika-networks.com/api/tags/1").mock(
        return_value=resp(status_code=200, json={"id": 1, "name": "Tag 1"})
    )

    tag = client.tags.get(1)
    assert tag["id"] == 1


@respx.mock
def test_tags_get_by_name(client: RMSClient):
    """Test tags.get() with name parameter (uses q= then client-side exact match)."""
    respx.get("https://rms.teltonika-networks.com/api/tags?q=DEPLOYED").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "DEPLOYED"},
                    {"id": 2, "name": "DEPLOYED_TEST"},
                ]
            },
        )
    )

    tag = client.tags.get(name="DEPLOYED")
    assert tag["id"] == 1
    assert tag["name"] == "DEPLOYED"


@respx.mock
def test_tags_get_multiple_results(client: RMSClient):
    """Test tags.get() raises error when multiple results found."""
    # Mock the all() call that _get_by_filters() makes internally
    respx.get("https://rms.teltonika-networks.com/api/tags?limit=100&offset=0").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "Tag 1", "company_id": 1},
                    {"id": 2, "name": "Tag 2", "company_id": 1},
                ],
                "meta": {"total": 2},
            },
        )
    )

    with pytest.raises(ValueError, match="Multiple tags found"):
        client.tags.get(company_id=1)


@respx.mock
def test_tags_get_no_results(client: RMSClient):
    """Test tags.get() raises error when no results found."""
    from teltonika_rms.exceptions import RMSNotFoundError

    respx.get("https://rms.teltonika-networks.com/api/tags?q=Nonexistent").mock(
        return_value=resp(status_code=200, json={"data": []})
    )

    with pytest.raises(RMSNotFoundError, match="No tags found"):
        client.tags.get(name="Nonexistent")


@respx.mock
def test_tags_create(client: RMSClient):
    """Test tags.create()."""
    respx.post("https://rms.teltonika-networks.com/api/tags").mock(
        return_value=resp(status_code=201, json={"id": 1, "name": "New Tag"})
    )

    tag = client.tags.create(name="New Tag")
    assert tag["name"] == "New Tag"


@respx.mock
def test_tags_filter_name_only(client: RMSClient):
    """Test tags.filter() with name only (uses q= parameter)."""
    respx.get("https://rms.teltonika-networks.com/api/tags?q=DEPLOYED").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "DEPLOYED"},
                    {"id": 2, "name": "DEPLOYED_TEST"},
                    {"id": 3, "name": "DEPLOYED_PROD"},
                ]
            },
        )
    )

    tags = client.tags.filter(name="DEPLOYED")
    # Should return exact matches after client-side filtering
    assert len(tags) == 1
    assert tags[0]["name"] == "DEPLOYED"


@respx.mock
def test_tags_filter_multiple_params(client: RMSClient):
    """Test tags.filter() with multiple params (client-side filtering)."""
    # First call to all() - page 1
    respx.get("https://rms.teltonika-networks.com/api/tags?limit=100&offset=0").mock(
        return_value=resp(
            status_code=200,
            json={
                "data": [
                    {"id": 1, "name": "DEPLOYED", "company_id": 1},
                    {"id": 2, "name": "OTHER", "company_id": 2},
                ],
                "meta": {"total": 2},
            },
        )
    )

    tags = client.tags.filter(name="DEPLOYED", company_id=1)
    assert len(tags) == 1
    assert tags[0]["name"] == "DEPLOYED"


@respx.mock
def test_devices_all(client: RMSClient):
    """Test devices.all()."""
    respx.get("https://rms.teltonika-networks.com/api/devices?limit=100&offset=0").mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "name": "Device 1"}], "meta": {"total": 1}},
        )
    )

    devices = client.devices.all()
    assert len(devices) == 1


@respx.mock
def test_devices_get_by_id(client: RMSClient):
    """Test devices.get(id)."""
    respx.get("https://rms.teltonika-networks.com/api/devices/1").mock(
        return_value=resp(
            status_code=200, json={"id": 1, "name": "Device 1", "serial": "12345"}
        )
    )

    device = client.devices.get(1)
    assert device["id"] == 1
    assert device["serial"] == "12345"


@respx.mock
def test_devices_get_by_mac(client: RMSClient):
    """Test devices.get() with mac parameter."""
    respx.get(
        "https://rms.teltonika-networks.com/api/devices?mac=00:11:22:33:44:55"
    ).mock(
        return_value=resp(
            status_code=200, json={"data": [{"id": 1, "mac": "00:11:22:33:44:55"}]}
        )
    )

    device = client.devices.get(mac="00:11:22:33:44:55")
    assert device["mac"] == "00:11:22:33:44:55"


@respx.mock
def test_devices_get_invalid_param(client: RMSClient):
    """Test devices.get() raises error for invalid parameters."""
    with pytest.raises(ValueError, match="Invalid filter parameters"):
        client.devices.get(serial="12345")


@respx.mock
def test_devices_filter_allowed_params(client: RMSClient):
    """Test devices.filter() with allowed parameters."""
    respx.get(
        "https://rms.teltonika-networks.com/api/devices?status=online&company_id=1"
    ).mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "status": "online", "company_id": 1}]},
        )
    )

    devices = client.devices.filter(status="online", company_id=1)
    assert len(devices) == 1
    assert devices[0]["status"] == "online"


@respx.mock
def test_devices_filter_invalid_param(client: RMSClient):
    """Test devices.filter() raises error for invalid parameters."""
    with pytest.raises(ValueError, match="Invalid filter parameters"):
        client.devices.filter(serial="12345")


@respx.mock
def test_devices_filter_mac_model(client: RMSClient):
    """Test devices.filter() with mac and model parameters."""
    respx.get(
        "https://rms.teltonika-networks.com/api/devices?mac=00:11:22:33:44:55&model=RUTX11"
    ).mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "mac": "00:11:22:33:44:55", "model": "RUTX11"}]},
        )
    )

    devices = client.devices.filter(mac="00:11:22:33:44:55", model="RUTX11")
    assert len(devices) == 1


@respx.mock
def test_devices_create_success(client: RMSClient):
    """Test devices.create() with all required fields."""
    respx.post("https://rms.teltonika-networks.com/api/devices").mock(
        return_value=resp(
            status_code=201,
            json={
                "success": True,
                "data": [{"id": 1, "mac": "00:11:22:33:44:55", "serial": "1234567890"}],
            },
        )
    )

    device = client.devices.create(
        company_id=123,
        device_series="rut",
        serial="1234567890",
        mac="00:11:22:33:44:55",
        imei="111111111111111",
        password_confirmation="Password123",
    )
    assert device["success"] is True

    # Verify the request was made with data wrapped in array
    request = respx.calls.last.request
    assert request is not None
    request_data = request.read()
    import json

    request_json = json.loads(request_data.decode("utf-8"))
    assert "data" in request_json
    assert isinstance(request_json["data"], list)
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["company_id"] == 123
    assert request_json["data"][0]["device_series"] == "rut"


@respx.mock
def test_devices_create_missing_required_field(client: RMSClient):
    """Test devices.create() raises ValueError when required field is missing."""
    with pytest.raises(ValueError, match="Missing required fields"):
        client.devices.create(mac="00:11:22:33:44:55")


@respx.mock
def test_devices_create_missing_mac_for_rut(client: RMSClient):
    """Test devices.create() raises ValueError when mac is missing for RUT device."""
    with pytest.raises(ValueError, match="MAC address.*required for RUT/TCR"):
        client.devices.create(
            company_id=123,
            device_series="rut",
            serial="1234567890",
            password_confirmation="Password123",
        )


@respx.mock
def test_devices_create_missing_imei_for_trb(client: RMSClient):
    """Test devices.create() raises ValueError when imei is missing for TRB device."""
    with pytest.raises(ValueError, match="IMEI.*required for TRB"):
        client.devices.create(
            company_id=123,
            device_series="trb",
            serial="1234567890",
            password_confirmation="Password123",
        )


@respx.mock
def test_devices_enable_monitoring_single(client: RMSClient):
    """Test devices.enable_monitoring() with single device ID."""
    respx.put("https://rms.teltonika-networks.com/api/devices/monitoring").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.enable_monitoring(123)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["device_id"] == 123
    assert request_json["data"][0]["monitoring_enabled"] == 1


@respx.mock
def test_devices_enable_monitoring_multiple(client: RMSClient):
    """Test devices.enable_monitoring() with list of device IDs."""
    respx.put("https://rms.teltonika-networks.com/api/devices/monitoring").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.enable_monitoring([123, 456, 789])
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert len(request_json["data"]) == 3
    assert request_json["data"][0]["device_id"] == 123
    assert request_json["data"][0]["monitoring_enabled"] == 1
    assert request_json["data"][1]["device_id"] == 456
    assert request_json["data"][1]["monitoring_enabled"] == 1
    assert request_json["data"][2]["device_id"] == 789
    assert request_json["data"][2]["monitoring_enabled"] == 1


@respx.mock
def test_devices_disable_monitoring_single(client: RMSClient):
    """Test devices.disable_monitoring() with single device ID."""
    respx.put("https://rms.teltonika-networks.com/api/devices/monitoring").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.disable_monitoring(123)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["device_id"] == 123
    assert request_json["data"][0]["monitoring_enabled"] == 0


@respx.mock
def test_devices_set_monitoring_enabled(client: RMSClient):
    """Test devices.set_monitoring() with enabled=True."""
    respx.put("https://rms.teltonika-networks.com/api/devices/monitoring").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.set_monitoring(123, enabled=True)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert request_json["data"][0]["monitoring_enabled"] == 1


@respx.mock
def test_devices_set_monitoring_disabled(client: RMSClient):
    """Test devices.set_monitoring() with enabled=False."""
    respx.put("https://rms.teltonika-networks.com/api/devices/monitoring").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.set_monitoring([123, 456], enabled=False)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert len(request_json["data"]) == 2
    assert request_json["data"][0]["monitoring_enabled"] == 0
    assert request_json["data"][1]["monitoring_enabled"] == 0


@respx.mock
def test_device_commands_execute(client: RMSClient):
    """Test device_commands.execute()."""
    respx.post("https://rms.teltonika-networks.com/api/devices/1/command").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.device_commands.execute(1, {"command": "reboot"})
    assert result["success"] is True


@respx.mock
def test_device_commands_actions_execute(client: RMSClient):
    """Test device_commands.actions.execute()."""
    respx.post("https://rms.teltonika-networks.com/api/devices/actions").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.device_commands.actions.execute(devices=[1, 2], action="reboot")
    assert result["success"] is True


@respx.mock
def test_device_commands_actions_cancel(client: RMSClient):
    """Test device_commands.actions.cancel()."""
    respx.post("https://rms.teltonika-networks.com/api/devices/actions/cancel").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.device_commands.actions.cancel([1, 2, 3])
    assert result["success"] is True


@respx.mock
def test_device_commands_actions_logs(client: RMSClient):
    """Test device_commands.actions.logs()."""
    respx.get(
        "https://rms.teltonika-networks.com/api/devices/actions/logs?device_id=1&limit=10"
    ).mock(
        return_value=resp(
            status_code=200, json={"data": [{"id": 1, "action": "reboot"}]}
        )
    )

    logs = client.device_commands.actions.logs(device_id=1, limit=10)
    assert logs is not None
    assert "data" in logs


@respx.mock
def test_devices_delete_single(client: RMSClient):
    """Test devices.delete() with single device ID."""
    respx.delete("https://rms.teltonika-networks.com/api/devices").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.delete(123)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    assert request.method == "DELETE"
    assert request.url.path == "/api/devices"
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "device_id" in request_json
    assert request_json["device_id"] == [123]


@respx.mock
def test_devices_delete_multiple(client: RMSClient):
    """Test devices.delete() with list of device IDs."""
    respx.delete("https://rms.teltonika-networks.com/api/devices").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.delete([123, 456, 789])
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "device_id" in request_json
    assert request_json["device_id"] == [123, 456, 789]


@respx.mock
def test_devices_delete_string_id(client: RMSClient):
    """Test devices.delete() with string device ID (should be cast to int)."""
    respx.delete("https://rms.teltonika-networks.com/api/devices").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.delete("123")
    assert result["success"] is True

    # Verify request format - string ID should be cast to int
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert request_json["device_id"] == [123]


@respx.mock
def test_devices_create_with_string_ids(client: RMSClient):
    """Test devices.create() with string IDs (company_id cast to int, serial remains string)."""
    respx.post("https://rms.teltonika-networks.com/api/devices").mock(
        return_value=resp(
            status_code=201,
            json={
                "success": True,
                "data": [{"id": 1, "mac": "00:11:22:33:44:55", "serial": "1234567890"}],
            },
        )
    )

    device = client.devices.create(
        company_id="123",  # String should be cast to int
        device_series="rut",
        serial="1234567890",  # String should remain as string
        mac="00:11:22:33:44:55",
        password_confirmation="Password123",
    )
    assert device["success"] is True

    # Verify the request was made with correct types
    request = respx.calls.last.request
    assert request is not None
    import json

    request_data = request.read()
    request_json = json.loads(request_data.decode("utf-8"))
    assert "data" in request_json
    assert isinstance(request_json["data"], list)
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["company_id"] == 123  # Should be int, not string
    assert (
        request_json["data"][0]["serial"] == "1234567890"
    )  # Should be string, not int


@respx.mock
def test_devices_get_with_string_id(client: RMSClient):
    """Test devices.get() with string ID (should be cast to int)."""
    respx.get("https://rms.teltonika-networks.com/api/devices/123").mock(
        return_value=resp(
            status_code=200, json={"id": 123, "name": "Device 1", "serial": "12345"}
        )
    )

    device = client.devices.get("123")  # String ID
    assert device["id"] == 123


@respx.mock
def test_devices_filter_with_string_company_id(client: RMSClient):
    """Test devices.filter() with string company_id (should be cast to int)."""
    respx.get("https://rms.teltonika-networks.com/api/devices?company_id=123").mock(
        return_value=resp(
            status_code=200,
            json={"data": [{"id": 1, "status": "online", "company_id": 123}]},
        )
    )

    devices = client.devices.filter(company_id="123")  # String company_id
    assert len(devices) == 1
    assert devices[0]["company_id"] == 123


def test_devices_delete_invalid_id_raises(client: RMSClient):
    """Test devices.delete() raises error for invalid ID."""
    with pytest.raises(ValueError, match="device_id must be an integer"):
        client.devices.delete("not-a-number")


def test_devices_create_invalid_company_id_raises(client: RMSClient):
    """Test devices.create() raises error for invalid company_id."""
    with pytest.raises(ValueError, match="company_id must be an integer"):
        client.devices.create(
            company_id="not-a-number",
            device_series="rut",
            serial="1234567890",
            mac="00:11:22:33:44:55",
            password_confirmation="Password123",
        )


@respx.mock
def test_devices_move_single(client: RMSClient):
    """Test devices.move() with single device ID."""
    respx.post("https://rms.teltonika-networks.com/api/devices/move/").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.move(123, company_id=2)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    assert request.method == "POST"
    assert request.url.path == "/api/devices/move/"
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "device_id" in request_json
    assert "company_id" in request_json
    assert request_json["device_id"] == [123]
    assert request_json["company_id"] == 2


@respx.mock
def test_devices_move_multiple(client: RMSClient):
    """Test devices.move() with list of device IDs."""
    respx.post("https://rms.teltonika-networks.com/api/devices/move/").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.move([123, 456, 789], company_id=2)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert request_json["device_id"] == [123, 456, 789]
    assert request_json["company_id"] == 2


@respx.mock
def test_devices_move_string_ids(client: RMSClient):
    """Test devices.move() with string device IDs and company_id (should be cast to ints)."""
    respx.post("https://rms.teltonika-networks.com/api/devices/move/").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.move(["123", "456"], company_id="2")
    assert result["success"] is True

    # Verify request format - string IDs should be cast to ints
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert request_json["device_id"] == [123, 456]  # Should be ints, not strings
    assert request_json["company_id"] == 2  # Should be int, not string


def test_devices_move_invalid_device_id_raises(client: RMSClient):
    """Test devices.move() raises error for invalid device ID."""
    with pytest.raises(ValueError, match="device_id must be an integer"):
        client.devices.move("not-a-number", company_id=2)


def test_devices_move_invalid_company_id_raises(client: RMSClient):
    """Test devices.move() raises error for invalid company_id."""
    with pytest.raises(ValueError, match="company_id must be an integer"):
        client.devices.move(123, company_id="not-a-number")


def test_devices_move_zero_company_id_raises(client: RMSClient):
    """Test devices.move() raises error for company_id <= 0."""
    with pytest.raises(ValueError, match="company_id must be a positive integer"):
        client.devices.move(123, company_id=0)


@respx.mock
def test_devices_assign_tags_single(client: RMSClient):
    """Test devices.assign_tags() with single tag ID."""
    respx.put("https://rms.teltonika-networks.com/api/devices/tags/assign").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.assign_tags(device_id=123, tag_ids=456)
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    assert request.method == "PUT"
    assert request.url.path == "/api/devices/tags/assign"
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert isinstance(request_json["data"], list)
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["device_id"] == 123
    assert request_json["data"][0]["tag_id"] == [456]


@respx.mock
def test_devices_assign_tags_multiple(client: RMSClient):
    """Test devices.assign_tags() with list of tag IDs."""
    respx.put("https://rms.teltonika-networks.com/api/devices/tags/assign").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.assign_tags(device_id=123, tag_ids=[456, 789])
    assert result["success"] is True

    # Verify request format
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert isinstance(request_json["data"], list)
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["device_id"] == 123
    assert request_json["data"][0]["tag_id"] == [456, 789]


@respx.mock
def test_devices_assign_tags_string_ids(client: RMSClient):
    """Test devices.assign_tags() with string device_id and tag_ids (should be cast to ints)."""
    respx.put("https://rms.teltonika-networks.com/api/devices/tags/assign").mock(
        return_value=resp(status_code=200, json={"success": True})
    )

    result = client.devices.assign_tags(device_id="123", tag_ids=["456", "789"])
    assert result["success"] is True

    # Verify request format - string IDs should be cast to ints
    request = respx.calls.last.request
    assert request is not None
    import json

    request_json = json.loads(request.read().decode("utf-8"))
    assert "data" in request_json
    assert isinstance(request_json["data"], list)
    assert len(request_json["data"]) == 1
    assert request_json["data"][0]["device_id"] == 123  # Should be int, not string
    assert request_json["data"][0]["tag_id"] == [
        456,
        789,
    ]  # Should be ints, not strings


def test_devices_assign_tags_invalid_device_id_raises(client: RMSClient):
    """Test devices.assign_tags() raises error for invalid device_id."""
    with pytest.raises(ValueError, match="device_id must be an integer"):
        client.devices.assign_tags(device_id="not-a-number", tag_ids=456)


def test_devices_assign_tags_invalid_tag_id_raises(client: RMSClient):
    """Test devices.assign_tags() raises error for invalid tag_id."""
    with pytest.raises(ValueError, match="tag_id must be an integer"):
        client.devices.assign_tags(device_id=123, tag_ids="not-a-number")
