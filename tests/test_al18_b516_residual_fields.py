"""Offline document/example checks, without companion code or native execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('architecture/al18-b516-residual-fields.md')
FIXTURE = Path('architecture/fixtures/al18_b516_residual_fields.json')
AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
        'field', 'alternative', 'group', 'instance_scope', 'register')
ORDER = ['minute', 'hour', 'day', 'month', 'year']
KEY_ROWS = [
    ['family', 'exact family token'],
    ['variant', 'exact variant token; synthetic token is not a native association'],
    ['primary', 'exact primary service'],
    ['secondary', 'null differs from zero'],
    ['operation', 'null differs from zero; OP02/03/08/0D/0E remain distinct'],
    ['direction', 'explicit none token differs from request or positive'],
    ['field', 'exact field token'],
    ['alternative', 'explicit none token differs from a named alternative'],
    ['group', 'null differs from zero; no B524 group is inferred'],
    ['instance_scope', 'explicit none token differs from a supplied scope'],
    ['register', 'null differs from zero; no B524 register is inferred'],
]
RESIDUAL_ROWS = [
    ['OP08', 'setpoint u8 / 2 degrees Celsius; mode; special-function; five independent message bytes; then minute/hour/day/month/year',
     'Hypothesis; unprovided widths, offsets and variant associations Unknown'],
    ['OP08 clock', 'FF replacement selection precedes packed-decimal validation; FA remains invalid/raw',
     'Hypothesis; replacement meaning, century and timezone Unknown'],
    ['OP0D', 'four independent raw little-endian u16 fields',
     'Hypothesis; units, labels, sentinels, offsets and variant associations Unknown'],
    ['OP0E', 'page plus variable raw data, including empty metadata',
     'Hypothesis; page width, data maximum and peer acceptance Unknown'],
    ['OP02', 'minute metadata on a second field conflicts with unprovided field associations; day/month default0 is out-of-domain',
     'Hypothesis; associations unresolved, calendar conflict retained'],
    ['voltage', 'conversion is variant-specific', 'Unknown here; no converter selected'],
    ['OP03', 'decimal software-version structures and identity-bearing structures exist as candidates',
     'Hypothesis; unprovided fields not imported or instantiated'],
]
REQUIRED_PROSE = (
    'The catalog prerequisite must merge before this page.',
    'Its merge and runtime checks are unverified here;',
    'no cross-repository runtime import is added.',
    '`Ab51Entries()` enumerates finite catalog metadata or returns an error.',
    '`Ab51Lookup(key)` returns one exact entry, a found flag and an error.',
    'An exact miss returns no usable entry, false and no error.',
    'lookup returns no usable entry, false and an error.',
    'The entire catalog must validate before a matching entry is admitted, including invalid later entries.',
    'Malformed JSON, trailing input, unknown properties, incomplete or duplicate exact keys and invalid grades fail closed.',
    'no wildcard, normalization, case folding, cross-family fallback or nearest match is permitted.',
    'Every returned enumeration and lookup owns independent memory, including nested maps, slices, raw buffers and optional key storage.',
    'Mutating one result must not change another held result or a later call.',
    'On failure preserve previously retained, independently owned last-known-good state and its raw provenance.',
    'Failed new data must not be admitted as fresh or qualified.',
    'Independently useful fields survive a partial interpretation failure;',
    'The clock has exactly five components, **minute/hour/day/month/year**, with no seconds.',
    'For each clock component, retain raw FF and select replacement before decimal validation.',
    'Raw 12 yields 12 under packed-decimal conversion, not 18 as a plain unsigned byte; FA has no decoded value.',
    'OP0D words 00 00, 01 00, 00 01, FF FF yield 0, 1, 256, 65535.',
    'OP0E page width stays null, not u8 by analogy.',
    'Variable data has no established maximum.',
    'Empty data is a metadata example, not evidence of peer acceptance.',
    'day/month default0 conflicts with their 1-based calendar domains',
    'total catalog size is Unknown.',
    'eBUS MCP compatibility and GraphQL parity remain requirements for later integration;',
    'Nothing is stable before Helianthus 1.0.',
    'No authorization gate is introduced before 0.9; roadmap wording remains 0.11.',
)


def tables(text):
    result, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            result.append(current[2:])
            current = []
    return result


def time_component(raw):
    """Synthetic arithmetic oracle only; no wire acceptance or calendar codec."""
    number = int(raw, 16)
    if number == 255:
        return 'replacement', None
    high, low = divmod(number, 16)
    if high > 9 or low > 9:
        return 'invalid', None
    return 'value', high * 10 + low


def partial_clock(raw, previous):
    # A retained value is separate from the new raw token and interpretation.
    result = []
    for token, old in zip(raw, previous):
        status, value = time_component(token)
        result.append(dict(raw=token, status=status, value=value,
                           useful=value if status == 'value' else old))
    return result


class ResidualFieldsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / FIXTURE).read_text())
        self.page = (ROOT / PAGE).read_text()

    def check_fixture(self, data):
        self.assertEqual(set(data), {'scope', 'grades', 'qualification', 'unknown',
                                     'clock_rule', 'examples'})
        self.assertEqual(data['scope'],
                         'synthetic representation examples only; not a catalog or native profile')
        self.assertEqual(data['grades'], dict(candidate_interpretation='Hypothesis',
                                             synthetic_arithmetic='Proven', companion_runtime='Unknown'))
        self.assertEqual(data['qualification'], dict.fromkeys(
            ('physical', 'presence', 'freshness', 'execution', 'effects', 'persistence', 'delivery'), 'Unknown'))
        self.assertEqual(data['unknown'], dict.fromkeys(
            ('catalog_size', 'offsets', 'variant_associations', 'clock_widths',
             'mode_width', 'special_function_width', 'century', 'timezone',
             'voltage_conversion', 'op03_fields')))
        self.assertEqual(data['clock_rule'], dict(
            order=ORDER, replacement_before_decimal=True, replacement_meaning=None,
            controls=[dict(raw='12', status='value', value=12),
                      dict(raw='FF', status='replacement', value=None),
                      dict(raw='FA', status='invalid', value=None)]))
        rows = data['examples']
        self.assertEqual(len(rows), 4)  # Examples, never a production catalog count.
        for row, operation, field in zip(rows, (8, 13, 14, 2),
                                         ('clock-message', 'raw-words', 'page-data', 'calendar-conflicts')):
            self.assertEqual(row['key'], dict(
                family='B516', variant='synthetic-residual', primary=181, secondary=22,
                operation=operation, direction='none', field=field, alternative='none',
                group=None, instance_scope='none', register=None))
        self.assertEqual({k: v for k, v in rows[0].items() if k != 'key'}, dict(
            setpoint=dict(raw='12', encoding='u8/2', value=9, unit='degrees Celsius'),
            mode_raw='21', special_function_raw='31', message_bytes=['41', '42', '43', '44', '45'],
            clock_raw=['12', '23', '31', '12', '99'], clock_values=[12, 23, 31, 12, 99]))
        self.assertEqual({k: v for k, v in rows[1].items() if k != 'key'}, dict(
            raw_words=['00 00', '01 00', '00 01', 'FF FF'], values=[0, 1, 256, 65535],
            unit=None, labels=None, sentinels=None))
        self.assertEqual({k: v for k, v in rows[2].items() if k != 'key'}, dict(
            page_raw=None, page_width=None, maximum_data_length=None,
            peer_acceptance='Unknown', data_examples=['', '01AB']))
        self.assertEqual({k: v for k, v in rows[3].items() if k != 'key'}, dict(
            second_field_minute_metadata=True, field_associations=None,
            conflicts=[dict(field='day', default=0, calendar_domain='starts at 1', status='out-of-domain'),
                       dict(field='month', default=0, calendar_domain='starts at 1', status='out-of-domain')]))

    def test_fixture_contract(self):
        self.check_fixture(self.data)

    def test_page_tables(self):
        self.assertEqual(tables(self.page), [KEY_ROWS, RESIDUAL_ROWS])

    def test_page_boundaries(self):
        text = ' '.join(self.page.split())
        for phrase in REQUIRED_PROSE:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn('../protocols/vaillant/ebus-vaillant-b516-energy.md#10-other-b516-sub-ids-candidate', text)
        self.assertIn('fixtures/al18_b516_residual_fields.json', text)
        self.assertIn('Synthetic examples deliberately supply no native direction or variant association.', text)

    def test_packed_decimal_replacement_and_invalid_raw(self):
        for control, expected in zip(self.data['clock_rule']['controls'],
                                     (('value', 12), ('replacement', None), ('invalid', None))):
            with self.subTest(raw=control['raw']):
                self.assertEqual(time_component(control['raw']), expected)
                self.assertEqual((control['status'], control['value']), expected)
        self.assertNotEqual(time_component('12')[1], 18)

    def test_clock_order_and_each_component_independently(self):
        raw = self.data['examples'][0]['clock_raw']
        self.assertEqual([time_component(token)[1] for token in raw], [12, 23, 31, 12, 99])
        controls = [('13', 13), ('22', 22), ('30', 30), ('11', 11), ('98', 98)]
        for index, (token, value) in enumerate(controls):
            with self.subTest(component=ORDER[index]):
                changed = raw.copy()
                changed[index] = token
                expected = [12, 23, 31, 12, 99]
                expected[index] = value
                self.assertEqual([time_component(t)[1] for t in changed], expected)

    def test_partial_clock_failure_at_each_position(self):
        previous = [10, 20, 29, 10, 98]
        raw = self.data['examples'][0]['clock_raw']
        for index in range(5):
            for token, status in (('FF', 'replacement'), ('FA', 'invalid')):
                with self.subTest(component=ORDER[index], token=token):
                    changed = raw.copy()
                    changed[index] = token
                    result = partial_clock(changed, previous)
                    self.assertEqual([r['raw'] for r in result], changed)
                    self.assertEqual(result[index], dict(raw=token, status=status,
                                                         value=None, useful=previous[index]))
                    for other in range(5):
                        if other != index:
                            self.assertEqual(result[other]['useful'], [12, 23, 31, 12, 99][other])
                            self.assertEqual(result[other]['status'], 'value')
        self.assertEqual(previous, [10, 20, 29, 10, 98])

    def test_setpoint_binary_u8_half_scale(self):
        point = self.data['examples'][0]['setpoint']
        self.assertEqual(int(point['raw'], 16) / 2, 9)
        for raw, expected in (('00', 0), ('01', 0.5), ('FF', 127.5)):
            with self.subTest(raw=raw):
                self.assertEqual(int(raw, 16) / 2, expected)

    def test_independent_raw_messages_mode_and_special_function(self):
        row = self.data['examples'][0]
        for field in ('mode_raw', 'special_function_raw', 'message_bytes'):
            count = 5 if field == 'message_bytes' else 1
            for index in range(count):
                with self.subTest(field=field, index=index):
                    changed = copy.deepcopy(row)
                    if field == 'message_bytes':
                        changed[field][index] = '51'
                    else:
                        changed[field] = '51'
                    # Independent raw slots, without assigning a native codec or offset.
                    for other in row:
                        if other != field:
                            self.assertEqual(changed[other], row[other])
                    if field == 'message_bytes':
                        self.assertEqual(len(changed[field]), 5)
                        self.assertEqual([v for i, v in enumerate(changed[field]) if i != index],
                                         [v for i, v in enumerate(row[field]) if i != index])

    def test_four_words_and_each_word_independently(self):
        raw = self.data['examples'][1]['raw_words']
        self.assertEqual([int.from_bytes(bytes.fromhex(w), 'little') for w in raw], [0, 1, 256, 65535])
        for index, (token, expected_value) in enumerate(
                (('02 00', 2), ('00 02', 512), ('02 01', 258), ('FE FF', 65534))):
            with self.subTest(word=index):
                changed = raw.copy()
                changed[index] = token
                expected = [0, 1, 256, 65535]
                expected[index] = expected_value
                self.assertEqual([int.from_bytes(bytes.fromhex(w), 'little') for w in changed], expected)
        # Each byte within a word independently detects endianness/byte loss.
        self.assertEqual(int.from_bytes(bytes.fromhex('01 00'), 'little'), 1)
        self.assertEqual(int.from_bytes(bytes.fromhex('00 01'), 'little'), 256)

    def test_variable_empty_metadata_without_maximum_or_page_width(self):
        row = self.data['examples'][2]
        self.assertEqual([bytes.fromhex(v) for v in row['data_examples']], [b'', b'\x01\xab'])
        for field in ('page_raw', 'page_width', 'maximum_data_length'):
            self.assertIsNone(row[field])
        self.assertEqual(row['peer_acceptance'], 'Unknown')

    def test_calendar_conflicts_and_unprovided_associations(self):
        row = self.data['examples'][3]
        self.assertTrue(row['second_field_minute_metadata'])
        self.assertIsNone(row['field_associations'])
        for conflict, field in zip(row['conflicts'], ('day', 'month')):
            with self.subTest(field=field):
                self.assertEqual(conflict['field'], field)
                self.assertEqual(conflict['default'], 0)
                self.assertLess(conflict['default'], 1)
                self.assertEqual(conflict['status'], 'out-of-domain')

    def test_each_key_axis_sensitive_in_disposable_fixture(self):
        # These test the document validator, never the unimported production lookup.
        changes = dict(family='B517', variant='other-residual', primary=182,
                       secondary=0, operation=0, direction='request', field='other-field',
                       alternative='other-alternative', group=0, instance_scope='00', register=0)
        scratch = ROOT / '.tmp'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            target = Path(directory) / FIXTURE.name
            target.write_text(json.dumps(self.data))
            self.check_fixture(json.loads(target.read_text()))
            for row_index in range(4):
                for axis in AXES:
                    with self.subTest(row=row_index, axis=axis):
                        changed = copy.deepcopy(self.data)
                        changed['examples'][row_index]['key'][axis] = changes[axis]
                        target.write_text(json.dumps(changed))
                        with self.assertRaises(AssertionError):
                            self.check_fixture(json.loads(target.read_text()))
            for axis in ('secondary', 'operation', 'group', 'register'):
                for value in (None, 0):
                    if self.data['examples'][0]['key'][axis] == value:
                        continue
                    with self.subTest(optional_axis=axis, value=value):
                        changed = copy.deepcopy(self.data)
                        changed['examples'][0]['key'][axis] = value
                        target.write_text(json.dumps(changed))
                        with self.assertRaises(AssertionError):
                            self.check_fixture(json.loads(target.read_text()))

    def test_each_scenario_axis_sensitive_in_disposable_fixture(self):
        # Change one declared leaf at a time; the untouched control passes first.
        # This is artifact sensitivity, not an executed production mutation kill.
        def leaves(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key != 'key':  # Every identity axis is tested separately above.
                        yield from leaves(child, path + (key,))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from leaves(child, path + (index,))
            else:
                yield path, value

        scratch = ROOT / '.tmp'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            target = Path(directory) / FIXTURE.name
            target.write_text(json.dumps(self.data))
            self.check_fixture(json.loads(target.read_text()))
            for path, value in leaves(self.data):
                with self.subTest(axis=path):
                    changed = copy.deepcopy(self.data)
                    parent = changed
                    for step in path[:-1]:
                        parent = parent[step]
                    if value is None:
                        replacement = 0
                    elif isinstance(value, bool):
                        replacement = not value
                    elif isinstance(value, int):
                        replacement = value + 1
                    elif value in ('Hypothesis', 'Unknown', 'Proven'):
                        replacement = 'Proven' if value != 'Proven' else 'Hypothesis'
                    elif value and all(c in '0123456789ABCDEF ' for c in value):
                        replacement = '01' if value != '01' else '02'
                    else:
                        replacement = value + '-control'
                    parent[path[-1]] = replacement
                    target.write_text(json.dumps(changed))
                    with self.assertRaises(AssertionError):
                        self.check_fixture(json.loads(target.read_text()))


if __name__ == '__main__':
    unittest.main()
