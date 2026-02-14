"""
Integration tests for rack units order toggling.
"""

from dcim.choices import DeviceFaceChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Rack, RackReservation, Site
from django.contrib.messages import get_messages
from django.urls import reverse
from users.models import ObjectPermission
from utilities.permissions import resolve_permission_type

from ..testing import PluginTestCase
from ..views import remap_position_for_descending_units


class RackToggleUnitsOrderViewTestCase(PluginTestCase):
    action_permissions = (
        "dcim.view_rack",
        "dcim.change_rack",
        "dcim.change_device",
        "dcim.change_rackreservation",
    )

    required_permissions = action_permissions

    def setUp(self):
        super().setUp()
        self.add_permissions(*self.required_permissions)

        self.site = Site.objects.create(name="Toggle Site", slug="toggle-site")
        self.manufacturer = Manufacturer.objects.create(name="Toggle Mfg", slug="toggle-mfg")
        self.role = DeviceRole.objects.create(name="Toggle Role", slug="toggle-role", color="00ff00")
        self.type_1u = DeviceType.objects.create(
            manufacturer=self.manufacturer,
            model="Toggle 1U",
            slug="toggle-1u",
            u_height=1,
        )
        self.type_2u = DeviceType.objects.create(
            manufacturer=self.manufacturer,
            model="Toggle 2U",
            slug="toggle-2u",
            u_height=2,
        )
        self.type_4u = DeviceType.objects.create(
            manufacturer=self.manufacturer,
            model="Toggle 4U",
            slug="toggle-4u",
            u_height=4,
        )

    def _toggle(self, rack, follow=False, route_name="plugins:netbox_rack_inverter:rack_toggle_units_order"):
        url = reverse(
            route_name,
            kwargs={"pk": rack.pk},
        )
        return self.client.post(url, follow=follow)

    def _create_device(self, *, rack, name, device_type, position):
        return Device.objects.create(
            name=name,
            device_type=device_type,
            role=self.role,
            site=self.site,
            rack=rack,
            position=position,
            face=DeviceFaceChoices.FACE_FRONT,
        )

    def _get_message_texts(self, response):
        return [m.message for m in get_messages(response.wsgi_request)]

    def _grant_constrained_permission(self, permission_name, *, constraints):
        object_type, action = resolve_permission_type(permission_name)
        permission = ObjectPermission.objects.create(
            name=f"scoped-{permission_name}-{ObjectPermission.objects.count()}",
            constraints=constraints,
            actions=[action],
        )
        permission.users.add(self.user)
        permission.object_types.add(object_type)

    def test_round_trip_toggle_mixed_1u_2u_4u_devices(self):
        rack = Rack.objects.create(name="Rack-Mixed", site=self.site, u_height=48, starting_unit=1)
        one_u = self._create_device(rack=rack, name="one-u", device_type=self.type_1u, position=48)
        two_u = self._create_device(rack=rack, name="two-u", device_type=self.type_2u, position=30)
        four_u = self._create_device(rack=rack, name="four-u", device_type=self.type_4u, position=6)

        original_positions = {
            one_u.id: one_u.position,
            two_u.id: two_u.position,
            four_u.id: four_u.position,
        }

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        self.assertTrue(rack.desc_units)

        one_u.refresh_from_db()
        two_u.refresh_from_db()
        four_u.refresh_from_db()

        self.assertEqual(
            one_u.position,
            remap_position_for_descending_units(
                position=original_positions[one_u.id],
                device_height=1,
                rack_starting_unit=1,
                rack_u_height=48,
            ),
        )
        self.assertEqual(
            two_u.position,
            remap_position_for_descending_units(
                position=original_positions[two_u.id],
                device_height=2,
                rack_starting_unit=1,
                rack_u_height=48,
            ),
        )
        self.assertEqual(
            four_u.position,
            remap_position_for_descending_units(
                position=original_positions[four_u.id],
                device_height=4,
                rack_starting_unit=1,
                rack_u_height=48,
            ),
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        self.assertFalse(rack.desc_units)

        one_u.refresh_from_db()
        two_u.refresh_from_db()
        four_u.refresh_from_db()

        self.assertEqual(one_u.position, original_positions[one_u.id])
        self.assertEqual(two_u.position, original_positions[two_u.id])
        self.assertEqual(four_u.position, original_positions[four_u.id])

    def test_toggle_with_non_default_starting_unit(self):
        rack = Rack.objects.create(name="Rack-Start10", site=self.site, u_height=12, starting_unit=10)
        top = self._create_device(rack=rack, name="top-1u", device_type=self.type_1u, position=21)
        middle = self._create_device(rack=rack, name="middle-2u", device_type=self.type_2u, position=15)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        top.refresh_from_db()
        middle.refresh_from_db()

        self.assertTrue(rack.desc_units)
        self.assertEqual(top.position, 10)
        self.assertEqual(
            middle.position,
            remap_position_for_descending_units(
                position=15,
                device_height=2,
                rack_starting_unit=10,
                rack_u_height=12,
            ),
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        top.refresh_from_db()
        middle.refresh_from_db()

        self.assertFalse(rack.desc_units)
        self.assertEqual(top.position, 21)
        self.assertEqual(middle.position, 15)

    def test_toggle_rack_with_reservations_round_trip(self):
        rack = Rack.objects.create(name="Rack-Reservations", site=self.site, u_height=10, starting_unit=1)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[9, 10],
            user=self.user,
            description="Top reservation",
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        reservation.refresh_from_db()

        self.assertTrue(rack.desc_units)
        self.assertEqual(reservation.units, [1, 2])

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        reservation.refresh_from_db()

        self.assertFalse(rack.desc_units)
        self.assertEqual(reservation.units, [9, 10])

    def test_toggle_rack_with_no_reservations(self):
        rack = Rack.objects.create(name="Rack-NoReservations", site=self.site, u_height=42, starting_unit=1)
        device = self._create_device(rack=rack, name="device-no-res", device_type=self.type_1u, position=42)

        self.assertEqual(RackReservation.objects.filter(rack=rack).count(), 0)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        device.refresh_from_db()

        self.assertTrue(rack.desc_units)
        self.assertEqual(device.position, 1)

    def test_toggle_empty_rack_only_flips_desc_units(self):
        rack = Rack.objects.create(name="Rack-Empty", site=self.site, u_height=42, starting_unit=1)
        self.assertEqual(Device.objects.filter(rack=rack).count(), 0)
        self.assertEqual(RackReservation.objects.filter(rack=rack).count(), 0)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        rack.refresh_from_db()
        self.assertTrue(rack.desc_units)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        rack.refresh_from_db()
        self.assertFalse(rack.desc_units)

    def test_toggle_requires_all_permissions(self):
        for permission in self.action_permissions:
            with self.subTest(permission=permission):
                rack = Rack.objects.create(
                    name=f"Rack-Permissions-{permission}",
                    site=self.site,
                    u_height=42,
                    starting_unit=1,
                )
                self.remove_permissions(permission)
                response = self._toggle(rack)
                self.assertHttpStatus(response, 403)
                rack.refresh_from_db()
                self.assertFalse(rack.desc_units)
                self.add_permissions(permission)

    def test_toggle_denies_when_user_cannot_change_all_devices(self):
        rack = Rack.objects.create(name="Rack-ObjectPerm-Device", site=self.site, u_height=10, starting_unit=1)
        allowed = self._create_device(rack=rack, name="allowed-device", device_type=self.type_1u, position=10)
        blocked = self._create_device(rack=rack, name="blocked-device", device_type=self.type_1u, position=9)

        self.remove_permissions("dcim.change_device")
        self._grant_constrained_permission("dcim.change_device", constraints={"name": "allowed-device"})

        response = self._toggle(rack)
        self.assertHttpStatus(response, 403)

        rack.refresh_from_db()
        allowed.refresh_from_db()
        blocked.refresh_from_db()
        self.assertFalse(rack.desc_units)
        self.assertEqual(allowed.position, 10)
        self.assertEqual(blocked.position, 9)

    def test_toggle_denies_when_user_cannot_change_all_reservations(self):
        rack = Rack.objects.create(name="Rack-ObjectPerm-Reservation", site=self.site, u_height=10, starting_unit=1)
        reservation_allowed = RackReservation.objects.create(
            rack=rack,
            units=[10],
            user=self.user,
            description="allowed-reservation",
        )
        reservation_blocked = RackReservation.objects.create(
            rack=rack,
            units=[9],
            user=self.user,
            description="blocked-reservation",
        )

        self.remove_permissions("dcim.change_rackreservation")
        self._grant_constrained_permission(
            "dcim.change_rackreservation",
            constraints={"description": "allowed-reservation"},
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 403)

        rack.refresh_from_db()
        reservation_allowed.refresh_from_db()
        reservation_blocked.refresh_from_db()
        self.assertFalse(rack.desc_units)
        self.assertEqual(reservation_allowed.units, [10])
        self.assertEqual(reservation_blocked.units, [9])

    def test_toggle_rejects_invalid_device_position(self):
        rack = Rack.objects.create(name="Rack-InvalidDevice", site=self.site, u_height=10, starting_unit=1)
        device = self._create_device(rack=rack, name="invalid-device", device_type=self.type_1u, position=10)
        Device.objects.filter(pk=device.pk).update(position=11)

        response = self._toggle(rack, follow=True)
        self.assertHttpStatus(response, 200)
        messages = self._get_message_texts(response)

        self.assertTrue(any("Cannot switch rack unit order" in m for m in messages))

        rack.refresh_from_db()
        device.refresh_from_db()
        self.assertFalse(rack.desc_units)
        self.assertEqual(device.position, 11)

    def test_toggle_rejects_invalid_reservation_units(self):
        rack = Rack.objects.create(name="Rack-InvalidReservation", site=self.site, u_height=10, starting_unit=1)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[9, 10],
            user=self.user,
            description="Invalid reservation seed",
        )
        RackReservation.objects.filter(pk=reservation.pk).update(units=[9, 11])

        response = self._toggle(rack, follow=True)
        self.assertHttpStatus(response, 200)
        messages = self._get_message_texts(response)

        self.assertTrue(any("Cannot switch rack unit order" in m for m in messages))

        rack.refresh_from_db()
        reservation.refresh_from_db()
        self.assertFalse(rack.desc_units)
        self.assertEqual(reservation.units, [9, 11])

    def test_invalid_device_aborts_all_changes_including_valid_objects(self):
        rack = Rack.objects.create(name="Rack-Abort-All", site=self.site, u_height=12, starting_unit=1)
        valid_device = self._create_device(rack=rack, name="valid", device_type=self.type_2u, position=5)
        invalid_device = self._create_device(rack=rack, name="invalid", device_type=self.type_1u, position=12)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[1, 2],
            user=self.user,
            description="Keep this unchanged on abort",
        )
        Device.objects.filter(pk=invalid_device.pk).update(position=13)

        response = self._toggle(rack, follow=True)
        self.assertHttpStatus(response, 200)
        messages = self._get_message_texts(response)
        self.assertTrue(any("Cannot switch rack unit order" in m for m in messages))

        rack.refresh_from_db()
        valid_device.refresh_from_db()
        invalid_device.refresh_from_db()
        reservation.refresh_from_db()

        self.assertFalse(rack.desc_units)
        self.assertEqual(valid_device.position, 5)
        self.assertEqual(invalid_device.position, 13)
        self.assertEqual(reservation.units, [1, 2])

    def test_invalid_reservation_aborts_all_changes_including_devices(self):
        rack = Rack.objects.create(name="Rack-Abort-Reservation", site=self.site, u_height=12, starting_unit=1)
        device = self._create_device(rack=rack, name="keep-position", device_type=self.type_2u, position=5)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[10, 11],
            user=self.user,
            description="Bad units injected",
        )
        RackReservation.objects.filter(pk=reservation.pk).update(units=[10, 13])

        response = self._toggle(rack, follow=True)
        self.assertHttpStatus(response, 200)
        messages = self._get_message_texts(response)
        self.assertTrue(any("Cannot switch rack unit order" in m for m in messages))

        rack.refresh_from_db()
        device.refresh_from_db()
        reservation.refresh_from_db()

        self.assertFalse(rack.desc_units)
        self.assertEqual(device.position, 5)
        self.assertEqual(reservation.units, [10, 13])

    def test_toggle_does_not_modify_other_racks(self):
        target_rack = Rack.objects.create(name="Rack-Target", site=self.site, u_height=42, starting_unit=1)
        other_rack = Rack.objects.create(name="Rack-Other", site=self.site, u_height=42, starting_unit=1)

        target_device = self._create_device(rack=target_rack, name="target-device", device_type=self.type_2u, position=40)
        other_device = self._create_device(rack=other_rack, name="other-device", device_type=self.type_2u, position=40)

        target_reservation = RackReservation.objects.create(
            rack=target_rack,
            units=[41, 42],
            user=self.user,
            description="Target reservation",
        )
        other_reservation = RackReservation.objects.create(
            rack=other_rack,
            units=[41, 42],
            user=self.user,
            description="Other reservation",
        )

        response = self._toggle(target_rack)
        self.assertHttpStatus(response, 302)

        target_rack.refresh_from_db()
        other_rack.refresh_from_db()
        target_device.refresh_from_db()
        other_device.refresh_from_db()
        target_reservation.refresh_from_db()
        other_reservation.refresh_from_db()

        self.assertTrue(target_rack.desc_units)
        self.assertFalse(other_rack.desc_units)
        self.assertNotEqual(target_device.position, 40)
        self.assertEqual(other_device.position, 40)
        self.assertNotEqual(target_reservation.units, [41, 42])
        self.assertEqual(other_reservation.units, [41, 42])

    def test_unpositioned_device_is_unchanged(self):
        rack = Rack.objects.create(name="Rack-Unpositioned", site=self.site, u_height=42, starting_unit=1)
        positioned = self._create_device(rack=rack, name="positioned", device_type=self.type_2u, position=40)
        unpositioned = Device.objects.create(
            name="unpositioned",
            device_type=self.type_2u,
            role=self.role,
            site=self.site,
            rack=rack,
            position=None,
            face=DeviceFaceChoices.FACE_REAR,
        )
        unpositioned.custom_field_data = {"untouched": True}
        unpositioned.save()

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        positioned.refresh_from_db()
        unpositioned.refresh_from_db()

        self.assertEqual(
            positioned.position,
            remap_position_for_descending_units(
                position=40,
                device_height=2,
                rack_starting_unit=1,
                rack_u_height=42,
            ),
        )
        self.assertIsNone(unpositioned.position)
        self.assertEqual(unpositioned.custom_field_data, {"untouched": True})

    def test_legacy_route_alias_toggles_successfully(self):
        rack = Rack.objects.create(name="Rack-LegacyRoute", site=self.site, u_height=42, starting_unit=1)
        device = self._create_device(rack=rack, name="legacy-device", device_type=self.type_1u, position=42)

        response = self._toggle(
            rack,
            route_name="plugins:netbox_rack_inverter:rack_convert_to_descending_units",
        )
        self.assertHttpStatus(response, 302)

        rack.refresh_from_db()
        device.refresh_from_db()

        self.assertTrue(rack.desc_units)
        self.assertEqual(device.position, 1)

    def test_toggle_endpoint_rejects_get(self):
        rack = Rack.objects.create(name="Rack-MethodCheck", site=self.site, u_height=42, starting_unit=1)
        url = reverse("plugins:netbox_rack_inverter:rack_toggle_units_order", kwargs={"pk": rack.pk})
        response = self.client.get(url)
        self.assertHttpStatus(response, 405)

    def test_legacy_toggle_endpoint_rejects_get(self):
        rack = Rack.objects.create(name="Rack-MethodCheckLegacy", site=self.site, u_height=42, starting_unit=1)
        url = reverse("plugins:netbox_rack_inverter:rack_convert_to_descending_units", kwargs={"pk": rack.pk})
        response = self.client.get(url)
        self.assertHttpStatus(response, 405)

    def test_success_message_includes_changed_counts(self):
        rack = Rack.objects.create(name="Rack-Messages", site=self.site, u_height=12, starting_unit=1)
        self._create_device(rack=rack, name="device-1", device_type=self.type_1u, position=12)
        self._create_device(rack=rack, name="device-2", device_type=self.type_2u, position=9)
        RackReservation.objects.create(
            rack=rack,
            units=[10, 11],
            user=self.user,
            description="Message reservation",
        )

        response = self._toggle(rack, follow=True)
        self.assertHttpStatus(response, 200)
        messages = self._get_message_texts(response)

        self.assertTrue(any("2 devices and 1 reservations" in m for m in messages))

    def test_reservation_metadata_is_preserved(self):
        rack = Rack.objects.create(name="Rack-ReservationMetadata", site=self.site, u_height=12, starting_unit=1)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[11, 12],
            user=self.user,
            description="Metadata preserved",
        )

        original_user_id = reservation.user_id
        original_description = reservation.description

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        reservation.refresh_from_db()
        self.assertEqual(reservation.user_id, original_user_id)
        self.assertEqual(reservation.description, original_description)

    def test_reservation_units_are_sorted_after_toggle(self):
        rack = Rack.objects.create(name="Rack-ReservationSort", site=self.site, u_height=12, starting_unit=1)
        reservation = RackReservation.objects.create(
            rack=rack,
            units=[12, 10, 11],
            user=self.user,
            description="Unsorted units",
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        reservation.refresh_from_db()
        self.assertEqual(reservation.units, sorted(reservation.units))

    def test_device_relationships_and_custom_field_data_preserved(self):
        rack = Rack.objects.create(name="Rack-Preserve", site=self.site, u_height=42, starting_unit=1)
        device = self._create_device(rack=rack, name="preserve-device", device_type=self.type_2u, position=40)
        device.custom_field_data = {"example_key": "example_value"}
        device.save()

        original_pk = device.pk
        original_site_id = device.site_id
        original_role_id = device.role_id
        original_device_type_id = device.device_type_id
        original_rack_id = device.rack_id
        original_face = device.face
        original_custom_field_data = dict(device.custom_field_data)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)

        device.refresh_from_db()

        self.assertEqual(device.pk, original_pk)
        self.assertEqual(device.site_id, original_site_id)
        self.assertEqual(device.role_id, original_role_id)
        self.assertEqual(device.device_type_id, original_device_type_id)
        self.assertEqual(device.rack_id, original_rack_id)
        self.assertEqual(device.face, original_face)
        self.assertEqual(device.custom_field_data, original_custom_field_data)
        self.assertEqual(device.position, 2)

    def test_rear_facing_device_round_trip(self):
        rack = Rack.objects.create(name="Rack-RearFace", site=self.site, u_height=20, starting_unit=1)
        device = Device.objects.create(
            name="rear-device",
            device_type=self.type_4u,
            role=self.role,
            site=self.site,
            rack=rack,
            position=17,
            face=DeviceFaceChoices.FACE_REAR,
        )

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        rack.refresh_from_db()
        device.refresh_from_db()
        self.assertTrue(rack.desc_units)
        self.assertEqual(device.face, DeviceFaceChoices.FACE_REAR)

        response = self._toggle(rack)
        self.assertHttpStatus(response, 302)
        rack.refresh_from_db()
        device.refresh_from_db()
        self.assertFalse(rack.desc_units)
        self.assertEqual(device.position, 17)

    def test_toggle_is_reversible_for_multiple_racks_and_starts(self):
        scenarios = [
            {"u_height": 24, "starting_unit": 1, "positions": [(self.type_1u, 24), (self.type_2u, 10), (self.type_4u, 2)]},
            {"u_height": 16, "starting_unit": 10, "positions": [(self.type_1u, 25), (self.type_2u, 18), (self.type_4u, 10)]},
        ]

        for index, scenario in enumerate(scenarios, start=1):
            with self.subTest(index=index):
                rack = Rack.objects.create(
                    name=f"Rack-Reversible-{index}",
                    site=self.site,
                    u_height=scenario["u_height"],
                    starting_unit=scenario["starting_unit"],
                )
                devices = []
                for pos_index, (device_type, position) in enumerate(scenario["positions"], start=1):
                    devices.append(
                        self._create_device(
                            rack=rack,
                            name=f"rev-{index}-{pos_index}",
                            device_type=device_type,
                            position=position,
                        )
                    )

                original_positions = {device.pk: device.position for device in devices}

                response = self._toggle(rack)
                self.assertHttpStatus(response, 302)
                response = self._toggle(rack)
                self.assertHttpStatus(response, 302)

                rack.refresh_from_db()
                self.assertFalse(rack.desc_units)
                for device in devices:
                    device.refresh_from_db()
                    self.assertEqual(device.position, original_positions[device.pk])
