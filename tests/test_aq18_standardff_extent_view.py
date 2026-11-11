"""Offline checks of the AQ18 FF extent arithmetic contract; no runtime implementation."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture' / 'aq18-standardff-extent-view.md'
RESERVED = ('state', 'results', 'physical', 'qualified')


def ff04(declared, available):
    declared_min = declared >= 2
    init_min = None if available is None else available >= 2
    bounded = bool(declared_min and init_min and declared <= 10 and available >= declared)
    return declared_min, init_min, bounded


def ff06(declared, available):
    dpairs = (declared - 1) // 2 if declared >= 1 else None
    tail = declared >= 1 and (declared - 1) % 2 == 1
    apairs = None
    if available is not None and min(available, declared) >= 1:
        apairs = (min(available, declared) - 1) // 2
    whole = bool(declared >= 1 and available is not None and available >= declared and not tail)
    return dpairs, apairs, tail, whole


def tables(text):
    result, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([c.strip() for c in line.strip('|').split('|')])
        elif current:
            result.append(current[2:])
            current = []
    return result


def section(text, title):
    start = text.index('## ' + title)
    nxt = text.find('\n## ', start + 1)
    return text[start:nxt if nxt != -1 else len(text)]


def flag(cell):
    return {'true': True, 'false': False}[cell]


def count(cell):
    return None if cell == 'absent' else int(cell)


class Aq18StandardFfExtentView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PAGE.read_text()

    def test_ff04_table_matches_formulas(self):
        rows = tables(section(self.text, 'FF04 minimum arithmetic'))[-1]
        self.assertEqual(len(rows), 4)
        for row in rows:
            declared, available = int(row[0]), int(row[1])
            self.assertEqual(
                ff04(declared, available),
                (flag(row[2]), flag(row[3]), flag(row[4])), row)

    def test_ff06_table_matches_formulas(self):
        rows = tables(section(self.text, 'FF06 pair arithmetic'))[-1]
        self.assertEqual(len(rows), 8)
        for row in rows:
            declared, available = int(row[0]), int(row[1])
            self.assertEqual(
                ff06(declared, available),
                (count(row[2]), count(row[3]), flag(row[4]), flag(row[5])), row)

    def test_missing_and_empty_body(self):
        self.assertEqual(ff06(3, None), (1, None, False, False))
        self.assertEqual(ff06(3, 0), (1, None, False, False))
        self.assertEqual(ff04(10, None), (True, None, False))

    def test_formula_rules_stated(self):
        for rule in (
            '`declared >= 2`',
            '`available >= 2`',
            '`floor((declared - 1) / 2)`',
            '`(declared - 1) % 2 == 1`',
            '`floor((min(available, declared) - 1) / 2)`',
            '`declared >= 1`, `available >= declared`',
        ):
            self.assertIn(rule, self.text)

    def test_json_examples(self):
        blocks = re.findall(r'```json\n(.*?)\n```', self.text, re.S)
        self.assertEqual(len(blocks), 2)
        inp, out = (json.loads(b) for b in blocks)
        for key in RESERVED:
            self.assertNotIn(key, inp)
        for key in inp:
            self.assertEqual(out[key], inp[key])
        body = inp['fields']['body']
        declared = inp['arguments']['declared_length']
        dp, ap, tail, whole = ff06(declared, len(body))
        result = out['results']['body']
        self.assertEqual(result['raw'], body)
        self.assertEqual(result['declared_length'], declared)
        self.assertEqual(result['available_length'], len(body))
        self.assertEqual(result['declared_pair_count'], dp)
        self.assertEqual(result['available_pair_count'], ap)
        self.assertEqual(result['declared_incomplete_tail'], tail)
        self.assertEqual(result['whole_declared_span'], whole)
        self.assertEqual(result['unmodeled'], body[declared:])
        self.assertEqual(out['physical'], 'Unknown')
        self.assertIs(out['qualified'], False)

    def test_reserved_names_documented(self):
        for key in RESERVED:
            self.assertIn('`%s`' % key, self.text)
        self.assertIn('reserved', self.text)
        self.assertIn('Input carrying any of them', self.text)


if __name__ == '__main__':
    unittest.main()
