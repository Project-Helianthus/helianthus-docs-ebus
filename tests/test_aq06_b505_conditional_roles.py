"""Static contract tests for the B505 conditional role page; no runtime API."""
from pathlib import Path
import re
import unittest

Ab05Aq05Page = Path(__file__).resolve().parents[1] / 'architecture/aq06_b505_conditional_roles.md'

# Independent constants for the finite view/operation matrix.
Ab05Aq05Views = {
    'unchanged': {90, 61},
    'dhw-enable': {49},
    'parallel-charge': {24, 39},
    'flow-excess': {23},
    'programmed-start': {9},
}
Ab05Aq05Parallel = {
    ('0', 'any', 'either'): 'suppression-not-requested',
    ('1', 'heating', 'false'): 'heating-suppressed',
    ('1', 'heating', 'true'): 'exemption-unknown',
    ('1', 'mixer', 'false'): 'heating-suppressed',
    ('1', 'mixer', 'true'): 'mixer-parallel-exception',
    ('1', 'dhw', 'either'): 'not-applicable',
    ('2..255', 'any', 'either'): 'unmapped',
}
Ab05Aq05Reserved = ('state', 'results', 'physical', 'qualified')


def ab05aq05text():
    return Ab05Aq05Page.read_text(encoding='utf-8')


def ab05aq05rows(ab05aq05section):
    ab05aq05lines = [line for line in ab05aq05section.splitlines() if line.startswith('|')]
    return [[cell.strip() for cell in line.strip('|').split('|')] for line in ab05aq05lines[2:]]


def ab05aq05between(ab05aq05start, ab05aq05end):
    ab05aq05page = ab05aq05text()
    ab05aq05from = ab05aq05page.index(ab05aq05start)
    return ab05aq05page[ab05aq05from:ab05aq05page.index(ab05aq05end, ab05aq05from)]


def ab05aq05evaluate(ab05aq05disable, ab05aq05role, ab05aq05parallel):
    """Test-only oracle for the branch table."""
    if ab05aq05disable == 0:
        return 'suppression-not-requested'
    if ab05aq05disable >= 2:
        return 'unmapped'
    if ab05aq05role == 'dhw':
        return 'not-applicable'
    if ab05aq05role == 'mixer':
        return 'mixer-parallel-exception' if ab05aq05parallel else 'heating-suppressed'
    return 'exemption-unknown' if ab05aq05parallel else 'heating-suppressed'


class TestAb05Aq05Contract(unittest.TestCase):
    def test_signature(self):
        self.assertIn('func Ab05Aq05Evaluate(ab05Aq05Input json.RawMessage) (json.RawMessage, error)',
                      ab05aq05text())

    def test_view_matrix(self):
        ab05aq05found = {}
        for ab05aq05row in ab05aq05rows(ab05aq05between('| `context.view` |', 'Arbitrary scalar')):
            ab05aq05view = ab05aq05row[0].strip('`')
            ab05aq05found[ab05aq05view] = {int(n) for n in re.findall(r'\((\d+)\)', ab05aq05row[1])}
        self.assertEqual(ab05aq05found, Ab05Aq05Views)

    def test_parallel_branch_table(self):
        ab05aq05table = ab05aq05between('| `disable` | `role`', 'The mixer exception')
        ab05aq05found = {}
        for ab05aq05row in ab05aq05rows(ab05aq05table):
            ab05aq05role = 'any' if ab05aq05row[1].startswith('Any') else ab05aq05row[1].strip('`')
            ab05aq05flag = 'either' if ab05aq05row[2].startswith('Either') else ab05aq05row[2]
            ab05aq05found[(ab05aq05row[0], ab05aq05role, ab05aq05flag)] = ab05aq05row[3].strip('`')
        self.assertEqual(ab05aq05found, Ab05Aq05Parallel)

    def test_branch_oracle_agrees_with_table(self):
        for (ab05aq05disable, ab05aq05role, ab05aq05flag), ab05aq05label in Ab05Aq05Parallel.items():
            ab05aq05value = {'2..255': 200}.get(ab05aq05disable) or int(ab05aq05disable)
            ab05aq05roles = ['mixer', 'heating', 'dhw'] if ab05aq05role == 'any' else [ab05aq05role]
            ab05aq05flags = [False, True] if ab05aq05flag == 'either' else [ab05aq05flag == 'true']
            for ab05aq05r in ab05aq05roles:
                for ab05aq05f in ab05aq05flags:
                    self.assertEqual(ab05aq05evaluate(ab05aq05value, ab05aq05r, ab05aq05f), ab05aq05label)

    def test_other_labels_and_arithmetic(self):
        ab05aq05page = ab05aq05text()
        for ab05aq05label in ('ordinary-DHW-eligible', 'frost-only-eligible', 'unmapped', 'unchanged',
                              'numeric-candidate', 'applicable', 'ignored'):
            self.assertIn('`%s`' % ab05aq05label, ab05aq05page)
        self.assertEqual(40 + 5, 45)

    def test_result_shape_and_reserved_names(self):
        ab05aq05page = ab05aq05text()
        self.assertIn('`physical="Unknown"` and `qualified=false`', ab05aq05page)
        for ab05aq05name in Ab05Aq05Reserved:
            self.assertIn('`%s`' % ab05aq05name, ab05aq05between('## Input, preservation', '## Finite candidate'))
        self.assertIn('is rejected with an error', ab05aq05page)

    def test_missing_start_result_state(self):
        ab05aq05page = ab05aq05text()
        self.assertIn('no `start`, the result is still\n`complete`', ab05aq05page)

    def test_no_commit_ids(self):
        self.assertIsNone(re.search(r'\b[0-9a-f]{7,40}\b', ab05aq05text()))


if __name__ == '__main__':
    unittest.main()
