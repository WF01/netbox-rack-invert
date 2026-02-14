"""
Tests for rack unit remapping logic.
"""

from django.test import SimpleTestCase

from ..views import is_valid_unit_span_for_rack, remap_position_for_descending_units


class RackUnitRemapTestCase(SimpleTestCase):
    def test_single_u_default_start(self):
        self.assertEqual(
            remap_position_for_descending_units(
                position=45,
                device_height=1,
                rack_starting_unit=1,
                rack_u_height=45,
            ),
            1,
        )

    def test_multi_u_device(self):
        self.assertEqual(
            remap_position_for_descending_units(
                position=44,
                device_height=2,
                rack_starting_unit=1,
                rack_u_height=45,
            ),
            1,
        )

    def test_non_default_starting_unit(self):
        self.assertEqual(
            remap_position_for_descending_units(
                position=24,
                device_height=1,
                rack_starting_unit=13,
                rack_u_height=12,
            ),
            13,
        )

    def test_remap_is_reversible(self):
        rack_starting_unit = 1
        rack_u_height = 45
        original_position = 37
        device_height = 3

        descending_position = remap_position_for_descending_units(
            position=original_position,
            device_height=device_height,
            rack_starting_unit=rack_starting_unit,
            rack_u_height=rack_u_height,
        )
        ascending_position = remap_position_for_descending_units(
            position=descending_position,
            device_height=device_height,
            rack_starting_unit=rack_starting_unit,
            rack_u_height=rack_u_height,
        )

        self.assertEqual(ascending_position, original_position)

    def test_valid_unit_span_for_rack(self):
        self.assertTrue(
            is_valid_unit_span_for_rack(
                position=10,
                object_height=2,
                rack_starting_unit=1,
                rack_u_height=42,
            )
        )

    def test_invalid_unit_span_for_rack(self):
        self.assertFalse(
            is_valid_unit_span_for_rack(
                position=42,
                object_height=2,
                rack_starting_unit=1,
                rack_u_height=42,
            )
        )

    def test_top_bottom_1u_symmetry(self):
        self.assertEqual(
            remap_position_for_descending_units(
                position=1,
                device_height=1,
                rack_starting_unit=1,
                rack_u_height=42,
            ),
            42,
        )
        self.assertEqual(
            remap_position_for_descending_units(
                position=42,
                device_height=1,
                rack_starting_unit=1,
                rack_u_height=42,
            ),
            1,
        )

    def test_top_bottom_multi_u_symmetry(self):
        self.assertEqual(
            remap_position_for_descending_units(
                position=39,
                device_height=4,
                rack_starting_unit=1,
                rack_u_height=42,
            ),
            1,
        )
        self.assertEqual(
            remap_position_for_descending_units(
                position=1,
                device_height=4,
                rack_starting_unit=1,
                rack_u_height=42,
            ),
            39,
        )

    def test_is_valid_unit_span_rejects_invalid_heights(self):
        self.assertFalse(
            is_valid_unit_span_for_rack(
                position=1,
                object_height=0,
                rack_starting_unit=1,
                rack_u_height=42,
            )
        )
        self.assertFalse(
            is_valid_unit_span_for_rack(
                position=1,
                object_height=1,
                rack_starting_unit=1,
                rack_u_height=0,
            )
        )

    def test_is_valid_unit_span_honors_non_default_starting_unit(self):
        self.assertTrue(
            is_valid_unit_span_for_rack(
                position=10,
                object_height=3,
                rack_starting_unit=10,
                rack_u_height=12,
            )
        )
        self.assertFalse(
            is_valid_unit_span_for_rack(
                position=21,
                object_height=2,
                rack_starting_unit=10,
                rack_u_height=12,
            )
        )
