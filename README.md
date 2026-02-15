![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/ffe094ad1d3ac054adccb854631a82ec5816ddd7/uploads/2026-02-13T14-26-33-645Z-t3g8wjwee.gif)

`netbox-rack-inverter` flips rack numbering direction (`ascending <-> descending`) while preserving physical rack layout (i.e., reorders devices to maintain their 'physical location').

In theory works with all rack sizes, device sizes and is non-destructive. May fix bugs if there's any interest.

## Demo

![header](https://raw.githubusercontent.com/free-whiteboard-online/Free-Erasorio-Alternative-for-Collaborative-Design/41a949c9c76ba03c2681d6810038890ea0c74264/uploads/2026-02-13T14-27-29-566Z-st51dm5t5.gif)

Grayed out if a permissions issue exists, otherwise allows a user to toggle individual racks via their [rackid] page.

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

- Plugin: `0.1.3`
- NetBox: `4.5.x`
- Python: `3.12+`

## Installation

### Quick choose (pick one)

- **Bare-metal / VM NetBox install** (systemd services): use **Path A** or **Path B** below.
- **netbox-docker**: use **Path C** below (recommended for Docker users).
- **Air-gapped / offline**: use **Path D** below.

### Common placeholders

- `<NETBOX_VENV_PYTHON>` = Python from the same virtualenv NetBox uses.
  - Typical: `/opt/netbox/venv/bin/python`
- `<NETBOX_MANAGE_PY>` = NetBox `manage.py` path.
  - Typical: `/opt/netbox/netbox/manage.py`

---

### Path A (recommended for bare-metal): pinned tag install

```bash
<NETBOX_VENV_PYTHON> -m pip install "git+https://github.com/WF01/netbox-rack-invert@v0.1.3"
```

### Path B (bare-metal helper script): auto-detect install

```bash
./scripts/install-netbox-plugin.sh
```

What the helper script does automatically:

- Looks for Python in:
  - `${NETBOX_ROOT}/venv/bin/python`
  - `/opt/netbox/venv/bin/python`
  - `/usr/local/netbox/venv/bin/python`
  - then `python3` / `python` fallback
- Looks for `manage.py` in:
  - `${NETBOX_ROOT}/netbox/manage.py`
  - `/opt/netbox/netbox/manage.py`
  - `/usr/local/netbox/netbox/manage.py`
- Installs from `requirements/netbox-plugin.txt`

If your paths are custom, force explicit values:

```bash
NETBOX_PYTHON=<NETBOX_VENV_PYTHON> NETBOX_MANAGE_PY=<NETBOX_MANAGE_PY> NETBOX_ROOT=<NETBOX_ROOT> ./scripts/install-netbox-plugin.sh
```

To persist plugin install across NetBox upgrades:

```bash
PERSIST_LOCAL_REQUIREMENTS=1 NETBOX_ROOT=<NETBOX_ROOT> ./scripts/install-netbox-plugin.sh
```

### Path C (netbox-docker): easiest repeatable setup

If `docker compose build` says **"No services to build"**, your compose files are image-only. Add a plugin build layer:

1. Create `plugin_requirements.txt` in your netbox-docker root:

```txt
git+https://github.com/WF01/netbox-rack-invert@v0.1.3
```

2. Create `Dockerfile-Plugins` in your netbox-docker root:

```dockerfile
FROM netboxcommunity/netbox:latest
COPY plugin_requirements.txt /opt/netbox/plugin_requirements.txt
RUN /usr/local/bin/uv pip install -r /opt/netbox/plugin_requirements.txt
```

3. Create or update `docker-compose.override.yml`:

```yaml
services:
  netbox:
    build:
      context: .
      dockerfile: Dockerfile-Plugins
    image: netboxcommunity/netbox:local-plugins
  netbox-worker:
    image: netboxcommunity/netbox:local-plugins
  netbox-housekeeping:
    image: netboxcommunity/netbox:local-plugins
```

4. Rebuild/start:

```bash
docker compose build --no-cache
docker compose up -d
```

5. Verify package in container:

```bash
docker compose exec netbox python -m pip show netbox-rack-inverter
```

### Path D (offline / air-gapped)

Build wheel on a connected host:

```bash
python -m pip install --upgrade build
python -m build
```

Install wheel on NetBox host:

```bash
<NETBOX_VENV_PYTHON> -m pip install /path/to/netbox_rack_inverter-0.1.3-py3-none-any.whl
```

---

### After any installation path: enable + finalize

1. Add plugin to `configuration/plugins.py`:

```python
PLUGINS = [
    "netbox_rack_inverter",
]

PLUGINS_CONFIG = {
    "netbox_rack_inverter": {},
}
```

2. Apply migrations/static:

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> migrate
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> collectstatic --no-input
```

3. Restart services:

- Bare-metal: `systemctl restart netbox netbox-rq`
- Docker: `docker compose restart netbox netbox-worker netbox-housekeeping`

### Post-install smoke checks

- Package installed:
  - Bare-metal: `<NETBOX_VENV_PYTHON> -m pip show netbox-rack-inverter`
  - Docker: `docker compose exec netbox python -m pip show netbox-rack-inverter`
- Plugin loaded: check NetBox/worker logs for startup errors.
- UI check: open a rack page and confirm the toggle action appears.

### Optional validation tests

```bash
<NETBOX_VENV_PYTHON> <NETBOX_MANAGE_PY> test netbox_rack_inverter.tests -v 2
```

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
