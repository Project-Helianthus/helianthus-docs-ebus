"""Finite synthetic representation checks; no device or companion Go execution."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ak20_b524_family_codebooks.md'
DATA = ROOT / 'architecture/fixtures/ak20_b524_family_codebooks.json'
AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
        'field', 'alternative', 'group', 'instance_scope', 'register')
FIELDS = ('Ab30Family', 'Ab30Variant', 'Ab30Primary', 'Ab30Secondary',
          'Ab30Operation', 'Ab30Direction', 'Ab30Field', 'Ab30Alternative',
          'Ab30Group', 'Ab30InstanceScope', 'Ab30Register')
INSTANCE_FIELD = ('Ab30Instance', '*uint8', 'lookup predicate')
TYPES = ('string', 'string', 'uint8', '*uint8', '*uint8', 'string', 'string',
         'string', '*uint8', 'string', '*uint16')
# Independent finite expectations, never loaded from the fixture or page.
MODES = ('0:off,1:automatic,2:day', '0:off,1:time-controlled,2:manual')
QUICK = ('0:no-quick-mode,1:ventilation-boost,3:party,4:quick-veto,5:one-day-holiday,6:one-day-bank-holiday,7:holiday,8:bank-holiday,10:system-off',
         '0:no-special-function,1:ventilation-boost,4:quick-veto,7:holiday,10:system-off')
TABLES = (
    (1, 3, '00', 'u16', *MODES),
    (2, 2, 'dynamic', 'u16', '0:deactivated,1:heating,2:fixed-flow,3:DHW,4:return-flow,5:pool', '0:deactivated,1:heating,2:fixed-flow,3:DHW,4:return-flow'),
    (3, 1, 'dynamic', 'u16', *MODES),
    (3, 6, 'dynamic', 'u16', MODES[0]+',3:setback', MODES[1]),
    (3, 19, 'dynamic', 'u16', '0:none,1:central,2:remote-circuit-one,3:remote-circuit-two,4:remote-circuit-three,5:remote-circuit-four,6:remote-circuit-five,7:remote-circuit-six,8:remote-circuit-seven,9:remote-circuit-eight', '0:none,1:central,2:remote-circuit-one,3:remote-circuit-two,4:remote-circuit-three,5:remote-circuit-four'),
    (3, 27, 'dynamic', 'u8', *QUICK),
    (3, 27, 'dynamic', 'u16', *QUICK),
    (3, 28, 'dynamic', 'signed8', '255:unbound,0:control-circuit-one,1:control-circuit-two,2:control-circuit-three', '255:unbound,0:control-circuit-one,1:control-circuit-two,2:control-circuit-three,3:control-circuit-four,4:control-circuit-five,5:control-circuit-six,6:control-circuit-seven,7:control-circuit-eight,8:control-circuit-nine'),
)
UNKNOWN = dict.fromkeys(('native_support', 'physical_effects', 'persistence',
                         'delivery', 'installed_cardinality', 'present_slots',
                         'freshness', 'unlisted_codes'), 'Unknown')
RELATIONS = dict(identity_grade='Proven', candidate_opcode='OP02',
                 instance_scope_role='metadata-only',
                 width_selection='explicit alternative; reply length does not select',
                 family_selection='explicit; no auto-detection')
FALLBACK = 'Preserve raw bytes; unlisted codes and unknown families have Unknown meaning.'


def key(family, group=2, register=2, scope='dynamic', alternative='u16'):
    return dict(zip(AXES, (family, 'none', 181, 36, 2, 'read', 'value',
                           alternative, group, scope, register)))


def expected_rows():
    rows = []
    for family, offset in (('controller-700', 4), ('controller-720', 5)):
        for table in TABLES:
            group, register, scope, width = table[:4]
            enumeration = {}
            for pair in table[offset].split(','):
                raw, label = pair.split(':')
                enumeration[raw] = dict(value=-1 if width == 'signed8' and raw == '255' else int(raw), label=label)
            rows.append(dict(
                id=f'ab30_{family}_gg{group:02X}_rr{register:04X}_{width}',
                key=key(family, group, register, scope, width), grade='Hypothesis',
                representation_grade='Proven', enumeration=enumeration,
                raw_form=dict(encoding=width, width_bytes=2 if width == 'u16' else 1,
                              signedness='signed' if width == 'signed8' else 'unsigned', preserved=True),
                raw_fallback=FALLBACK, relations=RELATIONS.copy(), unknown=UNKNOWN.copy()))
    return rows


def entries(payload):
    """Executable local model of the documented byte-copy/error contract."""
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError('array required')
    seen = []
    for row in rows:
        identity = row['key']
        if set(identity) != set(AXES) or identity in seen:
            raise ValueError('incomplete or duplicate identity')
        seen.append(identity)
    return bytearray(payload)


def instance_matches(scope, instance):
    if instance is None:
        return False
    return instance == 0 if scope == '00' else scope == 'dynamic' and 0 <= instance <= 0xFE


def lookup(payload, identity, instance=0):
    rows = json.loads(entries(payload))
    for row in rows:
        if row['key'] == identity and instance_matches(identity['instance_scope'], instance):
            return bytearray(json.dumps(row).encode()), True
    return None, False


def meaning(payload, identity, raw):
    row, found = lookup(payload, identity)
    if not found:
        return None, 'Unknown', raw
    value = json.loads(row)['enumeration'].get(str(raw))
    return value, 'Hypothesis' if value is not None else 'Unknown', raw


class FamilyCodebooks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.fixture = json.loads(DATA.read_text())
        cls.rows = cls.fixture['entries']
        cls.payload = json.dumps(cls.rows).encode()

    def test_complete_finite_data(self):
        self.assertEqual(set(self.fixture), {'service', 'provenance', 'entries', 'cases'})
        self.assertEqual(self.fixture['service'], 'B524')
        self.assertEqual(self.fixture['provenance'], 'synthetic')
        self.assertEqual(self.rows, expected_rows())
        self.assertEqual(len({r['id'] for r in self.rows}), 16)

    def test_page_tables_independent(self):
        actual = [line for line in self.page.splitlines() if line.startswith('| 0')]
        expected = [f'| {g:02X} | {r:04X} | {s} | {w} | {a} | {b} |'
                    for g, r, s, w, a, b in TABLES]
        self.assertEqual(actual, expected)

    def test_page_api_axes_and_types(self):
        for signature in ('Ab30Entries() (json.RawMessage, error)',
                          'Ab30Lookup(Ab30Key) (json.RawMessage, bool, error)'):
            self.assertIn(signature, self.page)
        actual = [line.split('|')[1:4] for line in self.page.splitlines()
                  if line.startswith('| Ab30')]
        self.assertEqual([[v.strip() for v in row] for row in actual],
                         [list(x) for x in zip(FIELDS, TYPES, AXES)] + [list(INSTANCE_FIELD)])

    def test_instance_predicate(self):
        dyn, single = key('controller-700'), key('controller-700', 1, 3, '00')
        for instance, want in ((0, True), (1, True), (0xFE, True), (0xFF, False), (None, False)):
            with self.subTest(scope='dynamic', instance=instance):
                self.assertEqual(lookup(self.payload, dyn, instance)[1], want)
        for instance, want in ((0, True), (1, False), (0xFF, False), (None, False)):
            with self.subTest(scope='00', instance=instance):
                self.assertEqual(lookup(self.payload, single, instance)[1], want)
        self.assertIn('Instance FF is the all-instances selector', ' '.join(self.page.split()))

    def test_page_boundaries(self):
        normalized = ' '.join(self.page.split())
        for phrase in ('package `vaillant`', 'OP06 cannot inherit OP02 labels',
                       'Unknown family returns raw/Unknown meaning',
                       'reply length does not select either alternative',
                       'metadata-only, not a scan bound or installed cardinality',
                       'false for a missing exact key',
                       'error for invalid embedded JSON or duplicate keys',
                       'No wildcard or nearest-key lookup',
                       'Optional absent and explicit zero differ',
                       'Non-applicable string axes use an explicit none token',
                       'independent deep byte copies on every call',
                       'cannot affect a later result', 'validates identity uniqueness',
                       'AK19 embeds its JSON in its Go file',
                       'partial last-known-good state and raw evidence',
                       'eBUS MCP compatibility and GraphQL parity remain unchanged',
                       'AK19 registry delivery precedes this page',
                       'Nothing is stable before Helianthus 1.0'):
            self.assertIn(phrase, normalized)
        for name in UNKNOWN:
            self.assertIn(name, normalized)
        for target in ('ebus-vaillant-B524.md', 'ebus-vaillant-B524-register-map.md',
                       'ebus-b524-scalar-shapes.md'):
            self.assertIn('../protocols/vaillant/'+target, self.page)
            self.assertTrue((ROOT/'protocols/vaillant'/target).is_file())

    def test_every_mapping_and_raw_fallback(self):
        for row in expected_rows():
            for raw in range(256):
                with self.subTest(id=row['id'], raw=raw):
                    want = row['enumeration'].get(str(raw))
                    self.assertEqual(meaning(self.payload, row['key'], raw),
                                     (want, 'Hypothesis' if want else 'Unknown', raw))
            for raw in (256, 65535):
                self.assertEqual(meaning(self.payload, row['key'], raw), (None, 'Unknown', raw))

    def test_synthetic_cases_and_coverage(self):
        cases = self.fixture['cases']
        self.assertGreater(len(cases), 100)
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(set(case), {'key', 'raw_code', 'expected', 'grade'})
                self.assertEqual(meaning(self.payload, case['key'], case['raw_code']),
                                 (case['expected'], case['grade'], case['raw_code']))
        for row in expected_rows():
            for raw, expected in row['enumeration'].items():
                self.assertIn(dict(key=row['key'], raw_code=int(raw), expected=expected,
                                   grade='Hypothesis'), cases)
        control = key('controller-700')
        variants = dict(family='unknown-family', variant='other', primary=0,
                        secondary=0, operation=6, direction='write', field='other',
                        alternative='none', group=0, instance_scope='00', register=0)
        for axis, value in variants.items():
            changed = dict(control, **{axis: value})
            self.assertIn(dict(key=changed, raw_code=5, expected=None, grade='Unknown'), cases)
        for axis in ('secondary', 'operation', 'group', 'register'):
            for value in (None, 0):
                self.assertIn(dict(key=dict(control, **{axis: value}), raw_code=5,
                                   expected=None, grade='Unknown'), cases)

    def test_all_eleven_axes_alone_with_valid_decoys(self):
        control = self.rows[1]
        variants = dict(family='unknown-family', variant='other', primary=0,
                        secondary=0, operation=6, direction='write', field='other',
                        alternative='none', group=0, instance_scope='00', register=0)
        for axis, value in variants.items():
            with self.subTest(axis=axis):
                changed = dict(control['key'], **{axis: value})
                self.assertEqual(lookup(self.payload, changed), (None, False))
                self.assertEqual(json.loads(lookup(self.payload, control['key'])[0]), control)
                decoy = copy.deepcopy(control)
                decoy.update(id='ab30_decoy', key=changed)
                pair = json.dumps([control, decoy]).encode()
                self.assertEqual(json.loads(lookup(pair, changed)[0]), decoy)
                self.assertEqual(json.loads(lookup(pair, control['key'])[0]), control)

    def test_optional_absent_zero_are_distinct(self):
        for axis in ('secondary', 'operation', 'group', 'register'):
            absent, zero = copy.deepcopy(self.rows[1]), copy.deepcopy(self.rows[1])
            absent['key'][axis], zero['key'][axis] = None, 0
            absent['id'], zero['id'] = 'ab30_absent', 'ab30_zero'
            payload = json.dumps([absent, zero]).encode()
            for row in (absent, zero):
                self.assertEqual(json.loads(lookup(payload, row['key'])[0]), row)
                self.assertEqual(lookup(self.payload, row['key']), (None, False))

    def test_invalid_duplicate_and_copy_contract_model(self):
        for invalid in (b'[', b'null', b'{}', b'[{}]',
                        json.dumps([self.rows[0], self.rows[0]]).encode()):
            with self.assertRaises((ValueError, KeyError, TypeError)):
                lookup(invalid, self.rows[0]['key'])
        before = bytes(self.payload)
        array = entries(self.payload)
        first, _ = lookup(self.payload, self.rows[0]['key'])
        second, _ = lookup(self.payload, self.rows[0]['key'])
        saved = bytes(second)
        array[:] = b'x' * len(array)
        first[:] = b'y' * len(first)
        self.assertEqual(bytes(entries(self.payload)), before)
        self.assertEqual(bytes(lookup(self.payload, self.rows[0]['key'])[0]), saved)
        self.assertEqual(bytes(second), saved)


if __name__ == '__main__':
    unittest.main(verbosity=2)
