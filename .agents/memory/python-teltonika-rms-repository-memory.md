# python-teltonika-rms repository memory

## Purpose

Python client for the Teltonika RMS API (`teltonika_rms` package).

## Key usage patterns

- Create `RMSClient(token=..., base_url=...)`.
- Use resource wrappers like `client.devices.get(...)` which delegate to `RMSClient.get/post/put/delete`.
- For endpoints not wrapped, call the low-level method directly: `client.get("/some/path", params={...})`.

## Conventions

- Resource methods should prefer query params over request bodies for `GET`.
- Datetime query params for historical monitoring endpoints must be formatted as `Y-m-d H:i:s` in RMS UTC.
- Naive `datetime` inputs are treated as UTC; aware datetimes are converted to UTC before formatting.

## Notable helpers

- `teltonika_rms.resources.devices.custom_data(...)`:
  - Calls `GET /devices/{id}/custom-data`
  - Accepts `start_date`/`end_date` as `datetime` and converts to RMS UTC strings.
  - Defaults `end_date` to current UTC time at call-time.

