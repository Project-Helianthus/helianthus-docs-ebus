"""Finite synthetic B51B representation; no peer or transport execution."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B51B.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac18_program_blocks.json'
# Independent finite oracle: operation, request fields/extent, positive fields/extent.
LAYOUTS = (
    ('06', 'none', '3', 'raw-a@3, raw-b@4, raw-c@5', '6'),
    ('07', 'none', '3', 'generic-feedback@3', '4'),
    ('08', 'block@3, segment@7', '11', 'block-feedback@3', '4'),
    ('09', 'offset@3, data@5', '5+k', 'generic-feedback@3', '4'),
    ('0A', 'none', '3', 'generic-feedback@3', '4'),
    ('0B', 'none', '3', 'CRC@3', '5'),
    ('0C', 'none', '3', 'state@3', '4'),
    ('0D', 'timeout@3', '4', 'generic-feedback@3', '4'),
    ('0E', 'direction@3', '4', 'generic-feedback@3', '4'),
)
FIELDS = [
    ['raw-a, raw-b, raw-c', 'raw u8 independent', '0..255', '0 each', 'unchanged', '1 each', 'none'],
    ['block, segment', 'LE u32 independent', '0..4294967295', '0 each', 'unchanged', '4 each', 'none'],
    ['offset', 'LE u16', '0..65535', 'Unknown', 'unchanged', '2', 'none'],
    ['data', 'opaque bytes', 'minimum 0; maximum absent', 'Unknown', 'unchanged', 'k; maximum absent', 'none'],
    ['CRC', 'LE u16', '0..65535', 'Unknown', 'unchanged', '2', 'none'],
    ['state', 'raw u8', '0..255', 'Unknown', 'unchanged', '1', '0 hardware-init; 1 wait-programming-request; 2 check-application-CRC; 3 preparation; 4 active; 5 application-running; 6..FF unlabeled'],
    ['timeout', 'raw u8 minutes', '0..255', '15', 'unchanged', '1', 'zero has no special meaning'],
    ['direction', 'raw u8', '0..255', 'F0 application', 'unchanged', '1', '0F boot-loader; F0 application; others unlabeled'],
]
FEEDBACK = [
    ['generic-feedback', '01 accepted; 00 and 02..FF rejected'],
    ['block-feedback', '00 rejected; 33 block-unavailable; 55 accepted; AA protected; others unlabeled'],
]
UNKNOWNS = ['full forwarding variants', 'segmentation variants', 'local CRC variants',
            'physical addresses', 'response adaptation', 'geometry', 'peer algorithm',
            'CRC coverage', 'persistence', 'native adaptation', 'peer effects',
            'physical qualification', 'negative response layouts', 'variant']
CLAIMS = (
    '**Hypothesis** applies to every candidate layout, meaning and physical interpretation.',
    '**Proven** describes synthetic representation checks only.',
    'Physical qualification remains **Unknown**.',
    'Logical coordinates include B5/1B/operation at 0/1/2; they are not established physical wire offsets.',
    'OP06 retains three independent raw numbers without BCD or version conversion.',
    'OP07 requests programming; OP0A requests block commit; OP0B requests CRC.',
    'OP0C has no request arguments; OP0D and OP0E have only their listed input.',
    'Constant 08 at position 2 is an operation, not a block number; bytes FF FF FF FF are not a sentinel.',
    'Empty OP09 data does not establish peer acceptance.',
    'OP0D byte 0F stays 15 minutes, without encoding 900 or converting to seconds.',
    'Commit feedback does not prove persistence.',
    'Requests that start, commit or transition are mutative declarations only.',
    'No runtime capability or write admission follows from this catalog.',
    'Unknown extent is absent information, never zero length.',
    'Preserve raw bytes, unresolved alternatives and independent useful fields; a failed interpretation does not erase last-known-good information.',
    'Other qualified variants remain separate; this partial catalog does not replace them.',
)

def rows():
    result = []
    for op, req, req_extent, pos, pos_extent in LAYOUTS:
        for alternative in ('request', 'positive', 'negative'):
            result.append(['Vaillant', 'Unknown', 'request' if alternative == 'request' else 'response',
                           'B51B', op, alternative,
                           req if alternative == 'request' else pos if alternative == 'positive' else 'Unknown',
                           req_extent if alternative == 'request' else pos_extent if alternative == 'positive' else 'Unknown',
                           'Hypothesis'])
    return result


def expected_tables():
    return [
        [['Family', 'Variant', 'Direction', 'Service', 'Operation', 'Alternative', 'Fields at logical position', 'Extent', 'Grade'], ['---'] * 9] + rows(),
        [['Field', 'Representation', 'Domain', 'Default', 'Conversion', 'Width or extent', 'Labels', 'Grade'], ['---'] * 8] + [r + ['Hypothesis'] for r in FIELDS],
        [['Field', 'Labels', 'Grade'], ['---'] * 3] + [r + ['Hypothesis'] for r in FEEDBACK],
        [['Property', 'Grade'], ['---'] * 2] + [[p, 'Unknown'] for p in UNKNOWNS],
    ]


def parse_tables(page):
    result, current = [], []
    for line in page.splitlines() + ['']:
        if line.startswith('|'):
            current.append([c.strip() for c in line.strip('|').split('|')])
        elif current:
            result.append(current)
            current = []
    return result


class ProgramBlocksTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_complete_declarations(self):
        # Kills any field/domain/default/conversion/enum/extent/grade drift,
        # missing alternatives, or replacing an absent extent by zero.
        self.assertEqual(self.data['rows'], rows())
        self.assertEqual(self.data['fields'], FIELDS)
        self.assertEqual(self.data['feedback'], FEEDBACK)
        self.assertEqual(self.data['unknowns'], dict.fromkeys(UNKNOWNS, 'Unknown'))
        self.assertEqual(self.data['grades'], {'representation': 'Proven', 'candidate': 'Hypothesis', 'physical': 'Unknown'})
        self.assertIs(self.data['synthetic_only'], True)
        self.assertEqual(self.data['coordinates'], ['B5', '1B', 'operation'])

    def test_scoped_page(self):
        # Page-only mutations cannot hide behind a correct fixture.
        self.assertEqual(parse_tables(self.page), expected_tables())
        prose = ' '.join(self.page.split())
        for claim in CLAIMS:
            with self.subTest(claim=claim):
                self.assertIn(claim, prose)

    def test_numeric_examples(self):
        # Literal controls kill endian reversal, block/operation confusion,
        # timeout scaling, data loss, enum sharing and invented CRC algorithms.
        examples = self.data['examples']
        self.assertEqual(examples, {
            'block': 16909060, 'segment': 84281096,
            'op08': [181, 27, 8, 4, 3, 2, 1, 8, 7, 6, 5],
            'offset': 4660, 'data': [0, 255], 'op09': [181, 27, 9, 52, 18, 0, 255],
            'timeout': {'raw': 15, 'minutes': 15},
            'crc': {'raw': [52, 18], 'number': 4660, 'algorithm': 'Unknown'},
            'state6': 'unlabeled', 'op08_55': 'accepted', 'generic_55': 'rejected',
            'op08_AA': 'protected', 'generic_AA': 'rejected', 'empty_data': []})
        self.assertEqual(bytes(examples['op08']), b'\xb5\x1b\x08' + examples['block'].to_bytes(4, 'little') + examples['segment'].to_bytes(4, 'little'))
        self.assertEqual(bytes(examples['op09']), b'\xb5\x1b\x09' + examples['offset'].to_bytes(2, 'little') + bytes(examples['data']))
        self.assertEqual(int.from_bytes(bytes(examples['crc']['raw']), 'little'), 0x1234)
        self.assertEqual(len(b'\xb5\x1b\x09\x00\x00' + bytes(examples['empty_data'])), 5)
        for literal in ('OP08 block 16909060 (decimal), segment 84281096 (decimal)',
                        'B5 1B 08 04 03 02 01 08 07 06 05', 'B5 1B 09 34 12 00 FF', '34 12', '0x1234'):
            self.assertIn(literal, self.page)

    def test_each_identity_axis_independently(self):
        # Valid controls followed by every axis of every alternative independently.
        # family/variant/direction/service/operation/alternative omissions all fail.
        control = self.data['rows']
        self.assertEqual(control, rows())
        page_control = parse_tables(self.page)[0]
        self.assertEqual(page_control, expected_tables()[0])
        for index in range(27):
            for axis, replacement in enumerate(('Other-family', 'Other-variant', 'other-direction', 'B519', 'FF', 'other-alternative')):
                with self.subTest(row=index, axis=axis):
                    mutant = copy.deepcopy(control)
                    mutant[index][axis] = replacement
                    with self.assertRaises(AssertionError):
                        self.assertEqual(mutant, rows())
                    page_mutant = copy.deepcopy(page_control)
                    page_mutant[index + 2][axis] = replacement
                    with self.assertRaises(AssertionError):
                        self.assertEqual(page_mutant, expected_tables()[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
