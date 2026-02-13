"""
API viewsets for Netbox Rack Inverter.

For more information on NetBox REST API viewsets, see:
https://docs.netbox.dev/en/stable/plugins/development/rest-api/#viewsets

For Django REST Framework viewsets, see:
https://www.django-rest-framework.org/api-guide/viewsets/
"""

from netbox.api.viewsets import NetBoxModelViewSet

from ..models import Rack_Inverter
from .serializers import Rack_InverterSerializer


class Rack_InverterViewSet(NetBoxModelViewSet):
    queryset = Rack_Inverter.objects.all()
    serializer_class = Rack_InverterSerializer

