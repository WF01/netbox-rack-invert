from django.urls import reverse
from dcim.models import Rack
from netbox.plugins import PluginTemplateExtension


class RackConvertToDescendingUnitsButton(PluginTemplateExtension):
    # Keep compatibility with NetBox versions that inspect either attribute.
    model = "dcim.rack"
    models = ["dcim.rack"]

    def buttons(self):
        rack = self.context.get("object")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not isinstance(rack, Rack) or rack.pk is None or user is None:
            return ""

        if not user.has_perm("dcim.change_rack", rack):
            return ""
        if not user.has_perm("dcim.change_device"):
            return ""
        if not user.has_perm("dcim.change_rackreservation"):
            return ""

        return self.render(
            "netbox_rack_inverter/inc/rack_convert_to_descending_units_button.html",
            extra_context={
                "action_url": reverse(
                    "plugins:netbox_rack_inverter:rack_toggle_units_order",
                    kwargs={"pk": rack.pk},
                ),
                "rack": rack,
            },
        )


template_extensions = [RackConvertToDescendingUnitsButton]
