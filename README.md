# Teltonika RMS Python Client

A Python client library for the Teltonika Remote Management System (RMS) API.

## Features

- **Resource-Based API**: Intuitive object-oriented interface (client.companies.all(), client.devices.get(id), etc.)
- **Full API Coverage**: Access to all RMS API endpoints
- **Type Hints**: Full type annotations for better IDE support
- **Error Handling**: Custom exceptions for different error scenarios
- **Retry Logic**: Automatic retry with exponential backoff
- **Authentication**: Secure Bearer token authentication
- **Logging**: Configurable logging throughout the client
- **Python 3.12+**: Modern Python features and type hints

## Installation

```bash
pip install teltonika-rms
```

Or install from source:

```bash
git clone https://github.com/wifinity/python-teltonika-rms.git
cd python-teltonika-rms
pip install -e .
```

## Quick Start

```python
(from teltonika_rms import RMSClient
)
# Initialize the client with your bearer token
client = RMSClient(token="your_bearer_token_here")

# Get authenticated user info
user = client.get_user()
print(f"Logged in as: {user['email']}")

# List all companies (automatically handles pagination)
companies = client.companies.all()
print(f"Found {len(companies)} companies")

# Get a specific company by ID
company = client.companies.get(123)

# Or get by filter parameters (returns single result or raises error if multiple/none found)
company = client.companies.get(name="Wifinity")

# Filter companies
filtered = client.companies.filter(name="Test", parent_id=1)

# Create a new company
new_company = client.companies.create(name="New Company", parent_id=1)

# Update a company
updated = client.companies.update(123, {"name": "Updated Company"})

# Delete a company
client.companies.delete(123)

# Work with devices
devices = client.devices.all()
device = client.devices.get(456)
filtered_devices = client.devices.filter(status="online", company_id=1)

# Work with tags
tags = client.tags.all()
tag = client.tags.get(789)
new_tag = client.tags.create(name="New Tag")

# Execute device commands
result = client.device_commands.execute(device_id=456, command_data={"command": "reboot"})
action_result = client.device_commands.actions.execute(devices=[456, 789], action="reboot")

# Close the client when done
client.close()
```

## Usage

### Client Initialization

```python
from teltonika_rms import RMSClient

# Basic initialization
client = RMSClient(token="your_token")

# With custom configuration
client = RMSClient(
    token="your_token",
    base_url="https://rms.teltonika-networks.com/api",
    timeout=30.0,
    max_retries=3,
    enable_retry=True,
)
```

### Context Manager

The client can be used as a context manager for automatic cleanup:

```python
with RMSClient(token="your_token") as client:
    companies = client.companies.all()
    # Client is automatically closed when exiting the context
```

### Resource-Based API

The client provides resource objects for intuitive API access:

#### Companies

```python
# Get all companies (automatically handles pagination)
companies = client.companies.all()

# Get a single company by ID
company = client.companies.get(123)

# Or get by filter parameters
company = client.companies.get(name="Wifinity")

# Filter companies
filtered = client.companies.filter(name="Test", parent_id=1, sort="company_name")

# Create a company
new_company = client.companies.create(name="New Company", parent_id=1)

# Update a company
updated = client.companies.update(123, {"name": "Updated Name"})

# Delete a company
client.companies.delete(123)
```

#### Tags

```python
# Get all tags
tags = client.tags.all()

# Get a single tag by ID
tag = client.tags.get(456)

# Or get by filter parameters
tag = client.tags.get(name="Production")

# Filter tags
filtered = client.tags.filter(name="tag_name")

# Create a tag
new_tag = client.tags.create(name="New Tag")

# Update a tag
updated = client.tags.update(456, {"name": "Updated Tag"})

# Delete a tag
client.tags.delete(456)
```

#### Devices

```python
# Get all devices
devices = client.devices.all()

# Get a single device by ID
device = client.devices.get(789)

# Get a single device by filter parameters (only status, mac, model, company_id allowed)
device = client.devices.get(mac="00:11:22:33:44:55")
device = client.devices.get(status="online", company_id=1)

# Filter devices (only status, mac, model, company_id parameters are supported)
filtered = client.devices.filter(status="online", company_id=1)
filtered = client.devices.filter(mac="00:11:22:33:44:55", model="RUTX11")

# Note: Only these filter parameters are supported by the API:
# - status: Device status (online, offline, not_activated)
# - mac: Device MAC address
# - model: Device model
# - company_id: Company ID

# Create a device (all required fields must be provided)
new_device = client.devices.create(
    company_id=123,
    device_series="rut",  # Options: rut, trb, tcr, tap, otd, swm
    serial="1234567890",
    mac="00:11:22:33:44:55",  # Required for RUT/TCR devices
    imei="111111111111111",  # Required for TRB devices
    password_confirmation="DevicePassword123",
    name="My Device",  # Optional
)

# Required fields:
# - company_id: Company ID that device belongs to
# - device_series: Device series type (rut, trb, tcr, tap, otd, swm)
# - serial: Device serial number
# - password_confirmation: Device password
#
# Conditional requirements:
# - mac: Required if device_series is "rut" or "tcr"
# - imei: Required if device_series is "trb"

# Enable monitoring on a device (after creation)
client.devices.enable_monitoring(123)

# Enable monitoring on multiple devices
client.devices.enable_monitoring([123, 456, 789])

# Disable monitoring
client.devices.disable_monitoring(123)
client.devices.disable_monitoring([123, 456])

# Generic method to set monitoring status
client.devices.set_monitoring(123, enabled=True)
client.devices.set_monitoring([123, 456], enabled=False)

# Update a device
updated = client.devices.update(789, {"name": "Updated Device"})

# Delete a device
client.devices.delete(789)

# Move a device to a different company
# WARNING: The move API endpoint does not actually work as expected
client.devices.move(789, company_id=2)

# Move multiple devices to a different company
# WARNING: The move API endpoint does not actually work as expected
client.devices.move([789, 790, 791], company_id=2)

# Assign tags to a device
client.devices.assign_tags(device_id=789, tag_ids=456)

# Assign multiple tags to a device
client.devices.assign_tags(device_id=789, tag_ids=[456, 789])
```

#### Device Commands

```python
# Execute a command for a specific device
result = client.device_commands.execute(
    device_id=789,
    command_data={"command": "reboot", "parameters": {}}
)

# Execute actions for multiple devices
action_result = client.device_commands.actions.execute(
    devices=[789, 790],
    action="reboot"
)

# Cancel device actions
client.device_commands.actions.cancel([789, 790])

# Get action logs
logs = client.device_commands.actions.logs(device_id=789, limit=10, offset=0)
```

### Low-Level API Access

For endpoints not covered by resources, use the low-level HTTP methods:

```python
# GET request
result = client.get("/custom/endpoint", params={"key": "value"})

# POST request
result = client.post("/custom/endpoint", json={"data": "value"})

# PUT request
result = client.put("/custom/endpoint", json={"data": "value"})

# DELETE request
result = client.delete("/custom/endpoint")
```

### Error Handling

The client raises specific exceptions for different error scenarios:

```python
from teltonika_rms import (
    RMSClient,
    RMSAuthenticationError,
    RMSNotFoundError,
    RMSPermissionError,
    RMSValidationError,
    RMSAPIError,
)

client = RMSClient(token="your_token")

try:
    company = client.companies.get(123)
except RMSNotFoundError:
    print("Company not found")
except RMSAuthenticationError:
    print("Authentication failed")
except RMSPermissionError:
    print("Permission denied")
except RMSValidationError as e:
    print(f"Validation error: {e.errors}")
except RMSAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

### Retry Logic

The client includes automatic retry logic with exponential backoff for connection errors:

```python
# Retry is enabled by default
client = RMSClient(token="your_token", enable_retry=True, max_retries=3)

# Disable retry for specific operations
client = RMSClient(token="your_token", enable_retry=False)
```

### Logging

The client supports configurable logging to help debug API interactions. You can set the log level in two ways:

#### Method 1: Client Parameter

```python
# Set log level when creating the client
client = RMSClient(token="your_token", log_level="DEBUG")
```

#### Method 2: Module-Level Function

```python
from teltonika_rms import set_log_level

# Set log level for all clients
set_log_level("DEBUG")
client = RMSClient(token="your_token")
```

#### Available Log Levels

- `DEBUG` - Detailed information including request/response bodies, headers, and status codes
- `INFO` - General informational messages
- `WARNING` - Warning messages (default)
- `ERROR` - Error messages only
- `CRITICAL` - Critical errors only

#### Debug Logging Output

When `DEBUG` level is enabled, you'll see detailed information about each API request:

```
DEBUG:teltonika_rms.client:GET https://rms.teltonika-networks.com/api/companies
DEBUG:teltonika_rms.client:Query parameters: {'limit': 10, 'offset': 0}
DEBUG:teltonika_rms.client:Request headers: {'Authorization': 'Bearer ***', 'Content-Type': 'application/json'}
DEBUG:teltonika_rms.client:Response status: 200
DEBUG:teltonika_rms.client:Response headers: {'Content-Type': 'application/json', 'Content-Length': '1234'}
DEBUG:teltonika_rms.client:Response body: {
  "data": [
    {
      "id": 1,
      "name": "Company 1"
    }
  ],
  "meta": {
    "total": 1
  }
}
```

#### Sensitive Data Masking

For security, sensitive data is automatically masked in logs:
- Authorization tokens: `Bearer abc123` → `Bearer ***`
- API keys and other sensitive headers are masked
- Request/response bodies are logged as-is (be careful with sensitive data in request bodies)

#### Example

```python
from teltonika_rms import RMSClient, set_log_level

# Enable debug logging
set_log_level("DEBUG")

client = RMSClient(token="your_token")

# All API calls will now log detailed information
companies = client.companies.all()
```

## Examples

### Working with Companies

```python
# List all companies
companies = client.companies.all()

# Filter companies by name and parent (client-side filtering)
# Note: This fetches all companies first, then filters locally
filtered = client.companies.filter(name="Subsidiary", parent_id=1)

# Create a new company
new_company = client.companies.create(
    name="New Subsidiary",
    parent_id=1
)

# Get company details
company = client.companies.get(new_company["id"])

# Update company
updated = client.companies.update(
    new_company["id"],
    {"name": "Updated Subsidiary Name"}
)

# Delete company
client.companies.delete(new_company["id"])
```

### Working with Devices

```python
# List all devices
devices = client.devices.all()

# Filter devices by MAC address
device = client.devices.filter(mac="00:11:22:33:44:55")[0]

# Get device details
device_info = client.devices.get(device["id"])

# Create a new device (all required fields must be provided)
new_device = client.devices.create(
    company_id=123,
    device_series="rut",
    serial="1234567890",
    mac="00:11:22:33:44:55",  # Required for RUT/TCR devices
    imei="111111111111111",  # Required for TRB devices
    password_confirmation="DevicePassword123",
    name="My New Device",  # Optional
)

# Enable monitoring on the newly created device
# Note: Extract device ID from response (structure may vary)
device_id = new_device.get("data", [{}])[0].get("id")
if device_id:
    client.devices.enable_monitoring(device_id)

# Execute a command on the device
result = client.device_commands.execute(
    device_id=device["id"],
    command_data={"command": "reboot"}
)
```

### Working with Tags

```python
# Create a tag
tag = client.tags.create(name="Production")

# Assign tag to a device
client.devices.assign_tags(device_id=123, tag_ids=tag["id"])

# Assign multiple tags to a device
client.devices.assign_tags(device_id=123, tag_ids=[tag["id"], another_tag["id"]])

# List all tags
all_tags = client.tags.all()
```
