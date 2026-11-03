"""Independent, bounded documentation oracles; no runtime API implementation."""
import copy
import json
import os
from pathlib import Path
import unittest

ab25ap25Root = Path(os.environ.get('ab25ap25_ROOT', Path(__file__).resolve().parents[1]))
ab25ap25Page = ab25ap25Root / 'architecture/ap26_b525_quality_config.md'
ab25ap25Fixture = ab25ap25Root / 'architecture/fixtures/ap26_b525_quality_config.json'


def ab25ap25Pairs(ab25ap25PairsInput):
    ab25ap25Object = {}
    for ab25ap25Key, ab25ap25Value in ab25ap25PairsInput:
        if ab25ap25Key in ab25ap25Object:
            raise ValueError('duplicate key')
        ab25ap25Object[ab25ap25Key] = ab25ap25Value
    return ab25ap25Object


def ab25ap25RejectConstant(ab25ap25Value):
    raise ValueError('non-finite JSON')


def ab25ap25Admit(ab25ap25Text):
    """Test-only JSON admission predicate, independent of any Go decoder."""
    ab25ap25Input = json.loads(ab25ap25Text, object_pairs_hook=ab25ap25Pairs,
                              parse_constant=ab25ap25RejectConstant)
    if type(ab25ap25Input) is not dict:
        raise ValueError('object required')
    for ab25ap25Key in ('context', 'fields'):
        if type(ab25ap25Input.get(ab25ap25Key)) is not dict:
            raise ValueError('object required')
    if 'arguments' in ab25ap25Input and type(ab25ap25Input['arguments']) is not dict:
        raise ValueError('arguments object required')
    for ab25ap25Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab25ap25Value = ab25ap25Input['context'].get(ab25ap25Key)
        ab25ap25Type = int if ab25ap25Key in ('primary', 'secondary', 'operation') else str
        if ab25ap25Value is not None and type(ab25ap25Value) is not ab25ap25Type:
            raise ValueError('selector kind')
    for ab25ap25Value in ab25ap25Input['fields'].values():
        if type(ab25ap25Value) is not list or any(
            type(ab25ap25Byte) is not int or not 0 <= ab25ap25Byte <= 255
            for ab25ap25Byte in ab25ap25Value
        ):
            raise ValueError('byte array required')
    return ab25ap25Input


def ab25ap25Expected(ab25ap25Input):
    """Bounded transition oracle for fixture results, never an exported evaluator."""
    ab25ap25Context = ab25ap25Input['context']
    ab25ap25Raw = ab25ap25Input['fields']
    ab25ap25Output = {'context': copy.deepcopy(ab25ap25Context),
                     'raw': copy.deepcopy(ab25ap25Raw), 'state': 'Unknown',
                     'fields': {}, 'physical': 'Unknown', 'qualified': False}
    if 'arguments' in ab25ap25Input:
        ab25ap25Output['arguments'] = copy.deepcopy(ab25ap25Input['arguments'])
    ab25ap25Identity = tuple(ab25ap25Context.get(ab25ap25Key) for ab25ap25Key in
                            ('primary', 'secondary', 'operation', 'direction', 'view'))
    ab25ap25Allowed = {(181, 37, 3, 'positive', 'quality')}
    ab25ap25Allowed.update((181, 37, ab25ap25Op, ab25ap25Direction, 'configuration')
                          for ab25ap25Op in (24, 25, 26, 27)
                          for ab25ap25Direction in ('request', 'positive'))
    if ab25ap25Identity not in ab25ap25Allowed:
        return ab25ap25Output
    ab25ap25Names = ('rssi', 'quality') if ab25ap25Identity[-1] == 'quality' else ('configuration', 'data')
    ab25ap25Output['state'] = 'complete'
    for ab25ap25Name in ab25ap25Names:
        ab25ap25Field = {'state': 'incomplete', 'grade': 'Hypothesis'}
        ab25ap25Output['fields'][ab25ap25Name] = ab25ap25Field
        if ab25ap25Name in ab25ap25Raw:
            ab25ap25Field['raw'] = copy.deepcopy(ab25ap25Raw[ab25ap25Name])
        if ab25ap25Name not in ab25ap25Raw or (
            ab25ap25Name != 'data' and len(ab25ap25Raw[ab25ap25Name]) != 1
        ):
            ab25ap25Output['state'] = 'partial'
            continue
        ab25ap25Field['state'] = 'complete'
        if ab25ap25Name == 'data':
            ab25ap25Field['value'] = copy.deepcopy(ab25ap25Raw[ab25ap25Name])
            continue
        ab25ap25Byte = ab25ap25Raw[ab25ap25Name][0]
        ab25ap25Field['calculation'] = 'Proven'
        if ab25ap25Name == 'rssi':
            ab25ap25Field.update(number=(ab25ap25Byte + 128) % 256 - 128, unit='Unknown')
        elif ab25ap25Name == 'quality':
            ab25ap25Field['flags'] = {
                'bit' + str(ab25ap25Bit): bool((ab25ap25Byte // (2 ** ab25ap25Bit)) % 2)
                for ab25ap25Bit in range(7)}
            ab25ap25Field['flags']['crc_okay'] = ab25ap25Byte >= 128
            ab25ap25Field['verified_crc'] = False
        else:
            ab25ap25Field.update(flags={'read_write': ab25ap25Byte % 2 == 1},
                                unmodeled=ab25ap25Byte - ab25ap25Byte % 2, default_read=0)
    return ab25ap25Output


def ab25ap25Table(ab25ap25Text, ab25ap25Header):
    ab25ap25Tail = ab25ap25Text.split(ab25ap25Header + '\n', 1)[1].splitlines()[1:]
    ab25ap25Rows = []
    for ab25ap25Line in ab25ap25Tail:
        if not ab25ap25Line.startswith('|'):
            break
        ab25ap25Rows.append(tuple(ab25ap25Cell.strip() for ab25ap25Cell in ab25ap25Line.strip('|').split('|')))
    return ab25ap25Rows


class Ab25Ap25Contract(unittest.TestCase):
    def setUp(self):
        self.ab25ap25Document = ab25ap25Page.read_text()
        self.ab25ap25Cases = json.loads(ab25ap25Fixture.read_text())
        self.ab25ap25ById = {ab25ap25Case['id']: ab25ap25Case for ab25ap25Case in self.ab25ap25Cases['cases']}

    def test_ab25ap25_page_tables_and_signature(self):
        self.assertEqual(self.ab25ap25Document.split('```go\n')[1].split('\n```')[0],
                         'func Ab25Ap25Evaluate(ab25ap25Input json.RawMessage) (json.RawMessage, error)')
        self.assertEqual(ab25ap25Table(self.ab25ap25Document, '| primary | secondary | operation | direction | view |'),
                         [('181', '37', '3', 'positive', 'quality')] +
                         [('181', '37', str(ab25ap25Op), ab25ap25Direction, 'configuration')
                          for ab25ap25Op in (24, 25, 26, 27) for ab25ap25Direction in ('request', 'positive')])
        self.assertEqual(ab25ap25Table(self.ab25ap25Document, '| field | length | formula | metadata |'), [
            ('rssi', '1', 'b if b < 128 else b - 256', 'number; unit=Unknown; grade=Hypothesis; calculation=Proven'),
            ('quality', '1', 'bit_i = bool(b & (1 << i)), i=0..6; crc_okay = bool(b & 128)', 'flags; verified_crc=false; grade=Hypothesis; calculation=Proven'),
            ('configuration', '1', 'read_write = bool(b & 1); unmodeled = b & 254', 'default_read=0; grade=Hypothesis; calculation=Proven'),
            ('data', '0..unspecified', 'copy every byte in order', 'opaque; grade=Hypothesis')])
        self.assertEqual(ab25ap25Table(self.ab25ap25Document, '| condition | result state | semantic behavior |'), [
            ('supported; all required fields complete', 'complete', 'all independent results retained'),
            ('supported; any required field absent or wrong length', 'partial', 'incomplete field retained; complete siblings retained'),
            ('unsupported selector', 'Unknown', 'raw-only; no formulas'),
            ('malformed JSON; duplicate key anywhere; wrong kind; fractional or out-of-range byte', 'error', 'error and no successful result')])

        self.assertEqual(ab25ap25Table(self.ab25ap25Document, '| member or condition | kind or policy | preservation |'), [
            ('input', 'object', 'context and fields required'),
            ('context', 'object', 'unchanged; absent/null/zero distinct'),
            ('fields', 'object of byte arrays', 'raw deep copy; unknown names retained'),
            ('arguments', 'optional object; no typed members in these views', 'unchanged when supplied; unknown extra keys retained'),
            ('output', 'object', 'context, raw, state, fields, physical, qualified; optional arguments'),
            ('physical', 'string', 'Unknown'), ('qualified', 'Boolean', 'false'),
            ('candidate grade', 'string', 'Hypothesis'),
            ('arithmetic calculation', 'string', 'Proven; never replaces grade'),
            ('incomplete field', 'object', 'raw if present; state=incomplete; grade=Hypothesis; no number or label'),
            ('duplicate keys', 'reject at every nesting depth', 'error; no successful result'),
            ('byte kind', 'integer 0..255; Boolean excluded', 'reject null/string/fraction/out-of-range'),
            ('selector kind', 'integer primary/secondary/operation; string direction/view', 'absent/null unsupported; wrong kinds error'),
            ('storage', 'independent input/output/raw/semantic/call copies', 'nested mutation never propagates'),
            ('validation precedence', 'admission before selector dispatch', 'invalid bytes error even for unsupported selector')])

    def test_ab25ap25_all_scenario_transitions(self):
        self.assertGreaterEqual(len(self.ab25ap25ById), 80)
        self.assertEqual(len(self.ab25ap25ById), len(self.ab25ap25Cases['cases']))
        for ab25ap25Case in self.ab25ap25Cases['cases']:
            with self.subTest(ab25ap25Case=ab25ap25Case['id']):
                ab25ap25Input = ab25ap25Admit(json.dumps(ab25ap25Case['input']))
                self.assertEqual(ab25ap25Case['expected'], ab25ap25Expected(ab25ap25Input))
                self.assertEqual(json.loads(json.dumps(ab25ap25Case)), ab25ap25Case)

    def test_ab25ap25_independent_numeric_controls(self):
        for ab25ap25Byte, ab25ap25Number in ((255, -1), (128, -128), (127, 127)):
            ab25ap25Field = self.ab25ap25ById[f'ab25ap25_rssi_{ab25ap25Byte}']['expected']['fields']['rssi']
            self.assertEqual((ab25ap25Field['number'], ab25ap25Field['unit']), (ab25ap25Number, 'Unknown'))
        for ab25ap25Bit in range(8):
            ab25ap25Field = self.ab25ap25ById[f'ab25ap25_quality_{ab25ap25Bit}']['expected']['fields']['quality']
            self.assertEqual(ab25ap25Field['flags'], dict(zip(
                ('bit0', 'bit1', 'bit2', 'bit3', 'bit4', 'bit5', 'bit6', 'crc_okay'),
                [ab25ap25Index == ab25ap25Bit for ab25ap25Index in range(8)])))
            self.assertIs(ab25ap25Field['verified_crc'], False)
            self.assertNotIn('number', ab25ap25Field)
        for ab25ap25Byte, ab25ap25Choice, ab25ap25High in ((129, True, 128), (0, False, 0)):
            ab25ap25Field = self.ab25ap25ById[f'ab25ap25_configuration_{ab25ap25Byte}']['expected']['fields']['configuration']
            self.assertEqual(ab25ap25Field['flags'], {'read_write': ab25ap25Choice})
            self.assertEqual((ab25ap25Field['unmodeled'], ab25ap25Field['default_read']), (ab25ap25High, 0))

    def test_ab25ap25_operation_direction_data_product(self):
        for ab25ap25Op in (24, 25, 26, 27):
            for ab25ap25Direction in ('request', 'positive'):
                for ab25ap25Mode, ab25ap25Data in (('bytes', [0, 170, 255]), ('empty', []), ('missing', None)):
                    ab25ap25Case = self.ab25ap25ById[f'ab25ap25_config_{ab25ap25Op}_{ab25ap25Direction}_{ab25ap25Mode}']
                    ab25ap25Output = ab25ap25Case['expected']
                    self.assertEqual(ab25ap25Output['context'], dict(primary=181, secondary=37,
                        operation=ab25ap25Op, direction=ab25ap25Direction, view='configuration', family='synthetic-family', variant='synthetic-variant'))
                    self.assertEqual(ab25ap25Output['state'], 'partial' if ab25ap25Data is None else 'complete')
                    self.assertEqual(ab25ap25Output['fields']['configuration']['state'], 'complete')
                    if ab25ap25Data is None:
                        self.assertNotIn('data', ab25ap25Output['raw'])
                        self.assertNotIn('value', ab25ap25Output['fields']['data'])
                    else:
                        self.assertEqual(ab25ap25Output['fields']['data']['value'], ab25ap25Data)

    def test_ab25ap25_identity_axes_and_presence(self):
        for ab25ap25Key in ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant'):
            for ab25ap25Mode in ('alternate', 'absent', 'null'):
                ab25ap25Case = self.ab25ap25ById[f'ab25ap25_context_{ab25ap25Key}_{ab25ap25Mode}']
                ab25ap25Context = dict(primary=181, secondary=37, operation=3, direction='positive',
                                       view='quality', family='synthetic-family', variant='synthetic-variant')
                if ab25ap25Mode == 'absent':
                    del ab25ap25Context[ab25ap25Key]
                else:
                    ab25ap25Context[ab25ap25Key] = None if ab25ap25Mode == 'null' else (
                        0 if ab25ap25Key in ('primary', 'secondary', 'operation') else 'synthetic-other')
                self.assertEqual(ab25ap25Case['input'], dict(context=ab25ap25Context, fields=dict(rssi=[255], quality=[0])))
                self.assertEqual(ab25ap25Case['expected']['context'], ab25ap25Context)
                self.assertEqual(ab25ap25Case['expected']['state'], 'complete' if ab25ap25Key in ('family', 'variant') else 'Unknown')
                self.assertIs(ab25ap25Case['expected']['qualified'], False)
        for ab25ap25Name in ('rssi', 'quality', 'configuration'):
            for ab25ap25Mode in ('absent', 'empty', 'overlong', 'zero'):
                ab25ap25Case = self.ab25ap25ById[f'ab25ap25_field_{ab25ap25Name}_{ab25ap25Mode}']
                ab25ap25Output = ab25ap25Case['expected']
                self.assertEqual(ab25ap25Output['state'], 'complete' if ab25ap25Mode == 'zero' else 'partial')
                for ab25ap25Sibling in set(ab25ap25Output['fields']) - {ab25ap25Name}:
                    self.assertEqual(ab25ap25Output['fields'][ab25ap25Sibling]['state'], 'complete')
        for ab25ap25Mode, ab25ap25Value in (('absent', None), ('empty', {}), ('zero', {'opaque': 0}),
                ('false', {'opaque': False}), ('null', {'opaque': None}), ('array', {'opaque': []}),
                ('nested', {'opaque': {'items': [0, False, None]}})):
            ab25ap25Output = self.ab25ap25ById[f'ab25ap25_arguments_{ab25ap25Mode}']['expected']
            self.assertEqual('arguments' in ab25ap25Output, ab25ap25Mode != 'absent')
            if ab25ap25Mode != 'absent':
                self.assertEqual(ab25ap25Output['arguments'], ab25ap25Value)

    def test_ab25ap25_rejection_cases(self):
        self.assertGreaterEqual(len(self.ab25ap25Cases['rejected']), 25)
        for ab25ap25Case in self.ab25ap25Cases['rejected']:
            with self.subTest(ab25ap25Case=ab25ap25Case['id']):
                with self.assertRaises((ValueError, TypeError)):
                    ab25ap25Admit(ab25ap25Case['json'])
        # Valid controls distinguish admission from scalar-length completeness.
        for ab25ap25Case in self.ab25ap25Cases['cases']:
            ab25ap25Admit(json.dumps(ab25ap25Case['input']))

    def test_ab25ap25_nested_copy_oracle_and_fixture_independence(self):
        ab25ap25Input = copy.deepcopy(self.ab25ap25ById['ab25ap25_copy']['input'])
        ab25ap25Baseline = copy.deepcopy(ab25ap25Input)
        ab25ap25First = ab25ap25Expected(ab25ap25Input)
        ab25ap25Second = ab25ap25Expected(ab25ap25Input)
        ab25ap25Input['context']['opaque']['items'][0] = 99
        ab25ap25Input['fields']['data'][0] = 99
        ab25ap25Input['arguments']['opaque']['items'][0] = 99
        self.assertEqual(ab25ap25First, ab25ap25Second)
        ab25ap25First['context']['opaque']['items'][0] = 88
        ab25ap25First['arguments']['opaque']['items'][0] = 88
        ab25ap25First['raw']['data'][0] = 88
        self.assertEqual(ab25ap25First['fields']['data']['value'], [0, 170, 255])
        ab25ap25First['fields']['data']['value'][0] = 77
        self.assertEqual(ab25ap25First['fields']['data']['raw'], [0, 170, 255])
        ab25ap25First['fields']['configuration']['flags']['read_write'] = False
        self.assertEqual(ab25ap25Second, ab25ap25Expected(ab25ap25Baseline))
        self.assertEqual(self.ab25ap25ById['ab25ap25_copy']['expected'], ab25ap25Second)
