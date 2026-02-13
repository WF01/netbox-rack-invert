"""
Models for Netbox Rack Inverter.

For more information on NetBox models, see:
https://docs.netbox.dev/en/stable/plugins/development/models/

For NetBox model features (tags, custom fields, change logging, etc.), see:
https://docs.netbox.dev/en/stable/development/models/#netbox-model-features
"""

from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class Rack_Inverter(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        app_label = "netbox_rack_inverter"
        ordering = ("name",)
        verbose_name_plural = "Rack_Inverters"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # The plugin has no standalone CRUD UI; direct to the rack list.
        return reverse("dcim:rack_list")
