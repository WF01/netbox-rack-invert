"""
Template extension tests for rack toggle button visibility.
"""

from dcim.choices import DeviceFaceChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Rack, RackReservation, Site
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from users.models import ObjectPermission
from utilities.permissions import resolve_permission_type

from ..template_content import RackConvertToDescendingUnitsButton
from ..testing import PluginTestCase


class RackTemplateContentTestCase(PluginTestCase):
    required_permissions = (
        "dcim.view_rack",
        "dcim.change_rack",
        "dcim.change_device",
        "dcim.change_rackreservation",
    )

    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()
        self.site = Site.objects.create(name="Template Site", slug="template-site")
        self.rack = Rack.objects.create(name="Template Rack", site=self.site, u_height=42)
        self.manufacturer = Manufacturer.objects.create(name="Template Mfg", slug="template-mfg")
        self.role = DeviceRole.objects.create(name="Template Role", slug="template-role", color="ff9900")
        self.device_type = DeviceType.objects.create(
            manufacturer=self.manufacturer,
            model="Template Device Type",
            slug="template-device-type",
            u_height=1,
        )

    def _render_buttons(self, obj=None, user=None):
        request = self.request_factory.get("/")
        request.user = self.user if user is None else user
        context = {"request": request}
        if obj is not None:
            context["object"] = obj
        extension = RackConvertToDescendingUnitsButton(
            context=context
        )
        return extension.buttons()

    def _grant_constrained_permission(self, permission_name, *, constraints):
        object_type, action = resolve_permission_type(permission_name)
        permission = ObjectPermission.objects.create(
            name=f"template-scoped-{permission_name}-{ObjectPermission.objects.count()}",
            constraints=constraints,
            actions=[action],
        )
        permission.users.add(self.user)
        permission.object_types.add(object_type)

    def test_button_not_rendered_for_non_rack_object(self):
        html = self._render_buttons(self.site)
        self.assertEqual(html, "")

    def test_button_not_rendered_without_permissions(self):
        html = self._render_buttons(self.rack)
        self.assertEqual(html, "")

    def test_button_not_rendered_for_unsaved_rack(self):
        unsaved_rack = Rack(name="Unsaved Rack", site=self.site, u_height=42)
        html = self._render_buttons(unsaved_rack)
        self.assertEqual(html, "")

    def test_button_not_rendered_without_object_in_context(self):
        html = self._render_buttons()
        self.assertEqual(html, "")

    def test_button_not_rendered_for_anonymous_user(self):
        html = self._render_buttons(self.rack, user=AnonymousUser())
        self.assertEqual(html, "")

    def test_button_not_rendered_if_any_permission_missing(self):
        for permission in self.required_permissions:
            with self.subTest(permission=permission):
                self.add_permissions(*self.required_permissions)
                self.remove_permissions(permission)
                self.user = self.user.__class__.objects.get(pk=self.user.pk)
                html = self._render_buttons(self.rack)
                if permission == "dcim.view_rack":
                    self.assertEqual(html, "")
                else:
                    self.assertIn("disabled", html)
                    self.assertIn("Permission issues prevent you from performing this action", html)

    def test_button_disabled_with_details_when_change_permissions_are_missing(self):
        self.add_permissions("dcim.view_rack")
        html = self._render_buttons(self.rack)
        self.assertIn("Switch to Descending Units", html)
        self.assertIn("disabled", html)
        self.assertIn("Permission issues prevent you from performing this action", html)
        self.assertIn("dcim.change_rack on this rack", html)
        self.assertIn("dcim.change_device", html)
        self.assertIn("dcim.change_rackreservation", html)

    def test_button_disabled_when_device_object_permission_is_missing(self):
        self.add_permissions(*self.required_permissions)
        Device.objects.create(
            name="allowed-template-device",
            device_type=self.device_type,
            role=self.role,
            site=self.site,
            rack=self.rack,
            position=42,
            face=DeviceFaceChoices.FACE_FRONT,
        )
        Device.objects.create(
            name="blocked-template-device",
            device_type=self.device_type,
            role=self.role,
            site=self.site,
            rack=self.rack,
            position=41,
            face=DeviceFaceChoices.FACE_FRONT,
        )

        self.remove_permissions("dcim.change_device")
        self._grant_constrained_permission(
            "dcim.change_device",
            constraints={"name": "allowed-template-device"},
        )

        html = self._render_buttons(self.rack)
        self.assertIn("disabled", html)
        self.assertIn("dcim.change_device on 1 mounted device(s)", html)

    def test_button_disabled_when_reservation_object_permission_is_missing(self):
        self.add_permissions(*self.required_permissions)
        RackReservation.objects.create(
            rack=self.rack,
            units=[42],
            user=self.user,
            description="allowed-template-reservation",
        )
        RackReservation.objects.create(
            rack=self.rack,
            units=[41],
            user=self.user,
            description="blocked-template-reservation",
        )

        self.remove_permissions("dcim.change_rackreservation")
        self._grant_constrained_permission(
            "dcim.change_rackreservation",
            constraints={"description": "allowed-template-reservation"},
        )

        html = self._render_buttons(self.rack)
        self.assertIn("disabled", html)
        self.assertIn("dcim.change_rackreservation on 1 reservation(s)", html)

    def test_button_rendered_with_required_permissions(self):
        self.add_permissions(*self.required_permissions)

        html = self._render_buttons(self.rack)

        self.assertIn("Switch to Descending Units", html)
        self.assertNotIn("disabled", html)
        self.assertIn(
            reverse(
                "plugins:netbox_rack_inverter:rack_toggle_units_order",
                kwargs={"pk": self.rack.pk},
            ),
            html,
        )

    def test_button_label_switches_for_descending_racks(self):
        self.add_permissions(*self.required_permissions)
        self.rack.desc_units = True
        self.rack.save()

        html = self._render_buttons(self.rack)

        self.assertIn("Switch to Ascending Units", html)
        self.assertNotIn("Switch to Descending Units", html)

    def test_button_appears_on_rack_detail_page(self):
        self.add_permissions(
            *self.required_permissions,
            "dcim.view_rack",
        )

        response = self.client.get(self.rack.get_absolute_url())
        self.assertHttpStatus(response, 200)
        html = response.content.decode("utf-8")

        self.assertIn("Switch to Descending Units", html)
        self.assertIn(
            reverse(
                "plugins:netbox_rack_inverter:rack_toggle_units_order",
                kwargs={"pk": self.rack.pk},
            ),
            html,
        )

    def test_button_does_not_appear_on_non_rack_detail_page(self):
        self.add_permissions(
            *self.required_permissions,
            "dcim.view_site",
        )

        response = self.client.get(self.site.get_absolute_url())
        self.assertHttpStatus(response, 200)
        html = response.content.decode("utf-8")

        self.assertNotIn("Switch to Descending Units", html)
        self.assertNotIn("Switch to Ascending Units", html)
