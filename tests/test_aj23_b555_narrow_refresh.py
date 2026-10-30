"""Offline contract checks only; no runtime timer implementation."""
import copy
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'architecture/fixtures/aj23_b555_narrow_refresh.json'
PAGE = ROOT / 'architecture/aj23_b555_narrow_refresh.md'


def expected():
    # Independent arithmetic oracle: IEEE binary32 packing precedes scaling.
    floats = []
    for raw in (1.29, 6553.6, 1.3):
        f32 = struct.unpack('!f', struct.pack('!f', raw))[0]
        scaled = f32 * 10.0
        u32 = math.trunc(scaled)
        assert 0 <= u32 <= (2**32 - 1)
        floats.append(dict(raw=raw, float32=f32, scaled=scaled,
                           u32=u32, low16=u32 % 65536))
    identity = dict(variant='variant-alpha', timer_kind='local-1',
                    model_index=255, read_instance=0, a6_module=7)
    identities = [dict(changed='control', identity=identity)]
    for axis, alternate in [('variant', 'variant-beta'), ('timer_kind', 'local-2'),
                            ('model_index', 254), ('read_instance', 1), ('a6_module', 8)]:
        identities.append(dict(changed=axis, identity=dict(identity, **{axis: alternate})))
    return {
        'grade': 'Hypothesis', 'qualification': 'Unknown',
        'unknown': {key: 'Unknown' for key in (
            'native_behavior', 'native_kind_codes', 'module_admission_rule',
            'nonfinite_conversion', 'out_of_domain_conversion', 'persistence',
            'ttl_seconds', 'actual_cadence_seconds', 'physical_qualification',
            'mcp_runtime_support', 'graphql_runtime_support')},
        'implemented': dict(scheduler=False, cache_writer=False, consumer=False),
        'kinds': [dict(kind=f'local-{i}', native_code='Unknown', carrier=f'carrier-{i}',
                       cache=f'cache-{i}', consumer=f'consumer-{i}', grade='Hypothesis')
                  for i in range(1, 6)],
        'variants': [dict(variant=v, admission_predicate=f'{v}-module-predicate',
                          admission_result='Unknown')
                     for v in ('variant-alpha', 'variant-beta')],
        'integers': [dict(raw=x, low16=y) for x, y in
                     ((65535, 65535), (65536, 0), (-1, 65535))],
        'floats': floats,
        'undefined_conversions': [dict(raw=x, result='Unknown') for x in
                                  ('NaN', '+Infinity', '-Infinity', 'outside-u32-domain')],
        'setter': dict(generic_marker='synthetic-marker',
                       or_operands=['00010000', '00000001'],
                       or_return=f'{(1 << 16) | 1:08x}', local_commit='separate',
                       persistence='Unknown'),
        'senders': [dict(sender='ordinary', local_n=3, transmitted_count=3),
                    dict(sender='other', local_n=3, transmitted_count='Unknown')],
        # Explicit independent transition truth table, not a runtime state machine.
        'a6': [dict(count=0, callback='full', attempt_argument=500,
                    attempt_success='Unknown', request='root/full', dirty='Unknown'),
               dict(count=0, callback='partial', attempt_argument=500,
                    attempt_success='Unknown', request='root/full', dirty='Unknown'),
               dict(count=2, callback='full', attempt_argument=None,
                    attempt_success='Unknown', request=None, dirty='full'),
               dict(count=2, callback='partial', attempt_argument=None,
                    attempt_success='Unknown', request=None, dirty='partial')],
        'refresh': [dict(service=s, scope=c, direction='read-refresh', grade='Hypothesis')
                    for s in ('A4', 'A5')
                    for c in ('DHW', 'circulation', 'ventilation', 'heating', 'cooling')],
        'identities': identities,
        'timer': dict(argument_seconds=3600, ttl_seconds='Unknown',
                      actual_cadence_seconds='Unknown'),
        'partial': dict(raw_before=['synthetic-good', 'synthetic-pending'],
                        raw_after=['synthetic-good', 'synthetic-pending'],
                        last_known_good_before=['synthetic-good'],
                        last_known_good_after=['synthetic-good'], outcome='partial',
                        persistence='Unknown', admitted=False),
    }


def tables(page):
    result, current = [], []
    for line in page.splitlines() + ['']:
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if not all(set(cell) <= {'-', ':'} for cell in cells):
                current.append(cells)
        elif current:
            result.append(current)
            current = []
    return result


def expected_tables(e):
    return [
        [['Kind', 'Carrier', 'Cache', 'Consumer', 'Native code', 'Grade']] +
        [[k[f] for f in ('kind', 'carrier', 'cache', 'consumer', 'native_code', 'grade')]
         for k in e['kinds']],
        [['Integer64 input', 'Low 16']] +
        [[str(x['raw']), str(x['low16'])] for x in e['integers']],
        [['Float input', 'Widened float32', 'Multiplied by 10', 'u32', 'Low 16']] +
        [[str(x[f]) for f in ('raw', 'float32', 'scaled', 'u32', 'low16')]
         for x in e['floats']],
        [['Count predicate', 'Callback', 'Attempt argument', 'Attempt success', 'Request', 'Dirty']] +
        [[('zero' if x['count'] == 0 else 'nonzero'), x['callback'],
          'none' if x['attempt_argument'] is None else str(x['attempt_argument']),
          x['attempt_success'], x['request'] or 'none', x['dirty']] for x in e['a6']],
        [['Service', 'Scope', 'Direction', 'Grade']] +
        [[x[f] for f in ('service', 'scope', 'direction', 'grade')] for x in e['refresh']],
    ]


class NarrowRefreshContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def validate(self, data, page):
        self.assertEqual(data, expected())
        self.assertEqual(tables(page), expected_tables(expected()))
        for phrase in ('graded **Hypothesis**', 'physical qualification **Unknown**',
                       'No timer\nscheduler, cache writer or consumer is implemented.',
                       'both remain Unknown', 'full 32-bit OR return',
                       'root/full request', 'partial last-known-good state',
                       'input-derived A6 module', 'Module admission differs by software variant'):
            self.assertIn(phrase, page)

    def reject_disposable(self, data, page):
        # Use the existing worktree root; a fresh checkout need not have .tmp.
        # Mutant artifacts live only in a disposable worktree-local copy.
        with tempfile.TemporaryDirectory(prefix='.aj23-mutant-', dir=ROOT) as directory:
            sandbox = Path(directory)
            fixture = sandbox / FIXTURE.name
            document = sandbox / PAGE.name
            fixture.write_text(json.dumps(data))
            document.write_text(page)
            (sandbox / Path(__file__).name).write_text(Path(__file__).read_text())
            with self.assertRaises(AssertionError):
                self.validate(json.loads(fixture.read_text()), document.read_text())

    def test_scenarios_and_page_tables(self):
        self.validate(self.data, self.page)
        self.assertEqual(math.trunc(1.3 * 10), 13)  # discriminating control
        for row in self.data['identities'][1:]:
            changed = [key for key, value in row['identity'].items()
                       if value != self.data['identities'][0]['identity'][key]]
            self.assertEqual(changed, [row['changed']])

    def test_each_scenario_leaf_rejects_an_independent_mutation(self):
        # Every selector, direction, predicate, raw value, grade and outcome leaf
        # is altered alone. This also fences fabricated facts and schema growth.
        def leaves(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from leaves(child, path + (key,))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    yield from leaves(child, path + (i,))
            else:
                yield path
        paths = list(leaves(self.data))
        self.assertGreater(len(paths), 200)
        for path in paths:
            with self.subTest(path=path):
                mutated = copy.deepcopy(self.data)
                parent = mutated
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = 'fabricated-value'
                self.reject_disposable(mutated, self.page)
        mutated = copy.deepcopy(self.data)
        mutated['native_code'] = 5
        self.reject_disposable(mutated, self.page)
        self.validate(self.data, self.page)

    def test_required_faults_rejected(self):
        faults = [
            ('skip-float32', ('floats', 2, 'u32'), 13),
            ('integer-saturate', ('integers', 1, 'low16'), 65535),
            ('negative-saturate', ('integers', 2, 'low16'), 0),
            ('or-low16', ('setter', 'or_return'), '00000001'),
            ('attempt-is-success', ('a6', 0, 'attempt_success'), True),
            ('merge-model-instance', ('identities', 0, 'identity', 'model_index'), 0),
            ('merge-module-model', ('identities', 0, 'identity', 'a6_module'), 255),
            ('merge-module-instance', ('identities', 0, 'identity', 'a6_module'), 0),
            ('derive-ttl', ('timer', 'ttl_seconds'), 3600),
            ('derive-cadence', ('timer', 'actual_cadence_seconds'), 3600),
            ('promote-candidate', ('grade',), 'Proven'),
            ('promote-pending', ('partial', 'last_known_good_after'),
             ['synthetic-good', 'synthetic-pending']),
        ]
        for name, path, value in faults:
            with self.subTest(fault=name):
                mutated = copy.deepcopy(self.data)
                parent = mutated
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                self.reject_disposable(mutated, self.page)
        self.validate(self.data, self.page)

    def test_each_page_table_cell_rejects_mutation(self):
        count = 0
        for line_number, line in enumerate(self.page.splitlines()):
            if not line.startswith('|') or line.startswith('|---'):
                continue
            cells = line.split('|')
            for column in range(1, len(cells) - 1):
                with self.subTest(line=line_number + 1, column=column):
                    changed = cells.copy()
                    changed[column] = ' fabricated-value '
                    lines = self.page.splitlines()
                    lines[line_number] = '|'.join(changed)
                    self.reject_disposable(self.data, '\n'.join(lines))
                    count += 1
        self.assertGreater(count, 100)
        self.validate(self.data, self.page)


if __name__ == '__main__':
    unittest.main()
