"""Independent checks of the B514 typed row boundary page and fixture."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al25_b514_typed_row_boundaries.md'
DATA = ROOT / 'architecture/fixtures/al25_b514_typed_row_boundaries.json'


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def check_data(d):
    """Return a list of violations of the finite contract."""
    bad = []
    o2 = d['op02']
    if o2['contracts_declared'] != 20 or o2['logical_base'] != 5:
        bad.append('op02 shape')
    if o2['reused_existing_key_position'] != 3 or o2['inserted_keys'] != 0:
        bad.append('op02 key insertion')
    ra = o2['row_key_to_width']
    if ra['known_associations'] != 0 or ra['guessed_types'] != 0 or ra['width'] != 'Unknown' or ra['grade'] != 'Unknown':
        bad.append('op02 guessed associations')
    u = o2['u8_conflict']
    if u['declared_default'] != 256 or u['alternatives'] != 2 or u['repaired_value'] is not None or u['modulo_repair']:
        bad.append('u8 repair')
    if (u['domain_min'], u['domain_max']) != (0, 255) or u['status'] != 'unresolved-representability-conflict':
        bad.append('u8 domain')
    o3 = d['op03']
    if o3['separate_bytes'] * o3['bits_per_byte'] != 80 or o3['independent_bits'] != 80:
        bad.append('op03 bits')
    o4 = d['op04']
    if o4['scalar_enum_tables'] != 12 or o4['mappings_total'] != 96 or o4['bitmasks'] != 0:
        bad.append('op04 masks')
    if o4['equal_distribution_asserted'] or o4['bitwise_semantics_asserted']:
        bad.append('op04 semantics')
    o5 = d['op05']
    if o5['typed_rows'] != 128 or o5['divisor_10_rows'] != 50:
        bad.append('op05 counts')
    if o5['divisor_10_unit'] != 'Unknown' or o5['divisor_10_unit_state'] != 'raw':
        bad.append('op05 unit')
    t = d['temperature_candidate']
    if t['encoding'] != 'signed-LE16' or t['divisor'] != 16 or t['applies_to_divisor_10_rows']:
        bad.append('temperature candidate')
    if d['raw03_activity_flags']['boolean_mapping'] != 'Unknown':
        bad.append('raw03')
    return bad


def le16(bs, signed):
    v = bs[0] | (bs[1] << 8)
    if signed and v >= 0x8000:
        v -= 1 << 16
    return v


class B514Boundaries(unittest.TestCase):
    def test_control_passes(self):
        self.assertEqual(check_data(load()), [])

    def mutate(self, fn, expect):
        d = load()
        fn(d)
        self.assertIn(expect, check_data(d))

    def test_insert_key(self):
        self.mutate(lambda d: d['op02'].__setitem__('inserted_keys', 1), 'op02 key insertion')

    def test_key_position_moved(self):
        self.mutate(lambda d: d['op02'].__setitem__('reused_existing_key_position', 4), 'op02 key insertion')

    def test_truncate_256(self):
        self.mutate(lambda d: d['op02']['u8_conflict'].__setitem__('declared_default', 0), 'u8 repair')

    def test_modulo_repair(self):
        self.mutate(lambda d: d['op02']['u8_conflict'].__setitem__('modulo_repair', True), 'u8 repair')

    def test_widen_domain(self):
        self.mutate(lambda d: d['op02']['u8_conflict'].__setitem__('domain_max', 256), 'u8 domain')

    def test_enums_as_masks(self):
        self.mutate(lambda d: d['op04'].__setitem__('bitmasks', 12), 'op04 masks')

    def test_bitwise_semantics(self):
        self.mutate(lambda d: d['op04'].__setitem__('bitwise_semantics_asserted', True), 'op04 semantics')

    def test_mapping_total(self):
        self.mutate(lambda d: d['op04'].__setitem__('mappings_total', 12), 'op04 masks')

    def test_celsius_units(self):
        self.mutate(lambda d: d['op05'].__setitem__('divisor_10_unit', 'degC'), 'op05 unit')

    def test_div10_row_count(self):
        self.mutate(lambda d: d['op05'].__setitem__('divisor_10_rows', 51), 'op05 counts')

    def test_row_count(self):
        self.mutate(lambda d: d['op05'].__setitem__('typed_rows', 127), 'op05 counts')

    def test_guessed_width(self):
        self.mutate(lambda d: d['op02']['row_key_to_width'].__setitem__('width', 'u8'), 'op02 guessed associations')

    def test_guessed_known_association(self):
        self.mutate(lambda d: d['op02']['row_key_to_width'].__setitem__('known_associations', 20), 'op02 guessed associations')

    def test_contract_count(self):
        self.mutate(lambda d: d['op02'].__setitem__('contracts_declared', 21), 'op02 shape')

    def test_base(self):
        self.mutate(lambda d: d['op02'].__setitem__('logical_base', 6), 'op02 shape')

    def test_op03_bits(self):
        self.mutate(lambda d: d['op03'].__setitem__('separate_bytes', 9), 'op03 bits')

    def test_temperature_copied(self):
        self.mutate(lambda d: d['temperature_candidate'].__setitem__('applies_to_divisor_10_rows', True), 'temperature candidate')

    def test_temperature_divisor(self):
        self.mutate(lambda d: d['temperature_candidate'].__setitem__('divisor', 10), 'temperature candidate')

    def test_raw03_boolean(self):
        self.mutate(lambda d: d['raw03_activity_flags'].__setitem__('boolean_mapping', 'bit0'), 'raw03')

    def test_arithmetic(self):
        raw = bytes.fromhex('F0FF')
        self.assertEqual(le16(raw, True) / 16, -1)
        self.assertEqual(le16(raw, False) / 10, 6552.0)
        self.assertFalse(0 <= 256 <= 255)
        self.assertEqual(10 * 8, 80)
        ex = load()['examples']
        self.assertEqual(ex['signed_le16_div16']['result'], -1)
        self.assertEqual(ex['unsigned_le16_div10']['result'], 6552.0)
        self.assertEqual(ex['unsigned_le16_div10']['unit'], 'Unknown')
        self.assertFalse(ex['u8_domain']['in_domain'])

    def test_page_statements(self):
        t = PAGE.read_text(encoding='utf-8')
        for s in ('twenty key-to-row-to-value', 'logical base 5', 'position 3',
                  'known associations: 0, guessed types: 0', 'not a byte zero',
                  'no modulo repair', 'Ten separate bytes carry 80', 'Twelve scalar enum tables hold 96',
                  'not twelve\nbitmasks', '128 typed rows', 'fifty use a /10', 'signed little-endian 16-bit with /16',
                  'must not be copied across the /10 map', '6552.0', 'No Boolean mapping'):
            self.assertIn(s, t)
        for s in ('degC', 'Celsius,', 'twenty-one'):
            self.assertNotIn(s, t.replace('not Celsius', ''))

    def test_page_mutations_detected(self):
        t = PAGE.read_text(encoding='utf-8')
        self.assertNotIn('twelve bitmasks.', t.replace('not twelve\nbitmasks', ''))
        self.assertIn('not Celsius', t)


if __name__ == '__main__':
    unittest.main()
