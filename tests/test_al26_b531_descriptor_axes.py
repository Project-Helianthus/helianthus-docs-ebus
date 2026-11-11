"""Finite synthetic representation checks; no wire execution or qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Independent expected inputs: destination, operation, NN, R[0], buffer, wire.
EXPECTED = {
    'baseline': ('slotA', '01', None, None, None, None),
    'slot_only': ('slotB', '01', None, None, None, None),
    'operation02_only': ('slotA', '02', None, None, None, None),
    'operation03_only': ('slotA', '03', None, None, None, None),
    'nn_only': ('slotA', '01', 3, None, None, None),
    'local_count_only': ('slotA', '01', None, 5, None, None),
    'available_only': ('slotA', '01', None, None, 5, None),
    'distinct_counts': ('slotA', '01', 3, 5, 5, None),
    'partial_available': ('slotA', '01', 3, 5, 2, None),
    'op00_unknown': (None, '00', None, None, None, None),
}
AXES = ('logical_descriptor_count', 'local_response_count',
        'available_buffer_length', 'physical_wire_length')
QUALIFIERS = ('physical_qualification', 'presence', 'freshness', 'execution',
              'physical_ack', 'physical_crc', 'echo_correlation', 'remote_effect')


class DescriptorAxes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'architecture/fixtures/al26_b531_descriptor_axes.json').read_text())
        cls.page = (ROOT / 'architecture/al26-b531-descriptor-axes.md').read_text()
        cls.cases = {case['name']: case for case in cls.data['cases']}

    def test_finite_independent_expected_inputs(self):
        self.assertEqual(set(self.data), {'evidence', 'cases'})
        self.assertEqual(self.data['evidence'], 'synthetic inputs only; Proven values do not prove native behavior')
        self.assertEqual(len(self.data['cases']), 10)
        self.assertEqual(set(self.cases), set(EXPECTED))
        for name, (destination, operation, *values) in EXPECTED.items():
            with self.subTest(scenario=name):
                case = self.cases[name]
                self.assertEqual(set(case), {'name', 'descriptor', 'operation', 'descriptor_grade', 'axes', *QUALIFIERS})
                self.assertEqual(case['operation'], operation)
                if operation == '00':
                    self.assertIsNone(case['descriptor'])
                    self.assertEqual(case['descriptor_grade'], 'Unknown')
                else:
                    self.assertEqual(case['descriptor'], {
                        'source': 'F1', 'destination': destination, 'operation': operation})
                    self.assertEqual(case['descriptor_grade'], 'Hypothesis')
                self.assertEqual(set(case['axes']), set(AXES))
                for axis, value in zip(AXES, values):
                    self.assertEqual(case['axes'][axis], {
                        'value': value, 'grade': 'Unknown' if value is None else 'Proven'})
                for qualifier in QUALIFIERS:
                    self.assertEqual(case[qualifier], 'Unknown')

    def test_each_claimed_axis_varies_alone(self):
        pairs = (
            ('baseline', 'slot_only', 'destination'),
            ('baseline', 'operation02_only', 'operation'),
            ('baseline', 'operation03_only', 'operation'),
            ('baseline', 'nn_only', 'logical_descriptor_count'),
            ('baseline', 'local_count_only', 'local_response_count'),
            ('baseline', 'available_only', 'available_buffer_length'),
            ('distinct_counts', 'partial_available', 'available_buffer_length'),
        )
        for left, right, changed in pairs:
            with self.subTest(axis=changed, scenario=right):
                def independent_fields(name):
                    case = self.cases[name]
                    return {**case['descriptor'], **case['axes'],
                            **{key: case[key] for key in QUALIFIERS}}
                a, b = independent_fields(left), independent_fields(right)
                self.assertEqual({key for key in a if a[key] != b[key]}, {changed})

    def test_normative_page_tables(self):
        expected_rows = (
            '| logical_descriptor_count | command-inclusive NN | Unknown | independent |',
            '| local_response_count | local R[0] | Unknown | independent |',
            '| available_buffer_length | available local buffer | Unknown | independent |',
            '| physical_wire_length | physical wire extent | Unknown | independent |',
            '| 01 | independent Hypothesis |',
            '| 02 | independent Hypothesis |',
            '| 03 | independent Hypothesis |',
            '| 00 | Unknown; no descriptor body |',
            '| physical ACK | Unknown |',
            '| physical CRC | Unknown |',
            '| echo/correlation | Unknown |',
            '| remote effect | Unknown |',
        )
        rows = [line for line in self.page.splitlines() if line.startswith('|')]
        self.assertEqual(rows, [
            '| Property | Representation | Unsupplied grade | Relation |',
            '|---|---|---|---|', *expected_rows[:4],
            '| Operation | Descriptor status |', '|---|---|', *expected_rows[4:8],
            '| Consequence | Grade |', '|---|---|', *expected_rows[8:]])

    def test_native_boundary_and_scenario_explanation(self):
        for text in (
            '../protocols/vaillant/ebus-vaillant-b531-hem-power-limit.md',
            '**Hypothesis:** a local descriptor uses source `F1`',
            'destination selected\nfrom its slot, and command-inclusive `NN`',
            'NN is 3, local R[0] count is 5, available buffer length is\n5, and physical wire extent is **Unknown**',
            'No packet is\nconstructed',
            'OP00 request and response remain **Unknown**',
            'Admission remains fail closed',
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
