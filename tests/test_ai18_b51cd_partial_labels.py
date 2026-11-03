"""Independent oracles for synthetic partial declarations; no wire operations."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b51cd-partial-labels.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai18_b51cd_partial_labels.json'
# These constants are independent of both published artifacts.
LABELS = {
    'B51C': ('00', '01', '02', '03', '10', '13', '14', '19', '1B', '1C', '1D'),
    'B51D': ('00', '01', '02', '03', '10', '11', '12', '13', '14', '15', '16', '17'),
}
UNKNOWN = (
    'body-layout', 'codec', 'gating', 'confirmation', 'effect',
    'physical-framing', 'physical-equivalence', 'installed-support',
    'freshness', 'persistence', 'execution-permission', 'uninterpreted-controls',
)
COLUMNS = ['Group', 'Label suffix', 'Request constant', 'Positive constant',
           'Logical byte', 'Bit', 'Width bits', 'Secondary', 'Operation', 'Body', 'Grade']


def expected_entries():
    return [
        {'group': group, 'label': label,
         'request': {'constant': 181, 'logical_byte': 0, 'bit': 0, 'width_bits': 8},
         'positive': {'constant': 245, 'logical_byte': 0, 'bit': 0, 'width_bits': 8},
         'secondary': None, 'operation': None, 'body': None, 'grade': 'Hypothesis'}
        for group, labels in LABELS.items() for label in labels
    ]


def tables(text):
    result = []
    for block in re.findall(r'(?:^\|[^\n]*\n)+', text, re.MULTILINE):
        result.append([
            [cell.strip() for cell in line.strip('|').split('|')]
            for line in block.splitlines() if not line.startswith('|---')
        ])
    return result


def declaration(data, family, group, label, side, secondary=None, operation=None):
    """Test-only declaration lookup, with no packet construction or decoding."""
    if (family != data['family'] or secondary is not None or operation is not None
            or side not in ('request', 'positive')):
        return None
    for entry in data['entries']:
        if (entry['group'], entry['label']) == (group, label):
            return (family, group, label, side, entry[side])
    return None


class PartialLabelsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_fixture_against_independent_oracle(self):
        expected = {'family': 'vaillant', 'synthetic': True,
                    'entries': expected_entries(),
                    'unknowns': dict.fromkeys(UNKNOWN, 'Unknown')}
        # JSON comparison also distinguishes false from 0 and 181.0 from 181.
        self.assertEqual(json.dumps(self.data, sort_keys=True),
                         json.dumps(expected, sort_keys=True))

    def test_page_tables_against_independent_oracle_and_fixture(self):
        expected = [
            [group, label, 'B5', 'F5', '0', '0', '8',
             'absent', 'absent', 'absent', 'Hypothesis']
            for group, labels in LABELS.items() for label in labels
        ]
        parsed = tables(self.page)
        self.assertEqual(parsed, [
            [COLUMNS] + expected,
            [['Claim', 'Grade']] + [[name, 'Unknown'] for name in UNKNOWN],
            [['Side', 'Constant', 'Decimal', 'Minimum', 'Maximum', 'Start bit', 'End bit', 'Grade'],
             ['request', 'B5', '181', '0', '255', '0', '7', 'Proven'],
             ['positive', 'F5', '245', '0', '255', '0', '7', 'Proven']],
        ])
        for row, entry in zip(parsed[0][1:], self.data['entries']):
            self.assertEqual(row[:2], [entry['group'], entry['label']])
            for index, side in ((2, 'request'), (3, 'positive')):
                self.assertEqual(int(row[index], 16), entry[side]['constant'])
                self.assertEqual([int(value) for value in row[4:7]],
                                 [entry[side][key] for key in
                                  ('logical_byte', 'bit', 'width_bits')])

    def test_exact_counts_order_and_late_lexical_labels(self):
        identities = [(entry['group'], entry['label']) for entry in self.data['entries']]
        self.assertEqual(len(identities), 23)
        self.assertEqual(len(set(identities)), 23)
        self.assertEqual(identities, [(g, s) for g, labels in LABELS.items() for s in labels])
        for group, count in (('B51C', 11), ('B51D', 12)):
            self.assertEqual(sum(g == group for g, _ in identities), count)
        for suffix in ('15', '16', '17'):
            with self.subTest(suffix=suffix):
                self.assertIn(('B51D', suffix), identities)
                for side in ('request', 'positive'):
                    self.assertIsNotNone(declaration(self.data, 'vaillant', 'B51D', suffix, side))

    def test_range_bit_arithmetic_and_partial_extent(self):
        for entry in self.data['entries']:
            for side, expected in (('request', 181), ('positive', 245)):
                with self.subTest(group=entry['group'], label=entry['label'], side=side):
                    field = entry[side]
                    self.assertEqual(field['constant'], expected)
                    self.assertEqual(field['logical_byte'], 0)
                    self.assertEqual(field['bit'], 0)
                    self.assertEqual(field['width_bits'], 8)
                    start = field['logical_byte'] * 8 + field['bit']
                    end = start + field['width_bits'] - 1
                    self.assertEqual((start, end), (0, 7))
                    mask = (1 << field['width_bits']) - 1
                    self.assertEqual(mask, 255)
                    self.assertLessEqual(0, field['constant'])
                    self.assertLessEqual(field['constant'], mask)
                    self.assertEqual(sum(((expected >> bit) & 1) * 2 ** bit
                                         for bit in range(8)), field['constant'])
                    self.assertNotEqual(field['constant'], 0)

    def test_each_identity_axis_with_valid_control(self):
        control_key = ['vaillant', 'B51C', '00', 'request', None, None]
        control = declaration(self.data, *control_key)
        self.assertIsNotNone(control)
        # Group, lexical suffix and side each have another valid declaration.
        for axis, value in ((1, 'B51D'), (2, '01'), (3, 'positive')):
            changed = control_key.copy()
            changed[axis] = value
            with self.subTest(axis=('family', 'group', 'label', 'side')[axis]):
                found = declaration(self.data, *changed)
                self.assertIsNotNone(found)
                self.assertNotEqual(found, control)
                self.assertEqual(declaration(self.data, *control_key), control)
        for axis, value in ((0, 'other-family'), (1, 'other-group'), (2, '*'),
                            (3, 'other-side'), (4, 0), (4, 28), (4, 29),
                            (5, 0), (5, 21)):
            changed = control_key.copy()
            changed[axis] = value
            with self.subTest(axis=axis, value=value):
                self.assertIsNone(declaration(self.data, *changed))
                self.assertEqual(declaration(self.data, *control_key), control)

    def test_constants_do_not_merge_identity(self):
        for side in ('request', 'positive'):
            found = [declaration(self.data, 'vaillant', group, label, side)
                     for group, labels in LABELS.items() for label in labels]
            self.assertEqual(len({row[:4] for row in found}), 23)
            self.assertTrue(all(row[4] == found[0][4] for row in found))
            # Returning any same-constant label instead of the requested one fails.
            for row, (group, label) in zip(found, [(g, s) for g, ls in LABELS.items() for s in ls]):
                self.assertEqual(row[:4], ('vaillant', group, label, side))

    def test_unknowns_are_not_zero_or_encodable_empty_bodies(self):
        self.assertEqual(self.data['unknowns'], dict.fromkeys(UNKNOWN, 'Unknown'))
        for entry in self.data['entries']:
            self.assertEqual(set(entry), {'group', 'label', 'request', 'positive',
                                         'secondary', 'operation', 'body', 'grade'})
            for key in ('secondary', 'operation', 'body'):
                self.assertIsNone(entry[key])
                self.assertNotEqual(entry[key], 0)
                self.assertNotEqual(entry[key], [])
                self.assertNotEqual(entry[key], '')
            for side in ('request', 'positive'):
                self.assertEqual(set(entry[side]), {'constant', 'logical_byte', 'bit', 'width_bits'})
        # The page exposes only declarative tables, with no executable block.
        self.assertNotIn('```', self.page)
        self.assertNotIn('~~~', self.page)
        self.assertNotRegex(self.page, r'<(?:script|iframe)\b')
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn(':', target)
            self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)


if __name__ == '__main__':
    unittest.main()
