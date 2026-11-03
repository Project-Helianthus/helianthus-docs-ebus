"""Independent documentation oracles; no production Ab32 implementation is linked."""

import copy
import json
import os
from pathlib import Path
import re
import unittest


ROOT = Path(os.environ.get('AK22_ROOT', Path(__file__).resolve().parents[1]))
NATIVE = 'protocols/vaillant/ebus-b524-component-selectors.md'
FIXTURE = 'protocols/vaillant/fixtures/ak22_b524_component_selectors.json'
ARCH = 'architecture/ak22_b524_component_selectors_api.md'
AXES = (
    ('Ab32Family', 'string'), ('Ab32Variant', 'string'),
    ('Ab32Primary', 'uint8'), ('Ab32Secondary', '*uint8'),
    ('Ab32Operation', '*uint8'), ('Ab32Direction', 'string'),
    ('Ab32Field', 'string'), ('Ab32Alternative', 'string'),
    ('Ab32Group', '*uint8'), ('Ab32InstanceScope', 'string'),
    ('Ab32Register', '*uint16'),
)
# Independent finite selector oracle: deliberately not derived from the fixture.
SELECTORS = (
    ('controller-700', 0, '00', 52, 'clock-date', 'date'),
    ('controller-700', 0, '00', 53, 'clock-time', 'time'),
    ('controller-700', 0, '00', 113, 'system-holiday-start-date', 'date'),
    ('controller-700', 0, '00', 114, 'system-holiday-end-date', 'date'),
    ('controller-700', 3, 'dynamic', 3, 'zone-holiday-start-date', 'date'),
    ('controller-700', 3, 'dynamic', 4, 'zone-holiday-end-date', 'date'),
    ('controller-720', 0, '00', 52, 'clock-date', 'date'),
    ('controller-720', 0, '00', 53, 'clock-time', 'time'),
    ('controller-720', 0, '00', 218, 'system-holiday-start-date', 'date'),
    ('controller-720', 0, '00', 219, 'system-holiday-end-date', 'date'),
    ('controller-720', 3, 'dynamic', 3, 'zone-holiday-start-date', 'date'),
    ('controller-720', 3, 'dynamic', 4, 'zone-holiday-end-date', 'date'),
    ('controller-720', 3, 'dynamic', 30, 'zone-time-001e', 'time'),
    ('controller-720', 3, 'dynamic', 32, 'zone-time-0020', 'time'),
    ('controller-720', 3, 'dynamic', 33, 'zone-time-0021', 'time'),
)


def components(shape):
    return ['day', 'month', 'year'] if shape == 'date' else ['hour', 'minute', 'second']


def native_selector(row):
    return tuple(row[k] for k in
                 ('family', 'group', 'instance_scope', 'register', 'field', 'shape'))


def api_row(row):
    """Test-only example of the native-to-Ab32 mapping stated in the companion."""
    return {
        'id': 'ab32-' + row['id'],
        'identity': dict(zip((name for name, _ in AXES), (
            row['family'], 'none', 181, 36, row['opcode'], row['direction'],
            row['field'], row['shape'], row['group'], row['instance_scope'],
            row['register']))),
        'fields': row['components'], 'relations': row['selector_relations'],
        'grade': row['grade'], 'unknown': row['unknown'], 'raw_form': row['raw_form'],
    }


class CatalogExample:
    """Executable documentation example, not evidence about AK21 runtime code."""

    def __init__(self, raw, axes):
        self.raw = bytes(raw)
        self.axes = [name for name, _ in axes]

    def key(self, identity):
        # Presence is retained: null differs from an explicit zero.
        return tuple(identity[name] for name in self.axes)

    def entries(self):
        rows = json.loads(self.raw)
        if not isinstance(rows, list):
            raise ValueError('catalog is not an array')
        seen = set()
        for row in rows:
            key = self.key(row['identity'])
            if key in seen:
                raise ValueError('duplicate key')
            seen.add(key)
        return bytearray(json.dumps(rows).encode())

    def lookup(self, query):
        rows = json.loads(self.entries())  # validate all rows before selection
        for row in rows:
            if self.key(row['identity']) == self.key(query):
                return bytearray(json.dumps(row).encode()), True
        return None, False


def grouping_example(case, policy):
    """Evaluate only the declarative partial-merge example, not a decoder."""
    retained = list(case['previous'])
    for index, (raw, state) in enumerate(zip(case['incoming'], case['states'])):
        if state == 'present':
            retained[index] = raw
        elif policy['missing_overwrites_retained']:
            retained[index] = None
        if state != 'present' and not policy['retain_siblings']:
            retained = [None, None, None]
    return {
        'incoming_raw': list(case['incoming']), 'states': list(case['states']),
        'retained': retained,
        'complete': all(state == 'present' for state in case['states']),
        'timestamp': None, 'semantic_grade': policy['semantic_grade'],
        'native_grade': policy['native_grade'], 'admission': policy['admission'],
    }


class ComponentSelectorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT / NATIVE).read_text()
        cls.arch = (ROOT / ARCH).read_text()
        cls.data = json.loads((ROOT / FIXTURE).read_text())
        blocks = re.findall(r'```json\n(.*?)\n```', cls.arch, re.S)
        if len(blocks) != 1:
            raise AssertionError('one normative architecture declaration required')
        cls.contract = json.loads(blocks[0])

    def catalog(self, rows=None):
        if rows is None:
            rows = [api_row(row) for row in self.data['entries']]
        return CatalogExample(json.dumps(rows).encode(), self.contract['axes'])

    def test_native_finite_rows(self):
        rows = self.data['entries']
        self.assertEqual(len(rows), 15)
        self.assertEqual({native_selector(row) for row in rows}, set(SELECTORS))
        self.assertEqual(len({row['id'] for row in rows}), 15)
        for row in rows:
            with self.subTest(row=row['id']):
                self.assertEqual(set(row), {'id', 'family', 'opcode', 'group',
                    'instance_scope', 'register', 'direction', 'field', 'shape',
                    'components', 'encoding', 'raw_form', 'grade', 'qualification',
                    'selector_relations', 'unknown'})
                self.assertEqual(row['id'], row['family'] + '-' + row['field'])
                self.assertEqual(row['opcode'], 2)
                self.assertEqual(row['direction'], 'read')
                self.assertEqual(row['components'], components(row['shape']))
                self.assertEqual(row['encoding'], 'plain-u8')
                self.assertEqual(row['raw_form'], 'three-ordered-isolated-bytes')
                self.assertEqual(row['grade'], 'Hypothesis')
                self.assertEqual(row['qualification'], 'Unknown')
                self.assertEqual(row['selector_relations'], [])
                self.assertEqual(row['unknown'], dict.fromkeys((
                    'native_support', 'complete_reply_positions', 'physical_effects',
                    'persistence', 'delivery'), 'Unknown'))

    def test_native_page_table_independent(self):
        actual = []
        for line in self.native.splitlines():
            if line.startswith('| controller-'):
                family, op, group, scope, register, field, order = (
                    cell.strip() for cell in line.strip('|').split('|'))
                self.assertEqual(op, '02')
                shape = 'date' if order == 'day/month/year' else 'time'
                self.assertEqual(order, '/'.join(components(shape)))
                actual.append((family, int(group, 16), scope, int(register, 16), field, shape))
        self.assertEqual(actual, list(SELECTORS))

    def test_native_domains_and_unknowns(self):
        self.assertEqual(self.data['service'], {'primary': 181, 'secondary': 36})
        self.assertEqual(self.data['evidence'], 'synthetic-isolated-components')
        self.assertEqual(self.data['date_domains'], {
            'day': [1, 31], 'month': [1, 12], 'year': [0, 99]})
        self.assertEqual(self.data['time_representation_range'], [0, 255])
        unknown = dict.fromkeys(('century', 'timezone', 'joint_date_validity',
            'source', 'destination', 'firmware', 'capture_conditions',
            'installed_zone_domain', 'da_db_role_conflict'), 'Unknown')
        unknown['zone_name'] = dict.fromkeys(
            ('selectors', 'encoding', 'width', 'termination'), 'Unknown')
        self.assertEqual(self.data['unknown'], unknown)
        self.assertIn('role\nconflict remains **Unknown**', self.native)
        self.assertIn('profile-dependent BCD', self.native)
        self.assertIn('No cross-selector pair is declared', self.native)
        self.assertIn('ordered plain u8\ncomponents, not packed decimal', self.native)
        self.assertIn('day 1..31, month 1..12, year 0..99', self.native)
        self.assertIn('exact zone-name component selectors, string encoding, width and\ntermination', self.native)
        self.assertIn('there is\nno string-part entry', self.native)

    def test_plain_byte_examples_independent(self):
        expected = (
            ('date-plain', 'date', ['1F', '0C', '63'], [31, 12, 99]),
            ('time-plain', 'time', ['17', '3B', '3A'], [23, 59, 58]),
            ('hex12-plain', 'time', ['12', '00', '00'], [18, 0, 0]),
        )
        self.assertEqual(len(self.data['synthetic_cases']), 3)
        for case, (name, shape, raw, values) in zip(self.data['synthetic_cases'], expected):
            with self.subTest(case=name):
                self.assertEqual(case, {'id': name, 'shape': shape, 'raw_hex': raw,
                    'components': values, 'numeric_grade': 'Proven',
                    'semantic_grade': 'Hypothesis', 'native_grade': 'Unknown'})
                self.assertEqual([int(value, 16) for value in case['raw_hex']], values)
        for text in ('1F 0C 63', 'day=31, month=12, year=99', '17 3B 3A',
                     'hour=23, minute=59, second=58', 'hour=18, minute=0, second=0'):
            self.assertIn(text, self.native)

    def test_native_application_separation(self):
        text = self.native + json.dumps(self.data)
        self.assertNotRegex(text, r'(?i)Ab32|GraphQL|\bMCP\b|last.known.good|freshness|fresh_on_merge|retain_siblings|missing_overwrites')
        self.assertIn('ebus-vaillant-B524.md', self.native)
        self.assertNotIn('architecture/', self.native)

    def test_exact_api_and_eleven_axes(self):
        self.assertIn('func Ab32Entries() (json.RawMessage, error)', self.arch)
        self.assertIn('func Ab32Lookup(Ab32Key) (json.RawMessage, bool, error)', self.arch)
        struct = re.search(r'type Ab32Key struct \{(.*?)\n\}', self.arch, re.S)
        self.assertIsNotNone(struct)
        self.assertEqual(re.findall(r'(Ab32\w+)\s+(\*?\w+)', struct[1]), list(AXES))
        self.assertEqual(self.contract['axes'], [list(axis) for axis in AXES])
        for key, value in {
            'package': 'vaillant', 'entries_shape': 'array',
            'lookup_result': 'whole-row', 'missing_result': [None, False, None],
            'invalid_json': 'error', 'duplicate_keys': 'error',
            'validate_before_lookup': True, 'copy': 'independent-deep-bytes-every-call',
            'matching': 'all-eleven-exact-with-optional-presence',
            'wildcard': False, 'nearest': False, 'id_prefix': 'ab32-',
        }.items():
            self.assertEqual(self.contract[key], value, key)
        self.assertIn('prefix its ID with `ab32-`', self.arch)
        self.assertIn('Variant=`none`, Primary=181', self.arch)
        self.assertIn('Secondary=36, Operation=2, Direction=`read`', self.arch)

    def test_all_finite_rows_have_whole_row_controls(self):
        catalog = self.catalog()
        raw = catalog.entries()
        self.assertIsInstance(json.loads(raw), list)
        self.assertEqual(len(json.loads(raw)), 15)
        for row in self.data['entries']:
            expected = api_row(row)
            actual, found = catalog.lookup(expected['identity'])
            self.assertTrue(found)
            self.assertEqual(json.loads(actual), expected)
            self.assertEqual(json.loads(actual)['grade'], 'Hypothesis')
            self.assertEqual(json.loads(actual)['unknown']['native_support'], 'Unknown')
            self.assertEqual(json.loads(actual)['raw_form'], 'three-ordered-isolated-bytes')

    def test_each_key_axis_varied_alone_with_valid_controls(self):
        baseline = api_row(self.data['entries'][0])
        changes = {
            'Ab32Family': 'controller-720', 'Ab32Variant': 'synthetic-variant',
            'Ab32Primary': 180, 'Ab32Secondary': 37, 'Ab32Operation': 6,
            'Ab32Direction': 'write', 'Ab32Field': 'synthetic-field',
            'Ab32Alternative': 'time', 'Ab32Group': 3,
            'Ab32InstanceScope': 'dynamic', 'Ab32Register': 53,
        }
        self.assertEqual(set(changes), {name for name, _ in AXES})
        for axis, value in changes.items():
            with self.subTest(axis=axis):
                query = dict(baseline['identity'], **{axis: value})
                self.assertEqual(sum(query[k] != baseline['identity'][k] for k in query), 1)
                self.assertEqual(self.catalog([baseline]).lookup(query), (None, False))
                control = copy.deepcopy(baseline)
                control['id'] = 'ab32-synthetic-control'
                control['identity'] = query
                found, ok = self.catalog([baseline, control]).lookup(query)
                self.assertTrue(ok)
                self.assertEqual(json.loads(found), control)

    def test_optional_absent_and_zero_are_distinct_for_each_axis(self):
        baseline = api_row(self.data['entries'][0])
        for axis in ('Ab32Secondary', 'Ab32Operation', 'Ab32Group', 'Ab32Register'):
            with self.subTest(axis=axis):
                absent = copy.deepcopy(baseline)
                zero = copy.deepcopy(baseline)
                absent['identity'][axis] = None
                zero['identity'][axis] = 0
                absent['id'], zero['id'] = 'ab32-absent', 'ab32-zero'
                self.assertEqual(self.catalog([zero]).lookup(absent['identity']), (None, False))
                self.assertEqual(self.catalog([absent]).lookup(zero['identity']), (None, False))
                catalog = self.catalog([absent, zero])
                for row in (absent, zero):
                    actual, found = catalog.lookup(row['identity'])
                    self.assertTrue(found)
                    self.assertEqual(json.loads(actual), row)

    def test_family_operation_group_and_string_rejections(self):
        catalog = self.catalog()
        for family, register in (('controller-700', 218), ('controller-700', 219),
                                 ('controller-720', 113), ('controller-720', 114)):
            base = next(api_row(row) for row in self.data['entries']
                        if row['register'] == register)
            base['identity']['Ab32Family'] = family
            self.assertEqual(catalog.lookup(base['identity']), (None, False))
        base = api_row(self.data['entries'][0])['identity']
        for changes in ({'Ab32Operation': 6}, {'Ab32Group': 1},
                        {'Ab32Field': 'zone-name-suffix'}, {'Ab32InstanceScope': '01'}):
            self.assertEqual(catalog.lookup(dict(base, **changes)), (None, False))

    def test_copy_isolation_example(self):
        catalog = self.catalog()
        expected = api_row(self.data['entries'][0])
        before = catalog.entries()
        entries = catalog.entries()
        entries[:] = b'[]'
        row, found = catalog.lookup(expected['identity'])
        self.assertTrue(found)
        row[:] = b'{}'
        self.assertEqual(catalog.entries(), before)
        again, found = catalog.lookup(expected['identity'])
        self.assertTrue(found)
        self.assertEqual(json.loads(again), expected)

    def test_invalid_json_duplicate_and_array_errors_example(self):
        baseline = api_row(self.data['entries'][0])
        duplicate = copy.deepcopy(baseline)
        duplicate['id'] = 'ab32-different-id-same-key'
        for raw in (b'{', b'{}', json.dumps([baseline, duplicate]).encode()):
            catalog = CatalogExample(raw, self.contract['axes'])
            for operation in (catalog.entries,
                              lambda: catalog.lookup(baseline['identity']),
                              lambda: catalog.lookup(dict(baseline['identity'], Ab32Primary=0))):
                with self.assertRaises(ValueError):
                    operation()

    def test_grouping_policy_independent(self):
        self.assertEqual(self.contract['grouping'], {
            'retain_siblings': True, 'retain_last_known_good': True,
            'missing_overwrites_retained': False,
            'component_raw_and_failure_independent': True,
            'fresh_on_merge': False, 'timestamp': False,
            'century': 'Unknown', 'timezone': 'Unknown',
            'admission': 'withheld', 'semantic_grade': 'Hypothesis',
            'native_grade': 'Unknown'})

    def test_partial_grouping_examples_independent(self):
        expected = (
            ('missing-month', [None, None, None], [31, None, 99],
             ['present', 'missing', 'present'], [31, None, 99]),
            ('failed-month', [30, 11, 98], [31, 255, 99],
             ['present', 'failed', 'present'], [31, 11, 99]),
            ('missing-retained-month', [30, 11, 98], [31, None, 99],
             ['present', 'missing', 'present'], [31, 11, 99]),
        )
        self.assertEqual(len(self.contract['synthetic_grouping_cases']), 3)
        for case, (name, previous, incoming, states, retained) in zip(
                self.contract['synthetic_grouping_cases'], expected):
            self.assertEqual(case, {'id': name, 'previous': previous,
                'incoming': incoming, 'states': states, 'expected_retained': retained,
                'expected_complete': False})
            self.assertEqual(grouping_example(case, self.contract['grouping']), {
                'incoming_raw': incoming, 'states': states, 'retained': retained,
                'complete': False, 'timestamp': None, 'semantic_grade': 'Hypothesis',
                'native_grade': 'Unknown', 'admission': 'withheld'})

    def test_failure_in_each_component_preserves_other_cells(self):
        for index in range(3):
            for state in ('missing', 'failed'):
                with self.subTest(index=index, state=state):
                    case = {'previous': [30, 11, 98], 'incoming': [31, 12, 99],
                            'states': ['present'] * 3}
                    case['incoming'][index] = None if state == 'missing' else 255
                    case['states'][index] = state
                    expected = [31, 12, 99]
                    expected[index] = [30, 11, 98][index]
                    result = grouping_example(case, self.contract['grouping'])
                    self.assertEqual(result['retained'], expected)
                    self.assertEqual(result['states'][index], state)
                    self.assertEqual(result['incoming_raw'], case['incoming'])
                    self.assertFalse(result['complete'])
                    self.assertNotIn('fresh', result)
                    self.assertIsNone(result['timestamp'])

    def test_architecture_unknowns_parity_and_registry_order(self):
        for phrase in ('AK21 before AK22', 'no dependency back to this page',
                       'eBUS MCP compatibility and GraphQL parity',
                       'no suffix creates a string-part row',
                       'Existing\ncatalog/provider APIs and routability remain unchanged',
                       'Mutating a returned row or entries buffer cannot affect later results',
                       'Missing/failed', 'Merge creates no fresh flag'):
            # The lowercase spelling is intentional for prose case independence.
            self.assertIn(phrase.lower(), self.arch.lower())
        self.assertIn('Unknown', self.arch)
        self.assertIn('independent checks', self.arch)


if __name__ == '__main__':
    unittest.main()
