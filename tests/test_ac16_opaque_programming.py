"""Independent finite B519 expectations; synthetic representation only."""

import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B519.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac16_opaque_programming.json'
# Explicit operation/request/positive expectations, independent of page and JSON.
CASES = (
    ('00', 'none', 'crc'), ('01', 'data', 'crc'),
    ('02', 'none', 'crc'), ('03', 'data', 'data'),
    ('04', 'data', 'crc'), ('05', 'data', 'crc'),
    ('06', 'data', 'prefix'), ('07', 'data', 'crc'),
    ('08', 'address-data', 'crc'), ('AA', 'none', 'data'),
)
UNKNOWNS = (
    'crc_algorithm', 'crc_coverage', 'crc_initialization', 'persistence_reset',
    'correlation', 'transport_crc_relation', 'mode_dependent_reply_policy',
    'full_positive_layouts', 'physical_native_effects', 'negative_layouts',
    'variant', 'data_maximum', 'prefix_only_physical_response',
    'native_adaptation', 'peer_effects',
)


def expected_rows():
    rows = []
    for operation, request, positive in CASES:
        for alternative in ('request', 'positive', 'negative'):
            layout, fields = 'Unknown', []
            if alternative == 'request':
                layout = 'declared-fields'
                if request == 'none':
                    layout = 'no-declared-inputs'
                elif request == 'data':
                    fields = [{'name': 'data', 'logical_position': 3}]
                else:
                    fields = [{'name': 'slave-address', 'logical_position': 3},
                              {'name': 'data', 'logical_position': 4}]
            elif alternative == 'positive':
                if positive == 'crc':
                    layout = 'partial'
                    fields = [{'name': 'CRC', 'logical_position': None}]
                elif positive == 'data':
                    layout = 'declared-fields'
                    fields = [{'name': 'data', 'logical_position': 3}]
                else:
                    layout = 'prefix-only'
            rows.append({
                'family': 'Vaillant', 'variant': 'Unknown',
                'direction': 'request' if alternative == 'request' else 'response',
                'service': 'B519', 'operation': operation,
                'alternative': alternative, 'layout': layout, 'extent': None,
                'grade': 'Hypothesis', 'fields': fields,
            })
    return rows


def expected_types():
    raw = {'representation': 'raw-u8', 'conversion': 'unchanged',
           'minimum': 0, 'maximum': 255, 'default': 0,
           'mappings': {}, 'grade': 'Hypothesis'}
    return {
        'data': {'representation': 'opaque-bytefield', 'conversion': 'unchanged',
                 'extent': 'through-end-of-PDU', 'minimum_bytes': 0,
                 'maximum_bytes': None, 'width_bytes': None, 'mappings': {},
                 'grade': 'Hypothesis'},
        'CRC': dict(raw), 'slave-address': dict(raw),
    }


def tables(page):
    """Read scoped tables without using fixture values as an oracle."""
    result, current = [], []
    for line in page.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            result.append(current)
            current = []
    return result


class OpaqueProgrammingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def check_rows(self, rows):
        self.assertEqual(rows, expected_rows())

    def check_page_rows(self, rows):
        self.assertEqual(rows[0], [
            'Family', 'Variant', 'Direction', 'Service', 'Selector', 'Alternative',
            'Layout', 'Fields at logical position', 'Extent', 'Grade'])
        self.assertEqual(rows[1], ['---'] * 10)
        expected = []
        for row in expected_rows():
            fields = ', '.join(
                field['name'] + '@' + ('Unknown' if field['logical_position'] is None
                                       else str(field['logical_position']))
                for field in row['fields']) or 'none declared'
            expected.append([
                row['family'], row['variant'], row['direction'], row['service'],
                row['operation'], row['alternative'], row['layout'], fields,
                'Unknown', row['grade']])
        self.assertEqual(rows[2:], expected)

    def test_all_fixture_alternatives(self):
        # Kills changed selector/direction/layout/grade, guessed coordinates,
        # missing alternatives, or absent extent replaced by zero.
        self.check_rows(self.fixture['rows'])

    def test_field_types_and_raw_boundaries(self):
        # Kills numeric conversions, ASCII/u32, fixed/unlimited maxima,
        # enum/sentinel mappings, domain/default changes and grade promotion.
        self.assertEqual(self.fixture['field_types'], expected_types())
        self.assertEqual(self.fixture['examples'], {
            'data': [[0, 255, 65], []], 'CRC': [0, 255],
            'slave-address': [0, 255]})
        self.assertEqual(bytes(self.fixture['examples']['data'][0]), b'\x00\xffA')
        self.assertEqual(len(self.fixture['examples']['data'][0]), 3)
        for name in ('CRC', 'slave-address'):
            for value in self.fixture['examples'][name]:
                self.assertIs(type(value), int)
                self.assertEqual(json.loads(json.dumps(value)), value)

    def test_metadata_and_unknowns(self):
        # Kills invented algorithms/effects and physical qualification promotion.
        metadata = {key: value for key, value in self.fixture.items()
                    if key not in ('rows', 'field_types', 'examples')}
        self.assertEqual(metadata, {
            'synthetic_only': True, 'representation_grade': 'Proven',
            'candidate_grade': 'Hypothesis', 'physical_qualification': 'Unknown',
            'limitations': dict.fromkeys(UNKNOWNS, 'Unknown')})

    def test_scoped_page_tables(self):
        # Kills page-only drift independently of the JSON.
        scoped = tables(self.page)
        self.assertEqual(len(scoped), 3)
        self.check_page_rows(scoped[0])
        self.assertEqual(scoped[1], [
            ['Field', 'Representation', 'Conversion', 'Extent', 'Minimum',
             'Maximum', 'Default', 'Enum or sentinel', 'Grade'],
            ['---'] * 9,
            ['data', 'opaque-bytefield', 'unchanged', 'through-end-of-PDU',
             '0 bytes', 'Unknown', 'Unknown', 'none established', 'Hypothesis'],
            ['CRC', 'raw-u8', 'unchanged', '1 byte', '0', '255', '0',
             'none established', 'Hypothesis'],
            ['slave-address', 'raw-u8', 'unchanged', '1 byte', '0', '255', '0',
             'none established', 'Hypothesis']])
        self.assertEqual(scoped[2], [['Property', 'Grade'], ['---', '---']] +
                         [[key, 'Unknown'] for key in UNKNOWNS])

    def test_page_grade_and_extent_boundaries(self):
        # Kills removal/reversal of the finite physical/representation boundaries.
        prose = ' '.join(self.page.split())
        for claim in (
            '**Hypothesis** applies to all native layouts, field meanings and physical interpretations',
            '**Proven** applies only to the declared representation',
            'Physical qualification is **Unknown**.',
            'No runtime capability or write admission follows from this catalog.',
            'Those alternatives remain unreconciled;',
            'It does not replace other qualified variants.',
            'they are not physical wire offsets.',
            '`Unknown` extent means absent information, not zero length.',
            'All rows preserve the raw PDU, including unresolved bytes.',
            'A prefix-only positive declaration for 06 does not establish no physical response.',
            'Positive CRC coordinates on the partial alternatives are absent, never inferred.',
            'It is not scalar, text, a fixed buffer or a promise of unlimited carrier capacity.',
            'The declared minimum of zero does not establish physical acceptance of empty data.',
            'AA is a separate selector, not a fill-byte/count.',
            'a failed interpretation does not erase last-known-good information',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, prose)

    def test_each_fixture_identity_axis_rejected_independently(self):
        # Valid control plus one changed axis at a time for all 30 alternatives.
        # No identity field can be silently ignored by the comparison.
        control = self.fixture['rows']
        self.check_rows(control)
        for index in range(30):
            for axis, replacement in (
                ('family', 'Other-family'), ('variant', 'Other-variant'),
                ('direction', 'response' if control[index]['direction'] == 'request' else 'request'),
                ('service', 'B518'),
                ('operation', '01' if control[index]['operation'] == '00' else '00'),
                ('alternative', 'positive' if control[index]['alternative'] == 'request' else 'request'),
            ):
                with self.subTest(index=index, axis=axis):
                    mutant = copy.deepcopy(control)
                    mutant[index][axis] = replacement
                    with self.assertRaises(AssertionError):
                        self.check_rows(mutant)

    def test_each_page_identity_axis_rejected_independently(self):
        control = tables(self.page)[0]
        self.check_page_rows(control)
        for index in range(2, 32):
            for axis in range(6):
                with self.subTest(index=index, axis=axis):
                    mutant = copy.deepcopy(control)
                    replacements = ['Other-family', 'Other-variant',
                                    'response' if control[index][2] == 'request' else 'request',
                                    'B518', '01' if control[index][4] == '00' else '00',
                                    'positive' if control[index][5] == 'request' else 'request']
                    mutant[index][axis] = replacements[axis]
                    with self.assertRaises(AssertionError):
                        self.check_page_rows(mutant)


if __name__ == '__main__':
    unittest.main(verbosity=2)
