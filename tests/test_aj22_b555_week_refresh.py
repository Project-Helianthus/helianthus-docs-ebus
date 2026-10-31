"""Offline candidate oracle; no production feature or native qualification.

Prospective production mutation coverage (no production mutants are executed):
family/transport/zone/channel: dropping or aliasing any identity axis;
day/slot: reusing a day or slot index across reads;
start hour/minute, end hour/minute, setpoint: altering or reordering any input;
count: treating zero as one, off-by-one slot processing or overflow acceptance;
heating: applying FFFF to heating or omitting it for non-heating;
operation/direction: merging A6 write preparation with A4/A5 reads;
A4 status: scheduling A5 before admission; capacity: ignoring the local bound;
raw slots/last-known-good: losing evidence or prior state after a failure;
retained days/partial day/complete: erasing progress or admitting a partial week;
grade/each Unknown: promoting the candidate or fabricating an absent fact.
Negative fixture/page checks execute only in disposable worktree-local copies.
"""

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'architecture/fixtures/aj22_b555_week_refresh.json'
PAGE = ROOT / 'architecture/aj22_b555_week_refresh.md'
UNKNOWN = {'native_behavior', 'physical_schedule_effects', 'persistence',
           'atomicity', 'a6_dispatch_count', 'mid_slot_failure', 'retry_or_rollback'}


def preparation_oracle(case):
    # Derive slot count from arithmetic, never from the fixture's expected output.
    assert type(case['count']) is int and case['count'] in (0, 1)
    assert type(case['heating']) is bool
    assert len(case['inputs']) == 5
    slots = []
    for _ in range(case['count']):
        a, b, c, d, setpoint = case['inputs']
        slots.append([a, b, c, d, setpoint if case['heating'] else 'FFFF'])
    return {'retained_inputs': deepcopy(case['inputs']), 'processed': slots}


def week_oracle(case):
    assert case['operation'] == 'A4/A5' and case['direction'] == 'read'
    assert set(case['identity']) == {'family', 'transport', 'zone', 'channel'}
    assert len(case['days']) == 7
    assert type(case['capacity']) is int and case['capacity'] > 0
    assert case['a4_status'] in ('success', 'failure')
    retained, requests, partial = [], [], None
    raw_days = [{'day': day['day'], 'count': day['count']} for day in case['days']]
    if case['a4_status'] == 'success':
        for index, day in enumerate(case['days']):
            assert day['day'] == index
            assert type(day['count']) is int and day['count'] >= 0
            if day['count'] > case['capacity']:
                partial = {'day': index, 'count': day['count'], 'raw_slots': []}
                break
            assert len(day['raw_slots']) == day['count']
            raw_days[index]['raw_slots'] = deepcopy(day['raw_slots'])
            retained.append(deepcopy(day))
            requests.extend({'day': index, 'slot': s} for s in range(day['count']))
    return dict(identity=deepcopy(case['identity']), raw_days=raw_days,
                retained_days=retained, a5_requests=requests,
                a5_attempts=len(requests), partial_day=partial,
                complete=len(retained) == 7, admission=False,
                last_known_good=deepcopy(case['last_known_good']))


def validate(data):
    assert data['grade'] == 'Hypothesis'
    assert set(data['unknown']) == UNKNOWN
    assert all(value == 'Unknown' for value in data['unknown'].values())
    assert data['preparation_operation'] == 'A6'
    assert data['preparation_direction'] == 'write'
    assert len(data['preparation']) == 4
    assert {(c['count'], c['heating']) for c in data['preparation']} == {
        (0, False), (1, False), (0, True), (1, True)}
    for case in data['preparation']:
        assert case['expected'] == preparation_oracle(case)
    assert len(data['weekly']) == 9
    for case in data['weekly']:
        assert case['expected'] == week_oracle(case)


def table_rows(page, heading):
    section = page.split(heading, 1)[1].split('\n## ', 1)[0]
    return [[part.strip() for part in line.strip().strip('|').split('|')]
            for line in section.splitlines() if line.startswith('|')][2:]


def validate_tables(page):
    assert table_rows(page, '## A6 preparation table') == [
        ['0', 'non-heating', 'unchanged five', '0', 'absent'],
        ['1', 'non-heating', 'unchanged five', '1', 'FFFF'],
        ['0', 'heating', 'unchanged five', '0', 'absent'],
        ['1', 'heating', 'unchanged five', '1', 'input']]
    assert table_rows(page, '## Weekly refresh transition table') == [
        ['A4 failure before day 0', '0', 'none', 'absent', 'false'],
        ['overflow at day d', 'sum of counts before d', '0 through d-1',
         'day d, raw count, no slots', 'false'],
        ['all seven days accepted', 'sum of seven counts', '0 through 6',
         'absent', 'true']]
    assert table_rows(page, '## Evidence table') == [
        ['software candidate', 'Hypothesis'], ['native behavior', 'Unknown'],
        ['physical schedule effects', 'Unknown'], ['persistence', 'Unknown'],
        ['atomicity', 'Unknown'], ['A6 dispatch count', 'Unknown'],
        ['mid-slot failure', 'Unknown'], ['retry or rollback', 'Unknown']]


class WeeklyRefreshContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def reject_copy(self, document, page=False):
        # Every executed negative variant is a disposable copy of an owned file.
        local = ROOT / '.tmp'
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as directory:
            path = Path(directory) / (PAGE.name if page else FIXTURE.name)
            path.write_text(document if page else json.dumps(document))
            with self.assertRaises(AssertionError):
                if page:
                    validate_tables(path.read_text())
                else:
                    validate(json.loads(path.read_text()))

    def test_published_tables_and_explicit_scenarios(self):
        validate_tables(self.page)
        validate(self.data)
        # Independent constants ensure the examples cannot disappear together.
        self.assertEqual([c['count'] for c in self.data['preparation']], [0, 1, 0, 1])
        weeks = self.data['weekly']
        self.assertEqual(weeks[0]['expected']['a5_attempts'], 8)
        self.assertTrue(weeks[0]['expected']['complete'])
        self.assertEqual(weeks[1]['a4_status'], 'failure')
        self.assertEqual(weeks[1]['expected']['a5_requests'], [])
        self.assertEqual([c['expected']['partial_day']['day'] for c in weeks[2:]],
                         list(range(7)))
        self.assertEqual([c['expected']['a5_attempts'] for c in weeks[2:]],
                         [0, 1, 3, 3, 4, 6, 7])
        for d, case in enumerate(weeks[2:]):
            self.assertEqual([r['day'] for r in case['expected']['retained_days']],
                             list(range(d)))
            self.assertFalse(case['expected']['complete'])
            self.assertFalse(case['expected']['admission'])

    def test_raw_days_only_include_acquired_slots(self):
        for index, case in enumerate(self.data['weekly']):
            visited = (7 if index == 0 else 0 if index == 1 else index - 2)
            result = week_oracle(case)
            for day, raw in enumerate(result['raw_days']):
                with self.subTest(case=case['name'], day=day):
                    self.assertEqual(raw['day'], day)
                    self.assertEqual(raw['count'], case['days'][day]['count'])
                    if day < visited:
                        self.assertEqual(raw, case['days'][day])
                        data = deepcopy(self.data)
                        del data['weekly'][index]['expected']['raw_days'][day]['raw_slots']
                        self.reject_copy(data)
                    else:
                        self.assertEqual(set(raw), {'day', 'count'})
                        data = deepcopy(self.data)
                        data['weekly'][index]['expected']['raw_days'][day]['raw_slots'] = (
                            deepcopy(case['days'][day]['raw_slots']) or ['unread-slot'])
                        self.reject_copy(data)
                        changed = deepcopy(case)
                        changed['days'][day]['raw_slots'] = ['unread-slot']
                        self.assertEqual(week_oracle(changed), result)

    def test_five_inputs_count_and_heating_independently(self):
        for field in range(5):
            for heating in (False, True):
                for count in (0, 1):
                    with self.subTest(field=field, heating=heating, count=count):
                        case = deepcopy(self.data['preparation'][0])
                        case.update(count=count, heating=heating)
                        case['inputs'][field] = f'changed-input-{field}'
                        result = preparation_oracle(case)
                        self.assertEqual(result['retained_inputs'], case['inputs'])
                        self.assertEqual(len(result['processed']), count)
                        if count:
                            self.assertEqual(result['processed'][0][:4], case['inputs'][:4])
                            self.assertEqual(result['processed'][0][4],
                                             case['inputs'][4] if heating else 'FFFF')

    def test_identity_raw_and_last_known_good_independently(self):
        for axis in ('family', 'transport', 'zone', 'channel'):
            case = deepcopy(self.data['weekly'][4])  # day 2 failure
            case['identity'][axis] = f'alternative-{axis}'
            result = week_oracle(case)
            self.assertEqual(result['identity'], case['identity'])
            data = deepcopy(self.data)
            data['weekly'][4] = case
            case['expected'] = result
            validate(data)  # positive control; then erase only this identity axis
            case['expected']['identity'][axis] = 'aliased'
            self.reject_copy(data)
        for day in range(7):
            for slot in range(self.data['weekly'][0]['days'][day]['count']):
                case = deepcopy(self.data['weekly'][0])
                case['days'][day]['raw_slots'][slot] = f'changed-{day}-{slot}'
                result = week_oracle(case)
                self.assertEqual(result['retained_days'][day]['raw_slots'][slot],
                                 f'changed-{day}-{slot}')
                self.assertIn({'day': day, 'slot': slot}, result['a5_requests'])
                for field in ('day', 'slot'):
                    data = deepcopy(self.data)
                    data['weekly'][0] = case
                    case['expected'] = deepcopy(result)
                    request = next(r for r in case['expected']['a5_requests']
                                   if r == {'day': day, 'slot': slot})
                    request[field] += 1
                    self.reject_copy(data)
        for index in range(9):
            case = deepcopy(self.data['weekly'][index])
            case['last_known_good'] = ['different-prior-state']
            self.assertEqual(week_oracle(case)['last_known_good'], ['different-prior-state'])

    def test_count_status_capacity_predicates(self):
        for count in (0, 1, 2, 3):
            for capacity in (1, 2, 3):
                for status in ('success', 'failure'):
                    case = deepcopy(self.data['weekly'][0])
                    case.update(capacity=capacity, a4_status=status)
                    case['days'][0] = dict(day=0, count=count,
                                          raw_slots=[f'raw-{s}' for s in range(count)])
                    result = week_oracle(case)
                    if status == 'failure' or count > capacity:
                        self.assertEqual(result['a5_attempts'], 0)
                        self.assertFalse(result['complete'])
                    else:
                        self.assertEqual(result['retained_days'][0], case['days'][0])
                        self.assertEqual(result['a5_requests'][:count],
                                         [{'day': 0, 'slot': s} for s in range(count)])

    def test_disposable_outcome_corruptions_are_rejected(self):
        for index, case in enumerate(self.data['preparation']):
            for field in ('retained_inputs', 'processed'):
                data = deepcopy(self.data)
                data['preparation'][index]['expected'][field] = ['incorrect']
                self.reject_copy(data)
        for index, case in enumerate(self.data['weekly']):
            for field, value in case['expected'].items():
                data = deepcopy(self.data)
                data['weekly'][index]['expected'][field] = (
                    not value if isinstance(value, bool) else 'incorrect')
                self.reject_copy(data)
        # Direct regressions: FFFF at zero, A5 before failed A4, lost prior days,
        # and a partial week labelled complete.
        data = deepcopy(self.data)
        data['preparation'][0]['expected']['retained_inputs'][4] = 'FFFF'
        self.reject_copy(data)
        for index, field, value in [(1, 'a5_attempts', 1),
                                    (4, 'retained_days', []), (4, 'complete', True)]:
            data = deepcopy(self.data)
            data['weekly'][index]['expected'][field] = value
            self.reject_copy(data)

    def test_operation_direction_and_evidence_fail_closed(self):
        for field, value in [('preparation_operation', 'A5'),
                             ('preparation_direction', 'read'), ('grade', 'Proven'),
                             ('grade', 'Unknown')]:
            data = deepcopy(self.data)
            data[field] = value
            self.reject_copy(data)
        for field, value in [('operation', 'A6'), ('direction', 'write')]:
            data = deepcopy(self.data)
            data['weekly'][0][field] = value
            self.reject_copy(data)
        for key in UNKNOWN:
            for value in ('Proven', 'Hypothesis', True):
                data = deepcopy(self.data)
                data['unknown'][key] = value
                self.reject_copy(data)
        data = deepcopy(self.data)
        data['unknown']['invented_property'] = 'Proven'
        self.reject_copy(data)
        for old, new in [('unchanged five', 'FFFF'), ('| 0 | absent |', '| 1 | FFFF |'),
                         ('| 0 | none |', '| 1 | none |'),
                         ('0 through d-1', 'none'), ('| false |', '| true |'),
                         ('Hypothesis |', 'Proven |'), ('Unknown |', 'Proven |')]:
            self.assertIn(old, self.page)
            self.reject_copy(self.page.replace(old, new, 1), page=True)


if __name__ == '__main__':
    unittest.main()
