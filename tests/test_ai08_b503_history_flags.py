"""Independent native declaration checks; no equipment or application behavior."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b503-history-flags.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai08_b503_history_flags.json'
COMPONENTS = ('minute', 'hour', 'day', 'month', 'year')
BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 99))

# These expected rows are independent of both published artifacts.
EXPECTED_TABLES = [
    '''Family|PB|SB|Grade
B503|0xB5|0x03|Hypothesis''',
    '''Marker|Raw condition|Candidate result|Grade
0x00|seven 0xFF bytes|no_item|Hypothesis
0x01|code retained, even with five 0xFF components|code_only|Hypothesis
0x02|validate each of five components first|calendar_components|Hypothesis''',
    '''Component|Minimum|Maximum|Replacement|Absolute position|Grade
minute|0|59|0xFF|null|Hypothesis
hour|0|23|0xFF|null|Hypothesis
day|1|31|0xFF|null|Hypothesis
month|1|12|0xFF|null|Hypothesis
year|0|99|0xFF|null|Hypothesis''',
    '''Raw range|Label|Default|Grade
0|false|0|Hypothesis
1|true|none|Hypothesis
2..255|unlabeled|none|Hypothesis''',
    '''Bit|Name|Grade
0|history_flag_0|Hypothesis
1|history_flag_1|Hypothesis
2|history_flag_2|Hypothesis
3|history_flag_3|Hypothesis
4|history_flag_4|Hypothesis
5..7|reserved|Hypothesis''',
    '''Word|Low byte|High byte|Decimal value|Grade
current_error_1|0x01|0x00|1|Hypothesis
current_error_2|0x00|0x01|256|Hypothesis
current_error_3|0x34|0x12|4660|Hypothesis
current_error_4|0x00|0x00|0|Hypothesis
current_error_5|0xFF|0xFF|65535|Hypothesis''',
    '''Raw range|Result|Grade
0|rejected|Hypothesis
1|accepted|Hypothesis
2..255|rejected|Hypothesis''',
    '''Case|Field-level raw alternative|Independent expected result
no_item|marker 0x00; tail FF FF FF FF FF FF FF|no_item; no code or calendar claim
code_only|marker 0x01; code 0x1234; components FF FF FF FF FF|code 4660 retained; no calendar claim
calendar|marker 0x02; components 59,23,31,12,99|preserve 59,23,31,12,99; date validity Unknown
minute_outside|marker 0x02; components 60,23,31,12,99|minute invalid; retain valid sibling components
hour_outside|marker 0x02; components 59,24,31,12,99|hour invalid; retain valid sibling components
named_flags|flags 0x1F|named bits 0,1,2,3,4; reserved raw 0
reserved_flags|flags 0xE0|no named bits; reserved raw 224
reset_two|reset acceptance 2|unlabeled
feedback_two|OP07 feedback 2|rejected''',
]


def page_tables():
    tables = []
    current = []
    for line in PAGE.read_text().splitlines() + ['']:
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if not all(set(cell) <= set('-:') for cell in cells):
                current.append(cells)
        elif current:
            tables.append(current)
            current = []
    return tables


def calendar(values, rows):
    result = []
    for raw, row in zip(values, rows):
        if raw == int(row[3], 16):
            result.append(None)
        elif not int(row[1]) <= raw <= int(row[2]):
            result.append(None)
        else:
            result.append(int(str(raw), 10))
    return result


def history(case, tables):
    marker = case['marker']
    if marker == int(tables[1][1][0], 16) and case['tail'] == [255] * 7:
        return ('no_item', None, None)
    if marker == int(tables[1][2][0], 16):
        return ('code_only', case['code'], None)
    if marker == int(tables[1][3][0], 16):
        return ('calendar_components', case['code'], calendar(case['components'], tables[2][1:]))
    return ('Unknown', case['code'], None)


def label(raw, rows):
    for row in rows:
        endpoints = [int(value) for value in row[0].split('..')]
        if endpoints[0] <= raw <= endpoints[-1]:
            return row[1]
    raise AssertionError('unsigned byte not covered')


class HistoryFlagsTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.tables = page_tables()

    def test_page_and_fixture_declarations_independently(self):
        expected = [[line.split('|') for line in table.splitlines()]
                    for table in EXPECTED_TABLES]
        self.assertEqual(self.tables, expected)
        self.assertEqual(self.data['tables'], expected)
        self.assertEqual(set(self.data), {'identity', 'positions', 'grade',
                                        'qualification', 'tables', 'cases', 'words'})
        self.assertEqual(self.data['identity'], {'family': 'B503', 'primary': 181,
                                              'secondary': 3})
        self.assertEqual(self.data['positions'], dict.fromkeys(
            ['marker', 'code', *COMPONENTS, 'reset_acceptance']))
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')

    def test_exact_synthetic_tuples(self):
        def entry(name, marker, tail, code, components):
            return dict(name=name, operation=1, marker=marker, tail=tail,
                        code=code, components=components)
        self.assertEqual(self.data['cases'], [
            entry('no_item', 0, [255] * 7, None, None),
            entry('code_only', 1, None, 0x1234, [255] * 5),
            entry('calendar', 2, None, 0x1234, [59, 23, 31, 12, 99]),
            entry('minute_outside', 2, None, 0x1234, [60, 23, 31, 12, 99]),
            entry('hour_outside', 2, None, 0x1234, [59, 24, 31, 12, 99]),
            dict(name='named_flags', operation=7, raw=31),
            dict(name='reserved_flags', operation=7, raw=224),
            dict(name='reset_two', operation=None, raw=2),
            dict(name='feedback_two', operation=7, raw=2),
        ])

    def test_marker_precedes_calendar(self):
        expected = [('no_item', None, None), ('code_only', 4660, None),
                    ('calendar_components', 4660, [59, 23, 31, 12, 99]),
                    ('calendar_components', 4660, [None, 23, 31, 12, 99]),
                    ('calendar_components', 4660, [59, None, 31, 12, 99])]
        for tables in (self.tables, self.data['tables']):
            for case, want in zip(self.data['cases'][:5], expected):
                with self.subTest(case=case['name']):
                    self.assertEqual(history(case, tables), want)
            for index in range(7):
                case = dict(self.data['cases'][0], tail=[255] * 7)
                case['tail'][index] = 0
                self.assertEqual(history(case, tables)[0], 'Unknown')
            for marker in range(3, 256):
                case = dict(self.data['cases'][2], marker=marker)
                self.assertEqual(history(case, tables)[0], 'Unknown')

    def test_each_calendar_domain_and_partial_state(self):
        for tables in (self.tables, self.data['tables']):
            for index, (low, high) in enumerate(BOUNDS):
                for raw in range(256):
                    values = [59, 23, 31, 12, 99]
                    values[index] = raw
                    expected = values.copy()
                    expected[index] = raw if low <= raw <= high else None
                    with self.subTest(component=COMPONENTS[index], raw=raw):
                        case = dict(self.data['cases'][2], components=values)
                        self.assertEqual(history(case, tables),
                                         ('calendar_components', 4660, expected))

    def test_flags_exclude_reserved_bits(self):
        for tables in (self.tables, self.data['tables']):
            bits = [(int(row[0]), row[1]) for row in tables[4][1:-1]]
            for raw in range(256):
                got = [name for bit, name in bits if raw & (1 << bit)]
                self.assertEqual(got, [f'history_flag_{bit}' for bit in range(5)
                                       if raw & (1 << bit)])
                self.assertEqual(sum(1 << bit for bit, _ in bits if raw & (1 << bit)),
                                 raw & 31)
            self.assertEqual(self.data['cases'][5]['raw'] & 31, 31)
            self.assertEqual(self.data['cases'][6]['raw'] & 31, 0)
            self.assertEqual(self.data['cases'][6]['raw'] & 224, 224)

    def test_five_independent_little_endian_words(self):
        self.assertEqual(self.data['words'], [[1, 0], [0, 1], [52, 18], [0, 0], [255, 255]])
        for tables in (self.tables, self.data['tables']):
            decoded = []
            for index, row in enumerate(tables[5][1:]):
                low, high = int(row[1], 16), int(row[2], 16)
                self.assertEqual([low, high], self.data['words'][index])
                self.assertTrue(0 <= low <= 255 and 0 <= high <= 255)
                value = low + 256 * high
                self.assertEqual(value, int(row[3]))
                decoded.append(value)
            self.assertEqual(decoded, [1, 256, 4660, 0, 65535])

    def test_reset_and_feedback_are_separate(self):
        for tables in (self.tables, self.data['tables']):
            for raw in range(256):
                self.assertEqual(label(raw, tables[3][1:]),
                                 {0: 'false', 1: 'true'}.get(raw, 'unlabeled'))
                self.assertEqual(label(raw, tables[6][1:]),
                                 'accepted' if raw == 1 else 'rejected')
            self.assertEqual(label(self.data['cases'][7]['raw'], tables[3][1:]), 'unlabeled')
            self.assertEqual(label(self.data['cases'][8]['raw'], tables[6][1:]), 'rejected')


if __name__ == '__main__':
    unittest.main()
