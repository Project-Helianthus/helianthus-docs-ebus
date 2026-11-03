"""Finite documentation conformance oracles; no companion library execution."""
import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al16_b511_class_candidates.md'
FIXTURE = ROOT / 'architecture/fixtures/al16_b511_class_candidates.json'

AXES = [
    ('Family', 'string', 'exact family'),
    ('Variant', 'string', 'exact variant'),
    ('Primary', 'uint8', 'exact primary service'),
    ('Secondary', '*uint8', 'absent differs from explicit zero'),
    ('Operation', '*uint8', 'absent differs from explicit zero'),
    ('Direction', '*string', 'absent differs from a supplied direction'),
    ('Field', 'string', 'exact field'),
    ('Group', '*uint8', 'absent differs from explicit zero'),
    ('RequestedInstance', '*uint8', 'absent differs from explicit zero'),
    ('Register', '*uint16', 'absent differs from explicit zero'),
    ('CommandRole', '*string', 'absent differs from a supplied role'),
]
CLASS_ROWS = [
    ['00', 'three flag bytes; optional second modulation'],
    ['01', 'separate handshakes and forced-mode guards; warm-start bit5 only in applicable variants'],
    ['02', 'status domain 0/1; DHW-enabled covers tank-loading/warm-start while tapping remains enabled'],
    ['03', 'basic-state domain 0..6; two flag bytes; message domain 0..3; other labels Unknown'],
    ['04', 'status and two temperatures'],
    ['05', 'four setpoints and two status bytes'],
    ['06', 'CH/DHW/pressure/cooling limits; raw status values 4/9/16 remain unlabelled'],
    ['07', 'power percent; LEu16 energy kWh 0..9999; pump/status flags'],
    ['08', 'volume percent and pump/status'],
    ['09', 'LEu16 yield kWh 0..65535; power percent; activity/display/day-night'],
    ['0A', 'error/loading'],
    ['0B', 'fan/radiator/bypass/error/maintenance/assistant'],
    ['0C', 'operation domain 0..3 and switch-on flags'],
    ['0D', 'status/configuration'],
]
CONTROL_ROWS = [
    ['OP07 energy upper', '0F 27', '9999 kWh; inside candidate domain'],
    ['OP07 energy outside', '10 27', '10000 kWh; outside candidate domain; raw retained'],
    ['OP09 yield maximum', 'FF FF', '65535 kWh; inside candidate domain; no sentinel'],
    ['OP06 status controls', '4 / 9 / 16', 'raw retained; each label Unknown'],
    ['OP03 message controls', '3 / 4', 'inside / outside; both labels Unknown'],
    ['OP03 basic-state controls', '6 / 7', 'inside / outside; both labels Unknown'],
    ['OP01 applicability controls', 'bit5 set in applicable / inapplicable variant', 'candidate warm-start true / Unknown'],
    ['OP07 incomplete energy', '0F', 'partial; no candidate number; raw retained'],
    ['OP07 extra energy', '0F 27 00', 'extra; no candidate number; raw retained'],
]
BASE_KEY = dict(family='vaillant', variant='synthetic-class', primary=181,
                secondary=17, operation=7, direction='positive', field='energy',
                group=None, requested_instance=None, register=None, command_role=None)

# Separately authored expectations: input bytes and expected numbers are literals.
# No expected value is calculated from the fixture or page.
CASES = [
    ('op07-upper', 7, 'energy', [15, 39], 9999, True, 'candidate', 16, 'synthetic-class', None),
    ('op07-outside', 7, 'energy', [16, 39], 10000, False, 'outside', 16, 'synthetic-class', None),
    ('op09-maximum', 9, 'yield', [255, 255], 65535, True, 'candidate', 16, 'synthetic-class', None),
    ('op06-status-4', 6, 'status', 4, 4, None, 'unlabelled', None, 'synthetic-class', None),
    ('op06-status-9', 6, 'status', 9, 9, None, 'unlabelled', None, 'synthetic-class', None),
    ('op06-status-16', 6, 'status', 16, 16, None, 'unlabelled', None, 'synthetic-class', None),
    ('op03-message-inside', 3, 'message', 3, 3, True, 'candidate', None, 'synthetic-class', None),
    ('op03-message-outside', 3, 'message', 4, 4, False, 'outside', None, 'synthetic-class', None),
    ('op03-basic-inside', 3, 'basic-state', 6, 6, True, 'candidate', None, 'synthetic-class', None),
    ('op03-basic-outside', 3, 'basic-state', 7, 7, False, 'outside', None, 'synthetic-class', None),
    ('op01-applicable', 1, 'warm-start', 32, None, None, 'candidate', None, 'synthetic-applicable', True),
    ('op01-inapplicable', 1, 'warm-start', 32, None, None, 'unknown', None, 'synthetic-inapplicable', None),
    ('op07-partial', 7, 'energy', [15], None, None, 'partial', 16, 'synthetic-class', None),
    ('op07-extra', 7, 'energy', [15, 39, 0], None, None, 'extra', 16, 'synthetic-class', None),
]


def expected_examples():
    rows = []
    for name, op, field, raw, value, domain, status, width, variant, warm in CASES:
        rows.append(dict(case=name, key=dict(BASE_KEY, operation=op, field=field,
                                           variant=variant), raw=copy.deepcopy(raw),
                         offset=None, width_bits=width, default=None,
                         expected=dict(raw=copy.deepcopy(raw), value=value,
                                       in_domain=domain, label=None,
                                       warm_start=warm, status=status)))
    return rows


def tables(page):
    result, current = [], []
    for line in page.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            result.append(current[2:])
            current = []
    return result


def interpret(row):
    """Test-only oracle for explicit field slices, never a telegram parser."""
    raw = row['raw']
    op, field = row['key']['operation'], row['key']['field']
    result = dict(raw=copy.deepcopy(raw), value=None, in_domain=None, label=None,
                  warm_start=None, status='unknown')
    if (op, field) in ((7, 'energy'), (9, 'yield')):
        if len(raw) != 2:
            result['status'] = 'partial' if len(raw) < 2 else 'extra'
            return result
        value = int.from_bytes(bytes(raw), byteorder='little', signed=False)
        limit = 9999 if op == 7 else 65535
        result.update(value=value, in_domain=value <= limit,
                      status='candidate' if value <= limit else 'outside')
    elif op == 3 and field in ('message', 'basic-state'):
        limit = 3 if field == 'message' else 6
        result.update(value=raw, in_domain=0 <= raw <= limit,
                      status='candidate' if 0 <= raw <= limit else 'outside')
    elif (op, field) == (6, 'status'):
        result.update(value=raw, status='unlabelled')
    elif (op, field) == (1, 'warm-start'):
        if row['key']['variant'] == 'synthetic-applicable':
            result.update(warm_start=bool(raw & 32), status='candidate')
    return result


def exact_lookup(rows, key):
    """Local identity oracle only; no claim about companion implementation."""
    return next((copy.deepcopy(row) for row in rows if row['key'] == key), None)


def project(row, previous):
    """Local partial-result contract oracle; retained state is independently owned."""
    current = interpret(row)
    retained = copy.deepcopy(previous)
    if (row['key']['operation'], row['key']['field']) == (7, 'energy'):
        if current['status'] == 'candidate':
            retained['last_known_good_energy'] = current['value']
    return dict(current=current, retained=retained)


class B511ClassCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text()
        self.fixture = json.loads(FIXTURE.read_text())

    def test_exact_declared_shape_and_small_example_set(self):
        self.assertEqual(self.fixture, dict(
            interpretation_grade='Hypothesis', arithmetic_grade='Proven', shape_grade='Proven',
            physical_qualification='Unknown', presence='Unknown', freshness='Unknown',
            execution='Unknown', examples=expected_examples(),
            partial_context=dict(last_known_good_energy=9999, power_percent=25)))
        self.assertEqual(len(self.fixture['examples']), 14)
        for row in self.fixture['examples']:
            with self.subTest(case=row['case']):
                self.assertIsNone(row['offset'])
                self.assertIsNone(row['default'])
                self.assertIsNone(row['expected']['label'])

    def test_page_identity_class_and_control_tables(self):
        self.assertEqual(tables(self.page), [
            [['Ab50' + field, kind, rule] for field, kind, rule in AXES],
            CLASS_ROWS, CONTROL_ROWS])
        self.assertEqual([line for line in self.page.splitlines() if line.startswith('func ')], [
            'func Ab50Entries() ([]Ab50Entry, error)',
            'func Ab50Lookup(ab50Key Ab50Key) (Ab50Entry, bool, error)'])

    def test_independent_arithmetic_and_unknown_labels(self):
        for row in self.fixture['examples']:
            with self.subTest(case=row['case']):
                self.assertEqual(interpret(row), row['expected'])
                self.assertEqual(row['raw'], row['expected']['raw'])
        # Little-endian, unsigned and both byte positions vary independently.
        for op, field in ((7, 'energy'), (9, 'yield')):
            for raw, expected in (([0, 0], 0), ([1, 0], 1), ([0, 1], 256),
                                  ([0, 128], 32768), ([255, 255], 65535)):
                with self.subTest(op=op, raw=raw):
                    row = dict(key=dict(BASE_KEY, operation=op, field=field), raw=raw)
                    result = interpret(row)
                    self.assertEqual(result['value'], expected)
                    self.assertEqual(result['in_domain'], op == 9 or expected <= 9999)
                    self.assertEqual(result['raw'], raw)

    def test_all_key_axes_with_otherwise_identical_valid_controls(self):
        changes = dict(family=['other-family', 'Vaillant'],
                       variant=['synthetic-other', 'Synthetic-class'], primary=[182],
                       secondary=[None, 0, 18], operation=[None, 0, 9],
                       direction=[None, 'request', 'Positive'], field=['yield', 'Energy'],
                       group=[0, 1], requested_instance=[0, 1], register=[0, 256],
                       command_role=['read', 'write'])
        self.assertEqual(set(changes), set(BASE_KEY))
        for axis, alternatives in changes.items():
            for value in alternatives:
                with self.subTest(axis=axis, value=value):
                    a = dict(key=copy.deepcopy(BASE_KEY), marker='a')
                    key = dict(BASE_KEY, **{axis: value})
                    b = dict(key=key, marker='b')
                    self.assertIsNone(exact_lookup([a], key))
                    # The alternate is valid identity data, not a malformed-key miss.
                    self.assertEqual(exact_lookup([a, b], BASE_KEY)['marker'], 'a')
                    self.assertEqual(exact_lookup([a, b], key)['marker'], 'b')
        for axis in ('secondary', 'operation', 'group', 'requested_instance', 'register'):
            with self.subTest(absence_zero=axis):
                absent = dict(BASE_KEY, **{axis: None})
                zero = dict(BASE_KEY, **{axis: 0})
                self.assertIsNone(exact_lookup([dict(key=absent)], zero))
        # Both registers are present: losing the high byte must not merge them.
        low = dict(BASE_KEY, register=0)
        high = dict(BASE_KEY, register=256)
        rows = [dict(key=low, marker='low'), dict(key=high, marker='high')]
        self.assertEqual(exact_lookup(rows, low)['marker'], 'low')
        self.assertEqual(exact_lookup(rows, high)['marker'], 'high')

    def test_warm_start_applicability_and_bit_independently(self):
        for variant, raw, expected in (
            ('synthetic-applicable', 0, False), ('synthetic-applicable', 32, True),
            ('synthetic-inapplicable', 0, None), ('synthetic-inapplicable', 32, None),
            ('synthetic-other', 32, None)):
            with self.subTest(variant=variant, raw=raw):
                row = dict(key=dict(BASE_KEY, operation=1, field='warm-start',
                                    variant=variant), raw=raw)
                self.assertIs(interpret(row)['warm_start'], expected)
        for bit in (0, 1, 2, 3, 4, 6, 7):
            row = dict(key=dict(BASE_KEY, operation=1, field='warm-start',
                                variant='synthetic-applicable'), raw=1 << bit)
            self.assertIs(interpret(row)['warm_start'], False)

    def test_partial_outside_and_extra_keep_independent_knowledge(self):
        context = self.fixture['partial_context']
        # Each raw length, prior energy and useful independent field varies alone.
        for raw in ([], [15], [15, 39, 0], [16, 39]):
            for previous, power in ((9999, 25), (123, 25), (9999, 0)):
                with self.subTest(raw=raw, previous=previous, power=power):
                    held = dict(last_known_good_energy=previous, power_percent=power)
                    before = copy.deepcopy(held)
                    row = dict(key=BASE_KEY, raw=copy.deepcopy(raw))
                    view = project(row, held)
                    result = view['current']
                    self.assertNotEqual(result['status'], 'candidate')
                    self.assertEqual(result['raw'], raw)
                    self.assertEqual(view['retained'], before)
                    self.assertEqual(held, before)
                    result['raw'].append(99)
                    view['retained']['power_percent'] = 77
                    self.assertEqual(row['raw'], raw)
                    self.assertEqual(held, before)
                    admitted = project(dict(key=BASE_KEY, raw=[15, 39]), held)
                    self.assertEqual(admitted['retained'], dict(
                        last_known_good_energy=9999, power_percent=power))
                    self.assertEqual(held, before)
        self.assertEqual(context, dict(last_known_good_energy=9999, power_percent=25))

    def test_required_error_memory_grade_and_scope_declarations(self):
        for phrase in (
            '../protocols/vaillant/ebus-vaillant-B511.md#operating-data-classes-candidate',
            'must\nmerge before this page', 'merge status is not established',
            'Candidate interpretations are **Hypothesis**', '**Proven** is limited to',
            'Physical qualification, presence, freshness and execution\nremain **Unknown**',
            'not an observed companion code\nresult',
            'No native effect or full parity is\nclaimed before its own checks',
            'without normalization, wildcarding, variant fallback',
            'OP00 is present zero', 'List order is not an offset',
            '`Ab50Entry{}, false, nil`', '`Ab50Entry{}, false, error`',
            'enumeration yields no usable collection',
            'Empty data, malformed or trailing JSON, unknown\nfields, incomplete keys, invalid metadata and duplicate exact keys fail closed',
            "caller's independently retained",
            'last-known-good result', 'Unknown semantics alone do not erase raw evidence',
            'independent memory', 'key pointers, optional scalar pointers, slices, maps and nested contents',
            'another held result or a later call',
            'Grade, metadata presence, physical qualification, presence, freshness and\nexecution stay separate',
            'Every `offset` is null', 'unspecified\n`width_bits` and `default` are null',
            'Preserve unlabelled raw values without clipping or replacement',
            'not a\nnative profile or a full catalog',
            'Existing request declarations, OP0F special-function membership, overlapping\npositive extents and cache policies are outside',
            'eBUS MCP compatibility\nand GraphQL parity', 'before Helianthus 1.0',
            'before 0.9', '0.11', 'full Gate D',
            'No parser,\ncross-repository runtime import, transmit route, polling default, automatic native\nqualification or application integration',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.page)


if __name__ == '__main__':
    unittest.main()
