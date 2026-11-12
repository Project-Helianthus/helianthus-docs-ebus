"""AM08: page, synthetic package and a reference interpreter must agree."""

import json
import math
from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'architecture/fixtures/am08_b524_zone_scalars.json'
PAGE = ROOT / 'architecture/am08-b524-zone-scalars.md'

# Independent oracle, written from the contract rather than read from the package.
EXPECTED = {
    ('controller-720', 0x0002, '°C'), ('controller-720', 0x0005, '°C'),
    ('controller-720', 0x0009, '°C'), ('controller-720', 0x000F, '°C'),
    ('controller-720', 0x0014, '°C'), ('controller-720', 0x0015, '°C'),
    ('controller-720', 0x0023, '°C'), ('controller-720', 0x0028, '%'),
    ('controller-700', 0x0002, '°C'), ('controller-700', 0x0005, '°C'),
    ('controller-700', 0x0009, '°C'), ('controller-700', 0x000F, '°C'),
    ('controller-700', 0x0014, '°C'), ('controller-700', 0x0015, '°C'),
    ('controller-700', 0x0028, '%'),
}
CONTEXT_FIELDS = ('family', 'software', 'hardware', 'api_version', 'api_revision',
                  'opcode', 'group', 'instance', 'register', 'reply_kind',
                  'returned_group', 'returned_register', 'codec_grade')


def load_bindings(fixture):
    table = {}
    for binding in fixture['bindings']:
        for reg in binding['registers']:
            key = (binding['family'], int(fixture['selector']['opcode'], 16),
                   int(fixture['selector']['group'], 16), int(reg, 16))
            assert key not in table
            table[key] = (binding['codec'], binding['unit'])
    return table


def interpret(table, family=None, software=None, hardware=None, api_version=None,
              api_revision=None, opcode=None, group=None, instance=None,
              register=None, reply_kind=None, returned_group=None,
              returned_register=None, value=b'', codec_grade=None):
    context = dict(family=family, software=software, hardware=hardware,
                   api_version=api_version, api_revision=api_revision,
                   opcode=opcode, group=group, instance=instance,
                   register=register, reply_kind=reply_kind,
                   returned_group=returned_group,
                   returned_register=returned_register, codec_grade=codec_grade)
    raw = bytes(value)

    def raw_only(reason):
        return dict(status='raw-only', grade=None, value=None, unit=None,
                    codec=None, raw=raw, context=dict(context), reason=reason)

    if any(v is None for v in context.values()):
        return raw_only('missing context')
    if type(instance) is not int or not 0 <= instance <= 255:
        return raw_only('instance')
    binding = table.get((family, opcode, group, register))
    if binding is None:
        return raw_only('unlisted selector')
    if codec_grade not in ('Hypothesis', 'Proven'):
        return raw_only('codec grade')
    if reply_kind != 'echo_payload':
        return raw_only('reply kind')
    if (returned_group, returned_register) != (group, register):
        return raw_only('mismatch')
    codec, unit = binding
    assert codec == 'float32-le'
    if len(raw) != 4:
        return raw_only('width')
    number = struct.unpack('<f', raw)[0]
    if not math.isfinite(number):
        return raw_only('non-finite')
    return dict(status='interpreted', grade='Hypothesis', value=number, unit=unit,
                codec=codec, raw=raw, context=dict(context), reason=None)


def u16(raw):
    return struct.unpack('<H', raw)[0]


def valid(family, register, **over):
    args = dict(family=family, software='sw-synthetic-a', hardware='hw-synthetic-a',
                api_version=1, api_revision=0, opcode=2, group=3, instance=1,
                register=register, reply_kind='echo_payload', returned_group=3,
                returned_register=register, value=bytes.fromhex('0000C03F'),
                codec_grade='Hypothesis')
    args.update(over)
    return args


class AM08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.page = PAGE.read_text(encoding='utf-8')
        cls.table = load_bindings(cls.fixture)

    def test_bindings_match_independent_oracle_and_page(self):
        got = {(f, r, u) for (f, _o, _g, r), (_c, u) in
               ((k, v) for k, v in self.table.items())}
        self.assertEqual(got, EXPECTED)
        self.assertEqual(len(self.table), 15)
        self.assertTrue(all(k[1:3] == (2, 3) for k in self.table))
        self.assertEqual({v[0] for v in self.table.values()}, {'float32-le'})
        for family, reg, unit in EXPECTED:
            row = [ln for ln in self.page.splitlines()
                   if ln.startswith('| ' + family + ' |') and f'{reg:04X}' in ln]
            with self.subTest(family=family, reg=reg):
                self.assertTrue(any(f'| {unit} |' in ln for ln in row))
        self.assertNotIn('0023', [ln for ln in self.page.splitlines()
                                   if ln.startswith('| controller-700 |')][0])

    def test_grades_and_unknowns(self):
        self.assertEqual(self.fixture['grade'], 'Hypothesis')
        self.assertEqual(self.fixture['qualification'], 'Unknown')
        self.assertEqual(set(self.fixture['unresolved'].values()), {'Unknown'})
        for word in ('Hypothesis', 'Unknown', 'Proven', 'Refs'):
            self.assertIn(word, self.page)

    def test_valid_controls_every_binding(self):
        for family, reg, unit in sorted(EXPECTED):
            for hexv, want in (('0000C03F', 1.5), ('000080BF', -1)):
                raw = bytes.fromhex(hexv)
                self.assertEqual(struct.unpack('<f', raw)[0], want)
                with self.subTest(family=family, reg=reg, v=hexv):
                    r = interpret(self.table, **valid(family, reg, value=raw))
                    self.assertEqual((r['status'], r['value'], r['unit'], r['grade']),
                                     ('interpreted', want, unit, 'Hypothesis'))
                    self.assertEqual(r['raw'], raw)

    def test_fixture_controls_agree(self):
        self.assertEqual([c['expected'] for c in self.fixture['float_controls']],
                         [1.5, -1])
        for c in self.fixture['float_controls']:
            self.assertEqual(struct.unpack('<f', bytes.fromhex(c['value_hex']))[0],
                             c['expected'])
        for c in self.fixture['uint16_controls']:
            self.assertEqual(u16(bytes.fromhex(c['value_hex'])), c['expected'])
        self.assertEqual([c['expected'] for c in self.fixture['uint16_controls']],
                         [4660, 65535])
        ctx = self.fixture['context_control']
        self.assertEqual((ctx['opcode'], ctx['group']), ('02', '03'))

    def test_uint16_is_not_a_listed_codec_and_width_never_chooses(self):
        self.assertEqual(u16(b'\x34\x12'), 0x1234)
        self.assertEqual(u16(b'\xff\xff'), 65535)
        for family, reg, _u in sorted(EXPECTED):
            with self.subTest(family=family, reg=reg):
                r = interpret(self.table, **valid(family, reg, value=b'\x34\x12'))
                self.assertEqual((r['status'], r['value']), ('raw-only', None))
                self.assertEqual(r['raw'], b'\x34\x12')

    def test_endianness_and_no_offset(self):
        r = interpret(self.table, **valid('controller-720', 2,
                                          value=bytes.fromhex('3FC00000')))
        self.assertNotEqual(r['value'], 1.5)
        r = interpret(self.table, **valid('controller-720', 2,
                                          value=bytes.fromhex('00000000')))
        self.assertEqual(r['value'], 0.0)

    def test_non_finite_and_width(self):
        for hexbe in self.fixture['non_finite_float_hex_be']:
            raw = struct.pack('<I', int(hexbe, 16))
            self.assertFalse(math.isfinite(struct.unpack('<f', raw)[0]))
            for family, reg, _u in sorted(EXPECTED):
                with self.subTest(family=family, reg=reg, v=hexbe):
                    r = interpret(self.table, **valid(family, reg, value=raw))
                    self.assertEqual((r['status'], r['value']), ('raw-only', None))
                    self.assertEqual(r['raw'], raw)
        good = bytes.fromhex('0000C03F')
        for family, reg, _u in sorted(EXPECTED):
            for raw in (good[:3], good + b'\x00', b''):
                with self.subTest(family=family, reg=reg, n=len(raw)):
                    r = interpret(self.table, **valid(family, reg, value=raw))
                    self.assertEqual((r['status'], r['raw']), ('raw-only', raw))

    def test_unlisted_selectors(self):
        cases = [
            valid('controller-700', 0x0023),          # register of the other family
            valid('controller-720', 0x0003),          # neighbouring register
            valid('controller-720', 0x0029),
            valid('controller-720', 2, opcode=6),     # OP06, identical otherwise
            valid('controller-720', 2, group=2, returned_group=2),
            valid('controller-fallback', 2),          # unknown family, no fallback
            valid('controller-7200', 2),
        ]
        for i, args in enumerate(cases):
            with self.subTest(i=i):
                r = interpret(self.table, **args)
                self.assertEqual((r['status'], r['value']), ('raw-only', None))
                self.assertEqual(r['raw'], bytes.fromhex('0000C03F'))

    def test_instance(self):
        for inst in (0, 1, 255):
            r = interpret(self.table, **valid('controller-720', 2, instance=inst))
            self.assertEqual(r['status'], 'interpreted')
            self.assertEqual(r['context']['instance'], inst)
        for bad in (None, 256, -1, True, '01'):
            with self.subTest(bad=bad):
                r = interpret(self.table, **valid('controller-720', 2, instance=bad))
                self.assertEqual(r['status'], 'raw-only')

    def test_non_echo_reply_kinds_and_mismatch(self):
        for kind in self.fixture['non_echo_reply_kinds']:
            for family, reg, _u in sorted(EXPECTED):
                with self.subTest(kind=kind, family=family, reg=reg):
                    r = interpret(self.table, **valid(family, reg, reply_kind=kind))
                    self.assertEqual((r['status'], r['value']), ('raw-only', None))
                    self.assertEqual(r['raw'], bytes.fromhex('0000C03F'))
                    self.assertEqual(r['context']['reply_kind'], kind)
        for family, reg, _u in sorted(EXPECTED):
            for over in (dict(returned_group=4), dict(returned_register=reg ^ 1)):
                with self.subTest(family=family, reg=reg, over=over):
                    r = interpret(self.table, **valid(family, reg, **over))
                    self.assertEqual(r['status'], 'raw-only')

    def test_codec_grade(self):
        for family, reg, _u in sorted(EXPECTED):
            for grade, ok in (('Hypothesis', True), ('Proven', True),
                              ('Unknown', False), (None, False), ('', False)):
                with self.subTest(family=family, reg=reg, grade=grade):
                    r = interpret(self.table, **valid(family, reg, codec_grade=grade))
                    self.assertEqual(r['status'] == 'interpreted', ok)
                    if ok:
                        self.assertEqual(r['grade'], 'Hypothesis')
                    self.assertEqual(r['context']['codec_grade'], grade)

    def test_each_context_axis_is_retained_and_independent(self):
        variants = dict(
            software='sw-synthetic-b', hardware='hw-synthetic-b', api_version=2,
            api_revision=7,
        )
        for family, reg, unit in sorted(EXPECTED):
            base = valid(family, reg)
            for axis, new in variants.items():
                with self.subTest(family=family, reg=reg, axis=axis):
                    r = interpret(self.table, **dict(base, **{axis: new}))
                    self.assertEqual((r['status'], r['value'], r['unit']),
                                     ('interpreted', 1.5, unit))
                    self.assertEqual(r['context'][axis], new)
                    for other in CONTEXT_FIELDS:
                        if other != axis:
                            self.assertEqual(r['context'][other],
                                             interpret(self.table, **base)['context'][other])
            with self.subTest(family=family, reg=reg, axis='instance'):
                r = interpret(self.table, **dict(base, instance=9))
                self.assertEqual(r['context']['instance'], 9)
                self.assertEqual(r['status'], 'interpreted')
            # absent is not zero: every axis is required, explicit zero is supplied
            for axis in ('software', 'hardware', 'api_version', 'api_revision'):
                with self.subTest(family=family, reg=reg, absent=axis):
                    r = interpret(self.table, **dict(base, **{axis: None}))
                    self.assertEqual(r['status'], 'raw-only')
                    self.assertIsNone(r['context'][axis])
            for axis in ('api_version', 'api_revision'):
                r = interpret(self.table, **dict(base, **{axis: 0}))
                self.assertEqual((r['status'], r['context'][axis]), ('interpreted', 0))
            for axis in CONTEXT_FIELDS:
                if axis in ('codec_grade',):
                    continue
                r = interpret(self.table, **dict(base, **{axis: None}))
                self.assertEqual(r['status'], 'raw-only')

    def test_retained_family_is_caller_family(self):
        a = interpret(self.table, **valid('controller-720', 2))
        b = interpret(self.table, **valid('controller-700', 2))
        self.assertEqual((a['value'], a['unit']), (b['value'], b['unit']))
        self.assertNotEqual(a['context']['family'], b['context']['family'])

    def test_memory_ownership(self):
        buf = bytearray(bytes.fromhex('0000C03F'))
        r = interpret(self.table, **valid('controller-720', 2, value=buf))
        buf[:] = b'\xff\xff\xff\xff'
        self.assertEqual(r['raw'], bytes.fromhex('0000C03F'))
        self.assertIsInstance(r['raw'], bytes)
        ctx = r['context']
        r2 = interpret(self.table, **valid('controller-720', 2))
        ctx['family'] = 'x'
        self.assertEqual(r2['context']['family'], 'controller-720')

    def test_page_statements_and_links(self):
        for text in ('never fabricated or inferred', 'raw-only', 'echo_payload',
                     '273.15', '7F800000', '34 12', '4660', '65535', '00 00 C0 3F',
                     'Nothing here is stable before Helianthus 1.0', 'OP06',
                     'fixed II00 rule would accept only 00'):
            with self.subTest(text=text):
                self.assertIn(text, self.page)
        for target in re.findall(r'\]\(([^)#]+)\)', self.page):
            if target.startswith('http'):
                continue
            with self.subTest(link=target):
                self.assertTrue((PAGE.parent / target).exists())


if __name__ == '__main__':
    unittest.main()
