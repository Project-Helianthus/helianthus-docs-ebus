"""Independent synthetic declaration checks; no runtime or physical qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ebus_standard/ai04-05-burner-bodies.md'
FIXTURE = PAGE.parent / 'fixtures/ai04_05_burner_bodies.json'

# Expected constants are independent of both published artifacts.
FIELDS = [
    (2, 'heat_state', 'u8', 0, 255, 0, None, 1, 0, 'Hypothesis'),
    (3, 'boiler_target', 'u8', 0, 90, 0, 'degC', 1, 0, 'Hypothesis'),
    (4, 'dhw_target', 'u8', 0, 90, 0, 'degC', 1, 0, 'Hypothesis'),
    (5, 'outside_temp', 'signed8', -128, 127, 0, 'degC', 1, 0, 'Hypothesis'),
    (6, 'setting_degree', 'u8', 0, 255, 0, '%', 1, 0, 'Hypothesis'),
]
KEYS = ('logical', 'name', 'carrier', 'minimum', 'maximum', 'default',
        'unit', 'scale', 'offset', 'grade')
LABELS = [('00', 'shutdown'), ('55', 'DHW'), ('AA', 'heating'),
          ('CC', 'emission check'), ('EE', 'controller stop')]
CASES = [
    ('heating', ['AA', '5A', '00', 'FF', 'FF'], [170, 90, 0, -1, 255], True),
    ('boiler_91', ['AA', '5B', '00', 'FF', 'FF'], [170, 91, 0, -1, 255], False),
    ('dhw_91', ['AA', '00', '5B', 'FF', 'FF'], [170, 0, 91, -1, 255], False),
    ('outside_3f', ['AA', '00', '00', '3F', 'FF'], [170, 0, 0, 63, 255], True),
    ('outside_min', ['00', '00', '00', '80', '00'], [0, 0, 0, -128, 0], True),
    ('outside_max', ['EE', '5A', '5A', '7F', 'FF'], [238, 90, 90, 127, 255], True),
]
UNKNOWNS = ['physical_positive_body', 'acknowledgement', 'outside_3F_replacement',
            'control_permission', 'scheduling', 'other_05_candidate_bodies',
            'physical_qualification', 'freshness', 'persistence', 'execution_permission']


HEADERS = {
    'Forms': ['Form', 'PB', 'SB', 'Logical fields', 'Grade', 'Interpretation'],
    'Candidate fields': ['Logical', 'Field', 'Carrier', 'Minimum', 'Maximum',
                         'Default', 'Unit', 'Scale', 'Offset', 'Grade'],
    'Candidate heat labels': ['Raw', 'Label', 'Grade'],
    'Synthetic results': ['Case', 'PB', 'SB', 'Raw fields', 'Values', 'Local valid', 'Grade'],
    'Unknowns': ['Property', 'Grade'],
}


def table(page, section):
    """Parse whole table bodies, detecting changed, duplicate or extra rows."""
    block = page.split('## ' + section + '\n', 1)[1].split('\n## ', 1)[0]
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in block.splitlines() if line.startswith('|')]
    if not rows or rows[0] != HEADERS[section]:
        raise ValueError("Unexpected table columns: " + section)
    return rows[2:]


def decode(fields, raw):
    """Local declaration arithmetic only; not a gateway implementation."""
    if len(raw) != len(fields) or any(type(b) is not int or not 0 <= b <= 255 for b in raw):
        return None
    values = []
    for field, byte in zip(fields, raw):
        signed = byte - 256 if field['carrier'] == 'signed8' and byte >= 128 else byte
        values.append(signed * field['scale'] + field['offset'])
    return values


def request_valid(data, family, form, pb, sb, raw):
    if (family, form, pb, sb) != (data['family'], data['forms'][0]['form'],
                                 data['forms'][0]['pb'], data['forms'][0]['sb']):
        return False
    values = decode(data['fields'], raw)
    return values is not None and all(f['minimum'] <= v <= f['maximum']
                                     for f, v in zip(data['fields'], values))


class BurnerMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()

    def test_fields_and_page_table(self):
        self.assertEqual(self.data['fields'], [dict(zip(KEYS, row)) for row in FIELDS])
        expected = [[str(value) if value is not None else 'none' for value in row]
                    for row in FIELDS]
        self.assertEqual(table(self.page, 'Candidate fields'), expected)

    def test_forms_and_page_table(self):
        self.assertEqual(self.data['forms'], [
            dict(form='request', pb=5, sb=1, logical_fields=[2, 3, 4, 5, 6],
                 grade='Hypothesis', interpretation='five independent bytes'),
            dict(form='positive', pb=5, sb=1, logical_fields=[],
                 grade='Hypothesis', interpretation='two constants only'),
            dict(form='standard_response', pb=5, sb=4, logical_fields=None,
                 grade='Proven', interpretation='standard three-field response; no candidate alias'),
        ])
        self.assertEqual(table(self.page, 'Forms'), [
            ['request', '05', '01', '2,3,4,5,6', 'Hypothesis', 'five independent bytes'],
            ['positive', '05', '01', 'none', 'Hypothesis', 'two constants only'],
            ['standard_response', '05', '04', 'separate', 'Proven',
             'standard three-field response; no candidate alias'],
        ])

    def test_heat_labels_and_separate_dd(self):
        self.assertEqual(self.data['heat_labels'], dict(LABELS))
        self.assertEqual(self.data['separate_check'], dict(raw='DD',
                         label='unresolved separate check', grade='Unknown', enabled=False))
        self.assertEqual(table(self.page, 'Candidate heat labels'),
                         [[raw, label, 'Hypothesis'] for raw, label in LABELS] +
                         [['DD', 'unresolved separate check', 'Unknown']])
        self.assertEqual(self.data['heat_labels']['AA'], 'heating')
        self.assertNotIn('DD', self.data['heat_labels'])

    def test_fixture_cases_and_page_results(self):
        expected = [dict(case=name, pb=5, sb=1, raw=raw, values=values,
                         local_valid=valid, grade='Hypothesis')
                    for name, raw, values, valid in CASES]
        self.assertEqual(self.data['cases'], expected)
        self.assertEqual(table(self.page, 'Synthetic results'), [
            [name, '05', '01', ','.join(raw), ','.join(map(str, values)),
             str(valid).lower(), 'Hypothesis'] for name, raw, values, valid in CASES])
        for case in self.data['cases']:
            with self.subTest(case=case['case']):
                raw = [int(byte, 16) for byte in case['raw']]
                self.assertEqual(decode(self.data['fields'], raw), case['values'])
                self.assertEqual(request_valid(self.data, 'Vaillant', 'request', 5, 1, raw),
                                 case['local_valid'])

    def test_every_identity_axis_independently(self):
        control = ('Vaillant', 'request', 5, 1)
        raw = [170, 90, 0, 255, 255]
        self.assertTrue(request_valid(self.data, *control, raw))
        # Each changed axis has the same valid control; no compound mismatch.
        for axis, replacement in enumerate(('other_family', 'positive', 6, 4)):
            changed = list(control)
            changed[axis] = replacement
            with self.subTest(axis=('family', 'form', 'PB', 'SB')[axis]):
                self.assertFalse(request_valid(self.data, *changed, raw))
        self.assertFalse(request_valid(self.data, 'Vaillant', 'standard_response',
                                       5, 4, [0, 0, 100]))

    def test_full_byte_arithmetic_and_independent_ranges(self):
        for byte in range(256):
            for index in range(5):
                raw = [0] * 5
                raw[index] = byte
                expected = [0] * 5
                expected[index] = byte - 256 if index == 3 and byte >= 128 else byte
                with self.subTest(field=index, byte=byte):
                    self.assertEqual(decode(self.data['fields'], raw), expected)
                    valid = byte <= 90 if index in (1, 2) else True
                    self.assertEqual(request_valid(self.data, 'Vaillant', 'request', 5, 1, raw), valid)

    def test_malformed_fields_fail_closed_and_retain_raw(self):
        # Local predicate only; deployed persistence is outside this suite.
        for raw in ([0] * 4, [0] * 6, [0, 0, 0, 0, 256],
                    [0, -1, 0, 0, 0], [0, 0, True, 0, 0], [0, 0, 0, 1.5, 0]):
            original = list(raw)
            self.assertFalse(request_valid(self.data, 'Vaillant', 'request', 5, 1, raw))
            self.assertEqual(raw, original)

    def test_positive_declaration_not_ack_or_echo(self):
        positive = self.data['positive']
        self.assertEqual(positive, dict(constants=[5, 1], feedback_fields=[],
                         physical_body='Unknown', acknowledgement='Unknown', echo='Unknown'))
        for constants, complete in (([5, 1], True), ([5], False),
                                    ([6, 1], False), ([5, 4], False),
                                    ([5, 1, 0], False)):
            with self.subTest(constants=constants):
                self.assertEqual(constants == positive['constants'], complete)

    def test_unknowns_and_synthetic_qualification(self):
        self.assertIs(self.data['synthetic'], True)
        self.assertEqual(self.data['family'], 'Vaillant')
        self.assertEqual(self.data['unknown'], UNKNOWNS)
        self.assertEqual(table(self.page, 'Unknowns'), [[name, 'Unknown'] for name in UNKNOWNS])
        self.assertIn('catalog presence does not make a standard\ncommand executable', self.page)
        self.assertIn('Logical coordinates are library positions, not physical offsets.', self.page)
        self.assertIn('Celsius unit metadata adds no scale or\noffset.', self.page)
        self.assertIn('Outside 3F remains numeric raw 63, with no candidate sentinel.', self.page)


if __name__ == '__main__':
    unittest.main()
