"""Acceptance of finite declarations and fabricated representations, not a decoder."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLES = {1: 'remote-eight', 15: 'outdoor-sensor', 16: 'primary-control',
         21: 'base-station', 22: 'base-outdoor-sensor', 23: 'remote-four',
         48: 'remote-one', 55: 'remote-five', 112: 'remote-two',
         119: 'remote-six', 240: 'remote-three', 247: 'remote-seven',
         253: 'diagnosis-tool', 254: 'range-extender'}
STARTS = ((16, 0), (17, 32), (18, 64), (19, 96),
          (20, 128), (21, 160), (22, 192), (23, 224))


def expected_declarations():
    """Independent literal contract; no runtime codec or companion import."""
    result = {}

    def add(op, direction, field, position, width, codec, low, high, default,
            count=None, start=None, mappings=None, bits=None, unknowns=(),
            relation='Unknown'):
        result[(op, direction, field)] = dict(
            key=dict(family='Vaillant radio', variant=None, primary=181,
                     secondary=37, operation=op, direction=direction, field=field),
            grade='Hypothesis', position=position, width=width, codec=codec,
            minimum=low, maximum=high, default=default, count=count,
            start_index=start, unit=None, mappings=mappings or {}, bits=bits or {},
            unknowns=list(unknowns), raw_policy='preserve_all', relation=relation)

    directions = {0: ('Unknown',), 1: ('Unknown',), 2: ('Unknown',),
                  3: ('Unknown',), 4: ('request', 'positive')}
    directions.update({op: ('request', 'positive') for op in range(16, 28)})
    for op, sides in directions.items():
        for side in sides:
            for name, pos, value in [('primary', 0, 181), ('secondary', 1, 37),
                                     ('selector', 2, op)]:
                add(op, side, name, pos, 1, 'u8', value, value, None)
    for field, pos, width, codec, maximum in [
            ('layer', 3, 1, 'u8', 255), ('radio-domain', 4, 2, 'u16-le', 65535),
            ('request-id', 9, 1, 'u8', 255)]:
        add(0, 'Unknown', field, pos, width, codec, 0, maximum, 0,
            unknowns=('lifecycle',) if field == 'request-id' else ())
    add(0, 'Unknown', 'status', None, 1, 'u8', 0, 255, 0,
        bits=dict(enumerate(['repeat', 'group', 'encrypted', 'frame-type',
                             'outdoor-sensor-pairing', 'reserved', 'reserved', 'reserved'])))
    for field, pos in [('sender-role', 7), ('receiver-role', 8)]:
        add(0, 'Unknown', field, pos, 1, 'u8', 0, 255, 1, mappings=ROLES)
    for op in [1, 2]:
        add(op, 'Unknown', 'data', 3, None, 'opaque', 0, None, None,
            unknowns=('cipher', 'padding', 'sender-identity'))
    add(3, 'Unknown', 'RSSI', None, 1, 'signed8', -128, 127, 0,
        unknowns=('physical-unit',))
    add(3, 'Unknown', 'link-quality', None, 1, 'u8', 0, 255, 0,
        bits=dict(enumerate(['link-quality-0', 'link-quality-1', 'link-quality-2',
                            'link-quality-3', 'link-quality-4', 'link-quality-5',
                            'link-quality-6', 'CRC-okay'])), unknowns=('CRC-algorithm',))
    for side in ['request', 'positive']:
        add(4, side, 'bytes', None, 16, 'u8', 0, 255, 0, count=16,
            unknowns=('active-key', 'persistent-key', 'echo'))
    add(4, 'positive', 'feedback', None, 1, 'u8', 0, 255, 0,
        bits=dict(enumerate(['success', 'too-short', 'too-long', 'reserved',
                            'reserved', 'reserved', 'reserved', 'reserved'])),
        unknowns=('exclusivity',), relation='independent-bits')
    for op, start in STARTS:
        add(op, 'request', 'values', 3, 32, 'signed8', -128, 127, 0, count=32,
            start=start, unknowns=('frequency-mapping', 'scanning-effects'))
    for op in [24, 25, 26, 27]:
        for side in ['request', 'positive']:
            add(op, side, 'configuration', 3, 1, 'u8', 0, 255, 0,
                mappings={0: 'read'}, bits={0: 'configuration'},
                unknowns=('bits-1..7', 'effects'))
            add(op, side, 'data', None, None, 'opaque', 0, None, None,
                unknowns=('layout', 'units', 'correlation', 'effects'))
    # JSON object keys are strings, independently of the numeric declaration values.
    for entry in result.values():
        for name in ['bits', 'mappings']:
            entry[name] = {str(k): v for k, v in entry[name].items()}
    return result


class B525Candidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'protocols/vaillant/fixtures/ae22_b525_candidates.json').read_text())
        cls.page = (ROOT / 'protocols/vaillant/ebus-vaillant-B525.md').read_text()
        cls.cases = cls.data['synthetic_cases']
        cls.expected = expected_declarations()

    def test_complete_finite_metadata(self):
        actual = {}
        for entry in self.data['entries']:
            k = entry['key']
            identity = (k['operation'], k['direction'], k['field'])
            self.assertNotIn(identity, actual)
            actual[identity] = entry
        self.assertEqual(len(actual), 127)
        self.assertEqual(actual, self.expected)
        self.assertEqual(self.data['representation_grade'], 'Proven')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(self.data['coordinate_system'], 'logical_including_prefix')

    def test_structured_page_claims_and_adjacent_limits(self):
        rows = {}
        for line in self.page.splitlines():
            if not line.startswith('| ') or line.startswith(('| Selector', '| ---')):
                continue
            cells = [v.strip() for v in line.strip('|').split('|')]
            self.assertEqual(len(cells), 10)
            key = (int(cells[0], 16), cells[1], cells[2])
            self.assertNotIn(key, rows)
            rows[key] = cells
        self.assertEqual(set(rows), set(self.expected))
        def text(value):
            return 'Unknown' if value is None else str(value)
        for key, entry in self.expected.items():
            with self.subTest(identity=key):
                cells = rows[key]
                self.assertEqual(cells[3], 'Hypothesis')
                self.assertEqual(cells[4], '{}; width={}; count={}; start={}'.format(
                    *[text(entry[n]) for n in ['position', 'width', 'count', 'start_index']]))
                self.assertEqual(cells[5], '{}; min={}; max={}'.format(
                    entry['codec'], text(entry['minimum']), text(entry['maximum'])))
                self.assertEqual(cells[6], 'scale=Unknown; unit=Unknown')
                conflict = 'none declared'
                if key[2] in ['sender-role', 'receiver-role']:
                    conflict = '10: primary-control / master-control label alias; other bytes raw'
                if key[2] == 'feedback':
                    conflict = 'simultaneous flags; no exclusivity established'
                if key[2] == 'bytes':
                    conflict = 'no echo established'
                self.assertEqual(cells[7], f"default={text(entry['default'])}; sentinel=Unknown; {conflict}")
                bits = ', '.join(f'{k}={v}' for k, v in entry['bits'].items()) or 'none declared'
                codes = ', '.join(f'{int(k):02X}={v}' for k, v in entry['mappings'].items()) or 'none declared'
                self.assertEqual(cells[8], f'bits: {bits}; codes: {codes}')
                self.assertEqual(cells[9], '; '.join(entry['unknowns']) +
                                 f"; relation={entry['relation']}; preserve_all")
        for statement in ['A logical position is not a wire offset',
                          'minimum zero and maximum unset',
                          'empty-packet acceptance', 'positives are prefix-only',
                          'physical and\nnative qualification remain **Unknown**']:
            self.assertIn(statement, self.page)

    def test_roles_independently_and_unmapped_zero(self):
        codes = [1, 15, 16, 21, 22, 23, 48, 55, 112, 119, 240, 247, 253, 254, 0]
        self.assertEqual(self.cases['roles'],
                         [dict(sender=x, receiver=1) for x in codes] +
                         [dict(sender=1, receiver=x) for x in codes])
        self.assertNotIn(0, ROLES)

    def test_raw_signed_arithmetic_and_feedback(self):
        self.assertEqual(self.cases['rssi'], dict(raw=255, signed=-1, unit=None))
        self.assertEqual(int.from_bytes(bytes([255]), signed=True), -1)
        self.assertEqual(self.cases['signed_values'],
                         [dict(raw=128, value=-128), dict(raw=0, value=0), dict(raw=127, value=127)])
        for vector in self.cases['signed_values']:
            self.assertEqual(int.from_bytes(bytes([vector['raw']]), signed=True), vector['value'])
        self.assertEqual(self.cases['feedback'], dict(raw=7,
                         flags=['success', 'too-short', 'too-long'], relation='independent-bits'))
        self.assertEqual((7 & 1, 7 & 2, 7 & 4), (1, 2, 4))

    def test_sixteen_independent_bytes_on_both_sides(self):
        self.assertEqual(self.cases['zero_bytes'], [0] * 16)
        arrays = self.cases['byte_arrays']
        self.assertEqual(len(arrays), 32)
        for side in ['request', 'positive']:
            selected = [x for x in arrays if x['direction'] == side]
            self.assertEqual([x['varied_index'] for x in selected], list(range(16)))
            for i, vector in enumerate(selected):
                self.assertEqual(len(vector['raw']), 16)
                self.assertEqual(vector['raw'][i], 170)
                self.assertEqual(vector['raw'][:i] + vector['raw'][i+1:], [0] * 15)

    def test_blocks_and_opaque_representation(self):
        self.assertEqual(self.cases['block_lengths'], [dict(count=31, form='incomplete'),
                         dict(count=32, form='declared'), dict(count=33, form='extra')])
        self.assertEqual(self.cases['opaque'], [[], [0, 170, 255]])
        arrays = self.cases['signed_arrays']
        self.assertEqual(len(arrays), 24)
        for op in [16, 17, 18, 19, 20, 21, 22, 23]:
            selected = [v for v in arrays if v['operation'] == op]
            self.assertEqual([(v['raw'], v['values']) for v in selected],
                             [([128] * 32, [-128] * 32), ([0] * 32, [0] * 32),
                              ([127] * 32, [127] * 32)])
            for vector in selected:
                self.assertEqual(list(int.from_bytes(bytes([b]), signed=True)
                                      for b in vector['raw']), vector['values'])
        self.assertEqual(self.cases['independent_bytes'],
                         [dict(request=[0]*16, positive=[170]+[0]*15),
                          dict(request=[170]+[0]*15, positive=[0]*16)])
        self.assertEqual(34 - 3 + 1, 32)
        self.assertEqual((0 + 31, 224 + 31), (31, 255))

    def test_configuration_each_side_retains_every_high_bit(self):
        vectors = self.cases['configuration']
        literals = [(0, 0, 0), (1, 1, 0), (2, 0, 2), (4, 0, 4), (8, 0, 8),
                    (16, 0, 16), (32, 0, 32), (64, 0, 64), (128, 0, 128),
                    (170, 0, 170), (255, 1, 254)]
        self.assertEqual(len(vectors), 88)
        for op in [24, 25, 26, 27]:
            for side in ['request', 'positive']:
                group = [x for x in vectors if (x['operation'], x['direction']) == (op, side)]
                self.assertEqual([(x['raw'], x['bit0'], x['unknown_high']) for x in group], literals)
                for vector in group:
                    self.assertEqual(vector['bit0'] + vector['unknown_high'], vector['raw'])


if __name__ == '__main__':
    unittest.main()
