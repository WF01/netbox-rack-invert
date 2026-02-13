![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/ffe094ad1d3ac054adccb854631a82ec5816ddd7/uploads/2026-02-13T14-26-33-645Z-t3g8wjwee.gif)

`netbox-rack-inverter` flips rack numbering direction (`ascending <-> descending`) while preserving physical layout.

## Usage

![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/41a949c9c76ba03c2681d6810038890ea0c74264/uploads/2026-02-13T14-27-29-566Z-st51dm5t5.gif)

 Largely untested, use at your own risk on dummy data, feel free to add features / report bugs (and fix them) etc.

## Scope

This plugin is intentionally narrow:

- It adds a single action button on rack detail pages only (`/dcim/racks/<id>/`).
- It does not expose standalone plugin CRUD pages.
- It does not expose standalone plugin API endpoints.

## Behavior

When toggled, the plugin:

1. Flips `Rack.desc_units`.
2. Remaps mounted `Device.position` values.
3. Remaps `RackReservation.units`.

Writes run in one `transaction.atomic()` block with row-level locking (`select_for_update`) on the rack, affected devices, and reservations.

## Permission Model

The button is shown only when the current user has all required permissions:

- `dcim.change_rack` (object permission on the rack)
- `dcim.change_device`
- `dcim.change_rackreservation`

The view enforces the same permissions server-side.

## Data Safety

The toggle updates only:

- `Rack.desc_units`
- `Device.position`
- `RackReservation.units`

Objects are not recreated. IDs, relationships, tags, and `custom_field_data` remain intact.

## Compatibility

- Plugin: `0.1.2`
- NetBox: `4.5.x`
- Python: `3.12+`

## Installation

### NetBox Docker (GitHub tag)

Create `Dockerfile-Plugins` in `netbox-docker`:

```dockerfile
FROM netboxcommunity/netbox:v4.5-4.0.0
RUN /usr/local/bin/uv pip install "git+https://github.com/WF01/netbox-rack-invert@v0.1.2"
```

Point `netbox`, `netbox-worker`, and `netbox-housekeeping` to this Dockerfile in your compose override.

Enable plugin in `configuration/plugins.py`:

```python
PLUGINS = [
    "netbox_rack_inverter",
]

PLUGINS_CONFIG = {
    "netbox_rack_inverter": {},
}
```

Build and start:

```bash
docker compose build --no-cache
docker compose up -d
```

### NetBox Docker (local source checkout)

Place this repo at `netbox-docker/plugins/netbox-rack-inverter`, then use:

```dockerfile
FROM netboxcommunity/netbox:v4.5-4.0.0
RUN rm -rf /plugins/netbox-rack-inverter
COPY ./plugins /plugins
RUN /usr/local/bin/uv pip install -e /plugins/netbox-rack-inverter
```

The `rm -rf` step avoids stale deleted files persisting between rebuilds.

### Non-Docker NetBox

Install into NetBox venv:

```bash
/opt/netbox/venv/bin/python -m pip install "git+https://github.com/WF01/netbox-rack-invert@v0.1.2"
```

Enable plugin config (same `PLUGINS` / `PLUGINS_CONFIG` block), then:

```bash
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py migrate
systemctl restart netbox netbox-rq
```

## Offline / Air-Gapped Install

Build artifacts on an internet-connected machine:

```bash
python -m pip install --upgrade build
python -m build
```

Install wheel on target host:

```bash
/opt/netbox/venv/bin/python -m pip install /path/to/netbox_rack_inverter-0.1.2-py3-none-any.whl
```

Then enable plugin config, run migrations, and restart services.

## Usage

1. Open a rack detail page.
2. Click `Switch to Descending Units` or `Switch to Ascending Units`.
3. Confirm.

Toggling again returns to the previous numbering orientation with physical layout preserved.

## Caveats

- Remap scope is currently:
  - `Device.position`
  - `RackReservation.units`
- Other rack-unit-positioned object types are not remapped.
- Back up your NetBox database before bulk changes.

## Test Coverage

Current automated coverage includes:

- Round-trip toggle on mixed `1U` / `2U` / `4U` devices
- Non-default `starting_unit`
- Racks with reservations and without reservations
- Reversible remap logic
- Preservation of device relationships and custom field data
- Rack-only button rendering and permission-gated visibility

Latest local run (February 14, 2026):

- Command: `python /opt/netbox/netbox/manage.py test netbox_rack_inverter.tests -v 2`
- Result: `24 passed, 0 failed`

## License

MIT
