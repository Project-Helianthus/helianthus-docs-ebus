"""Offline contract checks; these do not exercise a runtime implementation."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('architecture/aj21_b531_getter.md')
FIXTURE = Path('architecture/fixtures/aj21_b531_getter.json')
SELF = Path('tests/test_aj21_b531_getter.py')


def tables(page):
    """Read only this page's plain pipe tables, without optional dependencies."""
    result = []
    active = False
    for line in page.splitlines():
        if not line.startswith('|'):
            active = False
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if all(cell and set(cell) <= {'-', ':'} for cell in cells):
            continue
        if not active:
            result.append([])
            active = True
        result[-1].append(cells)
    return result


def expected_fixture():
    # Independent oracle: retain each preceding field on failure. Never apply
    # factor metadata to a value. divmod then modulo expresses the arithmetic
    # independently of an implementation's divide and bit-mask expression.
    cache = []
    for name, minimum, maximum in (
        ('base', 4, 7), ('minimum-only', 5, 7), ('maximum-only', 4, 8)
    ):
        before = {'min': minimum, 'max': maximum}
        old_metadata = {'quality': 'Unknown'}
        cache.append({
            'case': name, 'opcode': 'OP02', 'before': before,
            'raw_outcome': 'failed', 'after': copy.deepcopy(before),
            'preceding_metadata': old_metadata,
            'retained_metadata': copy.deepcopy(old_metadata),
            'new_metadata': {}, 'freshness': 'Unknown',
        })
    getter = []
    for value in (0, 9, 10, 655359, 655360, 4294967295):
        quotient, _ = divmod(value, 10)
        getter.append({'raw_u32': value, 'floor_quotient': quotient,
                       'result': quotient % (2 ** 16)})
    identities = [
        {'participant': 'synthetic-a', 'slot': 2, 'route': 'route-a'},
        {'participant': 'synthetic-b', 'slot': 2, 'route': 'route-a'},
        {'participant': 'synthetic-a', 'slot': 3, 'route': 'route-a'},
        {'participant': 'synthetic-a', 'slot': 2, 'route': 'route-b'},
    ]
    return {
        'grade': 'Hypothesis',
        'unknown': dict.fromkeys((
            'native_behavior', 'physical_qualification',
            'factor_operation_order', 'factor_application', 'timer_argument',
            'initial_job_timing', 'physical_cadence', 'native_unit',
            'native_encoding', 'outside_u32', 'lifecycle_relationship',
        ), 'Unknown'),
        'admission': 'closed', 'cache_cases': cache, 'getter_cases': getter,
        'distribution': [
            {'alternative': alternative, 'factor_metadata': factor,
             'identities_before': copy.deepcopy(identities),
             'identities_after': copy.deepcopy(identities),
             'output_value': 'Unknown'}
            for alternative, factor in [('direct', 'Unknown'), ('aggregate', 86500)]
        ],
        'lifecycle': [
            {'event': event, 'argument': 'Unknown', 'timing': 'Unknown',
             'physical_cadence': 'Unknown'}
            for event in ('timer', 'delayed-initial-job')
        ],
        'outside_slice': ['raw-word*10', 'capability predicates', 'special index 1 branch'],
    }


def expected_tables():
    # Literal page expectations also cross-check the computed JSON oracle.
    return [
        [['Property', 'Grade or value'],
         ['Local software candidate', 'Hypothesis'], ['Native behavior', 'Unknown'],
         ['Physical qualification', 'Unknown'], ['Admission', 'closed'],
         ['Factor operation order', 'Unknown'], ['Factor application', 'Unknown'],
         ['Timer argument', 'Unknown'], ['Delayed initial job timing', 'Unknown'],
         ['Physical cadence', 'Unknown']],
        [['Case', 'Before min', 'Before max', 'Read outcome', 'After min',
          'After max', 'Freshness', 'New metadata'],
         ['base', '4', '7', 'failed', '4', '7', 'Unknown', 'none'],
         ['minimum-only', '5', '7', 'failed', '5', '7', 'Unknown', 'none'],
         ['maximum-only', '4', '8', 'failed', '4', '8', 'Unknown', 'none']],
        [['Raw u32', 'Floor quotient', 'Low16 result'],
         ['0', '0', '0'], ['9', '0', '0'], ['10', '1', '1'],
         ['655359', '65535', '65535'], ['655360', '65536', '0'],
         ['4294967295', '429496729', '39321']],
        [['Alternative', 'Participant', 'Slot', 'Route', 'Output value', 'Factor'],
         ['direct', 'synthetic-a', '2', 'route-a', 'Unknown', 'Unknown'],
         ['direct', 'synthetic-b', '2', 'route-a', 'Unknown', 'Unknown'],
         ['direct', 'synthetic-a', '3', 'route-a', 'Unknown', 'Unknown'],
         ['direct', 'synthetic-a', '2', 'route-b', 'Unknown', 'Unknown'],
         ['aggregate', 'synthetic-a', '2', 'route-a', 'Unknown', '86500'],
         ['aggregate', 'synthetic-b', '2', 'route-a', 'Unknown', '86500'],
         ['aggregate', 'synthetic-a', '3', 'route-a', 'Unknown', '86500'],
         ['aggregate', 'synthetic-a', '2', 'route-b', 'Unknown', '86500']],
        [['Event', 'Argument', 'Timing', 'Physical cadence'],
         ['timer', 'Unknown', 'Unknown', 'Unknown'],
         ['delayed-initial-job', 'Unknown', 'Unknown', 'Unknown']],
    ]


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, path + (index,))
    else:
        yield path, value


def replace(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


class AJ21Contract(unittest.TestCase):
    def validate(self, root):
        fixture = json.loads((root / FIXTURE).read_text())
        # Strict keys reject invented facts as well as missing evidence axes.
        self.assertEqual(fixture, expected_fixture())
        page = (root / PAGE).read_text()
        self.assertEqual(tables(page), expected_tables())
        for clause in (
            'Nothing is stable before 1.0.',
            'Missing evidence keeps admission closed.',
            'No physical qualification or admission follows',
            'Existing eBUS MCP compatibility and GraphQL parity are preserved;',
            'The parent remains open;',
        ):
            self.assertIn(clause, page)

    def disposable(self):
        directory = tempfile.TemporaryDirectory(prefix='aj21-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for relative in (PAGE, FIXTURE, SELF):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, root / relative)
        return root

    def test_valid_controls_and_independent_arithmetic(self):
        self.validate(ROOT)
        data = json.loads((ROOT / FIXTURE).read_text())
        self.assertEqual([row['result'] for row in data['getter_cases']],
                         [0, 0, 1, 65535, 0, 39321])
        value = 655360
        correct = divmod(value, 10)[0] % (2 ** 16)
        self.assertEqual(correct, divmod(value % (2 ** 16), 10)[0])
        discriminator = 4294967295
        self.assertNotEqual(
            divmod(discriminator, 10)[0] % (2 ** 16),
            divmod(discriminator % (2 ** 16), 10)[0],
        )
        self.assertNotEqual(correct, min(divmod(value, 10)[0], 65535))
        # Every claimed identity axis varies alone; no axis can be collapsed.
        for alternative in data['distribution']:
            baseline, *variants = alternative['identities_before']
            for field, variant in zip(('participant', 'slot', 'route'), variants):
                self.assertEqual([key for key in baseline if baseline[key] != variant[key]],
                                 [field])
            self.assertEqual(alternative['identities_before'], alternative['identities_after'])

    def test_every_fixture_leaf_rejects_independent_mutation(self):
        root = self.disposable()
        original = json.loads((root / FIXTURE).read_text())
        count = 0
        for path, value in leaves(original):
            mutated = copy.deepcopy(original)
            replacement = value + 1 if isinstance(value, int) else 'fabricated'
            replace(mutated, path, replacement)
            (root / FIXTURE).write_text(json.dumps(mutated))
            with self.subTest(path=path), self.assertRaises(AssertionError):
                self.validate(root)
            count += 1
        # Empty metadata and structural omissions/additions need explicit checks.
        for key in original:
            mutated = copy.deepcopy(original)
            del mutated[key]
            (root / FIXTURE).write_text(json.dumps(mutated))
            with self.subTest(missing=key), self.assertRaises(AssertionError):
                self.validate(root)
            count += 1
        for replacement in ({'fresh': True}, {'factor_arithmetic': 'multiply'}):
            mutated = copy.deepcopy(original)
            mutated['cache_cases'][0]['new_metadata'] = replacement
            (root / FIXTURE).write_text(json.dumps(mutated))
            with self.subTest(metadata=replacement), self.assertRaises(AssertionError):
                self.validate(root)
            count += 1
        mutated = copy.deepcopy(original)
        mutated['invented_native_fact'] = 'Proven'
        (root / FIXTURE).write_text(json.dumps(mutated))
        with self.assertRaises(AssertionError):
            self.validate(root)
        count += 1
        print(f'Fixture mutation rejections executed: {count}')

    def test_each_page_table_cell_rejects_independent_mutation(self):
        root = self.disposable()
        original = (root / PAGE).read_text().splitlines(keepends=True)
        count = 0
        for number, line in enumerate(original):
            if not line.startswith('|') or set(line.replace('|', '').strip()) <= {'-', ' '}:
                continue
            parts = line.split('|')
            for column in range(1, len(parts) - 1):
                mutated = original.copy()
                changed = parts.copy()
                changed[column] = ' fabricated '
                mutated[number] = '|'.join(changed)
                (root / PAGE).write_text(''.join(mutated))
                with self.subTest(line=number + 1, column=column), self.assertRaises(AssertionError):
                    self.validate(root)
                count += 1
        print(f'Page table mutation rejections executed: {count}')

    def test_named_semantic_mutants(self):
        root = self.disposable()
        original = json.loads((root / FIXTURE).read_text())
        mutations = [
            (('cache_cases', 0, 'after'), {'min': None, 'max': None}),
            (('cache_cases', 0, 'freshness'), 'fresh'),
            (('grade',), 'Proven'),
            (('unknown', 'native_behavior'), 'Proven'),
            (('getter_cases', 5, 'result'), 6553),
            (('getter_cases', 4, 'result'), 65535),
            (('distribution', 1, 'output_value'), 86500),
            (('distribution', 1, 'identities_after'), original['distribution'][1]['identities_after'][1:]),
        ]
        for path, replacement in mutations:
            mutated = copy.deepcopy(original)
            replace(mutated, path, replacement)
            (root / FIXTURE).write_text(json.dumps(mutated))
            with self.subTest(path=path, replacement=replacement), self.assertRaises(AssertionError):
                self.validate(root)
        print(f'Named semantic mutation rejections executed: {len(mutations)}')


if __name__ == '__main__':
    unittest.main()
