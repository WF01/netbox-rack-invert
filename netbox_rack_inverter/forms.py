"""
Forms for Netbox Rack Inverter.

For more information on NetBox forms, see:
https://docs.netbox.dev/en/stable/plugins/development/forms/
"""

from netbox.forms import NetBoxModelForm

from .models import Rack_Inverter


class Rack_InverterForm(NetBoxModelForm):
    class Meta:
        model = Rack_Inverter
        fields = ("name", "tags")
