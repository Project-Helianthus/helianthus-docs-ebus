"""Independent finite contract and local predicates; no wire executor."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b509-diagnostic-shapes.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai10_b509_diagnostic_shapes.json'
COLUMNS = ('operation direction field width_bits signedness byte_order conversion '
           'minimum maximum recommended_bytes maximum_bytes grade mapping_grade').split()
# Independently transcribed expected declarations, not derived from either product file.
EXPECTED_ROWS = [
    ['13', 'request', 'arguments', 0, 'Unknown', 'Unknown', 'no_arguments', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['13', 'response', 'result', None, 'Unknown', 'Unknown', 'Boolean', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['34', 'request', 'address', 32, 'unsigned', 'little_endian', 'identity', 0, 4294967295, None, None, 'Hypothesis', 'Hypothesis'],
    ['34', 'request', 'requested_count', 8, 'unsigned', 'not_applicable', 'identity', 0, 255, None, None, 'Hypothesis', 'Hypothesis'],
    ['34', 'response', 'address', 32, 'unsigned', 'little_endian', 'identity', 0, 4294967295, None, None, 'Hypothesis', 'Hypothesis'],
    ['34', 'response', 'data', None, 'Unknown', 'Unknown', 'raw_bytes', None, None, 10, None, 'Hypothesis', 'Unknown'],
    ['35', 'request', 'address', 32, 'unsigned', 'little_endian', 'identity', 0, 4294967295, None, None, 'Hypothesis', 'Hypothesis'],
    ['35', 'request', 'data', None, 'Unknown', 'Unknown', 'raw_bytes', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['35', 'response', 'write_status', None, 'Unknown', 'Unknown', 'status_domain', 0, 6, None, None, 'Hypothesis', 'Unknown'],
    ['51', 'Unknown', 'component', None, 'Unknown', 'Unknown', 'identity', 0, 7, None, None, 'Hypothesis', 'Hypothesis'],
    ['51', 'Unknown', 'master', 8, 'unsigned', 'not_applicable', 'identity', 0, 255, None, None, 'Hypothesis', 'Hypothesis'],
    ['51', 'Unknown', 'identity', 40, 'not_applicable', 'not_applicable', 'ASCII_exact', None, None, None, None, 'Hypothesis', 'Hypothesis'],
    ['51', 'Unknown', 'software_component_1', None, 'Unknown', 'Unknown', 'decimal_scalar', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['51', 'Unknown', 'software_component_2', None, 'Unknown', 'Unknown', 'decimal_scalar', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['51', 'Unknown', 'software_component_3', None, 'Unknown', 'Unknown', 'decimal_scalar', None, None, None, None, 'Hypothesis', 'Unknown'],
    ['51', 'Unknown', 'software_component_4', None, 'Unknown', 'Unknown', 'decimal_scalar', None, None, None, None, 'Hypothesis', 'Unknown'],
]
CASE_COLUMNS = 'case operation direction field raw value fits'.split()
EXPECTED_CASES = [
    ['address', '34', 'request', 'address', [120, 86, 52, 18], 305419896, True],
    ['response_address', '34', 'response', 'address', [120, 86, 52, 18], 305419896, True],
    ['write_address', '35', 'request', 'address', [120, 86, 52, 18], 305419896, True],
    ['count_zero', '34', 'request', 'requested_count', [0], 0, True],
    ['count_255', '34', 'request', 'requested_count', [255], 255, True],
    ['data_eleven', '34', 'response', 'data', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], True],
    ['write_data', '35', 'request', 'data', [170, 85], [170, 85], True],
    ['status_six', '35', 'response', 'write_status', [6], 6, True],
    ['status_seven', '35', 'response', 'write_status', [7], 7, False],
    ['identity_five', '51', 'Unknown', 'identity', [65, 66, 67, 68, 69], 'ABCDE', True],
    ['identity_short', '51', 'Unknown', 'identity', [65, 66], 'AB', False],
    ['identity_long', '51', 'Unknown', 'identity', [65, 66, 67, 68, 69, 70], 'ABCDEF', False],
    ['identity_non_ascii', '51', 'Unknown', 'identity', [65, 66, 67, 68, 128], None, False],
    ['identity_terminated', '51', 'Unknown', 'identity', [65, 66, 67, 68, 69, 0], 'ABCDE\0', False],
    ['component_seven', '51', 'Unknown', 'component', [7], 7, True],
    ['component_eight', '51', 'Unknown', 'component', [8], 8, False],
    ['software_1', '51', 'Unknown', 'software_component_1', None, 1, True],
    ['software_2', '51', 'Unknown', 'software_component_2', None, 20, True],
    ['software_3', '51', 'Unknown', 'software_component_3', None, 3, True],
    ['software_4', '51', 'Unknown', 'software_component_4', None, 40, True],
]
EXPECTED_UNKNOWN = dict.fromkeys([
    'offsets', 'defaults', 'response_correlation', 'variable_maximum', 'padding',
    'physical_effects', 'boolean_byte_mapping', 'software_widths', 'software_ranges',
    'source', 'destination', 'device', 'firmware'])
EXPECTED_UNKNOWN.update(qualification='Unknown', freshness='Unknown',
                        persistence='Unknown', execution_permission='Unknown',
                        raw_fallback='preserve original bytes')


def tables(text):
    """Parse every page table, retaining row and column ordering and JSON types."""
    result = []
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cells = [s.strip() for s in line.strip('|').split('|')]
        if all(s == '---' for s in cells):
            continue
        if not cells[0].startswith(('"', '[', 'null')) and not cells[0].isdigit():
            result.append((cells, []))
        else:
            result[-1][1].append([json.loads(s) for s in cells])
    return result


class DiagnosticShapes(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text()
        self.data = json.loads(FIXTURE.read_text())

    def contract(self, page, data):
        expected = dict(
            family='vaillant', service='B509', primary=181, secondary=9,
            representation='Proven', native_grade='Hypothesis', unknown=EXPECTED_UNKNOWN,
            fields=[dict(zip(COLUMNS, row)) for row in EXPECTED_ROWS],
            status_meanings={str(i): None for i in range(7)},
            cases=[dict(zip(CASE_COLUMNS, row)) for row in EXPECTED_CASES])
        # JSON serialization also distinguishes bool from int (Python equality does not).
        self.assertTrue(json.dumps(data, sort_keys=True) == json.dumps(expected, sort_keys=True),
                        "fixture differs from independent contract")
        self.assertTrue(tables(page) == [
            (['attribute', 'value'], [
                ['family', 'vaillant'], ['service', 'B509'], ['primary', 181],
                ['secondary', 9], ['representation', 'Proven'], ['native_grade', 'Hypothesis']]),
            (COLUMNS, EXPECTED_ROWS),
            (['status', 'meaning'], [[i, None] for i in range(7)]),
            (['property', 'value'], [list(p) for p in EXPECTED_UNKNOWN.items()]),
            (CASE_COLUMNS, EXPECTED_CASES)], "page tables differ from independent contract")

    def field(self, operation, direction, field):
        found = [r for r in self.data['fields'] if
                 (r['operation'], r['direction'], r['field']) == (operation, direction, field)]
        self.assertEqual(len(found), 1)
        return found[0]

    def test_page_and_fixture_independent_contract(self):
        self.contract(self.page, self.data)

    def test_unsigned_arithmetic_and_counts(self):
        for case in self.data['cases'][:5]:
            with self.subTest(case=case['case']):
                row = self.field(case['operation'], case['direction'], case['field'])
                self.assertEqual(len(case['raw']) * 8, row['width_bits'])
                self.assertEqual(row['signedness'], 'unsigned')
                value = sum(b * 256 ** i for i, b in enumerate(case['raw']))
                self.assertEqual(value, case['value'])
                self.assertLessEqual(row['minimum'], value)
                self.assertLessEqual(value, row['maximum'])
                if case['field'] == 'address':
                    self.assertEqual(row['byte_order'], 'little_endian')
                    self.assertEqual(value, 305419896)
                    self.assertGreater(value, 65535)
        self.assertEqual([c['value'] for c in self.data['cases'][3:5]], [0, 255])

    def test_variable_data_and_absent_write_count(self):
        row = self.field('34', 'response', 'data')
        self.assertEqual(row['recommended_bytes'], 10)
        self.assertIsNone(row['maximum_bytes'])
        raw = self.data['cases'][5]['raw']
        self.assertEqual(len(raw), 11)
        self.assertGreater(len(raw), row['recommended_bytes'])
        self.assertEqual([r['field'] for r in self.data['fields'] if
                          r['operation'] == '35' and r['direction'] == 'request'],
                         ['address', 'data'])

    def test_status_and_component_domains(self):
        for operation, direction, field, cases in [
            ('35', 'response', 'write_status', self.data['cases'][7:9]),
            ('51', 'Unknown', 'component', self.data['cases'][14:16])]:
            row = self.field(operation, direction, field)
            for case in cases:
                with self.subTest(case=case['case']):
                    self.assertEqual(row['minimum'] <= case['value'] <= row['maximum'], case['fits'])
                    self.assertEqual(case['raw'], [case['value']])
        self.assertEqual(list(self.data['status_meanings']), list('0123456'))
        self.assertTrue(all(v is None for v in self.data['status_meanings'].values()))
        self.assertNotIn('7', self.data['status_meanings'])

    def test_exact_ascii_identity(self):
        row = self.field('51', 'Unknown', 'identity')
        self.assertEqual(row['conversion'], 'ASCII_exact')
        for case in self.data['cases'][9:14]:
            raw = bytes(case['raw'])
            try:
                text = raw.decode('ascii')
            except UnicodeDecodeError:
                text = None
            self.assertEqual(text, case['value'])
            self.assertEqual(len(raw) * 8 == row['width_bits'] and text is not None, case['fits'])
        self.assertIsNone(self.data['unknown']['padding'])

    def test_four_separate_software_scalars(self):
        cases = self.data['cases'][16:]
        self.assertEqual([c['value'] for c in cases], [1, 20, 3, 40])
        self.assertEqual([c['field'] for c in cases], [f'software_component_{i}' for i in range(1, 5)])
        for case in cases:
            row = self.field('51', 'Unknown', case['field'])
            self.assertEqual(row['conversion'], 'decimal_scalar')
            self.assertIs(type(case['value']), int)
            self.assertIsNone(row['width_bits'])
            self.assertIsNone(case['raw'])

    def test_every_page_table_cell_is_guarded(self):
        self.contract(self.page, self.data)  # valid control
        lines = self.page.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if not line.startswith('|') or line.startswith('| ---'):
                continue
            cells = line.strip().strip('|').split('|')
            for j in range(len(cells)):
                with self.subTest(line=i + 1, column=j):
                    changed = cells.copy()
                    changed[j] = ' "mutated" '
                    mutant = lines.copy()
                    mutant[i] = '|' + '|'.join(changed) + '|\n'
                    with self.assertRaises((AssertionError, ValueError, IndexError)):
                        self.contract(''.join(mutant), self.data)

    def test_every_fixture_leaf_and_identity_axis_is_guarded(self):
        self.contract(self.page, self.data)  # valid control for every independent change

        def paths(value, prefix=()):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield from paths(item, (*prefix, key))
            elif isinstance(value, list):
                for key, item in enumerate(value):
                    yield from paths(item, (*prefix, key))
            else:
                yield prefix

        for path in paths(self.data):
            with self.subTest(path=path):
                mutant = copy.deepcopy(self.data)
                target = mutant
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = 'mutated'
                with self.assertRaises(AssertionError):
                    self.contract(self.page, mutant)

    def test_order_and_missing_fields_are_guarded(self):
        self.contract(self.page, self.data)
        for section in ['fields', 'cases']:
            for mutation in ['reverse', 'drop', 'duplicate']:
                with self.subTest(section=section, mutation=mutation):
                    mutant = copy.deepcopy(self.data)
                    if mutation == 'reverse':
                        mutant[section].reverse()
                    elif mutation == 'drop':
                        mutant[section].pop()
                    else:
                        mutant[section].append(copy.deepcopy(mutant[section][0]))
                    with self.assertRaises(AssertionError):
                        self.contract(self.page, mutant)


if __name__ == '__main__':
    unittest.main()
