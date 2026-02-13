"""
Views for Netbox Rack Inverter.

For more information on NetBox views, see:
https://docs.netbox.dev/en/stable/plugins/development/views/

For generic view classes, see:
https://docs.netbox.dev/en/stable/development/views/
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from dcim.models import Device, Rack, RackReservation


def remap_position_for_descending_units(
    *,
    position: int,
    device_height: int,
    rack_starting_unit: int,
    rack_u_height: int,
) -> int:
    """
    Convert an ascending rack position to its descending equivalent while
    preserving physical placement within the rack.
    """
    top_unit = rack_starting_unit + rack_u_height - 1
    return top_unit - (position - rack_starting_unit) - device_height + 1


class RackToggleUnitsOrderView(View):
    http_method_names = ["post"]

    def post(self, request, pk):
        rack = get_object_or_404(Rack, pk=pk)

        if not request.user.has_perm("dcim.change_rack", rack):
            raise PermissionDenied("You do not have permission to modify this rack.")
        if not request.user.has_perm("dcim.change_device"):
            raise PermissionDenied("You do not have permission to modify devices.")
        if not request.user.has_perm("dcim.change_rackreservation"):
            raise PermissionDenied("You do not have permission to modify rack reservations.")

        with transaction.atomic():
            # Lock the rack and all affected rows to prevent concurrent toggles
            # from producing inconsistent position calculations.
            rack = Rack.objects.select_for_update().get(pk=pk)
            starting_unit = rack.starting_unit or 1
            rack_u_height = rack.u_height
            target_desc_units = not rack.desc_units

            devices = list(
                Device.objects.filter(rack=rack, position__isnull=False)
                .select_for_update()
                .select_related("device_type")
            )
            reservations = list(
                RackReservation.objects.filter(rack=rack)
                .select_for_update()
            )

            remapped_device_positions = {}
            for device in devices:
                device_height = max(device.device_type.u_height, 1)
                remapped_device_positions[device.id] = remap_position_for_descending_units(
                    position=device.position,
                    device_height=device_height,
                    rack_starting_unit=starting_unit,
                    rack_u_height=rack_u_height,
                )

            remapped_reservation_units = {}
            for reservation in reservations:
                remapped_units = sorted(
                    remap_position_for_descending_units(
                        position=unit,
                        device_height=1,
                        rack_starting_unit=starting_unit,
                        rack_u_height=rack_u_height,
                    )
                    for unit in (reservation.units or [])
                )
                remapped_reservation_units[reservation.id] = remapped_units

            if remapped_device_positions:
                for device in devices:
                    device.position = None
                    device.save()
                for device in devices:
                    device.position = remapped_device_positions[device.id]
                    device.save()

            for reservation in reservations:
                reservation.units = remapped_reservation_units[reservation.id]
                reservation.save()

            rack.desc_units = target_desc_units
            rack.save()

        target_mode_label = "descending" if target_desc_units else "ascending"
        messages.success(
            request,
            (
                f"Switched {rack} to {target_mode_label} units while preserving layout for "
                f"{len(devices)} devices and {len(reservations)} reservations."
            ),
        )
        return redirect(rack.get_absolute_url())
