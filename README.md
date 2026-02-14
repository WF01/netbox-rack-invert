![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/ffe094ad1d3ac054adccb854631a82ec5816ddd7/uploads/2026-02-13T14-26-33-645Z-t3g8wjwee.gif)

`netbox-rack-inverter` flips rack numbering direction (`ascending <-> descending`) while preserving physical rack layout (i.e., reorders devices to maintain their 'physical location'

## Demo

![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/41a949c9c76ba03c2681d6810038890ea0c74264/uploads/2026-02-13T14-27-29-566Z-st51dm5t5.gif)

Allows rack inversion through transforming device (RUs) - designed to work with all RU / rack sizes.
Largely untested - please use at your own risk; tested on a local docker instance without issue.

## What It Does

This plugin adds one action button on rack detail pages (`/dcim/racks/<id>/`) to toggle rack unit order while preserving physical placement.

When toggled, it updates:

- `Rack.desc_units`
- `Device.position` (mounted devices only)
- `RackReservation.units`

No objects are recreated. IDs, relationships, tags, and custom fields remain intact.

## Caveats

This plugin is intentionally narrow: it only toggles rack unit orientation and remaps `Device.position` plus `RackReservation.units` to preserve physical placement.

Before using in production:

- Test on dummy/non-production data first
- Back up your NetBox database
- Verify the acting user has all required permissions (including object-level permissions)
- Validate rack data quality (invalid existing positions/reservations will cause safe aborts)

The action is designed to be safe and non-destructive, but any bulk positional change should still be treated as an operational change.

## Safety Guarantees

- Changes run inside one `transaction.atomic()` block
- `select_for_update()` row locks are used for rack, devices, and reservations
- If any affected object has invalid unit placement, the operation is aborted safely
- Permissions are enforced both in UI and server-side, including object-level checks for each affected device/reservation
- Only `POST` is allowed on the action endpoint
- If permissions are missing, the button is shown as disabled with a tooltip explaining what is missing

## Compatibility

- Plugin: `0.1.2`
- NetBox: `4.5.x`
- Python: `3.12+`

## Installation

### Option A (recommended): install from a pinned release tag

```bash
<NETBOX_VENV_PYTHON> -m pip install "git+https://github.com/WF01/netbox-rack-invert@v0.1.2"
```

### Option B: install from `main`

```bash
<NETBOX_VENV_PYTHON> -m pip install "git+https://github.com/WF01/netbox-rack-invert@main"
```

### Option C: install via requirements file

```bash
<NETBOX_VENV_PYTHON> -m pip install \
  -r https://raw.githubusercontent.com/WF01/netbox-rack-invert/main/requirements/netbox-plugin.txt
```

### Option D: helper installer script

```bash
NETBOX_ROOT=<NETBOX_ROOT> ./scripts/install-netbox-plugin.sh
```

To persist plugin installation across NetBox upgrades:

```bash
PERSIST_LOCAL_REQUIREMENTS=1 NETBOX_ROOT=<NETBOX_ROOT> ./scripts/install-netbox-plugin.sh
```

## Enable Plugin

Add to `configuration/plugins.py`:

```python
PLUGINS = [
    "netbox_rack_inverter",
]

PLUGINS_CONFIG = {
    "netbox_rack_inverter": {},
}
```

Then run:

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> migrate
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> collectstatic --no-input
systemctl restart netbox netbox-rq
```

## Docker Install

Use a plugin Dockerfile and install from Git:

```dockerfile
FROM netboxcommunity/netbox:v4.5-4.0.0
RUN /usr/local/bin/uv pip install "git+https://github.com/WF01/netbox-rack-invert@v0.1.2"
```

Then rebuild and start:

```bash
docker compose build --no-cache
docker compose up -d
```

## Offline / Air-Gapped Install

Build wheel:

```bash
python -m pip install --upgrade build
python -m build
```

Install wheel:

```bash
<NETBOX_VENV_PYTHON> -m pip install /path/to/netbox_rack_inverter-0.1.2-py3-none-any.whl
```

Then enable the plugin and run migrations as shown above.

## Permissions Required

- `dcim.view_rack` on the rack
- `dcim.change_rack` on the rack
- `dcim.change_device` on each affected device
- `dcim.change_rackreservation` on each affected reservation

If any required permission is missing, the action is denied.
Users with `dcim.view_rack` but missing required change permissions will see a disabled action button with a tooltip that lists missing permissions.

## Scope and Limits

- The action button appears only on rack detail pages
- No standalone plugin CRUD views
- No standalone plugin REST API endpoints
- Remap scope is intentionally narrow (`Device.position`, `RackReservation.units`)

## Use

1. Open a rack detail page.
2. Click `Switch to Descending Units` or `Switch to Ascending Units`.
3. Confirm.

Running the action again toggles back to the previous orientation.

## Migration Notes

This plugin intentionally defines no custom models.

Compatibility migrations include safe legacy cleanup behavior:

- Fresh installs create no plugin model tables
- Legacy scaffold tables are removed only when empty
- Non-empty legacy scaffold tables are left untouched to avoid destructive changes

## Testing

Run the full plugin suite:

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> test netbox_rack_inverter.tests -v 2
```

Latest verified run (February 14, 2026): `46 passed, 0 failed`.

## License

MIT
