"""
Tables for Netbox Rack Inverter.

For more information on NetBox tables, see:
https://docs.netbox.dev/en/stable/plugins/development/tables/

For django-tables2 documentation, see:
https://django-tables2.readthedocs.io/
"""

import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import Rack_Inverter


class Rack_InverterTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Rack_Inverter
        fields = ("pk", "id", "name", "actions")
        default_columns = ("name",)
