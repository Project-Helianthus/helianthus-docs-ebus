"""Synthetic B514 activation-vector contract; no native qualification."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am24_b514_activation_vectors.md'
DATA = ROOT / 'architecture/fixtures/am24_b514_activation_vectors.json'
IDENT = ('vaillant', 'B514', 3, 'positive')
SIZES = {3: 10, 4: 12}
OP04 = bytes.fromhex('000380ff0102040810204055')


def view(family, variant, operation, direction, data, *, mutant=None):
    """Reference implementation of the page contract (mutants for kill checks)."""
    raw = bytes(data) if mutant != 'alias-raw' else data
    ok = (family, variant, direction) == ('vaillant', 'B514', 'positive') \
        and operation in SIZES
    if not ok:
        return {'recognized': False, 'grade': 'Unknown', 'raw': bytes(raw),
                'present_mask': None, 'complete': False, 'remainder': b'',
                'fields': None}
    size = SIZES[operation]
    if mutant == 'accept-extra':
        size = max(size, len(raw))
    present = min(len(raw), size)
    fields = []
    for i in range(size):
        if i >= present:
            v = 0 if mutant == 'zero-fill' else None
            fields.append({'present': mutant == 'zero-fill', 'value': v})
            continue
        entry = {'present': True, 'value': raw[i]}
        if operation == 3:
            order = range(7, -1, -1) if mutant == 'bit-order' else range(8)
            entry['bits'] = [bool(raw[i] >> b & 1) for b in order]
            if mutant == 'alias':
                entry['bits'][7] = entry['bits'][6]
            entry['label'] = 'Unknown'
        else:
            entry['interpretation'] = 'Unknown'
            if mutant == 'op04-bits':
                entry['bits'] = [bool(raw[i] >> b & 1) for b in range(8)]
        fields.append(entry)
    return {'recognized': True, 'grade': 'Hypothesis', 'raw': raw,
            'present_mask': (1 << present) - 1,
            'complete': (len(raw) == SIZES[operation]) if mutant != 'short-complete'
            else len(raw) >= 1,
            'remainder': bytes(raw[SIZES[operation]:]), 'fields': fields}


def tables(text):
    out, cur = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            cur.append([c.strip() for c in line.strip('|').split('|')])
        elif cur:
            out.append((cur[0], cur[2:]))
            cur = []
    return out


def check_view(t, v, op, data):
    """Independent oracle: int arithmetic only, no shared code with view()."""
    size = SIZES[op]
    n = len(data)
    t.assertTrue(v['recognized'])
    t.assertEqual(v['grade'], 'Hypothesis')
    t.assertEqual(v['raw'], data)
    t.assertEqual(v['present_mask'], 2 ** min(n, size) - 1)
    t.assertEqual(v['complete'], n == size)
    t.assertEqual(v['remainder'], data[size:])
    t.assertEqual(len(v['fields']), size)
    for i, f in enumerate(v['fields']):
        if i >= n:
            t.assertEqual(f, {'present': False, 'value': None})
            continue
        t.assertTrue(f['present'])
        t.assertEqual(f['value'], data[i])
        if op == 3:
            t.assertEqual(f['label'], 'Unknown')
            t.assertEqual(len(f['bits']), 8)
            for b in range(8):
                t.assertIs(f['bits'][b], (data[i] // 2 ** b) % 2 == 1)
        else:
            t.assertEqual(set(f), {'present', 'value', 'interpretation'})
            t.assertEqual(f['interpretation'], 'Unknown')


class B514ActivationVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.page = PAGE.read_text()

    def v(self, data, op=3, **kw):
        return view('vaillant', 'B514', op, 'positive', data, **kw)

    def test_op03_walk_80_positions(self):
        seen = set()
        for pos in range(80):
            idx, bit = divmod(pos, 8)
            data = bytearray(10)
            data[idx] = 1 << bit
            v = self.v(bytes(data))
            check_view(self, v, 3, bytes(data))
            trues = [(i, b) for i, f in enumerate(v['fields'])
                     for b, x in enumerate(f['bits']) if x]
            self.assertEqual(trues, [(idx, bit)])
            seen.add(trues[0])
        self.assertEqual(len(seen), 80)

    def test_op03_neighbours_retained(self):
        data = bytes([0xA5, 0x00, 0xFF, 0x10, 0x81, 0x7E, 0x01, 0x80, 0x02, 0x55])
        check_view(self, self.v(data), 3, data)

    def test_op04_twelve_scalars(self):
        check_view(self, self.v(OP04, 4), 4, OP04)
        self.assertEqual([f['value'] for f in self.v(OP04, 4)['fields']],
                         list(OP04))
        self.assertEqual(len(set(OP04)), 12)
        for b in (0x00, 0x03, 0x80, 0xFF):
            self.assertIn(b, OP04)

    def test_every_length_both_operations(self):
        for op, size in SIZES.items():
            base = (bytes(range(1, 11)) + b'\x00\xFF')[:size] if op == 3 else OP04
            for n in range(size + 3):
                data = (base + b'\x7f\x00\x01')[:n]
                check_view(self, self.v(data, op), op, data)

    def test_missing_differs_from_present_zero(self):
        short = self.v(b'\x00')
        zero = self.v(b'\x00' * 10)
        self.assertEqual(short['fields'][0], zero['fields'][0])
        self.assertEqual(short['fields'][1], {'present': False, 'value': None})
        self.assertTrue(zero['fields'][1]['present'])
        self.assertEqual(zero['fields'][1]['value'], 0)
        self.assertNotEqual(short['present_mask'], zero['present_mask'])

    def test_identity_axes_vary_independently(self):
        data = bytes(10)
        for axis, bad in enumerate(['other', 'B515', 99, 'negative']):
            ident = list(IDENT)
            ident[axis] = bad
            v = view(*ident, data)
            self.assertFalse(v['recognized'], axis)
            self.assertEqual((v['grade'], v['raw'], v['remainder'], v['complete']),
                             ('Unknown', data, b'', False))
            self.assertIsNone(v['present_mask'])
            self.assertIsNone(v['fields'])
        for good in (IDENT, ('vaillant', 'B514', 4, 'positive')):
            self.assertTrue(view(*good, data)['recognized'])
        for bad_op in (0, 1, 2, 5, 255, None, '3'):
            self.assertFalse(view('vaillant', 'B514', bad_op, 'positive', data)['recognized'])

    def test_owned_raw_memory(self):
        src = bytearray(b'\x01' * 11)
        v = self.v(src)
        src[0] = 0xFF
        src[10] = 0xEE
        self.assertEqual(v['raw'], b'\x01' * 11)
        self.assertEqual(v['remainder'], b'\x01')
        r1 = self.v(bytes(11))
        r2 = self.v(bytes(11))
        self.assertIsNot(r1['raw'], r2['raw'])
        self.assertIsNot(r1['fields'], r2['fields'])
        r1['fields'][0]['bits'][0] = True
        self.assertFalse(r2['fields'][0]['bits'][0])
        raw = self.v(src, 5)
        src[1] = 9
        self.assertEqual(raw['raw'][1], 1)

    def test_fixture_cases_match_independent_arithmetic(self):
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['identity'],
                         {'family': 'vaillant', 'variant': 'B514', 'direction': 'positive'})
        self.assertEqual({k: v['size'] for k, v in self.data['operations'].items()},
                         {'3': 10, '4': 12})
        self.assertEqual(len(self.data['cases']), 9)
        for c in self.data['cases']:
            data = bytes.fromhex(c['input'])
            v = self.v(data, c['operation'])
            if c['operation'] in SIZES:
                check_view(self, v, c['operation'], data)
                self.assertEqual(c['present_mask'], 2 ** min(len(data), SIZES[c['operation']]) - 1)
                self.assertEqual(c['complete'], len(data) == SIZES[c['operation']])
                self.assertEqual(c['remainder'], data[SIZES[c['operation']]:].hex())
            else:
                self.assertFalse(v['recognized'])
                self.assertIsNone(c['present_mask'])
                self.assertFalse(c['complete'])
                self.assertEqual(c['remainder'], '')

    def test_page_agrees_with_fixture(self):
        rows = [r for h, r in tables(self.page) if h[0] == 'Case']
        self.assertEqual(len(rows), 1)
        rows = rows[0]
        cases = {c['id']: c for c in self.data['cases']}
        self.assertEqual([r[0] for r in rows], list(cases))
        for r in rows:
            c = cases[r[0]]
            self.assertEqual(int(r[1]), c['operation'])
            self.assertEqual('' if r[2] == '(empty)' else r[2], c['input'])
            self.assertEqual(None if r[3] == 'null' else int(r[3]), c['present_mask'])
            self.assertEqual(r[4], 'true' if c['complete'] else 'false')
            self.assertEqual('' if r[5] == '(empty)' else r[5], c['remainder'])
        for s in ('Hypothesis', 'Unknown', 'ten separate u8', 'twelve separate scalar',
                  '80 independent', '96 declared', 'never\n`false` or zero'.replace('\n', ' ')):
            self.assertIn(s, ' '.join(self.page.split()))
        self.assertNotRegex(self.page, r'\b[0-9a-f]{40}\b')

    def test_page_links_resolve(self):
        links = re.findall(r'\]\(([^)\s]+)\)', self.page)
        self.assertTrue(links)
        for link in links:
            self.assertTrue((PAGE.parent / link).exists(), link)

    def test_mutants_are_killed(self):
        def passes(mutant, op, data):
            try:
                check_view(self, self.v(data, op, mutant=mutant), op, data)
                return True
            except AssertionError:
                return False
        full3 = bytes([0x01, 0x80] + [0x40] * 8)
        cases = [('bit-order', 3, full3), ('alias', 3, bytes([0x40] + [0] * 9)),
                 ('op04-bits', 4, OP04), ('zero-fill', 3, b'\x01'),
                 ('zero-fill', 4, b'\x01\x02'), ('accept-extra', 3, bytes(11)),
                 ('short-complete', 3, b'\x01'), ('short-complete', 4, OP04[:5])]
        self.assertTrue(passes(None, 3, full3))
        for mutant, op, data in cases:
            self.assertFalse(passes(mutant, op, data), mutant)
        src = bytearray(10)
        v = self.v(src, mutant='alias-raw')
        src[0] = 1
        self.assertIs(v['raw'], src)
        self.assertNotEqual(bytes(v['raw']), bytes(10))


if __name__ == '__main__':
    unittest.main()
