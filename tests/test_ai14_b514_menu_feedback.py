"""Finite synthetic contract checks; no installed-device qualification."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b514-menu-feedback.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai14_b514_menu_feedback.json'
HEADERS = 'operation variant direction field primary secondary position width extent encoding scale unit default constant conflict labels ranges grade'.split()


def expected_rows():
    """Constants from the supplied finite contract, independent of both files."""
    result = []

    def row(op, variant, direction, field, *, extent='Unknown', labels='-',
            ranges='-', default='Unknown', position='Unknown', width='Unknown',
            encoding='Unknown', scale='Unknown', unit='Unknown',
            constant='Unknown', conflict='-'):
        result.append(dict(zip(HEADERS, [op, variant, direction, field,
            'B5' if direction == 'request' else 'F5',
            '-' if op == '-' else '14', position, width, extent, encoding,
            scale, unit, default, constant, conflict, labels, ranges, 'Hypothesis'])))

    row('01', 'menu', 'request', 'mode', extent='4', labels='0=off;1=on', ranges='2..255=off')
    row('01', 'menu', 'positive', 'answer', extent='5', labels='0=normal;1=actors-deactivated')
    row('01', 'menu', 'positive', 'feedback', extent='5', labels='1=accepted')
    for variant in ('generic', 'specific-a', 'specific-b'):
        row('06', variant, 'request', 'command', labels='0=query;1=start')
        row('06', variant, 'positive', 'feedback',
            labels='1=in-progress;255=unsupported' if variant == 'generic' else '1=not-successful',
            ranges='-' if variant == 'generic' else '3..255=invalid')
    row('07', 'menu', 'request', 'command', default='0',
        labels='0=query;1=start-liquefied-gas;2=start-natural-gas;3=abort')
    row('07', 'menu', 'positive', 'feedback', default='0',
        labels='0=idle;1=progress;2=passed;3=warning;4=combustion-error;5=gas-type-error;6=aborted;255=unsupported')
    for direction, field, position, width, extent in (
            ('request', 'command', 3, 1, 6), ('request', 'pressure', 4, 2, 6),
            ('positive', 'feedback', 3, 1, 13), ('positive', 'pressure', 4, 2, 13),
            ('positive', 'minimum', 6, 2, 13), ('positive', 'maximum', 8, 2, 13),
            ('positive', 'step', 10, 1, 13), ('positive', 'flow', 11, 2, 13)):
        row('08', 'menu', direction, field, position=str(position), width=str(width),
            extent=str(extent), encoding='u16 LE' if width == 2 else 'u8',
            scale='/100' if field == 'flow' else 'Unknown',
            unit='l/min' if field == 'flow' else 'mbar' if field == 'step' else 'Unknown',
            default='0' if field == 'step' else 'Unknown',
            constant='1' if field == 'step' else 'Unknown',
            conflict='constant 1 mbar versus default zero; unresolved' if field == 'step' else '-')
    for direction, prefix in (('request', '181'), ('positive', '245')):
        row('-', 'named-09', direction, 'prefix', position='0', width='1',
            encoding='u8', constant=prefix)
    return result


def page_rows(text):
    lines = [line for line in text.splitlines() if line.startswith('|')]
    cells = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
    if len(cells) != 23 or cells[0] != HEADERS or cells[1] != ['---'] * len(HEADERS):
        raise ValueError('declaration table shape changed')
    if any(len(row) != len(HEADERS) for row in cells[2:]):
        raise ValueError('declaration row shape changed')
    return [dict(zip(HEADERS, row)) for row in cells[2:]]


def label(row, value):
    if not 0 <= value <= 255:
        raise ValueError('outside byte domain')
    pairs = {} if row['labels'] == '-' else dict(item.split('=') for item in row['labels'].split(';'))
    if str(value) in pairs:
        return pairs[str(value)]
    if row['ranges'] != '-':
        bounds, meaning = row['ranges'].split('=')
        low, high = map(int, bounds.split('..'))
        if low <= value <= high:
            return meaning
    return 'unmapped'


def decode(row, data):
    """Local abstract-object predicate; deliberately no transport or executor."""
    if row['extent'] == 'Unknown' or len(data) != int(row['extent']):
        raise ValueError('incomplete or unexpected abstract extent')
    if any(type(value) is not int or not 0 <= value <= 255 for value in data):
        raise ValueError('outside byte domain')
    if data[:3] != [int(row['primary'], 16), int(row['secondary'], 16), int(row['operation'], 16)]:
        raise ValueError('prefix mismatch')
    position, width = int(row['position']), int(row['width'])
    raw = int.from_bytes(bytes(data[position:position + width]), 'little')
    return raw / 100 if row['scale'] == '/100' else raw


class MenuFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text()
        self.fixture = json.loads(FIXTURE.read_text())
        self.sources = [page_rows(self.page), self.fixture['declarations']]

    def test_independent_ordered_declarations_and_grades(self):
        for rows in self.sources:
            self.assertEqual(rows, expected_rows())
        self.assertEqual(set(self.fixture), {'family', 'provenance', 'native_grade',
            'physical_qualification', 'declarations', 'label_cases', 'op08_request',
            'op08_positive', 'op08_incomplete', 'named_09'})
        self.assertEqual(self.fixture['family'], 'B514')
        self.assertEqual(self.fixture['provenance'], 'synthetic; issue #840 supplied finite declarations')
        self.assertEqual(self.fixture['native_grade'], 'Hypothesis')
        self.assertEqual(self.fixture['physical_qualification'], 'Unknown')
        for phrase in (
                'Every native declaration\nbelow is **Hypothesis**.',
                '**Proven** applies\nonly to the local synthetic representation and arithmetic, never native behavior.',
                'Candidate cessation after fifteen minutes\nor mode zero is not established enforcement (**Unknown**).',
                'No pressure factor is a qualified unit conversion;',
                'constant 1 mbar versus default zero is an unresolved conflict;',
                'No encoded 09 or executable form follows from the label.'):
            self.assertIn(phrase, self.page)
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertFalse('://' in target or target.startswith('/'))
            self.assertTrue((ROOT / 'protocols/vaillant' / target.split('#')[0]).is_file())

    def test_complete_byte_domains_and_separate_feedback(self):
        expected_cases = [
            ['01', 'menu', 'request', 'mode', 2, 'off'],
            ['01', 'menu', 'positive', 'answer', 1, 'actors-deactivated'],
            ['01', 'menu', 'positive', 'feedback', 1, 'accepted'],
            ['01', 'menu', 'positive', 'feedback', 0, 'unmapped']]
        for variant in ('generic', 'specific-a', 'specific-b'):
            expected_cases += [
                ['06', variant, 'positive', 'feedback', 1, 'in-progress' if variant == 'generic' else 'not-successful'],
                ['06', variant, 'positive', 'feedback', 255, 'unsupported' if variant == 'generic' else 'invalid']]
        expected_cases += [['07', 'menu', 'positive', 'feedback', 6, 'aborted'],
                           ['07', 'menu', 'positive', 'feedback', 7, 'unmapped']]
        self.assertEqual(self.fixture['label_cases'], expected_cases)
        for rows in self.sources:
            for row in rows[:11]:
                for value in range(256):
                    op, direction, field = row['operation'], row['direction'], row['field']
                    expected = 'unmapped'
                    if op == '01':
                        expected = ('on' if value == 1 else 'off') if direction == 'request' else (
                            {0: 'normal', 1: 'actors-deactivated'}.get(value, 'unmapped') if field == 'answer' else
                            {1: 'accepted'}.get(value, 'unmapped'))
                    elif op == '06':
                        expected = {0: 'query', 1: 'start'}.get(value, 'unmapped') if direction == 'request' else (
                            {1: 'in-progress', 255: 'unsupported'}.get(value, 'unmapped') if row['variant'] == 'generic' else
                            'invalid' if value >= 3 else {1: 'not-successful'}.get(value, 'unmapped'))
                    elif op == '07':
                        expected = ({0: 'query', 1: 'start-liquefied-gas', 2: 'start-natural-gas', 3: 'abort'} if direction == 'request' else
                            {0: 'idle', 1: 'progress', 2: 'passed', 3: 'warning', 4: 'combustion-error', 5: 'gas-type-error', 6: 'aborted', 255: 'unsupported'}).get(value, 'unmapped')
                    self.assertEqual(label(row, value), expected, (row, value))
                for invalid in (-1, 256):
                    with self.assertRaises(ValueError):
                        label(row, invalid)

    def test_raw_words_flow_conflict_and_extents(self):
        request = [181, 20, 8, 0, 52, 18]
        positive = [245, 20, 8, 0, 1, 0, 0, 1, 52, 18, 0, 100, 0]
        self.assertEqual(self.fixture['op08_request'], request)
        self.assertEqual(self.fixture['op08_positive'], positive)
        self.assertEqual(self.fixture['op08_incomplete'], positive[:12])
        self.assertIn('`B5 14 08 00 34 12` has extent 6 and raw pressure 4660.', self.page)
        self.assertIn('`F5 14 08 00 01 00 00 01 34 12 00 64 00` has extent 13: raw pressure 1,\nminimum 256, maximum 4660, step zero and flow 1.0 l/min (`64 00` / 100).', self.page)
        for rows in self.sources:
            op08 = [row for row in rows if row['operation'] == '08']
            for row in op08:
                data = request if row['direction'] == 'request' else positive
                expected = 4660 if row['direction'] == 'request' and row['field'] == 'pressure' else {
                    'command': 0, 'feedback': 0, 'pressure': 1, 'minimum': 256,
                    'maximum': 4660, 'step': 0, 'flow': 1.0}[row['field']]
                self.assertEqual(decode(row, data), expected)
                for partial in (data[:-1], data + [0]):
                    with self.assertRaises(ValueError):
                        decode(row, partial)
                for pos in range(3):
                    changed = data.copy()
                    changed[pos] ^= 1
                    with self.assertRaises(ValueError):
                        decode(row, changed)
                for invalid in (-1, 256):
                    changed = data.copy()
                    changed[3] = invalid
                    with self.assertRaises(ValueError):
                        decode(row, changed)
            step = next(row for row in op08 if row['field'] == 'step')
            self.assertEqual((step['constant'], step['default'], step['unit'], step['conflict']),
                ('1', '0', 'mbar', 'constant 1 mbar versus default zero; unresolved'))

    def test_named_09_supplies_prefix_only(self):
        self.assertEqual(self.fixture['named_09'], {'request': [181], 'positive': [245],
                         'secondary': None, 'operation': None, 'body': None})
        for rows in self.sources:
            named = [row for row in rows if row['variant'] == 'named-09']
            self.assertEqual(len(named), 2)
            for row in named:
                self.assertEqual((row['operation'], row['secondary'], row['position'], row['extent']),
                                 ('-', '-', '0', 'Unknown'))
                with self.assertRaises(ValueError):
                    decode(row, [int(row['primary'], 16)])

    def test_each_declared_identity_axis_has_independent_control(self):
        # Reject each changed axis against independent constants; no lookup API is claimed.
        axes = ('operation', 'variant', 'direction', 'field', 'primary', 'secondary')
        expected = expected_rows()
        for rows in self.sources:
            self.assertEqual(rows, expected)
            for index in range(len(rows)):
                for axis in axes:
                    with self.subTest(row=index, axis=axis):
                        changed = copy.deepcopy(rows)
                        changed[index][axis] = 'different'
                        self.assertNotEqual(changed, expected)


if __name__ == '__main__':
    unittest.main()
