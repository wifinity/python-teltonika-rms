# Agent guide — python-teltonika-rms

## What this repo is

Python client for the Teltonika RMS REST API. Resource wrappers cover devices,
tags, companies, and device commands; unwrapped endpoints use low-level
`client.get/post/put/delete`. Does **not** own MR provisioning workflows.

## Package layout (`teltonika_rms/`)

| Path | Purpose |
|------|---------|
| `teltonika_rms/client.py` | `RMSClient` — HTTP session and verb helpers |
| `teltonika_rms/auth.py` | API token authentication |
| `teltonika_rms/retry.py` | Retry policy for transient failures |
| `teltonika_rms/logging_config.py` | Request/response logging |
| `teltonika_rms/exceptions.py` | `RMSNotFoundError`, etc. |
| `teltonika_rms/resources/base.py` | Shared resource behavior |
| `teltonika_rms/resources/devices.py` | Device CRUD + `custom_data(...)` helper |
| `teltonika_rms/resources/tags.py` | Tag management |
| `teltonika_rms/resources/companies.py` | Company-scoped operations |
| `teltonika_rms/resources/device_commands.py` | Device command dispatch |

Repo root: `tests/`, `Makefile`, `pyproject.toml`.

## Conventions

- **Entry point:** `RMSClient(token=..., base_url=...)`.
- **Resource methods** delegate to `RMSClient.get/post/put/delete`.
- **GET requests:** prefer query params over request bodies.
- **Datetime params** for monitoring endpoints: format `Y-m-d H:i:s` in RMS UTC; naive datetimes treated as UTC.
- **Unwrapped endpoints:** call `client.get("/path", params={...})` directly.

## Where to look

- **Index:** [INDEX.md](INDEX.md)
- **Memory:** [.agents/memory/python-teltonika-rms-repository-memory.md](../.agents/memory/python-teltonika-rms-repository-memory.md)

## Starting a new task

1. Read `.agents/memory/python-teltonika-rms-repository-memory.md`.
2. Run `make tests` before opening a PR.

## Testing

- Full suite: `make tests` (`lint`, `type-check`, `unit-tests`).
- Tests in `tests/` with `pytest`.
