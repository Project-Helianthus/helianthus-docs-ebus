"""Pins the structure and critical invariants of the local-worker qualification record."""
import re
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'development' / 'local-worker-qualification-decisions.md'
GRADES = ('**Hypothesis**', '**Proven**', '**Unknown**')


def section(text, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', text, re.S | re.M)
    assert match, heading
    return match.group(1)


def table_rows(body):
    rows = [line for line in body.splitlines() if line.startswith('|')]
    return [[c.strip() for c in r.strip('|').split('|')] for r in rows[2:]]


class LocalWorkerQualificationDecisions(unittest.TestCase):
    def setUp(self):
        self.text = PAGE.read_text(encoding='utf-8')

    def test_fifteen_requirements_in_sequence_with_grades(self):
        rows = table_rows(section(self.text, 'Decided acceptance requirements (2026-11-03)'))
        self.assertEqual([r[0] for r in rows], [str(i) for i in range(1, 16)])
        for row in rows:
            self.assertEqual(len(row), 3)
            self.assertTrue(row[1])
            self.assertEqual(row[2], '**Hypothesis**')

    def test_engine_and_profile_mappings(self):
        rows = {r[0]: r[1] for r in table_rows(
            section(self.text, 'Decided acceptance requirements (2026-11-03)'))}
        self.assertIn('10x GPIO bit-level userland engine', rows['2'])
        self.assertIn('PL011 kernel-driver path', rows['2'])
        self.assertIn('41.7 µs', rows['2'])
        self.assertIn('Exactly one profile', rows['8'])
        self.assertIn('Every other combination is Unknown and off', rows['8'])
        self.assertIn('no user-space MMIO', rows['10'])
        self.assertIn('Unknown', rows['12'])
        self.assertIn('Independent hardware containment', rows['15'])

    def test_evidence_table_placeholder_and_columns(self):
        rows = table_rows(section(self.text, 'Qualification evidence'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 14)
        self.assertEqual(rows[0][0], '—')
        self.assertIn('No run recorded', rows[0][-1])
        self.assertIn('AA22QualifiedTiming', rows[0][-1])
        self.assertIn('Unknown', rows[0][-1])

    def test_nothing_is_qualified_or_authorized(self):
        head = self.text[:self.text.index('## Evidence and software boundary')]
        self.assertIn('unqualified and off', head)
        self.assertIn('does not authorize', head)
        self.assertNotIn('qualified**', head.replace('unqualified', ''))
        self.assertIn('authorizes no device access, bench run or live write', self.text)

    def test_evidence_vocabulary_and_no_commit_ids(self):
        for grade in GRADES:
            self.assertIn(grade, self.text)
        self.assertIsNone(re.search(r'(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])\b[0-9a-f]{7,40}\b', self.text))


if __name__ == '__main__':
    unittest.main()
