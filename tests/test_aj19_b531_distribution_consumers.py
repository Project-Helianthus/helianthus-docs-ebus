"""Offline artifact checks; no distribution runtime or native decoder."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('architecture/aj19_b531_distribution_consumers.md')
FIXTURE = Path('architecture/fixtures/aj19_b531_distribution_consumers.json')
FIELDS = ('cap', 'sequence', 'limited', 'changed', 'current_integral',
          'aggregate_integral', 'sequence_count', 'energy_flag', 'counter', 'gates')
BEFORE = dict(zip(FIELDS, (11, 2, True, True, 7, 19, 4, True, 3, 5)))


def reset_expectation(before, arguments):
    # Independent transition oracle: replace exactly two fields.
    return {key: arguments['new_current'] if key == 'current_integral' else
            arguments['new_energy'] if key == 'energy_flag' else before[key]
            for key in FIELDS}


def expected_fixture():
    return {
        'grade': 'Hypothesis', 'native_behavior': 'Unknown',
        'qualification': 'Unknown', 'implemented': False,
        'unknowns': dict.fromkeys(('integral_units', 'capability_formula',
            'capability_result', 'capability_units', 'eligibility_predicates',
            'cadence', 'native_identity', 'replay_a', 'replay_b'), 'Unknown'),
        'reset': {'before': BEFORE, 'arguments': {'new_current': 0, 'new_energy': False},
                  'after': reset_expectation(BEFORE, {'new_current': 0, 'new_energy': False})},
        'status': [{'raw': i, 'class': 'in_range' if i in (0, 1, 2, 3, 4)
                    else 'above_range'} for i in range(6)],
        'markers': [
            {'width': 32, 'raw': 'FFFFFFFF', 'class': 'null'},
            {'width': 32, 'raw': 0, 'class': 'value'},
            {'width': 16, 'raw': 'FFFF', 'class': 'null'},
            {'width': 16, 'raw': 0, 'class': 'value'}],
        'use_cases': ['limit-control', 'temperature-control'],
        'completion': {'variant': 'ignored_completion', 'before': 9, 'requested': 12,
                       'completion': False, 'after': 12},
        'replay': [{'variant': 'replay_a', 'behavior': 'Unknown'},
                   {'variant': 'replay_b', 'behavior': 'Unknown'}],
        'recalculation': [{'variant': 'direct', 'mode': 'direct_recalculation'},
                          {'variant': 'timer', 'mode': 'timer_driven_recalculation'}],
        'job': {'label': 'daily', 'cadence': 'Unknown'},
        'acknowledgments': [{'operation': 'set_limit', 'acknowledged': True, 'executed': False},
                            {'operation': 'set_limited', 'acknowledged': True, 'executed': False}],
        'capability': {'inputs': {'input_a': 3, 'input_b': 8},
                       'formula': 'Unknown', 'result': 'Unknown'},
        'partial': {'raw': [7, 19], 'last_known_good': 7, 'requested': 12,
                    'observed': 'Unknown', 'admitted': False},
    }


def required_rows():
    rows = [f'| {field} | ' + {'current_integral': 'new_current',
            'energy_flag': 'new_energy'}.get(field, 'retain') + ' | Hypothesis |'
            for field in FIELDS]
    rows += ['| 0..4 | in_range | Hypothesis |', '| >4 | above_range | Hypothesis |',
             '| 32 | FFFFFFFF | value | Hypothesis |', '| 16 | FFFF | value | Hypothesis |']
    for selector, behavior in (
        ('set_limit', 'ack_before_execution_possible'),
        ('set_limited', 'ack_before_execution_possible'),
        ('direct', 'direct_recalculation'), ('timer', 'timer_driven_recalculation'),
        ('ignored_completion', 'retain_requested_state'),
        ('replay_a', 'separate_unknown_replay'), ('replay_b', 'separate_unknown_replay')):
        rows.append(f'| {selector} | {behavior} | Hypothesis |')
    return rows


def check_artifacts(root):
    data = json.loads((root / FIXTURE).read_text())
    # Serialization equality also distinguishes false from numeric zero.
    assert json.dumps(data, sort_keys=True) == json.dumps(expected_fixture(), sort_keys=True)
    page = (root / PAGE).read_text()
    actual = [line for line in page.splitlines() if line.startswith('| ')
              and 'Hypothesis' in line]
    assert actual == required_rows()
    for phrase in ('**Hypothesis**', '**Unknown**', 'No distribution service or consumer',
                   'Integral units\nremain Unknown', 'actual formula, result,\nunits',
                   '`limit-control`, then `temperature-control`',
                   'without rollback', 'last-known-good', 'Admission stays\nclosed',
                   'Nothing is stable before 1.0', 'no authorization gate before 0.9',
                   '0.11', 'eBUS MCP compatibility and GraphQL\nparity'):
        assert phrase in page, phrase


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, path + (index,))
    else:
        yield path, value


class DistributionContractTests(unittest.TestCase):
    def test_page_and_scenarios(self):
        check_artifacts(ROOT)

    def test_explicit_reset_arithmetic(self):
        reset = json.loads((ROOT / FIXTURE).read_text())['reset']
        self.assertEqual(reset['after'], reset_expectation(reset['before'], reset['arguments']))
        self.assertEqual(reset['after']['current_integral'] - reset['before']['current_integral'], -7)
        for field in ('aggregate_integral', 'counter', 'gates'):
            self.assertEqual(reset['after'][field] - reset['before'][field], 0)

    def test_independent_reset_controls(self):
        for field in FIELDS:
            with self.subTest(field=field):
                before = dict(BEFORE)
                before[field] = not before[field] if isinstance(before[field], bool) else before[field] + 23
                result = reset_expectation(before, {'new_current': 6, 'new_energy': True})
                for retained in set(FIELDS) - {'current_integral', 'energy_flag'}:
                    self.assertEqual(result[retained], before[retained])
                self.assertEqual(result['current_integral'], 6)
                self.assertIs(result['energy_flag'], True)

    def test_fixture_mutations_are_rejected(self):
        original = json.loads((ROOT / FIXTURE).read_text())
        # Every scalar selector, field, variant and predicate is varied separately.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / PAGE).parent.mkdir(parents=True)
            (root / FIXTURE).parent.mkdir(parents=True)
            (root / PAGE).write_text((ROOT / PAGE).read_text())
            for path, value in leaves(original):
                with self.subTest(path=path):
                    changed = copy.deepcopy(original)
                    target = changed
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = (not value if isinstance(value, bool) else
                                       value + 1 if isinstance(value, int) else value + '_mutant')
                    (root / FIXTURE).write_text(json.dumps(changed))
                    with self.assertRaises(AssertionError):
                        check_artifacts(root)
            (root / FIXTURE).write_text(json.dumps(original))
            check_artifacts(root)
            # In particular, adding an energy input or losing a raw/partial field fails.
            for section, key in [('capability', 'inputs'), ('partial', 'raw')]:
                changed = copy.deepcopy(original)
                if section == 'capability':
                    changed[section][key]['energy_flag'] = False
                else:
                    del changed[section][key]
                (root / FIXTURE).write_text(json.dumps(changed))
                with self.assertRaises(AssertionError):
                    check_artifacts(root)

    def test_named_semantic_mutations_are_rejected(self):
        original = expected_fixture()
        mutations = []
        for field in ('aggregate_integral', 'counter', 'gates', 'sequence', 'limited', 'changed'):
            mutations.append((('reset', 'after', field), False if isinstance(BEFORE[field], bool) else 0))
        mutations += [(('status', 5, 'class'), 'in_range'),
                      (('markers', 1, 'class'), 'null'),
                      (('markers', 3, 'class'), 'null'),
                      (('use_cases',), list(reversed(original['use_cases']))),
                      (('completion', 'after'), original['completion']['before']),
                      (('grade',), 'Proven'), (('unknowns', 'capability_formula'), 'input_a + input_b')]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / FIXTURE).parent.mkdir(parents=True)
            (root / PAGE).write_text((ROOT / PAGE).read_text())
            for path, value in mutations:
                with self.subTest(path=path):
                    changed = copy.deepcopy(original)
                    target = changed
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value
                    (root / FIXTURE).write_text(json.dumps(changed))
                    with self.assertRaises(AssertionError):
                        check_artifacts(root)
            (root / FIXTURE).write_text(json.dumps(original))
            check_artifacts(root)

    def test_page_table_mutations_are_rejected(self):
        page = (ROOT / PAGE).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / FIXTURE).parent.mkdir(parents=True)
            (root / FIXTURE).write_text((ROOT / FIXTURE).read_text())
            for row in required_rows():
                for column in (1, 2, 3):
                    with self.subTest(row=row, column=column):
                        parts = row.split('|')
                        parts[column] = ' fabricated '
                        (root / PAGE).write_text(page.replace(row, '|'.join(parts)))
                        with self.assertRaises(AssertionError):
                            check_artifacts(root)
            (root / PAGE).write_text(page)
            check_artifacts(root)


if __name__ == '__main__':
    unittest.main()
