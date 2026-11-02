"""Synthetic declaration checks; no device behavior is established here."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B508.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac08_pump_roles.json'
AXES = ('family', 'variant', 'direction', 'service', 'operation', 'alternative')
IDENTITIES = (
    ('B508', 'pump role', None, 'B508', 'OP05', 'candidate default'),
    ('B508', 'solar cascading', None, 'B508', 'OP0B', 'independent tank flags'),
    ('B508', 'noise-reduction', 'broadcast', 'B508', 'OP02',
     'distinct noise-reduction candidate'),
)


def check_entries(case, entries):
    case.assertEqual(len(entries), 3)
    for entry, identity in zip(entries, IDENTITIES):
        case.assertEqual(entry, dict(
            zip(AXES + ('logical_extent', 'grade', 'physical_qualification'),
                identity + (None, 'Hypothesis', 'Unknown'))))


def table_rows(section):
    return [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in section.splitlines() if line.startswith('| ')]


class PumpRolesTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()
        self.section = self.page.split(
            '## Pump roles and independent solar flags\n', 1)[1].split(
                '\n## Profiles', 1)[0]

    def test_identity_and_grade(self):
        # Catches selector/direction changes, missing alternatives, extent=0
        # and promotion of candidate or physical grades.
        check_entries(self, self.data['entries'])
        self.assertEqual({k: v for k, v in self.data.items()
                          if k not in ('entries', 'pump', 'solar', 'examples')}, {
            'synthetic_only': True, 'representation_grade': 'Proven',
            'physical_interpretation': 'Hypothesis',
            'native_adaptation': 'Unknown', 'peer_effects': 'Unknown'})

    def test_each_identity_axis_rejects_independent_change(self):
        # A valid control then one changed axis per alternative. Dropping any
        # axis from check_entries must break these rejection assertions.
        check_entries(self, self.data['entries'])
        for index in range(3):
            for axis in AXES:
                with self.subTest(alternative=index, axis=axis):
                    changed = copy.deepcopy(self.data['entries'])
                    changed[index][axis] = 'synthetic-other'
                    with self.assertRaises(AssertionError):
                        check_entries(self, changed)

    def test_pump_raw_values_and_candidate_default(self):
        # Swapped enums, lost raw 0/1, an erased conflicting description or any
        # selected pump state as the default fail.
        self.assertEqual(self.data['pump'], {
            'raw_values': [0, 1],
            'mappings': {'0': 'blocked', '1': 'released'},
            'default': 'Unknown',
            'conflicting_default_descriptions': [
                {'description': 'blocked', 'raw_value': 0},
                {'description': 'released', 'raw_value': 1}]})

    def test_solar_positions_conversion_and_reserved_bits(self):
        # Catches coupled selectors, mask/shift changes and lost reserved bits.
        self.assertEqual(self.data['solar'], {
            'cycle_pause_position': 3,
            'tanks': [
                {'name': 'tank-one', 'logical_position': 4, 'width_bytes': 1,
                 'mask': 1, 'shift': 0, 'reserved_bits': [1, 7]},
                {'name': 'tank-two', 'logical_position': 5, 'width_bytes': 1,
                 'mask': 1, 'shift': 0, 'reserved_bits': [1, 7]}]})

    def test_synthetic_independent_flags(self):
        # Literal expected results are independent of the declaration under test.
        controls = [(['01', '00'], [1, 0], ['00', '00']),
                    (['00', '01'], [0, 1], ['00', '00']),
                    (['80', '00'], [0, 0], ['80', '00'])]
        self.assertEqual(self.data['examples'], [
            {'raw_hex': raw, 'flags': flags, 'reserved_hex': reserved}
            for raw, flags, reserved in controls])
        for raw_hex, flags, reserved_hex in controls:
            with self.subTest(raw=raw_hex):
                raw = bytes([0xB5, 0x08, 0x0B, 0] +
                            [int(value, 16) for value in raw_hex])
                before = bytes(raw)
                actual_flags, actual_reserved = [], []
                for tank in self.data['solar']['tanks']:
                    value = raw[tank['logical_position']]
                    actual_flags.append((value & tank['mask']) >> tank['shift'])
                    actual_reserved.append(value & (255 ^ tank['mask']))
                self.assertEqual(actual_flags, flags)
                self.assertEqual(actual_reserved,
                                 [int(value, 16) for value in reserved_hex])
                self.assertEqual(raw, before)

    def test_page_scoped_tables(self):
        # Independently fixes every scoped identity, grade, extent and field.
        rows = table_rows(self.section)
        self.assertEqual(rows, [
            ('Family', 'Variant', 'Direction', 'Service', 'Operation',
             'Alternative', 'Logical extent', 'Grade', 'Physical qualification'),
            ('B508', 'pump role', 'Unknown', 'B508', 'OP05',
             'candidate default', 'Unknown', 'Hypothesis', 'Unknown'),
            ('B508', 'solar cascading', 'Unknown', 'B508', 'OP0B',
             'independent tank flags', 'Unknown', 'Hypothesis', 'Unknown'),
            ('B508', 'noise-reduction', 'broadcast', 'B508', 'OP02',
             'distinct noise-reduction candidate', 'Unknown', 'Hypothesis', 'Unknown'),
            ('Operation', 'Field', 'Logical position', 'Candidate declaration',
             'Operational default', 'Grade'),
            ('OP05', 'pump state', 'Unknown', 'raw 0 = blocked; raw 1 = released',
             'Unknown', 'Hypothesis'),
            ('OP0B', 'cycle-pause', '3',
             'interpretation unresolved in this scoped alternative', 'Unknown', 'Hypothesis'),
            ('OP0B', 'tank-one flag byte', '4',
             'bit 0 = flag; bits 1..7 reserved', 'Unknown', 'Hypothesis'),
            ('OP0B', 'tank-two flag byte', '5',
             'bit 0 = flag; bits 1..7 reserved', 'Unknown', 'Hypothesis'),
            ('Synthetic tank-one / tank-two bytes', 'Flag one', 'Flag two',
             'Reserved one / two'),
            ('01 / 00', '1', '0', '00 / 00'),
            ('00 / 01', '0', '1', '00 / 00'),
            ('80 / 00', '0', '0', '80 / 00'),
            ('OP05 default description', 'Raw value it names', 'Grade'),
            ('default is blocked', '0', 'Hypothesis'),
            ('default is released', '1', 'Hypothesis'),
        ])

    def test_page_claim_boundaries_and_preserved_variants(self):
        # Erasing uncertainty, claiming causal confirmation, changing the
        # conversion or replacing the distinct broadcast breaks these claims.
        text = ' '.join(self.section.split())
        for claim in (
            '**Hypothesis:** these B508 family declarations are candidate interpretations, not physical behavior.',
            'universal boiler support and exclusivity to one appliance remain **Unknown**.',
            'preserve absent extents as **Unknown**, not zero.',
            'Each tank byte is unsigned and one byte wide.',
            '`(raw & 1) >> 0`; 0 means flag clear and 1 means flag set.',
            "No bit in one tank byte supplies the other tank's state.",
            'Preserve the complete raw bytes, including reserved bits and unmapped values;',
            '**Proven** applies only to software verification of that representation;',
            'Native adaptation, peer effects and physical qualification remain **Unknown**.',
            'No runtime capability or permission to send follows.',
            'The OP05 operational default is **Unknown**. Two default descriptions conflict and both are preserved as unresolved alternatives; neither is selected, and neither is the meaning of a raw value by itself.',
            'The existing OP02 NoiseReduction broadcast remains a distinct candidate and is not replaced by the pump form.',
            'A candidate broadcast, timer and later register change establish no causal chain, physical support or exclusive use.',
            'An actuator effect remains **Unknown**.',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, text)
        for legacy in (
            '*BRC,BRC,B5,08,02,IGN:1,State,,onoff,,State,,onoff',
            '| `B5 08 02` | boiler 1 set flow temperature (`u8` °C, 0..90) | 2 | 0 |',
            '| `B5 08 05` | boiler pump (KP) release | 2 | 0 |',
            '| `B5 08 0B` | solar cascading | 4 | 1 |',
            'which layout op `02` carries is unresolved.',
        ):
            with self.subTest(legacy=legacy):
                self.assertIn(legacy, self.page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
