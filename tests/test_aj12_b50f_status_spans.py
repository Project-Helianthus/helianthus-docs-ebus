"""Offline documentation contracts; no library runtime or wire decoder is exercised."""

import copy
import json
from pathlib import Path
import tempfile
import unittest


AB12_ROOT = Path(__file__).resolve().parents[1]
AB12_NATIVE = Path('protocols/vaillant/ebus-b50f-status-spans.md')
AB12_FIXTURE = Path('protocols/vaillant/fixtures/aj12_b50f_status_spans.json')
AB12_API = Path('architecture/aj12_b50f_status_spans_api.md')
AB12_FIELDS = (
    'status_container_1', 'status_container_2', 'status_container_3',
    'status_container_4', 'status_container_5', 'status_container_6',
    'burner_status', 'gas_pump_status',
)
AB12_MASKS = (0x7F, 0x7F, 0x7F, 0xFF, 0x0F, 0x07)
AB12_RESERVED = (0x80, 0x80, 0x80, 0x00, 0xF0, 0xF8)
AB12_ROWS = (
    ('status_container_1', '0x7F', '0x80', 'Unknown', 'Unknown'),
    ('status_container_2', '0x7F', '0x80', 'Unknown', 'Unknown'),
    ('status_container_3', '0x7F', '0x80', 'temperature-limit', 'Unknown'),
    ('status_container_4', '0xFF', '0x00', 'plausibility/channel', 'Unknown'),
    ('status_container_5', '0x0F', '0xF0', 'Unknown',
     'valve_1_open, valve_1_error, valve_2_open, valve_2_error'),
    ('status_container_6', '0x07', '0xF8', 'Unknown', 'valve_open, error, air_check'),
    ('burner_status', 'Unknown', 'Unknown', 'Unknown', 'Unknown'),
    ('gas_pump_status', 'Unknown', 'Unknown', 'Unknown', 'Unknown'),
)
AB12_AXES = (
    ('Ab12Family', 'string'), ('Ab12Variant', 'string'),
    ('Ab12Primary', 'byte'), ('Ab12Secondary', '*byte'),
    ('Ab12Operation', '*byte'), ('Ab12Direction', '*string'),
    ('Ab12Field', 'string'), ('Ab12Group', '*byte'),
    ('Ab12RequestedInstance', '*byte'), ('Ab12Register', '*uint16'),
    ('Ab12CommandRole', '*string'),
)
AB12_SIGNATURES = (
    'Ab12Entries() ([]Ab12Entry, error)',
    'Ab12Lookup(key Ab12Key) (Ab12Entry, bool, error)',
)
AB12_PREDICATES = (
    'absence differs from an explicit zero',
    'absent strings differ from empty\nstrings',
    'Values are compared, never pointer addresses',
    'OP=0x02 and OP=0x06 never collapse',
    'independently owned nested\ndata',
    'share no mutable storage',
    'Mutating a returned value cannot\nalter a later result or another entry',
    'missing key returns an empty `Ab12Entry`, false and no error',
    'Invalid embedded data returns an error',
    '`Ab12Entries` returns no entries',
    '`Ab12Lookup` returns an empty entry and false',
    'Admission fails closed',
    'incomplete or duplicate identities',
    'invalid grade/unknown metadata',
    'malformed data must not become a missing-key\nsuccess',
    'does not erase earlier evidence',
    'Nothing is stable before\n1.0',
    '`Ab12Grade` is Hypothesis',
    '`Ab12Qualification` (Unknown)',
    '`Ab12CoordinateGrade` (Unknown)',
    '`Ab12Position` is absent',
    'An absent label remains absent',
    'including\nreserved bits',
)


def ab12_table(ab12_text, ab12_header):
    ab12_lines = ab12_text.splitlines()
    ab12_start = ab12_lines.index(ab12_header) + 2
    ab12_rows = []
    for ab12_line in ab12_lines[ab12_start:]:
        if not ab12_line.startswith('|'):
            break
        ab12_rows.append(tuple(ab12_cell.strip() for ab12_cell in
                               ab12_line.strip('|').split('|')))
    return ab12_rows


class Ab12StatusSpans(unittest.TestCase):
    def ab12_validate(self, ab12_root):
        ab12_native = (ab12_root / AB12_NATIVE).read_text()
        ab12_data = json.loads((ab12_root / AB12_FIXTURE).read_text())
        ab12_api = (ab12_root / AB12_API).read_text()
        self.assertEqual(ab12_table(ab12_native,
            '| Field | Allocated mask | Reserved mask | Allocated category | Individual names | Grade | Coordinate grade | Qualification |'),
            [ab12_row + ('Hypothesis', 'Unknown', 'Unknown') for ab12_row in AB12_ROWS])
        for ab12_fact in (
            'PB=0xB5, SB=0x0F, OP=0x02, variant B50F, family vaillant',
            'Direction, source, destination, absolute byte coordinates, product and firmware\ncontext, and physical qualification are **Unknown**',
            'not byte offsets or adjacency', 'Each span is eight bits',
            'individual channel names remain Unknown',
            'Reserved bits have no\nassigned semantic name',
            'OP03 demand-bit names and integrity-byte coordinates do not apply here',
            'Missing bytes remain absent, distinct from explicit zero',
            'a\npartial tuple retains its available bytes',
            'A last-known-good value remains separate',
            'No entry is Proven', 'No physical PDU is constructed',
        ):
            self.assertIn(ab12_fact, ab12_native)
        self.assertEqual(set(ab12_data), {
            'provenance', 'selectors', 'grade', 'coordinate_grade',
            'qualification', 'position', 'cases'})
        self.assertEqual(ab12_data['provenance'], 'synthetic; no physical PDU')
        self.assertEqual(ab12_data['selectors'], {
            'family': 'vaillant', 'variant': 'B50F', 'primary': 0xB5,
            'secondary': 0x0F, 'operation': 0x02, 'direction': None})
        for ab12_axis, ab12_expected in (
            ('grade', 'Hypothesis'), ('coordinate_grade', 'Unknown'),
            ('qualification', 'Unknown'), ('position', None),
        ):
            self.assertEqual(ab12_data[ab12_axis], ab12_expected)
        ab12_expected_cases = []
        for ab12_container in range(6):
            for ab12_bit in range(8):
                for ab12_side in range(2):
                    ab12_raw = dict.fromkeys(AB12_FIELDS, 0)
                    ab12_raw[AB12_FIELDS[ab12_container]] = 2 ** ab12_bit
                    ab12_raw[AB12_FIELDS[6 + ab12_side]] = 255 - 2 ** ab12_bit
                    ab12_expected_cases.append({
                        'case': f'container_{ab12_container+1}_bit_{ab12_bit}_raw_{ab12_side}',
                        'raw': ab12_raw})
        for ab12_container, ab12_values in enumerate(
                ((0x80, 0x7F), (0x80, 0x7F), (0x80, 0x7F),
                 (0xFF,), (0xF0,), (0xF8,))):
            for ab12_value in ab12_values:
                ab12_raw = dict.fromkeys(AB12_FIELDS, 0)
                ab12_raw[AB12_FIELDS[ab12_container]] = ab12_value
                ab12_expected_cases.append({
                    'case': f'partition_{ab12_container+1}_{ab12_value}', 'raw': ab12_raw})
        ab12_expected_cases.append({
            'case': 'partial', 'raw': {'status_container_2': 0, 'burner_status': 165},
            'last_known_good': {'status_container_1': 128, 'gas_pump_status': 90}})
        self.assertEqual(ab12_data['cases'], ab12_expected_cases)
        for ab12_case in ab12_data['cases'][:-1]:
            for ab12_index in range(6):
                ab12_raw = ab12_case['raw'][AB12_FIELDS[ab12_index]]
                self.assertIs(type(ab12_raw), int)
                self.assertEqual((ab12_raw & AB12_MASKS[ab12_index]) |
                                 (ab12_raw & AB12_RESERVED[ab12_index]), ab12_raw)
        self.assertEqual(ab12_table(ab12_api, '| Field | Type | Meaning |'),
                         [(ab12_name, ab12_type, ab12_meaning) for
                          (ab12_name, ab12_type), ab12_meaning in zip(AB12_AXES, (
                              'Device family', 'Native variant', 'Primary selector',
                              'Optional secondary selector', 'Optional operation',
                              'Optional direction', 'Independent field identity',
                              'B524 group', 'B524 requested instance',
                              'B524 register', 'B524 command role'))])
        ab12_code = ab12_api.split('```go\n')[1].split('```')[0].strip().splitlines()
        self.assertEqual(ab12_code, list(AB12_SIGNATURES))
        for ab12_predicate in AB12_PREDICATES:
            self.assertIn(ab12_predicate, ab12_api)

    def ab12_reject(self, ab12_path, ab12_text):
        # Mutated owned documents are exercised only in a disposable local copy.
        (AB12_ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ab12-', dir=AB12_ROOT / '.tmp') as ab12_temp:
            ab12_root = Path(ab12_temp)
            for ab12_file in (AB12_NATIVE, AB12_FIXTURE, AB12_API):
                (ab12_root / ab12_file).parent.mkdir(parents=True, exist_ok=True)
                (ab12_root / ab12_file).write_text((AB12_ROOT / ab12_file).read_text())
            (ab12_root / ab12_path).write_text(ab12_text)
            with self.assertRaises(AssertionError):
                self.ab12_validate(ab12_root)

    def test_ab12_valid_control(self):
        self.ab12_validate(AB12_ROOT)

    def test_ab12_each_native_field_and_predicate(self):
        ab12_text = (AB12_ROOT / AB12_NATIVE).read_text()
        for ab12_row in AB12_ROWS:
            ab12_full = '| ' + ' | '.join(ab12_row + ('Hypothesis', 'Unknown', 'Unknown')) + ' |'
            for ab12_column in range(8):
                with self.subTest(field=ab12_row[0], column=ab12_column):
                    ab12_cells = list(ab12_row + ('Hypothesis', 'Unknown', 'Unknown'))
                    ab12_cells[ab12_column] = ('Proven' if ab12_column == 5 else 'fabricated_demand')
                    self.ab12_reject(AB12_NATIVE, ab12_text.replace(
                        ab12_full, '| ' + ' | '.join(ab12_cells) + ' |'))
        for ab12_old in ('Missing bytes remain absent', 'No entry is Proven',
                         'A last-known-good value remains separate',
                         'No physical PDU is constructed',
                         'OP03 demand-bit names and integrity-byte coordinates do not apply here'):
            with self.subTest(predicate=ab12_old):
                self.ab12_reject(AB12_NATIVE, ab12_text.replace(ab12_old, 'fabricated'))

    def test_ab12_every_selector_grade_and_unknown(self):
        ab12_data = json.loads((AB12_ROOT / AB12_FIXTURE).read_text())
        for ab12_axis in ab12_data['selectors']:
            for ab12_value in (None, 0, 'synthetic_other'):
                if ab12_value == ab12_data['selectors'][ab12_axis]:
                    continue
                with self.subTest(axis=ab12_axis, value=ab12_value):
                    ab12_changed = copy.deepcopy(ab12_data)
                    ab12_changed['selectors'][ab12_axis] = ab12_value
                    self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))
        for ab12_axis, ab12_value in (
                ('grade', 'Proven'), ('coordinate_grade', 'Proven'),
                ('qualification', 'Proven'), ('position', 0),
                ('provenance', 'observed')):
            with self.subTest(axis=ab12_axis):
                ab12_changed = copy.deepcopy(ab12_data)
                ab12_changed[ab12_axis] = ab12_value
                self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))

    def test_ab12_single_bits_raw_alias_and_reserved_loss(self):
        ab12_data = json.loads((AB12_ROOT / AB12_FIXTURE).read_text())
        for ab12_index, ab12_case in enumerate(ab12_data['cases'][:-1]):
            for ab12_field, ab12_value in ab12_case['raw'].items():
                if not ab12_value:
                    continue
                with self.subTest(case=ab12_case['case'], field=ab12_field):
                    ab12_changed = copy.deepcopy(ab12_data)
                    ab12_changed['cases'][ab12_index]['raw'][ab12_field] = 0
                    self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))
        for ab12_field in AB12_FIELDS:
            ab12_changed = copy.deepcopy(ab12_data)
            del ab12_changed['cases'][0]['raw'][ab12_field]
            with self.subTest(missing_field=ab12_field):
                self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))
        for ab12_axis in ('raw', 'last_known_good'):
            ab12_changed = copy.deepcopy(ab12_data)
            ab12_changed['cases'][-1][ab12_axis]['status_container_1'] = 0
            with self.subTest(partial=ab12_axis):
                self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))

    def test_ab12_stated_document_mutations(self):
        ab12_text = (AB12_ROOT / AB12_NATIVE).read_text()
        ab12_common_mask = ab12_text
        for ab12_old, ab12_new in (
                ('0xFF | 0x00', '0x7F | 0x80'),
                ('0x0F | 0xF0', '0x7F | 0x80'),
                ('0x07 | 0xF8', '0x7F | 0x80')):
            ab12_common_mask = ab12_common_mask.replace(ab12_old, ab12_new)
        self.ab12_reject(AB12_NATIVE, ab12_common_mask)
        self.ab12_reject(AB12_NATIVE, ab12_text.replace(
            'Unknown | Unknown | Hypothesis', 'Unknown | demand | Hypothesis'))
        ab12_data = json.loads((AB12_ROOT / AB12_FIXTURE).read_text())
        for ab12_target, ab12_source in (
                ('burner_status', 'gas_pump_status'),
                ('gas_pump_status', 'burner_status'),
                ('burner_status', 'status_container_1'),
                ('status_container_1', 'burner_status')):
            ab12_changed = copy.deepcopy(ab12_data)
            for ab12_case in ab12_changed['cases'][:-1]:
                ab12_case['raw'][ab12_target] = ab12_case['raw'][ab12_source]
            with self.subTest(alias=(ab12_target, ab12_source)):
                self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))
        ab12_changed = copy.deepcopy(ab12_data)
        for ab12_case in ab12_changed['cases'][:-1]:
            for ab12_index in range(6):
                ab12_case['raw'][AB12_FIELDS[ab12_index]] &= AB12_MASKS[ab12_index]
        self.ab12_reject(AB12_FIXTURE, json.dumps(ab12_changed))

    def test_ab12_api_axes_signatures_and_predicates(self):
        ab12_text = (AB12_ROOT / AB12_API).read_text()
        for ab12_name, ab12_type in AB12_AXES:
            with self.subTest(axis=ab12_name):
                self.ab12_reject(AB12_API, ab12_text.replace(
                    f'| {ab12_name} | {ab12_type} |', f'| {ab12_name} | ignored |'))
        for ab12_fact in AB12_SIGNATURES + AB12_PREDICATES:
            with self.subTest(contract=ab12_fact):
                self.ab12_reject(AB12_API, ab12_text.replace(ab12_fact, 'fabricated'))


if __name__ == '__main__':
    unittest.main()
