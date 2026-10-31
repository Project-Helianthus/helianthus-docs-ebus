"""Offline synthetic/native documentation checks; no library execution."""
import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('protocols/vaillant/ebus-b507-energy-candidates.md')
FIXTURE = Path('protocols/vaillant/fixtures/aj14_b507_energy_candidates.json')
API = Path('architecture/aj14_b507_energy_candidates_api.md')

# Independent expectations: no values are derived from the page or fixture.
FIELD_ROWS = [
    ['06', 'capacity output', 'Hypothesis', '8', 'unsigned',
     'raw / 10 kW; raw 0..250 only', 'Unknown'],
    ['06', 'cost of primary energy', 'Hypothesis', '8', 'unsigned',
     'candidate unit 1/MWh, raw 0..250; mode and monetary/emissions reference dependent; converter Unknown',
     'calculated or estimated possible'],
    ['06', 'current flow temperature', 'Hypothesis', '16', 'signed little-endian',
     'raw / 16 °C', 'calculated or estimated possible'],
    ['08', 'efficiency word', 'Hypothesis', '16', 'Unknown',
     'operation-local candidate labels only', 'Unknown'],
]
WORD_ROWS = [['08', '0000', 'appliance-unavailable candidate', 'Hypothesis'],
             ['08', 'FFFF', 'maximum-efficiency-preference', 'Hypothesis'],
             ['08', '0001', 'unmapped', 'Unknown']]
CAPACITY_ROWS = [['0', '0', 'inside'], ['1', '0.1', 'inside'],
                 ['250', '25', 'inside'], ['251', 'Unknown', 'outside']]
COST_ROWS = [
    [mode, reference, '173', 'Unknown', 'calculated or estimated possible', 'Unknown']
    for mode in ('mode-a', 'mode-b') for reference in ('monetary', 'emissions')
]
TABLES = {'fields': FIELD_ROWS, 'capacity': CAPACITY_ROWS,
          'words': WORD_ROWS, 'cost_contexts': COST_ROWS}
PAGE_TABLES = [FIELD_ROWS, CAPACITY_ROWS, WORD_ROWS, COST_ROWS]
IDENTITY = {'family': 'vaillant', 'variant': 'B507', 'primary': 181,
            'secondary': 7, 'direction': None}
BOUNDARIES = {
    'evidence_class': 'Proven', 'candidate_status': 'Hypothesis',
    'physical_support': 'Unknown', 'coordinates': None,
    'actual_reference': 'Unknown', 'cost_converter': None,
    'execution_permission': False, 'preserve_raw': True,
    'capacity_alternative': 'negative mode-related prose unresolved',
    'temperature_direct_measurement': 'Unknown',
    'cost_direct_measurement': 'Unknown',
}


def page_tables(text):
    tables, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            tables.append(current[2:])  # Ignore only header and separator.
            current = []
    return tables


class EnergyCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / FIXTURE).read_text())
        self.native = (ROOT / NATIVE).read_text()
        self.api = (ROOT / API).read_text()

    def check_fixture(self, value):
        self.assertEqual(value, {'identity': IDENTITY, 'boundaries': BOUNDARIES,
                                 'synthetic_tuples': TABLES})

    def test_native_tables_and_tuples_independently(self):
        self.check_fixture(self.fixture)
        self.assertEqual(page_tables(self.native),
                         PAGE_TABLES)

    def test_preference_labels_are_op08_local(self):
        for operation in ('09', '0B'):
            with self.subTest(operation=operation):
                mutant = copy.deepcopy(self.fixture)
                mutant['synthetic_tuples']['fields'].append(
                    [operation, 'efficiency word', 'Hypothesis', '16', 'Unknown',
                     'operation-local candidate labels only', 'Unknown'])
                with self.assertRaises(AssertionError):
                    self.check_fixture(mutant)
                mutant = copy.deepcopy(self.fixture)
                mutant['synthetic_tuples']['words'].append(
                    [operation, '0000', 'appliance-unavailable candidate', 'Hypothesis'])
                with self.assertRaises(AssertionError):
                    self.check_fixture(mutant)
        for raw, meaning in (('0000', 'appliance-unavailable candidate'),
                             ('FFFF', 'maximum-efficiency-preference')):
            with self.subTest(raw=raw):
                # Candidate labels stay Hypothesis; promoting one is rejected.
                mutant = copy.deepcopy(self.fixture)
                rows = mutant['synthetic_tuples']['words']
                rows[[r[1] for r in rows].index(raw)][3] = 'Proven'
                with self.assertRaises(AssertionError):
                    self.check_fixture(mutant)

    def test_capacity_arithmetic_and_domain(self):
        # Literal expected outputs make multiply, signed8 and clipping mutations visible.
        rows = self.fixture['synthetic_tuples']['capacity']
        self.assertEqual(rows, CAPACITY_ROWS)
        for raw, expected in ((0, 0), (1, 0.1), (250, 25)):
            with self.subTest(raw=raw):
                self.assertEqual(int(rows[(0, 1, 250).index(raw)][0]) / 10, expected)
        self.assertEqual(rows[3], ['251', 'Unknown', 'outside'])

    def test_all_native_selectors_and_predicates_are_sensitive(self):
        # Each independent mutation must fail while an untouched control passes.
        # This checks the validator, not a runtime lookup or decoder.
        self.check_fixture(copy.deepcopy(self.fixture))
        for axis, changed in (('family', 'other-family'), ('variant', 'B524'),
                              ('primary', 182), ('secondary', 0),
                              ('secondary', None), ('direction', 'request'),
                              ('direction', 'response')):
            with self.subTest(axis=axis, changed=changed):
                mutant = copy.deepcopy(self.fixture)
                mutant['identity'][axis] = changed
                with self.assertRaises(AssertionError):
                    self.check_fixture(mutant)
        # Every cell includes operation, field, grade, width, encoding, scale,
        # origin, raw value, mode, reference, domain and directness predicates.
        for table, rows in TABLES.items():
            for row_index, row in enumerate(rows):
                for column in range(len(row)):
                    with self.subTest(table=table, row=row_index, column=column):
                        mutant = copy.deepcopy(self.fixture)
                        mutant['synthetic_tuples'][table][row_index][column] = 'fabricated'
                        with self.assertRaises(AssertionError):
                            self.check_fixture(mutant)
        for field in BOUNDARIES:
            with self.subTest(boundary=field):
                mutant = copy.deepcopy(self.fixture)
                mutant['boundaries'][field] = 'fabricated'
                with self.assertRaises(AssertionError):
                    self.check_fixture(mutant)

    def test_page_table_mutations_are_sensitive(self):
        for index, rows in enumerate(PAGE_TABLES):
            for row, cells in enumerate(rows):
                for column in range(len(cells)):
                    with self.subTest(table=index, row=row, column=column):
                        mutant = page_tables(self.native)
                        mutant[index][row][column] = 'fabricated'
                        with self.assertRaises(AssertionError):
                            self.assertEqual(mutant, PAGE_TABLES)

    def test_native_evidence_and_partial_boundaries(self):
        for phrase in ('Provenance is not published', 'Physical support remains **Unknown**',
                       'Negative\nmode-related prose remains a separate unresolved alternative',
                       'neither signed8\nreinterpretation nor multiplication by 10 is selected',
                       'without clipping', 'not native mode codes',
                       'not evidence of an\nactual reference or supported mode',
                       'neither is qualified as a direct\nsensor measurement',
                       'partial knowledge must remain partial',
                       'no shared preference field is established',
                       'candidate labels only; no sentinel mapping is declared as established',
                       'do not transfer to\nOP09, OP0B',
                       'half-percent correction is outside'):
            self.assertIn(phrase, self.native)
        self.assertNotIn('](ebus-vaillant-B507.md', self.native)
        for forbidden in ('Ab13', 'GraphQL', 'MCP', 'CLI', 'unittest', 'ebusreg'):
            self.assertNotIn(forbidden, self.native)

    def test_api_signatures_and_independent_key_axes(self):
        signatures = [line for line in self.api.splitlines() if line.startswith('func ')]
        self.assertEqual(signatures, [
            'func Ab13Entries() ([]Ab13Entry, error)',
            'func Ab13Lookup(ab13Key Ab13Key) (Ab13Entry, bool, error)'])
        expected = [
            ['Ab13Family', 'string', 'exact family'],
            ['Ab13Variant', 'string', 'exact variant'],
            ['Ab13Primary', 'uint8', 'exact primary service'],
            ['Ab13Secondary', '*uint8', 'absent differs from explicit zero'],
            ['Ab13Operation', '*uint8', 'absent differs from explicit zero'],
            ['Ab13Direction', '*string', 'absent differs from a supplied direction'],
            ['Ab13Field', 'string', 'exact field'],
            ['Ab13Group', '*uint8', 'B524 group; absent differs from explicit zero'],
            ['Ab13RequestedInstance', '*uint8',
             'B524 requested instance; absent differs from explicit zero'],
            ['Ab13Register', '*uint16', 'B524 full register; absent differs from explicit zero'],
            ['Ab13CommandRole', '*string',
             'B524 command role; absent differs from a supplied role'],
        ]
        self.assertEqual(page_tables(self.api), [expected])
        for row_index, row in enumerate(expected):
            for column in range(len(row)):
                with self.subTest(axis=row[0], column=column):
                    mutant = page_tables(self.api)
                    mutant[0][row_index][column] = 'omitted'
                    with self.assertRaises(AssertionError):
                        self.assertEqual(mutant, [expected])

    def test_api_copy_errors_grades_and_compatibility(self):
        for phrase in ('`Ab13Entry`', '`Ab13Grade`', '`Ab13MetadataPresence`',
                       '`Ab13PhysicalQualification`', '`Ab13Invocation`',
                       'independently owned nested data',
                       'including results still held by the caller',
                       'key pointers, optional scalar pointers, slices, maps',
                       '`Ab13Entry{}, false, nil`', '`Ab13Entry{}, false, error`',
                       'entries yield no usable collection', 'duplicate exact keys',
                       'previously retained, independently owned',
                       'admission on failed data stays closed',
                       'OP08 operation-local preference candidate labels',
                       'do not transfer to OP09 or OP0B',
                       'no shared preference field or established sentinel mapping',
                       'remain Unknown',
                       'separate OP02 and OP06 identities',
                       'eBUS MCP or GraphQL', 'before 1.0', 'before 0.9', '0.11'):
            self.assertIn(phrase, self.api)
        self.assertIn('Provenance is not published', self.api)


if __name__ == '__main__':
    unittest.main()
