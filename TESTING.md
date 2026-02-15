# Testing Guide

This plugin is tested with Django/NetBox test cases under `netbox_rack_inverter/tests/`.

## Test Suites

- `netbox_rack_inverter/tests/test_rack_unit_remap.py`
  - Pure remap math and unit-span validation
- `netbox_rack_inverter/tests/test_toggle_units_order.py`
  - Integration tests for rack toggle behavior, safety, reversibility, and permissions
- `netbox_rack_inverter/tests/test_template_content.py`
  - Rack-page button rendering and permission gating

## Run Tests

Run from a NetBox environment where the plugin is installed and enabled:

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> test netbox_rack_inverter.tests -v 2
```

Run a single test module:

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> test netbox_rack_inverter.tests.test_toggle_units_order -v 2
```

## What Is Covered

- Round-trip toggles across mixed-height devices (`1U`, `2U`, `4U`)
- Non-default rack `starting_unit`
- Rack reservations remap + metadata preservation
- Atomic rollback when invalid unit positions are present
- Rack-only UI button visibility
- Permission enforcement (including constrained object permissions)
- No changes to unrelated racks or unpositioned devices


## Installer Validation

To validate installer behavior without a full NetBox deployment, run:

```bash
bash ./scripts/test-install-netbox-plugin.sh
```

This covers:

- Auto-detection success using a simulated NetBox layout
- Explicit `NETBOX_PYTHON` / `NETBOX_MANAGE_PY` override success
- `uv` fallback path when `pip` is unavailable
- Failure mode and actionable message when `manage.py` is missing
- `PERSIST_LOCAL_REQUIREMENTS` idempotency (no duplicate entries)
