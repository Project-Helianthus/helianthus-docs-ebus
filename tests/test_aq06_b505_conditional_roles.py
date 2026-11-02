"""Static contract tests for the B505 conditional role page; no runtime API."""
from pathlib import Path
import json
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


def ab05aq05dhw(ab05aq05byte):
    return {0: 'frost-only-eligible', 1: 'ordinary-DHW-eligible'}.get(ab05aq05byte, 'unmapped')


def ab05aq05prog(ab05aq05mode):
    return 'applicable' if ab05aq05mode == 0 else 'ignored'


def ab05aq05unchanged(ab05aq05replacement, ab05aq05previous, ab05aq05requested):
    if ab05aq05replacement:
        return ab05aq05previous, 'unchanged'
    return ab05aq05requested, 'numeric-candidate'


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

    def test_view_row_branches(self):
        ab05aq05rows_by_view = {r[0].strip('`'): r[3] for r in ab05aq05rows(
            ab05aq05between('| `context.view` |', 'Arbitrary scalar'))}
        ab05aq05dhw = ab05aq05rows_by_view['dhw-enable']
        self.assertEqual(re.findall(r'(\d)\s+labels\s+`([^`]+)`', ab05aq05dhw),
                         [('1', 'ordinary-DHW-eligible'), ('0', 'frost-only-eligible')])
        self.assertIn('2..255 remain `unmapped`', ab05aq05dhw)
        ab05aq05prog = ab05aq05rows_by_view['programmed-start']
        self.assertIn('Mode 0 labels `applicable`; other modes label `ignored`', ab05aq05prog)
        ab05aq05unch = ab05aq05rows_by_view['unchanged']
        self.assertIn('True retains previous and labels `unchanged`', ab05aq05unch)
        self.assertIn('false returns requested as `numeric-candidate`', ab05aq05unch)

    def test_synthetic_case_table(self):
        ab05aq05table = ab05aq05between('| View and explicit inputs |', 'Always overwriting')
        ab05aq05cases = [(r[0], r[1]) for r in ab05aq05rows(ab05aq05table)]
        # DHW: byte order maps to label order.
        ab05aq05in, ab05aq05out = next(c for c in ab05aq05cases if c[0].startswith('`dhw-enable`'))
        ab05aq05bytes = [int(n) for n in re.findall(r'`\[(\d+)\]`', ab05aq05in)]
        ab05aq05labels = re.findall(r'`([^`]+)`', ab05aq05out)
        self.assertEqual(ab05aq05bytes, [0, 1, 2])
        self.assertEqual(ab05aq05labels, [ab05aq05dhw(n) for n in ab05aq05bytes])
        # Programmed start: modes map to labels in order.
        ab05aq05in, ab05aq05out = next(c for c in ab05aq05cases if c[0].startswith('`programmed-start`'))
        ab05aq05modes = [int(n) for n in re.search(r'program_mode (\d) / (\d)', ab05aq05in).groups()]
        self.assertEqual(re.findall(r'`([^`]+)`', ab05aq05out), [ab05aq05prog(n) for n in ab05aq05modes])
        # Unchanged branches.
        ab05aq05in, ab05aq05out = next(c for c in ab05aq05cases if c[0].startswith('`unchanged`, previous 17'))
        self.assertEqual(ab05aq05unchanged(True, 17, 23), (17, 'unchanged'))
        self.assertIn('Retain 17, label `unchanged`', ab05aq05out)
        ab05aq05in, ab05aq05out = next(c for c in ab05aq05cases if c[0].startswith('Same tokens'))
        self.assertEqual(ab05aq05unchanged(False, 17, 23), (23, 'numeric-candidate'))
        self.assertIn('Return 23, label `numeric-candidate`', ab05aq05out)
        # Parallel-charge rows agree with the oracle.
        for ab05aq05in, ab05aq05out in ab05aq05cases:
            if ab05aq05in.startswith('`parallel-charge`'):
                ab05aq05role = re.search(r', (mixer|heating|dhw), parallel (true|false)', ab05aq05in)
                ab05aq05args = (ab05aq05role.group(1), ab05aq05role.group(2) == 'true')
            elif ab05aq05in.startswith('Same byte'):
                ab05aq05role = re.match(r'Same byte, (mixer|heating|dhw), parallel (true|false)', ab05aq05in)
                ab05aq05args = (ab05aq05role.group(1), ab05aq05role.group(2) == 'true')
            else:
                continue
            self.assertEqual(re.findall(r'`([^`]+)`', ab05aq05out),
                             [ab05aq05evaluate(1, *ab05aq05args)])

    def test_flow_excess_examples(self):
        ab05aq05page = ab05aq05text()
        ab05aq05blocks = [json.loads(b) for b in re.findall(r'```json\n(.*?)```', ab05aq05page, re.S)]
        ab05aq05request, ab05aq05result = ab05aq05blocks
        self.assertEqual({k: v for k, v in ab05aq05result.items()
                          if k not in Ab05Aq05Reserved}, ab05aq05request)
        ab05aq05args = ab05aq05request['arguments']
        self.assertEqual(set(ab05aq05result['results']),
                         {'flow-excess'} | set(ab05aq05request['fields']))
        self.assertEqual(ab05aq05result['results']['opaque'],
                         {'raw': ab05aq05request['fields']['opaque'], 'state': 'complete'})
        ab05aq05entry = ab05aq05result['results']['flow-excess']
        self.assertEqual(ab05aq05entry['raw'], ab05aq05args)
        self.assertEqual(ab05aq05entry['number'], ab05aq05args['demand'] + ab05aq05args['excess'])
        self.assertEqual(ab05aq05entry['number'], 45)
        self.assertEqual(ab05aq05entry['candidate_domain'], 'Hypothesis')
        self.assertEqual(ab05aq05entry['calculation'], 'Proven')
        self.assertEqual((ab05aq05result['physical'], ab05aq05result['qualified'], ab05aq05result['state']),
                         ('Unknown', False, 'complete'))
        self.assertIn('| `flow-excess`, demand 40, excess 5 | 45;', ab05aq05page)

    def test_results_key_table(self):
        ab05aq05table = ab05aq05between('| Context | Result key |', 'Return one JSON object')
        ab05aq05keys = {r[0].strip('`'): r[1] for r in ab05aq05rows(ab05aq05table)}
        self.assertEqual({k: v.strip('`') for k, v in ab05aq05keys.items() if k in Ab05Aq05Views},
                         {'unchanged': 'unchanged', 'dhw-enable': 'enabled', 'parallel-charge': 'disable',
                          'flow-excess': 'flow-excess', 'programmed-start': 'programmed-start'})
        self.assertIn('Unsupported context', ab05aq05keys)

    def test_result_shape_and_reserved_names(self):
        ab05aq05page = ab05aq05text()
        self.assertIn('`physical="Unknown"` and `qualified=false`', ab05aq05page)
        for ab05aq05name in Ab05Aq05Reserved:
            self.assertIn('`%s`' % ab05aq05name, ab05aq05between('## Input, preservation', '## Finite candidate'))
        self.assertIn('is rejected with an error, except\nthat `enabled` under `dhw-enable` and `disable` under '
                      '`parallel-charge` are the\ninterpreted inputs', ab05aq05page)

    def test_missing_start_result_state(self):
        ab05aq05page = ab05aq05text()
        self.assertIn('no `start`, the result is still\n`complete`', ab05aq05page)

    def test_no_commit_ids(self):
        self.assertIsNone(re.search(r'\b[0-9a-f]{7,40}\b', ab05aq05text()))


if __name__ == '__main__':
    unittest.main()
