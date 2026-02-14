"""
URL patterns for Netbox Rack Inverter.

For more information on URL routing, see:
https://netboxlabs.com/docs/netbox/plugins/development/views/

For Django URL patterns, see:
https://docs.djangoproject.com/en/stable/topics/http/urls/
"""

from django.urls import path

from . import views

app_name = "netbox_rack_inverter"

urlpatterns = (
    path(
        "racks/<int:pk>/toggle-units-order/",
        views.RackToggleUnitsOrderView.as_view(),
        name="rack_toggle_units_order",
    ),
    path(
        "racks/<int:pk>/convert-to-descending-units/",
        views.RackToggleUnitsOrderView.as_view(),
        name="rack_convert_to_descending_units",
    ),
)
