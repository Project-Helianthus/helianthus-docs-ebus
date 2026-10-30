"""Offline artifact checks only; no runtime implementation or wire qualification."""

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('architecture/aj28_ff_local_liveness.md')
FIXTURE = Path('architecture/fixtures/aj28_ff_local_liveness.json')

# Independent issue-derived expectations, not loaded from fixture outputs.
LIVENESS_ROWS = [
    ['transaction', 'crc_valid=true', 'sender', 'refresh associated only', 'Hypothesis'],
    ['transaction', 'crc_valid=false', 'sender', 'retain all', 'Hypothesis'],
    ['transaction', 'crc_valid=unknown', 'sender', 'retain all', 'Hypothesis'],
    ['response', 'success=true', 'participant', 'refresh associated only', 'Hypothesis'],
    ['response', 'success=false', 'participant', 'retain all', 'Hypothesis'],
    ['response', 'success=unknown', 'participant', 'retain all', 'Hypothesis'],
    ['destination_only', 'any', 'destination', 'retain all', 'Hypothesis'],
    ['eligible observation', 'association absent', 'none', 'retain all', 'Hypothesis'],
]
STATE_ROWS = [
    ['reset', 'any', 'true', 'retain', 'reset-state', 'retain', '0', 'Hypothesis'],
    ['longest_cycle', 'startup=true', 'false', 'retain', 'retain', 'retain', '1', 'Hypothesis'],
    ['longest_cycle', 'startup=false', 'false', 'retain', 'retain', 'retain', '0', 'Hypothesis'],
    ['initialize', 'any', 'retain', 'retain', 'normal', 'retain', '0', 'Hypothesis'],
    ['ff01', 'any', 'retain', 'retain', 'retain', 'empty', '0', 'Hypothesis'],
    ['ff02', 'responder=true', 'retain', 'retain', 'retain', 'retain', '0', 'Hypothesis'],
    ['ff02', 'responder=false', 'retain', 'retain', 'retain', 'retain', '0', 'Hypothesis'],
]
FF02_ROWS = [
    ['FF02', 'true', '0', 'empty', 'Hypothesis'],
    ['FF02', 'false', '0', 'empty', 'Hypothesis'],
]
UNKNOWN = {
    'native_behavior', 'physical_delivery', 'qualified_peer_behavior',
    'longest_cycle_duration', 'ff_query_bodies', 'physical_emission_policy',
    'unprovided_properties',
}
STATE_FIELDS = {
    'ages', 'startup', 'active', 'reset_state', 'dynamic_config',
    'clear_count', 'raw', 'admission',
}
EVENT_FIELDS = {
    'kind', 'sender', 'participant', 'destination', 'direction', 'crc_valid', 'success',
}


def tables(text):
    result = []
    current = []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            result.append(current[2:])
            current = []
    return result


class LocalLivenessContract(unittest.TestCase):
    def validate(self, root):
        page = (root / PAGE).read_text()
        data = json.loads((root / FIXTURE).read_text())
        self.assertEqual(tables(page), [LIVENESS_ROWS, STATE_ROWS, FF02_ROWS])
        self.assertIn('**Hypothesis:**', page)
        self.assertIn('**Unknown:** native', page)
        self.assertIn('../protocols/ebus-services/ebus-service-FFh.md', page)
        for statement in (
            'longest-cycle duration,', 'FF query bodies, physical emission policy,',
            'No scenario grants execution\nadmission.', 'Admission remains fail-closed.',
            'not an implemented\nruntime feature', 'no stability promise',
        ):
            self.assertIn(statement, page)
        self.assertEqual(set(data), {'grade', 'qualification', 'unknown', 'liveness', 'transitions', 'ff02'})
        self.assertEqual(data['grade'], 'Hypothesis')
        self.assertEqual(data['qualification'], 'Unknown')
        self.assertEqual(data['unknown'], dict.fromkeys(UNKNOWN))
        for case in data['liveness']:
            self.assertEqual(set(case), {'before', 'event', 'after'})
            before, event, after = (case[key] for key in ('before', 'event', 'after'))
            self.assertEqual(set(before), STATE_FIELDS)
            self.assertEqual(set(event), EVENT_FIELDS)
            self.assertEqual(set(before['ages']), {'A', 'B', 'C'})
            self.assertIn(event['kind'], {'transaction', 'response', 'destination_only'})
            self.assertIn(event['direction'], {'inbound', 'outbound'})
            for field in ('sender', 'participant', 'destination'):
                self.assertIn(event[field], {None, 'A', 'B', 'C'})
            for field in ('crc_valid', 'success'):
                self.assertTrue(event[field] is None or type(event[field]) is bool)
            expected = deepcopy(before)
            # Independent arithmetic: subtract the eligible age from itself;
            # destination never participates. Unknown becomes zero only on refresh.
            associated = None
            if event['kind'] == 'transaction' and event['crc_valid'] is True:
                associated = event['sender']
            if event['kind'] == 'response' and event['success'] is True:
                associated = event['participant']
            if associated is not None:
                age = before['ages'][associated]
                expected['ages'][associated] = age - age if age is not None else 0
            self.assertEqual(after, expected)
            self.assertIs(before['admission'], False)
        for case in data['transitions']:
            self.assertEqual(set(case), {'before', 'events', 'after_each'})
            before = case['before']
            self.assertEqual(set(before), STATE_FIELDS)
            self.assertIs(before['admission'], False)
            self.assertEqual(len(case['events']), len(case['after_each']))
            for event, actual in zip(case['events'], case['after_each']):
                expected = deepcopy(before)
                self.assertIn(event, {'initialize', 'reset', 'longest_cycle', 'ff01'})
                if event == 'initialize':
                    expected['reset_state'] = 'normal'
                elif event == 'reset':
                    expected['startup'] = True
                    expected['reset_state'] = 'reset-state'
                elif event == 'longest_cycle':
                    expected['startup'] = False
                    expected['clear_count'] += int(before['startup'])
                else:
                    expected['dynamic_config'] = []
                self.assertEqual(actual, expected)
                before = actual
        self.assertEqual(data['ff02'], [
            {'responder': False, 'nn': 0, 'data': []},
            {'responder': True, 'nn': 0, 'data': []},
        ])
        return data

    def test_page_and_scenarios(self):
        self.validate(ROOT)

    def test_independent_axis_coverage(self):
        data = self.validate(ROOT)
        cases = data['liveness']
        for kind, predicate in [('transaction', 'crc_valid'), ('response', 'success')]:
            baseline = next(c for c in cases if c['event']['kind'] == kind)
            for field, alternatives in (
                ('sender', ['B', None]), ('participant', ['B', None]),
                ('destination', ['B', None]), ('direction', ['outbound']),
                ('crc_valid', [False, None]), ('success', [False, None]),
            ):
                for value in alternatives:
                    expected_event = dict(baseline['event'], **{field: value})
                    with self.subTest(kind=kind, field=field, value=value):
                        self.assertTrue(any(c['before'] == baseline['before'] and
                                            c['event'] == expected_event for c in cases))
        self.assertEqual({c['before']['ages']['A'] for c in cases}, {0, 5, 17, None})
        for kind in ('transaction', 'response'):
            field = 'sender' if kind == 'transaction' else 'participant'
            self.assertTrue(any(c['event']['kind'] == kind and c['event'][field] == 'C'
                                and c['after']['ages']['C'] == 0 for c in cases))
        sequences = [c for c in data['transitions'] if len(c['events']) > 1]
        self.assertEqual({(c['before']['startup'], c['before']['active']) for c in sequences},
                         {(False, False), (False, True), (True, False), (True, True)})
        for c in sequences:
            self.assertEqual(c['events'], ['initialize', 'reset', 'initialize',
                                          'longest_cycle', 'longest_cycle', 'reset', 'longest_cycle'])
            self.assertEqual([s['reset_state'] for s in c['after_each'][:3]],
                             ['normal', 'reset-state', 'normal'])
            self.assertEqual([s['clear_count'] for s in c['after_each']], [0, 0, 0, 1, 1, 1, 2])
        self.assertEqual([c['before']['dynamic_config'] for c in data['transitions']
                          if c['events'] == ['ff01']],
                         [[], ['synthetic-target'], ['synthetic-other', 'synthetic-target']])

    def reject(self, change, target='fixture'):
        # Every executed altered artifact lives in a disposable worktree-local copy.
        (ROOT / '.tmp').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            root = Path(directory)
            for relative in (PAGE, FIXTURE):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text((ROOT / relative).read_text())
            if target == 'fixture':
                data = json.loads((root / FIXTURE).read_text())
                change(data)
                (root / FIXTURE).write_text(json.dumps(data))
            else:
                (root / PAGE).write_text(change((root / PAGE).read_text()))
            with self.assertRaises(AssertionError):
                self.validate(root)

    def test_reject_changed_liveness_outcomes(self):
        # Each outcome field independently catches overwriting a distinct axis.
        changes = {
            'ages': {'A': 0, 'B': 0, 'C': 0}, 'startup': True, 'active': False,
            'reset_state': 'normal', 'dynamic_config': [], 'clear_count': 1,
            'raw': [], 'admission': True,
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                self.reject(lambda d: d['liveness'][0]['after'].__setitem__(field, value))
        cases = json.loads((ROOT / FIXTURE).read_text())['liveness']
        for index, case in enumerate(cases):
            for participant in ('A', 'B', 'C'):
                with self.subTest(observation=index, participant=participant):
                    # Includes destination refresh, invalid/unknown CRC acceptance,
                    # unsuccessful response acceptance and wrong-participant refresh.
                    def alter(d):
                        ages = d['liveness'][index]['after']['ages']
                        ages[participant] = 1 if ages[participant] == 0 else 0
                    self.reject(alter)

    def test_reject_identity_and_predicate_changes(self):
        cases = json.loads((ROOT / FIXTURE).read_text())['liveness']
        # Swap an effective input independently, leaving its formerly correct result.
        for kind, field, value in (
            ('transaction', 'kind', 'destination_only'),
            ('transaction', 'sender', 'B'), ('transaction', 'crc_valid', False),
            ('response', 'participant', 'B'), ('response', 'success', False),
        ):
            index = next(i for i, c in enumerate(cases) if c['event']['kind'] == kind)
            with self.subTest(kind=kind, field=field):
                self.reject(lambda d: d['liveness'][index]['event'].__setitem__(field, value))

    def test_reject_changed_state_transitions(self):
        data = json.loads((ROOT / FIXTURE).read_text())
        for index, case in enumerate(data['transitions']):
            for step, state in enumerate(case['after_each']):
                changes = {
                    'startup': not state['startup'], 'active': not state['active'],
                    'reset_state': 'normal' if state['reset_state'] == 'reset-state' else 'reset-state',
                    'clear_count': state['clear_count'] + 1,
                    'dynamic_config': ['invented'], 'raw': [], 'admission': True,
                    'ages': {'A': 0, 'B': 0, 'C': 0},
                }
                for field, value in changes.items():
                    with self.subTest(case=index, step=step, field=field):
                        self.reject(lambda d: d['transitions'][index]['after_each'][step].__setitem__(field, value))

    def test_reject_ff02_data_and_promotions(self):
        for index in (0, 1):
            for field, value in [('nn', 1), ('data', [1]), ('responder', None)]:
                with self.subTest(variant=index, field=field):
                    self.reject(lambda d: d['ff02'][index].__setitem__(field, value))
        for grade in ('Proven', 'Unknown'):
            self.reject(lambda d: d.__setitem__('grade', grade))
        self.reject(lambda d: d.__setitem__('qualification', 'qualified'))
        for field in UNKNOWN:
            with self.subTest(unknown=field):
                self.reject(lambda d: d['unknown'].__setitem__(field, 'invented'))

    def test_reject_each_changed_table_cell(self):
        for rows in (LIVENESS_ROWS, STATE_ROWS, FF02_ROWS):
            for row in rows:
                original = '| ' + ' | '.join(row) + ' |'
                for index in range(len(row)):
                    changed = row.copy()
                    changed[index] = 'invented'
                    replacement = '| ' + ' | '.join(changed) + ' |'
                    with self.subTest(row=row[:2], column=index):
                        self.reject(lambda page: page.replace(original, replacement, 1), 'page')


if __name__ == '__main__':
    unittest.main()
