"""
Filtersets for Netbox Rack Inverter.

For more information on NetBox filtersets, see:
https://docs.netbox.dev/en/stable/plugins/development/filtersets/

For django-filters documentation, see:
https://django-filter.readthedocs.io/
"""

from netbox.filtersets import NetBoxModelFilterSet

from .models import Rack_Inverter


class Rack_InverterFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Rack_Inverter
        fields = ("id", "name")

    def search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)
