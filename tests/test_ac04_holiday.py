"""Synthetic declaration checks; no native execution or physical qualification."""
import copy
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac04_holiday.json'
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B50B.md'
AXES = ('family', 'variant', 'direction', 'service', 'operation', 'alternative')
UNKNOWN = [
    'calendar century', 'timezone', 'valid-date rules', 'start-before-end rules',
    'atomicity', 'persistent assignment', 'physical response', 'readback',
    'pairing of B50B writes with B50C reads', 'native adaptation', 'peer effects',
    'qualification',
]


def expected_fields():
    """Independent finite contract, never calculated from page or fixture."""
    rows = []

    def add(field, **changes):
        row = dict(field=field, family='Vaillant', variant=None, direction=None,
                   service=None, operation=None, alternative='field-declaration',
                   extent_bytes=None, offset=None, conversion='Unknown',
                   default=None, grade='Hypothesis')
        row.update(changes)
        rows.append(row)

    add('holiday_number', extent_bytes=1, conversion='unsigned byte', default=0,
        identity_relation='separate from circuit/room identity')
    for end in ('start', 'end'):
        for part in ('day', 'month', 'year'):
            add(f'{end}_{part}', default=0, zero_calendar_conflict=part != 'year')
    add('op02_setpoint', operation='OP02', extent_bytes=1,
        conversion='unsigned byte in degrees C', default=0,
        candidate_bounds=[5, 30], default_conflict=True, off_frost_deletion='Unknown')
    add('room_action', default=0,
        mappings={'0': 'no-action', '1': 'switch-on', '2': 'thermostat'})
    add('holiday_status', default=0, mappings={'0': '0', '1': '1'})
    for digit in (1, 2, 3, 4):
        add(f'keycode_{digit}', extent_bytes=1, conversion='independent numeric byte',
            excluded=['ASCII', 'packed decimal', 'u32'])
    add('circuit_name', extent_bytes=10, conversion='ASCII characters',
        unknown=['padding', 'trimming', 'NUL termination', 'UTF-8', 'truncation'])
    add('remote_control_write', variant='remote-control', alternative='remote-control-write')
    add('b50d_ui_direction_write', variant='UI-direction', service='B50D',
        alternative='UI-direction-write')
    return rows


def assert_declarations(case, doc):
    case.assertEqual(set(doc), {'evidence', 'representation_grade', 'physical_grade',
                              'qualification', 'fields', 'unknown', 'examples'})
    case.assertEqual(doc['evidence'], 'synthetic only')
    case.assertEqual(doc['representation_grade'], 'Proven')
    case.assertEqual(doc['physical_grade'], 'Hypothesis')
    case.assertEqual(doc['qualification'], 'Unknown')
    case.assertEqual(doc['unknown'], UNKNOWN)
    case.assertEqual(json.dumps(doc['fields'], sort_keys=True),
                     json.dumps(expected_fields(), sort_keys=True))


def tables(page):
    """Read scoped Markdown tables, preserving every cell and row."""
    result = {}
    section = None
    for line in page.splitlines():
        if line.startswith('## '):
            section = line[3:]
        elif line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(cell and set(cell) <= {'-', ':'} for cell in cells):
                continue
            result.setdefault(section, []).append(cells)
    return result


def expected_tables():
    fields = [['Field', 'Operation', 'Extent (bytes)', 'Conversion', 'Default', 'Grade']]
    for row in expected_fields()[:15]:
        fields.append([str(row[key]) if row[key] is not None else 'absent'
                       for key in ('field', 'operation', 'extent_bytes', 'conversion', 'default', 'grade')])
    return {
        'Candidate fields': fields,
        'Defaults and candidate domains': [
            ['Setpoint raw byte', 'Candidate degrees C', 'Inside candidate bounds', 'Physical meaning'],
            ['0', '0', 'false', 'Unknown'], ['5', '5', 'true', 'Unknown'],
            ['30', '30', 'true', 'Unknown'], ['31', '31', 'false', 'Unknown']],
        'Candidate enumerations': [
            ['Field', 'Raw value', 'Candidate label', 'Grade'],
            ['room_action', '0', 'no-action', 'Hypothesis'],
            ['room_action', '1', 'switch-on', 'Hypothesis'],
            ['room_action', '2', 'thermostat', 'Hypothesis'],
            ['room_action', '3', 'unlabeled', 'Hypothesis'],
            ['holiday_status', '0', '0', 'Hypothesis'],
            ['holiday_status', '1', '1', 'Hypothesis'],
            ['holiday_status', '2', 'unlabeled', 'Hypothesis']],
        'Unresolved write alternatives': [
            ['Family', 'Variant', 'Direction', 'Service', 'Operation', 'Alternative', 'Extent (bytes)', 'Grade'],
            ['Vaillant', 'remote-control', 'absent', 'absent', 'absent', 'remote-control-write', 'absent', 'Hypothesis'],
            ['Vaillant', 'UI-direction', 'absent', 'B50D', 'absent', 'UI-direction-write', 'absent', 'Hypothesis']],
        'Unknown physical properties': [['Property', 'Grade']] + [[item, 'Unknown'] for item in UNKNOWN],
    }


CLAIMS = (
    'These Vaillant family declarations are **Hypothesis**.',
    'that software result is **Proven** when checked, while physical interpretation remains **Hypothesis** and qualification remains **Unknown**.',
    'Holiday number is separate from circuit/room identity.',
    'Raw bytes and unlabeled values remain independent of candidate interpretation.',
    'A contradictory default does not invalidate other useful fields or establish a physical effect.',
    'All rows have family `Vaillant`, variant, direction and service absent, and alternative `field-declaration`.',
    '`absent` means unspecified, never zero. No field offsets are declared.',
    'Holiday number and all six calendar components default to zero.',
    'Zero day/month conflicts with calendar domains; it is not a valid calendar date and does not mean delete, disable or reset.',
    'Calendar year interpretation remains Unknown.',
    'OP02 setpoint has candidate bounds 5..30 degrees C.',
    'Default zero lies outside those bounds. Values remain raw, without clipping.',
    'Off/frost/deletion meaning is Unknown, including for zero.',
    'Room-action and holiday-status defaults are zero.',
    'Holiday status 0/1 is a raw value declaration with no on/off interpretation.',
    'Other raw values stay unlabeled.',
    'The four keycode bytes are independent numeric bytes, not ASCII, packed decimal or a u32.',
    'The synthetic bytes [1,2,3,4] retain four independent numeric values.',
    'A circuit name occupies exactly ten ASCII characters (ten bytes).',
    'Nine and eleven ASCII bytes do not match that declaration.',
    'Padding, trimming, NUL termination, UTF-8 and truncation are Unknown;',
    'These alternatives remain separate.',
    'Their direction, operation, offsets and extents are absent;',
    'The remote-control alternative has no declared service here.',
    'B50D is named only for the UI-direction alternative; neither alternative is paired with B50C reads.',
    'No operation numbers beyond OP02 or field offsets are supplied.',
    'Unspecified extents remain absent.',
    'These declarations grant no runtime capability, transmit route or write admission, and provide no automatic native qualification.',
)


def assert_page(case, page):
    case.assertEqual(tables(page), expected_tables())
    normalized = ' '.join(page.split())
    for claim in CLAIMS:
        case.assertIn(claim, normalized)


class HolidayTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_exact_declarations_and_grades(self):
        assert_declarations(self, self.doc)

    def test_page_tables_and_claims(self):
        assert_page(self, self.page)

    def test_calendar_conflicts(self):
        self.assertEqual(self.doc['examples']['calendar_defaults'], [
            {'field': 'start_day', 'raw': 0, 'calendar_valid': False, 'conflict': True, 'meaning': 'Unknown'},
            {'field': 'start_month', 'raw': 0, 'calendar_valid': False, 'conflict': True, 'meaning': 'Unknown'},
            {'field': 'end_day', 'raw': 0, 'calendar_valid': False, 'conflict': True, 'meaning': 'Unknown'},
            {'field': 'end_month', 'raw': 0, 'calendar_valid': False, 'conflict': True, 'meaning': 'Unknown'},
        ])

    def test_setpoint_conversion_without_clipping(self):
        self.assertEqual(self.doc['examples']['setpoints'], [
            {'raw': 0, 'degrees_c': 0, 'inside_candidate_bounds': False, 'meaning': 'Unknown'},
            {'raw': 5, 'degrees_c': 5, 'inside_candidate_bounds': True, 'meaning': 'Unknown'},
            {'raw': 30, 'degrees_c': 30, 'inside_candidate_bounds': True, 'meaning': 'Unknown'},
            {'raw': 31, 'degrees_c': 31, 'inside_candidate_bounds': False, 'meaning': 'Unknown'},
        ])

    def test_enums_preserve_unlabeled_values(self):
        self.assertEqual(self.doc['examples']['room_actions'], [
            {'raw': 0, 'label': 'no-action'}, {'raw': 1, 'label': 'switch-on'},
            {'raw': 2, 'label': 'thermostat'}, {'raw': 3, 'label': None}])
        self.assertEqual(self.doc['examples']['holiday_states'], [
            {'raw': 0, 'label': '0'}, {'raw': 1, 'label': '1'}, {'raw': 2, 'label': None}])

    def test_independent_numeric_keycode(self):
        self.assertEqual(self.doc['examples']['keycode'], [1, 2, 3, 4])
        for value in self.doc['examples']['keycode']:
            self.assertIs(type(value), int)

    def test_ascii_extent(self):
        examples = self.doc['examples']['circuit_names']
        self.assertEqual(examples, [
            {'raw_ascii': 'ABCDEFGHI', 'matches_declared_extent': False},
            {'raw_ascii': 'ABCDEFGHIJ', 'matches_declared_extent': True},
            {'raw_ascii': 'ABCDEFGHIJK', 'matches_declared_extent': False}])
        width = self.doc['fields'][14]['extent_bytes']
        for text, expected in [('ABCDEFGHI', False), ('ABCDEFGHIJ', True),
                               ('ABCDEFGHIJK', False), ('ABCDEFGHIé', False)]:
            with self.subTest(text=text):
                self.assertEqual(text.isascii() and len(text.encode('utf-8')) == width, expected)

    def test_each_identity_axis_rejects_mutation(self):
        assert_declarations(self, self.doc)  # valid control
        for index in range(17):
            for axis in AXES:
                with self.subTest(field=index, axis=axis):
                    mutant = copy.deepcopy(self.doc)
                    mutant['fields'][index][axis] = 'changed'
                    with self.assertRaises(AssertionError):
                        assert_declarations(self, mutant)

    def test_each_declaration_property_rejects_mutation(self):
        assert_declarations(self, self.doc)
        for index, row in enumerate(self.doc['fields']):
            for key in row:
                with self.subTest(field=index, property=key):
                    mutant = copy.deepcopy(self.doc)
                    mutant['fields'][index][key] = 0 if row[key] is None else 'changed'
                    with self.assertRaises(AssertionError):
                        assert_declarations(self, mutant)
        mutant = copy.deepcopy(self.doc)
        mutant['fields'].pop()
        with self.assertRaises(AssertionError):
            assert_declarations(self, mutant)

    def test_each_page_cell_and_claim_rejects_mutation(self):
        assert_page(self, self.page)
        for line in self.page.splitlines():
            if line.startswith('|') and not set(line) <= set('|-: '):
                cells = line.split('|')
                for index in range(1, len(cells) - 1):
                    with self.subTest(row=line, column=index):
                        mutated = cells.copy()
                        mutated[index] = ' changed '
                        with self.assertRaises(AssertionError):
                            assert_page(self, self.page.replace(line, '|'.join(mutated), 1))
        for claim in CLAIMS:
            pattern = r'\s+'.join(re.escape(word) for word in claim.split())
            mutant, count = re.subn(pattern, 'changed', self.page, count=1)
            self.assertEqual(count, 1)
            with self.subTest(claim=claim):
                with self.assertRaises(AssertionError):
                    assert_page(self, mutant)


if __name__ == '__main__':
    unittest.main()
