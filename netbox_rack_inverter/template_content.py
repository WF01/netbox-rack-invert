from dcim.models import Device, Rack, RackReservation
from django.urls import reverse
from netbox.plugins import PluginTemplateExtension


class RackConvertToDescendingUnitsButton(PluginTemplateExtension):
    # Keep compatibility with NetBox versions that inspect either attribute.
    model = "dcim.rack"
    models = ["dcim.rack"]

    @staticmethod
    def _get_missing_permissions(user, rack):
        missing_permissions = []

        if not user.has_perm("dcim.change_rack", rack):
            missing_permissions.append("dcim.change_rack on this rack")

        if not user.has_perm("dcim.change_device"):
            missing_permissions.append("dcim.change_device")
        else:
            blocked_devices = sum(
                1
                for device in Device.objects.filter(rack=rack, position__isnull=False).only("id")
                if not user.has_perm("dcim.change_device", device)
            )
            if blocked_devices:
                missing_permissions.append(f"dcim.change_device on {blocked_devices} mounted device(s)")

        if not user.has_perm("dcim.change_rackreservation"):
            missing_permissions.append("dcim.change_rackreservation")
        else:
            blocked_reservations = sum(
                1
                for reservation in RackReservation.objects.filter(rack=rack).only("id")
                if not user.has_perm("dcim.change_rackreservation", reservation)
            )
            if blocked_reservations:
                missing_permissions.append(
                    f"dcim.change_rackreservation on {blocked_reservations} reservation(s)"
                )

        return missing_permissions

    def buttons(self):
        rack = self.context.get("object")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not isinstance(rack, Rack) or rack.pk is None or user is None:
            return ""

        if not user.has_perm("dcim.view_rack", rack):
            return ""

        missing_permissions = self._get_missing_permissions(user, rack)
        disabled = bool(missing_permissions)
        permission_issue = ""
        if disabled:
            permission_issue = (
                "Permission issues prevent you from performing this action. Missing: "
                + "; ".join(missing_permissions)
            )

        return self.render(
            "netbox_rack_inverter/inc/rack_convert_to_descending_units_button.html",
            extra_context={
                "action_url": reverse(
                    "plugins:netbox_rack_inverter:rack_toggle_units_order",
                    kwargs={"pk": rack.pk},
                ),
                "rack": rack,
                "disabled": disabled,
                "permission_issue": permission_issue,
            },
        )


template_extensions = [RackConvertToDescendingUnitsButton]
