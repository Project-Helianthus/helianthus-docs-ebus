"""Finite documentation conformance; models below do not execute the Go API."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b516-directional-types.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak12_b516_directional_types.json'
API = ROOT / 'architecture/ak12_b516_directional_types_api.md'
ABSENT = object()
AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
        'field', 'alternative', 'group', 'instance_scope', 'register')
OPTIONAL = {'secondary': 255, 'operation': 255, 'group': 255, 'register': 65535}
UNKNOWN = ['encoded operation numbers', 'complete enum tables',
           'missing field positions', 'physical reply length', 'timeout', 'broadcast']
QUALIFICATION = dict.fromkeys(
    ('native_support', 'physical_effects', 'persistence', 'delivery'), 'Unknown')

# Independently authored finite expectations, never derived from a page or JSON.
RELATIONSHIPS = [
    ('generic-system-time', 'positive', 'system-time', 'header-only-positive', 'Hypothesis', 'Unknown'),
    ('other-system-time', 'positive', 'system-time', 'absent-positive', 'Hypothesis', 'Unknown'),
    ('energy-type', 'request', 'energy-type', 'raw-u8-enum', 'Hypothesis', 'Unknown'),
    ('energy-type', 'read-positive', 'energy-type', 'low-six-with-independent-flags', 'Hypothesis', 'Unknown'),
    ('energy-type', 'write-positive', 'energy-type', 'six-bit-scalar-with-unmodeled-upper-bits', 'Hypothesis', 'Unknown'),
]
FIELDS = [
    ('request', 'raw u8 token', 'part of enum token', 'part of enum token', 'Unknown', 'Unknown'),
    ('read-positive', 'low six bits', 'independent flag', 'independent flag', 'Unknown', 'Unknown'),
    ('write-positive', 'scalar six bits', 'unmodeled raw bit', 'unmodeled raw bit', 'Unknown', 'Unknown'),
]
CASES = [
    ('request-c1', 'energy-type', 'request', 'C1', 'enum-token=193', 'Hypothesis', 'Unknown'),
    ('read-c1', 'energy-type', 'read-positive', 'C1', 'low-six=1; bit6=true; bit7=true', 'Hypothesis', 'Unknown'),
    ('write-c1', 'energy-type', 'write-positive', 'C1', 'low-six=1; unmodeled=C0', 'Hypothesis', 'Unknown'),
    ('read-bit6', 'energy-type', 'read-positive', '40', 'low-six=0; bit6=true; bit7=false', 'Hypothesis', 'Unknown'),
    ('read-bit7', 'energy-type', 'read-positive', '80', 'low-six=0; bit6=false; bit7=true', 'Hypothesis', 'Unknown'),
    ('time-header', 'generic-system-time', 'positive', 'not supplied', 'header-only-positive', 'Hypothesis', 'Unknown'),
    ('time-absent', 'other-system-time', 'positive', 'not supplied', 'absent-positive', 'Hypothesis', 'Unknown'),
]
API_AXES = [
    ('Ab20Family', 'string', 'family', 'vaillant-b516'),
    ('Ab20Variant', 'string', 'variant', 'generic-system-time, other-system-time, energy-type'),
    ('Ab20Primary', 'uint8', 'primary', '181 (B5)'),
    ('Ab20Secondary', '*uint8', 'secondary', '22 (16)'),
    ('Ab20Operation', '*uint8', 'operation', 'absent'),
    ('Ab20Direction', 'string', 'direction', 'positive, request, read-positive, write-positive'),
    ('Ab20Field', 'string', 'field', 'system-time, energy-type'),
    ('Ab20Alternative', 'string', 'alternative', 'none'),
    ('Ab20Group', '*uint8', 'group', 'absent'),
    ('Ab20InstanceScope', 'string', 'instance_scope', 'none'),
    ('Ab20Register', '*uint16', 'register', 'absent'),
]
BEHAVIOR = [
    ('Exact hit', 'One whole row; found=true; error=nil'),
    ('Missing exact key', 'found=false; error=nil'),
    ('Invalid embedded JSON', 'error; no admitted result'),
    ('Duplicate complete key', 'error; no admitted result'),
    ('Lookup policy', 'All eleven axes; no wildcard or nearest-key lookup; no fallback'),
    ('Entries ownership', 'Independent deep byte copy on every call'),
    ('Lookup ownership', 'Independent deep byte copy on every call'),
    ('Return mutation', 'Changing any row or entries buffer cannot affect a later result'),
    ('Row contents', 'Ticket-prefixed ID; complete identity; fields and relations; candidate grade; explicit Unknown metadata; retained raw form'),
    ('Admission', 'Validate embedded JSON and identity uniqueness before exposing any row'),
]


def expected_rows():
    specs = [
        ('ak12-time-header', 'generic-system-time', 'positive', 'system-time',
         {'kind': 'header-only-positive'}, 'header-only-declaration'),
        ('ak12-time-absent', 'other-system-time', 'positive', 'system-time',
         {'kind': 'absent-positive'}, 'undeclared-positive'),
        ('ak12-energy-request', 'energy-type', 'request', 'energy-type',
         {'kind': 'raw-u8-enum', 'width_bits': 8}, 'u8-field-slice'),
        ('ak12-energy-read', 'energy-type', 'read-positive', 'energy-type',
         {'kind': 'low-six-with-independent-flags', 'value_bits': [0, 1, 2, 3, 4, 5],
          'independent_flags': {'bit6': 6, 'bit7': 7}}, 'u8-field-slice'),
        ('ak12-energy-write', 'energy-type', 'write-positive', 'energy-type',
         {'kind': 'six-bit-scalar-with-unmodeled-upper-bits',
          'value_bits': [0, 1, 2, 3, 4, 5], 'unmodeled_bits': [6, 7]}, 'u8-field-slice'),
    ]
    return [dict(id=i, identity=dict(family='vaillant-b516', variant=v, primary=181,
                                   secondary=22, direction=d, field=f,
                                   alternative='none', instance_scope='none'),
                 representation=r, raw_form=raw, grade='Hypothesis',
                 unknown=UNKNOWN[:], qualification=QUALIFICATION.copy(),
                 physical_reply_length='Unknown') for i, v, d, f, r, raw in specs]


def expected_cases():
    # Explicit tokens and results are independent of both data and table parsing.
    specs = [
        ('request-c1', 'ak12-energy-request', [193], {'enum_token': 193}),
        ('read-c1', 'ak12-energy-read', [193], {'low_six': 1, 'bit6': True, 'bit7': True}),
        ('write-c1', 'ak12-energy-write', [193], {'low_six': 1, 'unmodeled_raw': 192}),
        ('read-bit6', 'ak12-energy-read', [64], {'low_six': 0, 'bit6': True, 'bit7': False}),
        ('read-bit7', 'ak12-energy-read', [128], {'low_six': 0, 'bit6': False, 'bit7': True}),
        ('time-header', 'ak12-time-header', None, {'declared_positive': 'header-only-positive'}),
        ('time-absent', 'ak12-time-absent', None, {'declared_positive': 'absent-positive'}),
    ]
    result = []
    for i, row, raw, meaning in specs:
        item = dict(id=i, row=row, interpretation=meaning,
                    grade='Hypothesis', physical_reply_length='Unknown')
        if raw is not None:
            item['raw'] = raw
        result.append(item)
    return result


def table(page, name):
    block = page.split(f'<!-- {name}:start -->')[1].split(f'<!-- {name}:end -->')[0]
    lines = [line for line in block.splitlines() if line.startswith('|')]
    return [tuple(cell.strip() for cell in line.strip('|').split('|')) for line in lines[2:]]


def identity(key):
    """Test-only typed identity model; absent is never a numeric default."""
    if set(key) - set(AXES):
        raise ValueError('unknown axis')
    for axis in AXES:
        value = key.get(axis, ABSENT)
        if axis in OPTIONAL and value is ABSENT:
            continue
        if axis in OPTIONAL or axis == 'primary':
            if type(value) is not int or not 0 <= value <= OPTIONAL.get(axis, 255):
                raise ValueError(axis)
        elif type(value) is not str or not value:
            raise ValueError(axis)
    return tuple(key.get(axis, ABSENT) for axis in AXES)


def admit(raw):
    """Local JSON admission model, not the registry's Go parser."""
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise ValueError('array required')
    seen = set()
    for row in rows:
        k = identity(row['identity'])
        if k in seen:
            raise ValueError('duplicate complete key')
        seen.add(k)
    return copy.deepcopy(rows)


def lookup(rows, key):
    wanted = identity(key)
    for row in rows:
        if identity(row['identity']) == wanted:
            return copy.deepcopy(row)
    return None


def entries_buffer(rows):
    return bytearray(json.dumps(rows).encode())


def view(rows, key, raw, last_good=None):
    """Test-only field-slice model: no offsets, wire parsing or new API."""
    result = dict(raw=copy.deepcopy(raw), last_good=copy.deepcopy(last_good),
                  interpretation=None, grade='Hypothesis', status='unknown')
    try:
        row = lookup(rows, key)
    except ValueError:
        return result
    if row is None:
        return result
    result['grade'] = row['grade']
    if row['raw_form'] != 'u8-field-slice':
        return result
    if not isinstance(raw, list) or any(type(b) is not int or not 0 <= b <= 255 for b in raw):
        result['status'] = 'malformed'
        return result
    if len(raw) != 1:
        result['status'] = 'partial' if not raw else 'extra'
        return result
    rep, token = row['representation'], raw[0]
    kind = rep['kind']
    if kind == 'raw-u8-enum':
        meaning = {'enum_token': token}
    else:
        mask = sum(1 << bit for bit in rep['value_bits'])
        meaning = {'low_six': token & mask}
        if kind == 'low-six-with-independent-flags':
            meaning.update({label: bool(token & (1 << bit))
                            for label, bit in rep['independent_flags'].items()})
        elif kind == 'six-bit-scalar-with-unmodeled-upper-bits':
            meaning['unmodeled_raw'] = token & sum(1 << bit for bit in rep['unmodeled_bits'])
        else:
            return result
    result.update(status='candidate', interpretation=meaning)
    return result


class DirectionalTypes(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.rows = self.data['entries']
        self.native = NATIVE.read_text()
        self.api = API.read_text()

    def test_exact_native_fixture(self):
        self.assertEqual(self.data, dict(service='B516', provenance='synthetic',
                                        grade='Hypothesis', entries=expected_rows(),
                                        cases=expected_cases()))

    def test_native_relationship_and_bit_tables(self):
        self.assertEqual(table(self.native, 'relationships'), RELATIONSHIPS)
        self.assertEqual(table(self.native, 'fields'), FIELDS)

    def test_native_cases(self):
        self.assertEqual(table(self.native, 'cases'), CASES)

    def test_native_unknowns_and_boundary(self):
        self.assertEqual(table(self.native, 'unknowns'), [
            ('Encoded operation numbers', 'Unknown; absent'),
            ('Complete enum tables', 'Unknown; absent'),
            ('Missing field positions', 'Unknown; absent'),
            ('Physical reply length', 'Unknown'), ('Timeout', 'Unknown'),
            ('Broadcast', 'Unknown'), ('Native support', 'Unknown'),
            ('Physical effects', 'Unknown'), ('Persistence', 'Unknown'), ('Delivery', 'Unknown')])
        self.assertIn('An absent declaration does not mean a zero-length physical reply.', self.native)
        self.assertIn('unmodeled, not reserved-zero', self.native)
        self.assertNotRegex(self.native + DATA.read_text(), r'Ab20|GraphQL|\bMCP\b|json.RawMessage|gateway version')
        for row in self.rows:
            for axis in ('operation', 'group', 'register'):
                self.assertNotIn(axis, row['identity'])
            self.assertNotIn('positions', row['representation'])
            self.assertNotIn('enum_labels', row['representation'])
            self.assertEqual(row['grade'], 'Hypothesis')
            self.assertEqual(row['qualification'], QUALIFICATION)

    def test_exact_api_signatures_axes_and_behavior(self):
        self.assertEqual(table(self.api, 'api'), [
            ('Ab20Entries() (json.RawMessage, error)', 'JSON array of whole rows'),
            ('Ab20Lookup(Ab20Key) (json.RawMessage, bool, error)', 'One whole row for an exact key')])
        self.assertEqual(table(self.api, 'axes'), API_AXES)
        self.assertEqual(table(self.api, 'behavior'), BEHAVIOR)
        for phrase in ('**Proven (local API contract):** Package `vaillant`',
                       'Optional absent and explicit zero are',
                       'No cross-family, variant, direction, field or alternative fallback',
                       'AK11 must merge before this page',
                       'No dependency points\nback from that registry companion to this page',
                       'eBUS MCP compatibility and GraphQL parity are preserved',
                       'Existing catalog/provider APIs and routability remain unchanged',
                       'Registry error and byte-copy behavior require companion runtime verification',
                       'Nothing is stable before Helianthus 1.0.'):
            self.assertIn(phrase, self.api)

    def test_api_unknown_and_raw_boundaries(self):
        text = re.sub(r'\s+', ' ', self.api)
        for phrase in ('Complete enum labels, encoded operation numbers, missing positions,',
                       'physical reply length, timeout, broadcast, native support, physical effects,',
                       'persistence and delivery.', 'no reserved-zero assertion is made',
                       'Candidate grade is not qualification.',
                       'Raw evidence and independent last-known-good state survive those failures',
                       'retained state is not fresh evidence',
                       'The registry companion embeds its owned JSON in its owned Go file'):
            self.assertIn(phrase, text)

    def test_all_eleven_axes_isolated_with_valid_controls(self):
        base = copy.deepcopy(self.rows[3])
        alternatives = dict(family='other-family', variant='other-variant', primary=182,
                            secondary=23, operation=0, direction='request',
                            field='other-field', alternative='other-alternative',
                            group=0, instance_scope='00', register=0)
        self.assertEqual(set(alternatives), set(AXES))
        for axis, alternative in alternatives.items():
            with self.subTest(axis=axis):
                changed = dict(base['identity'], **{axis: alternative})
                differences = [name for name in AXES
                               if base['identity'].get(name, ABSENT) != changed.get(name, ABSENT)]
                self.assertEqual(differences, [axis])
                self.assertEqual(lookup([base], base['identity']), base)
                self.assertIsNone(lookup([base], changed))
                # A paired synthetic row is a valid exact hit, not just a miss.
                witness = dict(copy.deepcopy(base), id='ak12-test-control', identity=changed)
                controls = admit(json.dumps([base, witness]))
                self.assertEqual(lookup(controls, changed), witness)
                self.assertEqual(lookup(controls, base['identity']), base)

    def test_each_optional_absent_versus_zero(self):
        for axis in OPTIONAL:
            with self.subTest(axis=axis):
                absent = copy.deepcopy(self.rows[3])
                absent['identity'].pop(axis, None)
                zero = copy.deepcopy(absent)
                zero['id'] = 'ak12-test-zero'
                zero['identity'][axis] = 0
                rows = admit(json.dumps([absent, zero]))
                self.assertEqual(lookup(rows, absent['identity']), absent)
                self.assertEqual(lookup(rows, zero['identity']), zero)
                self.assertNotEqual(identity(absent['identity']), identity(zero['identity']))
        self.assertTrue(all('operation' not in row['identity'] for row in self.rows))
        self.assertIsNone(lookup(self.rows, dict(self.rows[3]['identity'], operation=0)))

    def test_admission_errors(self):
        for raw in ('{', '{}', 'null', json.dumps(self.rows + [self.rows[0]])):
            with self.subTest(raw=raw), self.assertRaises((ValueError, TypeError)):
                admit(raw)
        for axis, value in [('primary', True), ('secondary', -1), ('operation', 256),
                            ('group', None), ('register', 65536), ('instance_scope', 0)]:
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                identity(dict(self.rows[3]['identity'], **{axis: value}))
        self.assertEqual(admit(json.dumps(self.rows)), self.rows)

    def test_model_copy_isolation(self):
        original = copy.deepcopy(self.rows)
        admitted = admit(json.dumps(self.rows))
        row = lookup(admitted, self.rows[3]['identity'])
        row['representation']['value_bits'][0] = 7
        row['unknown'].clear()
        row['identity']['variant'] = 'changed'
        buffer = entries_buffer(admitted)
        buffer[:] = b'[]'
        later = json.loads(entries_buffer(admitted))
        self.assertEqual(later, original)
        self.assertEqual(lookup(admitted, original[3]['identity']), original[3])
        admitted[0]['qualification']['native_support'] = 'changed'
        self.assertEqual(self.rows, original)

    def test_case_interpretations_and_raw_retention(self):
        by_id = {row['id']: row for row in self.rows}
        for case in expected_cases():
            with self.subTest(case=case['id']):
                row = by_id[case['row']]
                if 'raw' not in case:
                    self.assertEqual(row['representation']['kind'], case['interpretation']['declared_positive'])
                    self.assertEqual(row['physical_reply_length'], 'Unknown')
                    continue
                raw = case['raw'][:]
                result = view(self.rows, row['identity'], raw)
                self.assertEqual(result['interpretation'], case['interpretation'])
                self.assertEqual(result['raw'], case['raw'])
                self.assertEqual((result['status'], result['grade']), ('candidate', 'Hypothesis'))
                raw[0] = 0
                self.assertEqual(result['raw'], case['raw'])

    def test_exhaustive_energy_tokens_independent_arithmetic(self):
        # Independent division/remainder oracle, not the metadata-driven model.
        for token in range(256):
            expected = [dict(enum_token=token),
                        dict(low_six=token % 64, bit6=(token // 64) % 2 == 1,
                             bit7=token // 128 == 1),
                        dict(low_six=token % 64, unmodeled_raw=(token // 64) * 64)]
            for row, meaning in zip(self.rows[2:], expected):
                with self.subTest(token=token, direction=row['identity']['direction']):
                    result = view(self.rows, row['identity'], [token])
                    self.assertEqual(result['interpretation'], meaning)
                    self.assertEqual(result['raw'], [token])

    def test_fail_closed_partial_and_last_good(self):
        key = self.rows[3]['identity']
        last = {'low_six': 7, 'raw': [7]}
        for raw, status in [([], 'partial'), ([193, 0], 'extra'), ([256], 'malformed'),
                            ([True], 'malformed'), (['C1'], 'malformed'), (None, 'malformed')]:
            with self.subTest(raw=raw):
                result = view(self.rows, key, raw, last)
                self.assertEqual(result['status'], status)
                self.assertIsNone(result['interpretation'])
                self.assertEqual(result['raw'], raw)
                self.assertEqual(result['last_good'], last)
                result['last_good']['raw'][0] = 0
                self.assertEqual(last['raw'], [7])
        missing = dict(key, operation=0)
        result = view(self.rows, missing, [193], last)
        self.assertEqual((result['status'], result['interpretation']), ('unknown', None))
        self.assertEqual((result['raw'], result['last_good']), ([193], last))
        self.assertEqual(view(self.rows, key, [193], last)['status'], 'candidate')


if __name__ == '__main__':
    unittest.main(verbosity=2)
