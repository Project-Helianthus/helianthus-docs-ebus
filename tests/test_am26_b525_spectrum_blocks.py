"""Synthetic AM26 prose model and independent oracles; no production codec."""
import copy
import json
from collections.abc import Mapping
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am26-b525-spectrum-blocks.md'
FIXTURE = ROOT / 'architecture/fixtures/am26_b525_spectrum_blocks.json'
FIELDS = ['family', 'variant', 'operation', 'direction', 'selector', 'form',
          'candidate_grade']
CONTEXT_AXES = ['family', 'variant', 'operation', 'direction']
STARTS = (0, 32, 64, 96, 128, 160, 192, 224)
RAW = bytes((0, 127, 128, 255)) * 8
POLICY = dict(context_fields=FIELDS,
              families=['synthetic-radio-family-a', 'synthetic-radio-family-b'],
              variants=['synthetic-variant-a', 'synthetic-variant-b'],
              operation='B525', direction='request', form='isolated_values',
              selectors=list(range(16, 24)), width=32, codec='signed8',
              grade='Hypothesis', positive_values=False, frequency_mapping=False,
              fill_missing=False, complete_distinct_blocks=8)
JOINS = [
    ('all_reversed', 8, 256, 0, True, True),
    ('missing_middle', 7, 224, 32, True, False),
    ('short_last', 8, 228, 28, True, False),
    ('extra_last', 8, 256, 0, True, False),
    ('conflicting_duplicate', 9, 0, 256, False, False),
    ('cross_family', 8, 0, 256, False, False),
    ('cross_variant', 8, 0, 256, False, False),
    ('identical_duplicate', 9, 256, 0, True, True),
    ('positive_only', 1, 0, 256, True, False),
    ('empty', 0, 0, 256, True, False),
]


def view(context, raw, policy):
    if not isinstance(context, Mapping):
        raise TypeError('context mapping required')
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError('value bytes required')
    r = dict(context=copy.deepcopy(context), raw=bytearray(raw), grade=None,
             values=[], present_indices=[], valid=False, incomplete=True,
             extra=False, remainder=bytearray(raw), state='raw_only')
    if any(k not in context for k in policy['context_fields']):
        return r
    if any(not isinstance(context[k], str) or not context[k]
           for k in FIELDS if k != 'selector'):
        return r
    if (context['family'] not in policy['families'] or
            context['variant'] not in policy['variants'] or
            any(context[k] != policy[k] for k in ('operation', 'direction', 'form')) or
            type(context['selector']) is not int or
            context['selector'] not in policy['selectors'] or
            context['candidate_grade'] not in ('Hypothesis', 'Proven')):
        return r
    start = (context['selector'] - 16) * policy['width']
    payload = r['raw'][:policy['width']]
    pairs = [(start + offset, b if b < 128 else b - 256)
             for offset, b in enumerate(payload)]
    n = len(r['raw'])
    r.update(grade='Hypothesis', values=pairs,
             present_indices=[i for i, _ in pairs], valid=n == 32,
             incomplete=n < 32, extra=n > 32, remainder=r['raw'][32:],
             state='short' if n < 32 else 'extra' if n > 32 else 'exact')
    return r


def join(inputs, policy):
    blocks = [view(c, raw, policy) for c, raw in inputs]
    out = dict(blocks=blocks, accepted=True, reason=None, values=[],
               present_indices=[], complete=False, grade=None)
    contexts = [tuple(b['context'].get(k) for k in CONTEXT_AXES) for b in blocks]
    if any(c != contexts[0] for c in contexts):
        out.update(accepted=False, reason='cross_context')
        return out
    unique = []
    for block in blocks:
        identity = tuple(block['context'].get(k) for k in CONTEXT_AXES + ['selector'])
        previous = next((b for key, b in unique if key == identity), None)
        if previous is not None:
            if previous['raw'] != block['raw'] or previous['context'] != block['context']:
                out.update(accepted=False, reason='conflicting_duplicate')
                return out
        else:
            unique.append((identity, block))
    values = sorted(pair for _, b in unique for pair in b['values'])
    out.update(values=values, present_indices=[i for i, _ in values],
               complete=len(unique) == 8 and all(b['valid'] for _, b in unique),
               grade='Hypothesis' if any(b['grade'] for b in blocks) else None)
    return out


class SpectrumBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(FIXTURE.read_text())
        cls.policy = cls.package['policy']

    def context(self, selector=16, **patch):
        return dict(dict(family='synthetic-radio-family-a', variant='synthetic-variant-a',
                         operation='B525', direction='request', selector=selector,
                         form='isolated_values', candidate_grade='Hypothesis'), **patch)

    def check_view(self, context, raw=RAW, selected=True):
        result = view(context, raw, self.policy)
        # Independent signed decoder, independent literal starts, never model output.
        expected = []
        if selected:
            start = STARTS[context['selector'] - 16]
            expected = [(start + i, struct.unpack('b', bytes((b,)))[0])
                        for i, b in enumerate(bytes(raw)[:32])]
        self.assertEqual(result['values'], expected)
        self.assertEqual(result['present_indices'], [i for i, _ in expected])
        self.assertEqual(result['context'], context)
        self.assertEqual(result['raw'], raw)
        self.assertIsNot(result['raw'], raw)
        self.assertEqual(result['grade'], 'Hypothesis' if selected else None)
        self.assertEqual(result['valid'], selected and len(raw) == 32)
        self.assertEqual(result['incomplete'], not selected or len(raw) < 32)
        self.assertEqual(result['extra'], selected and len(raw) > 32)
        self.assertEqual(result['remainder'], bytes(raw)[32:] if selected else raw)
        self.assertEqual(result['state'], 'raw_only' if not selected else
                         'short' if len(raw) < 32 else 'extra' if len(raw) > 32 else 'exact')
        self.assertEqual(set(result), {'context', 'raw', 'grade', 'values',
                         'present_indices', 'valid', 'incomplete', 'extra', 'remainder', 'state'})
        return result

    def test_page_policy_tables_and_links(self):
        page = PAGE.read_text()
        self.assertEqual(self.policy, POLICY)
        self.assertEqual(json.loads(re.search(r'```json\n(.*?)\n```', page, re.S)[1]), POLICY)
        rows = re.findall(r'^\| (1[0-7]) \| (\d+) \| (\d+) \|$', page, re.M)
        self.assertEqual([(int(s, 16), int(a), int(b)) for s, a, b in rows],
                         [(16+i, start, start+31) for i, start in enumerate(STARTS)])
        rows = re.findall(r'^\| (\w+) \| (\d+) \| (\d+) \| (\d+) \| (true|false) \| (true|false) \|$', page, re.M)
        self.assertEqual([(n, int(b), int(i), int(a), ok == 'true', c == 'true')
                          for n, b, i, a, ok, c in rows], JOINS)
        for link in re.findall(r'\]\(([^)]+)\)', page):
            path, _, anchor = link.partition('#')
            target = PAGE.parent / path
            self.assertTrue(target.is_file(), link)
            if anchor:
                headings = re.findall(r'^#+ (.+)$', target.read_text(), re.M)
                self.assertIn(anchor, [re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-')
                                      for h in headings])
        for clause in ('Frequency, band, channel spacing, RSSI unit,',
                       'cadence and native scan action remain Unknown.',
                       'Positive declarations are prefix-only',
                       'Extra values never advance into',
                       'last-known-good', 'GraphQL parity', 'eBUS MCP compatibility',
                       'never an active scan or one atomic device',
                       'Index is a logical integer, never a frequency or scaled',
                       'output grade stays Hypothesis',
                       '`0 / 127 / -128 / -1`',
                       'Complete is true only for eight distinct valid',
                       'Absent indices stay absent',
                       'Conflicting duplicates of one identity',
                       'Unknown,\nmissing or malformed grade is raw-only'):
            self.assertIn(clause, page)

    def test_exact_examples_and_independent_signed_arithmetic(self):
        self.assertEqual(len(self.package['blocks']), 8)
        for i, case in enumerate(self.package['blocks']):
            self.assertEqual(case['name'], f'block_{16+i:02x}')
            self.assertEqual(case['context'], self.context(16+i))
            self.assertEqual(bytes.fromhex(case['raw_hex']), RAW)
            self.assertEqual(case['expected'], dict(first=STARTS[i], last=STARTS[i]+31,
                             count=32, grade='Hypothesis', state='exact', valid=True, remainder_hex=''))
            r = self.check_view(case['context'], bytes.fromhex(case['raw_hex']))
            self.assertEqual(r['values'][0][0], STARTS[i])
            self.assertEqual(r['values'][-1][0], STARTS[i]+31)
            self.assertEqual([v for _, v in r['values'][:4]], [0, 127, -128, -1])
            for b, value in zip(RAW, [v for _, v in r['values']]):
                self.assertEqual(value, int.from_bytes(bytes([b]), 'big', signed=True))

    def test_scenario_inventory_and_results(self):
        expected = [
            ('short', {}, RAW[:4], 4, 'short', False, b''),
            ('extra', {}, RAW+b'\x80\xff', 32, 'extra', False, b'\x80\xff'),
            ('empty_vector', {}, b'', 0, 'short', False, b''),
            ('positive', {'form': 'positive_prefix'}, RAW, 0, 'raw_only', False, RAW),
            ('positive_direction', {'direction': 'positive'}, RAW, 0, 'raw_only', False, RAW),
            ('unknown_form', {'form': 'unknown'}, RAW, 0, 'raw_only', False, RAW),
            ('unknown_selector', {'selector': 24}, RAW, 0, 'raw_only', False, RAW),
            ('unknown_family', {'family': 'unknown'}, RAW, 0, 'raw_only', False, RAW),
            ('unknown_grade', {'candidate_grade': 'Unknown'}, RAW, 0, 'raw_only', False, RAW),
            ('proven_input', {'candidate_grade': 'Proven'}, RAW, 32, 'exact', True, b''),
        ]
        self.assertEqual(self.package['scenarios'], [dict(name=n, patch=p, raw_hex=raw.hex(),
                         expected=dict(count=count, state=state, valid=valid,
                                       remainder_hex=rem.hex(), grade=None if state=='raw_only' else 'Hypothesis'))
                         for n, p, raw, count, state, valid, rem in expected])
        for n, patch, raw, count, state, valid, rem in expected:
            with self.subTest(case=n):
                self.check_view(self.context(**patch), raw, selected=state != 'raw_only')

    def test_every_context_axis_independently(self):
        for family in POLICY['families']:
            for variant in POLICY['variants']:
                for selector in range(16, 24):
                    base = self.context(selector, family=family, variant=variant)
                    self.check_view(base)
                    for field in FIELDS:
                        for bad in (None, '', False, [], {}, 'unknown'):
                            with self.subTest(selector=selector, field=field, bad=bad):
                                self.check_view(dict(base, **{field: bad}), selected=False)
                        absent = dict(base)
                        del absent[field]
                        self.check_view(absent, selected=False)
                    # Each independently changed valid axis retains its own identity.
                    for field, value in [('family', POLICY['families'][1-POLICY['families'].index(family)]),
                                         ('variant', POLICY['variants'][1-POLICY['variants'].index(variant)]),
                                         ('selector', 16+(selector-15) % 8),
                                         ('candidate_grade', 'Proven')]:
                        changed = dict(base, **{field: value})
                        self.assertEqual(sum(changed[k] != base[k] for k in FIELDS), 1)
                        self.check_view(changed)
                    for field, value in [('operation', 'B524'), ('direction', 'positive'),
                                         ('form', 'positive_prefix'), ('selector', 0),
                                         ('selector', -1), ('selector', 256), ('selector', '10')]:
                        self.check_view(dict(base, **{field: value}), selected=False)

    def test_each_raw_byte_axis_partial_extra_and_zero(self):
        for selector in range(16, 24):
            for size in (0, 1, 4, 31, 32, 33, 64):
                raw = (RAW*2)[:size]
                self.check_view(self.context(selector), raw)
                self.check_view(self.context(selector, form='positive_prefix'), raw, False)
            for offset in range(32):
                for byte in (0, 127, 128, 255):
                    raw = bytearray(32)
                    raw[offset] = byte
                    self.check_view(self.context(selector), raw)
            short = self.check_view(self.context(selector), b'')
            zero = self.check_view(self.context(selector), b'\0')
            self.assertNotEqual(short['present_indices'], zero['present_indices'])
            self.assertEqual(zero['values'], [(STARTS[selector-16], 0)])

    def inputs(self):
        return [(self.context(s), RAW) for s in range(16, 24)]

    def test_join_examples_and_order_independent_sparse_oracle(self):
        inputs = self.inputs()
        cases = dict(all_reversed=list(reversed(inputs)),
                     missing_middle=inputs[:3]+inputs[4:],
                     short_last=inputs[:-1]+[(inputs[-1][0], RAW[:4])],
                     extra_last=inputs[:-1]+[(inputs[-1][0], RAW+b'\xff')],
                     conflicting_duplicate=inputs+[(inputs[0][0], b'\x01'+RAW[1:])],
                     cross_family=inputs[:-1]+[(dict(inputs[-1][0], family='synthetic-radio-family-b'), RAW)],
                     cross_variant=inputs[:-1]+[(dict(inputs[-1][0], variant='synthetic-variant-b'), RAW)],
                     identical_duplicate=inputs+[inputs[0]],
                     positive_only=[(self.context(form='positive_prefix'), RAW)], empty=[])
        self.assertEqual(self.package['joins'], [dict(name=n, blocks=b, indices=i,
                         absent=a, accepted=ok, complete=c) for n, b, i, a, ok, c in JOINS])
        oracle = {i: (0, 127, -128, -1)[i % 4] for i in range(256)}
        for name, b, indices, absent, accepted, complete in JOINS:
            with self.subTest(case=name):
                r = join(cases[name], self.policy)
                self.assertEqual(len(r['blocks']), b)
                self.assertEqual(len(r['present_indices']), indices)
                self.assertEqual(256-len(r['present_indices']), absent)
                self.assertEqual(r['accepted'], accepted)
                self.assertEqual(r['complete'], complete)
                mask = set(oracle) if indices else set()
                if name == 'missing_middle':
                    mask -= set(range(96, 128))
                if name == 'short_last':
                    mask -= set(range(228, 256))
                self.assertEqual(r['values'], [(i, oracle[i]) for i in sorted(mask)])
                self.assertEqual(r['present_indices'], sorted(mask))
                self.assertEqual(r['grade'], 'Hypothesis' if indices else None)
                reason = ('conflicting_duplicate' if name == 'conflicting_duplicate' else
                          'cross_context' if name.startswith('cross_') else None)
                self.assertEqual(r['reason'], reason)
                for block, (c, raw) in zip(r['blocks'], cases[name]):
                    self.assertEqual(block, view(c, raw, self.policy))
        for rotation in range(8):
            r = join(inputs[rotation:]+inputs[:rotation], self.policy)
            self.assertEqual(r['values'], list(oracle.items()))
            self.assertTrue(r['complete'])
        for missing in range(8):
            r = join(inputs[:missing]+inputs[missing+1:], self.policy)
            self.assertFalse(r['complete'])
            self.assertEqual(set(oracle)-set(r['present_indices']),
                             set(range(STARTS[missing], STARTS[missing]+32)))

    def test_join_every_identity_axis_and_duplicate_conflict(self):
        inputs = self.inputs()
        for field, changed in [('family', 'synthetic-radio-family-b'),
                               ('variant', 'synthetic-variant-b'),
                               ('operation', 'B524'), ('direction', 'positive')]:
            mixed = inputs[:-1]+[(dict(inputs[-1][0], **{field: changed}), RAW)]
            r = join(mixed, self.policy)
            self.assertFalse(r['accepted'])
            self.assertEqual(r['reason'], 'cross_context')
            self.assertEqual(r['values'], [])
            # Valid uniform family/variant controls cannot accidentally ban joins.
            if field in ('family', 'variant'):
                r = join([(dict(c, **{field: changed}), raw) for c, raw in inputs], self.policy)
                self.assertTrue(r['complete'])
        # Selector is part of duplicate identity, not merely arrival position.
        for s in range(16, 24):
            r = join(inputs+[(self.context(s), RAW[:31]+b'\0')], self.policy)
            self.assertFalse(r['accepted'])
            self.assertEqual(r['reason'], 'conflicting_duplicate')
        for field, value in [('form', 'positive_prefix'), ('candidate_grade', 'Proven')]:
            r = join(inputs+[(self.context(**{field: value}), RAW)], self.policy)
            self.assertEqual(r['reason'], 'conflicting_duplicate')
        short = join([(self.context(), b'')], self.policy)
        self.assertEqual(short['grade'], 'Hypothesis')
        self.assertFalse(short['complete'])

    def test_owned_memory_and_type_errors(self):
        for selected in (True, False):
            c = self.context(form='isolated_values' if selected else 'positive_prefix',
                             extra={'items': [0]})
            snapshot = copy.deepcopy(c)
            raw = bytearray(RAW+b'\xff')
            for container in (raw, memoryview(raw)):
                r = self.check_view(c, container, selected)
                joined = join([(c, container)], self.policy)
                raw[0] = 77
                c['extra']['items'][0] = 77
                self.assertEqual(r['raw'], RAW+b'\xff')
                self.assertEqual(r['context'], snapshot)
                self.assertEqual(joined['blocks'][0]['raw'], RAW+b'\xff')
                r['raw'][1] = 66
                r['remainder'][0] = 66
                r['context']['extra']['items'].append(1)
                self.assertEqual(raw[1], 127)
                self.assertEqual(c['extra']['items'], [77])
                self.assertEqual(joined['blocks'][0]['context'], snapshot)
                raw[0] = 0
                c['extra']['items'][0] = 0
        for raw in (None, [], '007f80ff', 32):
            with self.assertRaises(TypeError):
                view(self.context(), raw, self.policy)
        for c in (None, [], 'context'):
            with self.assertRaises(TypeError):
                view(c, RAW, self.policy)


if __name__ == '__main__':
    unittest.main()
