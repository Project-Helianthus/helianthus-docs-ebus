"""Finite documentation checks, not a substitute for production API execution."""
import copy
import json
from pathlib import Path
import re
import unittest

ab25ao25Root = Path(__file__).resolve().parents[1]
ab25ao25Page = ab25ao25Root / 'architecture/ao26_b522_demand_views.md'
ab25ao25Fixture = ab25ao25Root / 'architecture/fixtures/ao26_b522_demand_views.json'
ab25ao25Labels = (
    'no-heating-demand-to-source-or-circuits',
    'no-source-demand-but-demand-from-sink',
    'source-heating-demand',
    'no-source-cooling-demand-but-demand-from-sink',
    'source-cooling-demand',
)
ab25ao25Contract = {
    'api': 'Ab25Ao25Interpret(ab25ao25Input json.RawMessage) (json.RawMessage, error)',
    'package': 'vaillant',
    'implementation': 'standard-library; pure; no runtime call site',
    'selection': {'primary': 181, 'secondary': 34, 'operation': 0,
                  'view': 'isolated-fields', 'directions': {
                      'request': ['mode', 'fan', 'room_temperature', 'automatic'],
                      'positive': ['positive_flags']}},
    'grades': {'semantic': 'Hypothesis', 'calculation': 'Proven',
               'physical': 'Unknown', 'qualified': False},
    'mode_labels': dict(zip(('0', '1', '2', '3', '4'), ab25ao25Labels)),
    'mode_1': {'state': 'label-conflict', 'competing_label': 'Unknown'},
    'mode_unmapped': [5, 255], 'fan': {'carrier': [0, 255], 'enum': None},
    'room_temperature': {'carrier': [0, 255], 'divisor': 2,
                         'unit': 'Celsius', 'sentinel': None},
    'automatic': {'allocated_bits': [0], 'reserved_bits': [1, 2, 3, 4, 5, 6, 7]},
    'positive_flags': {'allocated_bits': [0, 1, 2],
                       'reserved_bits': [3, 4, 5, 6, 7], 'roles': None},
    'width': 1, 'empty_state': 'incomplete', 'overlong_state': 'unknown-order',
    'missing': 'absent result; partial aggregate',
    'arguments': 'absent or empty object; no scalar arguments are allocated',
    'unknown_selection': {'state': 'Unknown', 'fields': {},
                          'physical': 'Unknown', 'qualified': False},
    'copy_contract': ['context', 'raw', 'arguments', 'result fields', 'later calls'],
    'error_contract': ['duplicate keys at any depth', 'malformed JSON',
                       'wrong JSON kinds', 'noninteger bytes', 'bytes outside 0..255'],
    'non_executable_candidates': ['heating priority', 'bypass behavior', 'FF FF unset'],
    'qualification': 'No native support, effects or persistence inferred',
    'scope': 'Synthetic software contract; no output-control, UI, scan or transport change',
}


def ab25ao25Result(ab25ao25Raw, ab25ao25State='complete', **ab25ao25Values):
    """Construct an expected JSON record; never interpret input bytes."""
    return dict(raw=ab25ao25Raw, state=ab25ao25State,
                grade='Hypothesis', **ab25ao25Values)


ab25ao25FullFields = {'mode': [2], 'fan': [255],
                      'room_temperature': [255], 'automatic': [128]}
ab25ao25FullResults = {
    'mode': ab25ao25Result([2], label='source-heating-demand'),
    'fan': ab25ao25Result([255], number=255, calculation='Proven'),
    'room_temperature': ab25ao25Result([255], number=127.5, calculation='Proven'),
    'automatic': ab25ao25Result([128], label='disabled', reserved=128),
}


def ab25ao25ExpectedCases():
    """Independent expected tuples, with no input decoder or selector evaluator."""
    ab25ao25Rows = []

    def ab25ao25Append(ab25ao25Id, ab25ao25Direction, ab25ao25Fields,
                      ab25ao25Results, ab25ao25State='partial',
                      ab25ao25Override=None, ab25ao25Arguments=None):
        ab25ao25Context = dict(primary=181, secondary=34, operation=0,
                              direction=ab25ao25Direction, view='isolated-fields',
                              family='synthetic-family', variant='synthetic-variant')
        ab25ao25Context.update(ab25ao25Override or {})
        ab25ao25Input = dict(context=ab25ao25Context, fields=ab25ao25Fields)
        ab25ao25Output = dict(context=copy.deepcopy(ab25ao25Context),
                             raw=copy.deepcopy(ab25ao25Fields),
                             state=ab25ao25State, fields=ab25ao25Results,
                             physical='Unknown', qualified=False)
        if ab25ao25Arguments is not None:
            ab25ao25Input['arguments'] = ab25ao25Arguments
            ab25ao25Output['arguments'] = copy.deepcopy(ab25ao25Arguments)
        ab25ao25Rows.append(dict(id='ab25ao25-' + ab25ao25Id,
                                 input=ab25ao25Input, output=ab25ao25Output))

    for ab25ao25Byte, ab25ao25State, ab25ao25Label in (
        (0, 'complete', ab25ao25Labels[0]),
        (1, 'label-conflict', ab25ao25Labels[1]),
        (2, 'complete', ab25ao25Labels[2]),
        (3, 'complete', ab25ao25Labels[3]),
        (4, 'complete', ab25ao25Labels[4]),
    ):
        ab25ao25Append('mode-' + str(ab25ao25Byte), 'request', {'mode': [ab25ao25Byte]},
                       {'mode': ab25ao25Result([ab25ao25Byte], ab25ao25State,
                                              label=ab25ao25Label)})
    for ab25ao25Byte in (5, 255):
        ab25ao25Append('mode-' + str(ab25ao25Byte), 'request', {'mode': [ab25ao25Byte]},
                       {'mode': ab25ao25Result([ab25ao25Byte], 'unmapped')})
    for ab25ao25Byte, ab25ao25Number in ((0, 0), (1, .5), (16, 8), (153, 76.5), (255, 127.5)):
        ab25ao25Append('room-' + str(ab25ao25Byte), 'request',
                       {'room_temperature': [ab25ao25Byte]},
                       {'room_temperature': ab25ao25Result(
                           [ab25ao25Byte], number=ab25ao25Number, calculation='Proven')})
    for ab25ao25Byte, ab25ao25Number in ((0, 0), (1, 1), (255, 255)):
        ab25ao25Append('fan-' + str(ab25ao25Byte), 'request', {'fan': [ab25ao25Byte]},
                       {'fan': ab25ao25Result([ab25ao25Byte], number=ab25ao25Number,
                                             calculation='Proven')})
    # Every allocated/reserved bit independently, then both carrier boundaries.
    for ab25ao25Byte, ab25ao25Label, ab25ao25Reserved in (
        (0, 'disabled', 0), (1, 'enabled', 0), (2, 'disabled', 2),
        (4, 'disabled', 4), (8, 'disabled', 8), (16, 'disabled', 16),
        (32, 'disabled', 32), (64, 'disabled', 64), (128, 'disabled', 128),
        (255, 'enabled', 254),
    ):
        ab25ao25Append('automatic-' + str(ab25ao25Byte), 'request',
                       {'automatic': [ab25ao25Byte]},
                       {'automatic': ab25ao25Result([ab25ao25Byte],
                           label=ab25ao25Label, reserved=ab25ao25Reserved)})
    for ab25ao25Byte, ab25ao25Flags, ab25ao25Reserved in (
        (0, [False, False, False], 0), (1, [True, False, False], 0),
        (2, [False, True, False], 0), (4, [False, False, True], 0),
        (8, [False, False, False], 8), (16, [False, False, False], 16),
        (32, [False, False, False], 32), (64, [False, False, False], 64),
        (128, [False, False, False], 128), (255, [True, True, True], 248),
    ):
        ab25ao25Append('positive-' + str(ab25ao25Byte), 'positive',
                       {'positive_flags': [ab25ao25Byte]},
                       {'positive_flags': ab25ao25Result([ab25ao25Byte],
                           flags=ab25ao25Flags, reserved=ab25ao25Reserved)}, 'complete')
    ab25ao25Append('complete', 'request', ab25ao25FullFields,
                   ab25ao25FullResults, 'complete', ab25ao25Arguments={})
    ab25ao25ZeroResults = {
        'mode': ab25ao25Result([0], label='no-heating-demand-to-source-or-circuits'),
        'fan': ab25ao25Result([0], number=0, calculation='Proven'),
        'room_temperature': ab25ao25Result([0], number=0, calculation='Proven'),
        'automatic': ab25ao25Result([0], label='disabled', reserved=0),
    }
    for ab25ao25Name in ('mode', 'fan', 'room_temperature', 'automatic'):
        for ab25ao25Tag, ab25ao25Raw, ab25ao25State in (
            ('empty', [], 'incomplete'), ('overlong', [0, 255], 'unknown-order'),
            ('missing', None, None), ('zero', [0], 'complete'),
        ):
            ab25ao25Fields = copy.deepcopy(ab25ao25FullFields)
            ab25ao25Results = copy.deepcopy(ab25ao25FullResults)
            if ab25ao25Tag == 'missing':
                del ab25ao25Fields[ab25ao25Name]
                del ab25ao25Results[ab25ao25Name]
            else:
                ab25ao25Fields[ab25ao25Name] = ab25ao25Raw
                ab25ao25Results[ab25ao25Name] = (
                    ab25ao25ZeroResults[ab25ao25Name] if ab25ao25Tag == 'zero' else
                    ab25ao25Result(ab25ao25Raw, ab25ao25State))
            ab25ao25Append(ab25ao25Name + '-' + ab25ao25Tag, 'request',
                           ab25ao25Fields, ab25ao25Results,
                           'complete' if ab25ao25Tag == 'zero' else 'partial')
    for ab25ao25Tag, ab25ao25Fields, ab25ao25Results in (
        ('empty', {'positive_flags': []}, {'positive_flags': ab25ao25Result([], 'incomplete')}),
        ('overlong', {'positive_flags': [0, 255]},
         {'positive_flags': ab25ao25Result([0, 255], 'unknown-order')}),
        ('missing', {}, {}),
    ):
        ab25ao25Append('positive-' + ab25ao25Tag, 'positive', ab25ao25Fields, ab25ao25Results)
    for ab25ao25Key, ab25ao25Value in (
        ('primary', 180), ('secondary', 35), ('operation', 1),
        ('direction', 'other'), ('view', 'other'),
    ):
        ab25ao25Append('selection-' + ab25ao25Key, 'request', ab25ao25FullFields,
                       {}, 'Unknown', {ab25ao25Key: ab25ao25Value})
    for ab25ao25Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab25ao25Append('missing-selection-' + ab25ao25Key, 'request',
                       ab25ao25FullFields, {}, 'Unknown')
        del ab25ao25Rows[-1]['input']['context'][ab25ao25Key]
        del ab25ao25Rows[-1]['output']['context'][ab25ao25Key]
    for ab25ao25Key, ab25ao25Value in (
        ('family', {'opaque': [1, 'other-family']}),
        ('variant', {'opaque': [2, 'other-variant']}), ('extra', {'opaque': [3]}),
    ):
        ab25ao25Append('opaque-' + ab25ao25Key, 'request', ab25ao25FullFields,
                       ab25ao25FullResults, 'complete', {ab25ao25Key: ab25ao25Value})
    ab25ao25Append('cross-request', 'request', {'positive_flags': [7]}, {})
    ab25ao25Append('cross-positive', 'positive', ab25ao25FullFields, {})
    ab25ao25Append('unknown-sibling', 'request', dict(ab25ao25FullFields, unmodelled=[0, 255]),
                   ab25ao25FullResults, 'complete')
    ab25ao25Append('all-absent', 'request', {}, {})
    return ab25ao25Rows


def ab25ao25ExpectedErrors():
    ab25ao25Texts = [
        '{', '[]', 'null', '{"context":{},"context":{},"fields":{}}',
        '{"context":{"primary":181,"primary":181},"fields":{}}',
        '{"context":{},"fields":{"fan":[0],"fan":[1]}}',
        '{"context":{"opaque":{"x":1,"x":2}},"fields":{}}',
    ]
    ab25ao25Control = {'context': {'primary': 181, 'secondary': 34, 'operation': 0,
                                  'direction': 'request', 'view': 'isolated-fields'},
                       'fields': {'fan': [0]}}
    for ab25ao25Bad in (-1, 256, 1.5, True, None, '0', {}, []):
        ab25ao25Probe = copy.deepcopy(ab25ao25Control)
        ab25ao25Probe['fields']['fan'] = [ab25ao25Bad]
        ab25ao25Texts.append(json.dumps(ab25ao25Probe, separators=(',', ':')))
    for ab25ao25Key, ab25ao25Bad in (
        ('context', None), ('context', []), ('fields', []), ('fields', None),
        ('arguments', None), ('arguments', []), ('arguments', {'enabled': True}),
    ):
        ab25ao25Probe = copy.deepcopy(ab25ao25Control)
        ab25ao25Probe[ab25ao25Key] = ab25ao25Bad
        ab25ao25Texts.append(json.dumps(ab25ao25Probe, separators=(',', ':')))
    for ab25ao25Key, ab25ao25Bad in (
        ('primary', True), ('secondary', '34'), ('operation', .5),
        ('operation', None), ('direction', 0), ('view', []),
    ):
        ab25ao25Probe = copy.deepcopy(ab25ao25Control)
        ab25ao25Probe['context'][ab25ao25Key] = ab25ao25Bad
        ab25ao25Texts.append(json.dumps(ab25ao25Probe, separators=(',', ':')))
    for ab25ao25Bad in (None, 0, '00', {}):
        ab25ao25Probe = copy.deepcopy(ab25ao25Control)
        ab25ao25Probe['fields']['fan'] = ab25ao25Bad
        ab25ao25Texts.append(json.dumps(ab25ao25Probe, separators=(',', ':')))
    for ab25ao25Operation in (1, 0):
        ab25ao25Probe = copy.deepcopy(ab25ao25Control)
        ab25ao25Probe['context']['operation'] = ab25ao25Operation
        ab25ao25Probe['fields']['unmodelled'] = [256]
        ab25ao25Texts.append(json.dumps(ab25ao25Probe, separators=(',', ':')))
    return [dict(id='ab25ao25-error-' + str(ab25ao25Index), input_json=ab25ao25Text,
                 error=True, successful_result=False)
            for ab25ao25Index, ab25ao25Text in enumerate(ab25ao25Texts)]


def ab25ao25Expected():
    return dict(id='ab25ao25-demand-views', provenance='synthetic',
                contract=ab25ao25Contract, cases=ab25ao25ExpectedCases(),
                errors=ab25ao25ExpectedErrors())


def ab25ao25Unique(ab25ao25Pairs):
    ab25ao25Object = {}
    for ab25ao25Key, ab25ao25Value in ab25ao25Pairs:
        if ab25ao25Key in ab25ao25Object:
            raise ValueError('duplicate key: ' + ab25ao25Key)
        ab25ao25Object[ab25ao25Key] = ab25ao25Value
    return ab25ao25Object


def ab25ao25ReadPage(ab25ao25Text):
    ab25ao25Blocks = re.findall(
        r'<!-- ab25ao25-contract-start -->\s*```json\n(.*?)\n```\s*'
        r'<!-- ab25ao25-contract-end -->', ab25ao25Text, re.S)
    if len(ab25ao25Blocks) != 1:
        raise ValueError('exactly one finite contract table required')
    return json.loads(ab25ao25Blocks[0], object_pairs_hook=ab25ao25Unique)


class TestAb25Ao25DemandViews(unittest.TestCase):
    def TestAb25Ao25PageContract(ab25ao25Self):
        ab25ao25Self.assertTrue(
            json.dumps(ab25ao25ReadPage(ab25ao25Page.read_text()), sort_keys=True, allow_nan=False) ==
            json.dumps(ab25ao25Expected(), sort_keys=True, allow_nan=False),
            'page finite table differs from independent constants')

    def TestAb25Ao25FixtureContract(ab25ao25Self):
        ab25ao25Self.assertTrue(
            json.dumps(json.loads(ab25ao25Fixture.read_text(), object_pairs_hook=ab25ao25Unique),
                       sort_keys=True, allow_nan=False) ==
            json.dumps(ab25ao25Expected(), sort_keys=True, allow_nan=False),
            'fixture finite table differs from independent constants')

    def TestAb25Ao25RenderedTables(ab25ao25Self):
        ab25ao25Tables = []
        for ab25ao25Block in ab25ao25Page.read_text().split('\n\n'):
            ab25ao25Lines = ab25ao25Block.splitlines()
            if ab25ao25Lines and all(ab25ao25Line.startswith('|') for ab25ao25Line in ab25ao25Lines):
                ab25ao25Tables.append([[ab25ao25Cell.strip() for ab25ao25Cell in
                                        ab25ao25Line.strip('|').split('|')]
                                       for ab25ao25Line in ab25ao25Lines])
        ab25ao25Self.assertEqual(ab25ao25Tables[0][0], ['Direction', 'Field', 'Width', 'Result', 'Grade'])
        ab25ao25Self.assertEqual(ab25ao25Tables[0][2:], [
            ['request', 'mode', '1', '0..4 labels below; 1 label-conflict; 5..255 unmapped', 'Hypothesis'],
            ['request', 'fan', '1', 'raw u8 number 0..255, no enum or clipping', 'Hypothesis; calculation Proven'],
            ['request', 'room_temperature', '1', 'u8 / 2 Celsius, 0..127.5; FF is 127.5', 'Hypothesis; calculation Proven'],
            ['request', 'automatic', '1', 'bit 0 disabled/enabled; reserved mask 254', 'Hypothesis'],
            ['positive', 'positive_flags', '1', 'three independent unnamed Booleans in bit order 0,1,2; reserved mask 248', 'Hypothesis'],
        ])
        ab25ao25Self.assertEqual(ab25ao25Tables[1][0], ['Mode', 'State', 'Candidate label'])
        ab25ao25Self.assertEqual(ab25ao25Tables[1][2:], [
            ['0', 'complete', ab25ao25Labels[0]], ['1', 'label-conflict', ab25ao25Labels[1]],
            ['2', 'complete', ab25ao25Labels[2]], ['3', 'complete', ab25ao25Labels[3]],
            ['4', 'complete', ab25ao25Labels[4]], ['5..255', 'unmapped', 'absent'],
        ])
        ab25ao25Self.assertEqual(len(ab25ao25Tables), 2)

    def TestAb25Ao25RoundTrips(ab25ao25Self):
        for ab25ao25Document in (ab25ao25ReadPage(ab25ao25Page.read_text()),
                                 json.loads(ab25ao25Fixture.read_text())):
            ab25ao25Self.assertTrue(json.loads(json.dumps(ab25ao25Document)) == ab25ao25Expected(),
                                     'round-trip finite table differs from independent constants')
            ab25ao25Cases = {ab25ao25Case['id']: ab25ao25Case for ab25ao25Case in ab25ao25Document['cases']}
            ab25ao25Self.assertNotIn('arguments', ab25ao25Cases['ab25ao25-fan-0']['output'])
            ab25ao25Self.assertEqual(ab25ao25Cases['ab25ao25-complete']['output']['arguments'], {})
            for ab25ao25Name in ('mode', 'fan', 'room_temperature', 'automatic'):
                ab25ao25Self.assertNotIn(ab25ao25Name, ab25ao25Cases['ab25ao25-' + ab25ao25Name + '-missing']['output']['fields'])
                ab25ao25Self.assertEqual(ab25ao25Cases['ab25ao25-' + ab25ao25Name + '-empty']['output']['fields'][ab25ao25Name]['raw'], [])
                ab25ao25Self.assertEqual(ab25ao25Cases['ab25ao25-' + ab25ao25Name + '-zero']['output']['fields'][ab25ao25Name]['raw'], [0])

    def TestAb25Ao25ExactArithmetic(ab25ao25Self):
        # Verify declared numeric examples using exact rational arithmetic only.
        for ab25ao25Document in (ab25ao25ReadPage(ab25ao25Page.read_text()),
                                 json.loads(ab25ao25Fixture.read_text())):
            ab25ao25Cases = {ab25ao25Case['id']: ab25ao25Case for ab25ao25Case in ab25ao25Document['cases']}
            for ab25ao25Byte, ab25ao25Twice in ((0, 0), (1, 1), (16, 16), (153, 153), (255, 255)):
                ab25ao25ResultValue = ab25ao25Cases['ab25ao25-room-' + str(ab25ao25Byte)]['output']['fields']['room_temperature']
                ab25ao25Self.assertEqual(ab25ao25ResultValue['number'] * 2, ab25ao25Twice)
                ab25ao25Self.assertEqual(ab25ao25ResultValue['grade'], 'Hypothesis')
                ab25ao25Self.assertEqual(ab25ao25ResultValue['calculation'], 'Proven')

    def TestAb25Ao25SelectionAxes(ab25ao25Self):
        for ab25ao25Document in (ab25ao25ReadPage(ab25ao25Page.read_text()),
                                 json.loads(ab25ao25Fixture.read_text())):
            ab25ao25Cases = {ab25ao25Case['id']: ab25ao25Case for ab25ao25Case in ab25ao25Document['cases']}
            ab25ao25Control = ab25ao25Cases['ab25ao25-complete']['input']['context']
            for ab25ao25Axis in ('primary', 'secondary', 'operation', 'direction', 'view'):
                ab25ao25Probe = ab25ao25Cases['ab25ao25-selection-' + ab25ao25Axis]
                ab25ao25Self.assertEqual([ab25ao25Key for ab25ao25Key in ab25ao25Control if
                                         ab25ao25Control[ab25ao25Key] != ab25ao25Probe['input']['context'][ab25ao25Key]], [ab25ao25Axis])
                ab25ao25Self.assertEqual(ab25ao25Probe['output']['state'], 'Unknown')
                ab25ao25Self.assertEqual(ab25ao25Probe['output']['raw'], ab25ao25FullFields)
                ab25ao25Self.assertEqual(ab25ao25Probe['output']['fields'], {})

    def TestAb25Ao25ContractMutations(ab25ao25Self):
        """Execute table mutations only; these are not production mutation kills."""
        ab25ao25ExpectedDocument = ab25ao25Expected()
        for ab25ao25Source in (ab25ao25ReadPage(ab25ao25Page.read_text()),
                               json.loads(ab25ao25Fixture.read_text())):
            ab25ao25Self.assertTrue(ab25ao25Source == ab25ao25ExpectedDocument,
                                     'mutation control differs from independent constants')
            for ab25ao25Id, ab25ao25FieldName, ab25ao25Key, ab25ao25Value in (
                ('mode-1', 'mode', 'state', 'complete'),
                ('room-153', 'room_temperature', 'number', 49.5),
                ('room-255', 'room_temperature', 'number', None),
                ('fan-255', 'fan', 'number', 3),
                ('positive-8', 'positive_flags', 'flags', [False, False, False, True]),
                ('mode-missing', 'mode', 'raw', [0]),
                ('room-1', 'room_temperature', 'grade', 'Proven'),
            ):
                ab25ao25Mutant = copy.deepcopy(ab25ao25Source)
                ab25ao25Case = next(ab25ao25Row for ab25ao25Row in ab25ao25Mutant['cases']
                                    if ab25ao25Row['id'] == 'ab25ao25-' + ab25ao25Id)
                ab25ao25Case['output']['fields'].setdefault(ab25ao25FieldName, {})[ab25ao25Key] = ab25ao25Value
                with ab25ao25Self.subTest(case=ab25ao25Id):
                    with ab25ao25Self.assertRaises(AssertionError):
                        ab25ao25Self.assertEqual(ab25ao25Mutant, ab25ao25ExpectedDocument)
            ab25ao25Mutant = copy.deepcopy(ab25ao25Source)
            ab25ao25Mutant['contract']['mode_1'].pop('competing_label')
            with ab25ao25Self.assertRaises(AssertionError):
                ab25ao25Self.assertEqual(ab25ao25Mutant, ab25ao25ExpectedDocument)
            ab25ao25Mutant = copy.deepcopy(ab25ao25Source)
            next(ab25ao25Row for ab25ao25Row in ab25ao25Mutant['cases'] if
                 ab25ao25Row['id'] == 'ab25ao25-cross-positive')['output']['fields'] = ab25ao25FullResults
            with ab25ao25Self.assertRaises(AssertionError):
                ab25ao25Self.assertEqual(ab25ao25Mutant, ab25ao25ExpectedDocument)


# unittest's documented loader hook preserves the requested TestAb25Ao25 names.
def load_tests(ab25ao25Loader, ab25ao25Tests, ab25ao25Pattern):
    ab25ao25DedicatedLoader = unittest.TestLoader()
    ab25ao25DedicatedLoader.testMethodPrefix = 'TestAb25Ao25'
    return ab25ao25DedicatedLoader.loadTestsFromTestCase(TestAb25Ao25DemandViews)
