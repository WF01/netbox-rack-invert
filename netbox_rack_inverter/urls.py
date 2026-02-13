"""
URL patterns for Netbox Rack Inverter.

For more information on URL routing, see:
https://docs.netbox.dev/en/stable/plugins/development/views/#url-registration

For Django URL patterns, see:
https://docs.djangoproject.com/en/stable/topics/http/urls/
"""

from django.urls import path

from . import views

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
