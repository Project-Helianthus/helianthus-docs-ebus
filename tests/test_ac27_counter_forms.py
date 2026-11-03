"""Synthetic representation checks; no physical exchange qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'protocols/ebus-services/fixtures/ac27_counter_forms.json'
PAGE = ROOT / 'protocols/ebus-services/ebus-service-03h.md'
EXPECTED = {
    '04': (['decimal_1s', 'decimal_100s', 'decimal_10000s'], [99, 99, 99]),
    '05': (['minutes', 'hours_100s', 'hours_10000s'], [59, 59, 59]),
    '06': (['minutes', 'hours_1s', 'hours_100s', 'hours_10000s'], [59, 99, 99, 99]),
}


def valid_values(form, values):
    return len(values) == len(form['components']) and all(
        type(value) is int and field['minimum'] <= value <= field['maximum']
        for field, value in zip(form['components'], values)
    )


class CounterForms(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.forms = self.data['forms']
        self.page = PAGE.read_text()
        self.variant = self.page.split('## Vaillant variants\n', 1)[1].split('## Communication Flow', 1)[0]

    def test_service_identity(self):
        self.assertEqual([(f['pb'], f['sb']) for f in self.forms], [('03', s) for s in EXPECTED])

    def test_distinct_component_sets(self):
        for f in self.forms:
            with self.subTest(service=f['sb']):
                self.assertEqual([c['name'] for c in f['components']], EXPECTED[f['sb']][0])

    def test_domains_and_defaults(self):
        for f in self.forms:
            with self.subTest(service=f['sb']):
                self.assertEqual([c['maximum'] for c in f['components']], EXPECTED[f['sb']][1])
                for c in f['components']:
                    self.assertEqual((c['minimum'], c['default']), (0, 0))
                    self.assertEqual((c['width_bits'], c['type'], c['conversion'], c['unit']),
                                     (8, 'unsigned8', 'identity', 'raw'))

    def test_logical_not_physical(self):
        self.assertEqual(self.data['coordinate_system'], 'logical including two service-prefix positions')
        for f in self.forms:
            self.assertEqual([c['logical_position'] for c in f['components']], list(range(2, 2 + len(f['components']))))
            self.assertIsNone(f['physical_offsets'])
            self.assertIsNone(f['physical_response_length'])

    def test_direction_alternatives(self):
        for f in self.forms:
            self.assertEqual(f['placement_alternatives'], ['request', 'positive'])
            self.assertIs(f['positive_prefix_only_alternative'], True)
        self.assertIn('A prefix-only PeBUS-positive alternative does not establish an empty physical\nresponse.', self.variant)

    def test_encoding_distinction(self):
        self.assertEqual(self.data['encoding_controls'], [
            {'declaration': 'explicit', 'encoding': 'unsigned8'},
            {'declaration': 'unspecified', 'encoding': None}])
        for f in self.forms:
            self.assertTrue(all(c['encoding'] is None for c in f['components']))
        self.assertIn('label does not establish packed BCD.', self.variant)
        self.assertIn('`0x63` is decimal 99, not a packed-BCD 63.', self.variant)

    def test_raw_examples_and_arithmetic(self):
        expected = [[99, 99, 99], [59, 59, 59], [59, 99, 99, 99]]
        self.assertEqual([f['values'] for f in self.forms], expected)
        for f in self.forms:
            self.assertEqual([int(v, 16) for v in f['raw_component_hex']], f['values'])
            self.assertTrue(valid_values(f, f['values']))
        a, b, c = self.forms[0]['values']
        self.assertEqual(a + b * 100 + c * 10000, 999999)
        self.assertIn('**Proven (arithmetic only):**', self.variant)

    def test_malformed_representations(self):
        forms = {f['pb'] + f['sb']: f for f in self.forms}
        self.assertEqual(len(self.data['invalid_examples']), 7)
        for case in self.data['invalid_examples']:
            f = forms[case['service']]
            self.assertFalse(valid_values(f, case['values']))
            self.assertEqual(case['reason'], 'width' if len(case['values']) != len(f['components']) else 'domain')
        for f in self.forms:
            for i, c in enumerate(f['components']):
                for value, valid in [(0, True), (c['maximum'], True), (-1, False), (c['maximum'] + 1, False)]:
                    values = list(f['values'])
                    values[i] = value
                    with self.subTest(service=f['sb'], component=c['name'], value=value):
                        self.assertEqual(valid_values(f, values), valid)
                values = list(f['values'])
                values[i] = True
                self.assertFalse(valid_values(f, values))
            self.assertFalse(valid_values(f, f['values'][:-1]))
            self.assertFalse(valid_values(f, f['values'] + [0]))

    def test_unknown_and_qualification(self):
        self.assertEqual(self.data['unknown_body_forms'], ['0307', '0308', '0310'])
        for f in self.forms:
            self.assertEqual((f['status'], f['qualification']), ('Hypothesis', 'Unknown'))
        self.assertIn('not unsupported.', self.variant)
        self.assertIn('they are not captures or physical qualification evidence.', self.variant)

    def test_scoped_page_table(self):
        rows = [line.split('|')[1:-1] for line in self.variant.splitlines() if line.startswith('| `0x')]
        self.assertEqual(len(rows), 6)
        for row, (sb, (names, maxima)) in zip(rows[:3], EXPECTED.items()):
            self.assertEqual([v.strip() for v in row], [f'`0x{sb}`', ', '.join(names),
                ', '.join(f'0–{v}' for v in maxima), ', '.join('0' for _ in names),
                ', '.join(str(i) for i in range(2, 2 + len(names))),
                'Hypothesis; request/positive alternatives unresolved'])
        for row, sb in zip(rows[3:], ['07', '08', '10']):
            self.assertEqual([v.strip() for v in row], [f'`0x{sb}`', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Missing body form; support Unknown'])

    def test_generic_standard_tables_preserved(self):
        generic = self.page.split('## Vaillant variants')[0]
        for row in ['| 0 | start_count_1s | CHAR | 0–99 | 1s position (decimal, not BCD) |',
                    '| 1 | hours_1s | CHAR | 0–99 | 1s hours |',
                    '| 3 | hours_10000s | CHAR | 0–99 | 10000s hours |']:
            self.assertIn(row, generic)
        self.assertEqual(generic.count('**Request payload:** Empty (`NN=0x00`).'), 5)
        self.assertIn('The response carries three CHAR bytes', generic)
        self.assertIn('**Response payload:** Identical layout to [0x03 0x05]', generic)


if __name__ == '__main__':
    unittest.main()
