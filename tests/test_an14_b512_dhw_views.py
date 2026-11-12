"""Synthetic AN14 B512 OP06 logical-image contract. Not a native codec.

Each identity axis names the production mutation its assertion catches:
family — caller family dropped or replaced by a constant;
variant — caller variant dropped or replaced by a constant;
direction — request and positive layouts swapped;
prefix position 0 — typed values attached when the first byte is not 181;
prefix position 1 — typed values attached when the second byte is not 18;
prefix position 2 — typed values attached when the third byte is not 6;
length — missing cells filled from declared defaults.
"""
import copy
from fractions import Fraction
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/an14-b512-dhw-views.md'
FIXTURE = ROOT / 'architecture/fixtures/an14_b512_dhw_views.json'
PREFIX = (181, 18, 6)
REQUEST_LAST = 9
POSITIVE_LAST = 6
REQUEST_BITS = (
    (0, 'task_active', 'task_active', 'Hypothesis'),
    (1, 'heat_demand', 'heat_demand', 'Hypothesis'),
    (2, 'loading_active', 'loading_active', 'Hypothesis'),
    (3, 'loading_pump_fault', 'loading_pump_fault', 'Hypothesis'),
    (4, 'unnamed_sensor_condition_4', None, 'Unknown'),
    (5, 'unnamed_sensor_condition_5', None, 'Unknown'),
    (6, 'unnamed_sensor_condition_6', None, 'Unknown'),
    (7, 'unnamed_sensor_condition_7', None, 'Unknown'),
)
INLET_BITS = (
    (0, 'unnamed_inlet_condition_0', None, 'Unknown'),
    (1, 'unnamed_inlet_condition_1', None, 'Unknown'),
)
POSITIVE_BITS = (
    (0, 'loading_disabled', 'loading_disabled', 'Hypothesis'),
    (1, 'internal_test_active', 'internal_test_active', 'Hypothesis'),
    (2, 'ready', 'ready', 'Hypothesis'),
    (3, 'frost_protection_active', 'frost_protection_active', 'Hypothesis'),
    (4, 'legionella_demand', 'legionella_demand', 'Hypothesis'),
    (5, 'reset', 'reset', 'Hypothesis'),
)
ADJUSTMENT_LABELS = {
    -1: 'at_minimum',
    0: 'in_range',
    1: 'at_maximum',
    2: 'modulation_regulator_not_active',
}
QUALIFICATION = {
    'physical': 'Unknown',
    'presence': 'Unknown',
    'freshness': 'Unknown',
    'execution': 'Unknown',
    'support': 'Unknown',
    'family_inference': 'Unknown',
    'physical_adaptation': 'Unknown',
    'requested_versus_actual': 'Unknown',
}
REQUEST_KEYS = frozenset(
    [item[1] for item in REQUEST_BITS] + [item[1] for item in INLET_BITS] + [
        'modulation', 'dhw_water_flow', 'temperature_logical6',
        'temperature_logical7', 'temperature_logical8'])
POSITIVE_KEYS = frozenset(
    [item[1] for item in POSITIVE_BITS] + [
        'dhw_setpoint', 'return_temperature', 'adjustment'])
FIELD_KEYS = frozenset({
    'key', 'position', 'bit', 'raw', 'numeric', 'value', 'scale', 'unit',
    'quantity', 'formal_unit', 'unit_conflict', 'semantic_label', 'unlabelled',
    'numeric_grade', 'semantic_grade', 'native_grade'})
RESULT_KEYS = frozenset({
    'context', 'raw_cells', 'prefix_ok', 'admission', 'reason', 'fields',
    'partial', 'extra', 'qualification'})


def _bit(bit, key, label, grade):
    return {'bit': bit, 'key': key, 'semantic_label': label, 'semantic_grade': grade}


def _scalar(position, key, scale, divisor, unit, unit_conflict=False,
            formal_unit=None, quantity=None):
    return {
        'position': position, 'key': key, 'scale': scale, 'divisor': divisor,
        'quantity': quantity or key, 'unit': unit, 'formal_unit': formal_unit,
        'unit_conflict': unit_conflict, 'semantic_grade': 'Hypothesis',
    }


POLICY = {
    'signature': 'interpret_b512_op06_fields(context, logical_image)',
    'context_fields': ['family', 'variant', 'direction'],
    'directions': ['request', 'positive'],
    'prefix': [181, 18, 6],
    'request_last_position': REQUEST_LAST,
    'positive_last_position': POSITIVE_LAST,
    'require_prefix': True,
    'preserve_reserved_raw': True,
    'preserve_unmodelled': True,
    'materialize_missing': False,
    'admit_any_nonempty_family': True,
    'admit_any_nonempty_variant': True,
    'infer_family': False,
    'flow_divisor': 10,
    'modulation_divisor': 2,
    'temperature_divisor': 2,
    'modulation_formal_unit': 'celsius',
    'modulation_unit_conflict': True,
    'adjustment_codec': 'signed8',
    'adjustment_named_domain': [-1, 0, 1, 2],
    'adjustment_labels': {
        '-1': 'at_minimum', '0': 'in_range', '1': 'at_maximum',
        '2': 'modulation_regulator_not_active'},
    'unlabelled_semantic_grade': 'Unknown',
    'defaults_metadata': {'bits': False, 'adjustment': -1},
    'native_grade': 'Unknown',
    'software_contract': 'Proven',
    'layout_grade': 'Hypothesis',
    'example_families': ['synthetic-dhw-family-a', 'synthetic-dhw-family-b'],
    'example_variants': ['synthetic-variant-a', 'synthetic-variant-b'],
    'request_bits': [_bit(*item) for item in REQUEST_BITS],
    'request_inlet_bits': [_bit(*item) for item in INLET_BITS],
    'request_reserved_bits': [2, 3, 4, 5, 6, 7],
    'positive_bits': [_bit(*item) for item in POSITIVE_BITS],
    'positive_reserved_bits': [6, 7],
    'request_scalars': [
        _scalar(4, 'modulation', 'u8/2', 2, 'celsius', True, 'celsius'),
        _scalar(5, 'dhw_water_flow', 'u8/10', 10, 'litres_per_minute'),
        _scalar(6, 'temperature_logical6', 'u8/2', 2, 'celsius'),
        _scalar(7, 'temperature_logical7', 'u8/2', 2, 'celsius'),
        _scalar(8, 'temperature_logical8', 'u8/2', 2, 'celsius'),
    ],
    'positive_scalars': [
        _scalar(4, 'dhw_setpoint', 'u8/2', 2, 'celsius'),
        _scalar(5, 'return_temperature', 'u8/2', 2, 'celsius'),
        {'position': 6, 'key': 'adjustment', 'scale': 'signed8',
         'named_domain': [-1, 0, 1, 2], 'semantic_grade': 'Hypothesis'},
    ],
}
REQUEST_BIT_ROWS = tuple(
    (str(bit), key, label or 'none', grade)
    for bit, key, label, grade in REQUEST_BITS)
INLET_ROWS = tuple(
    (str(bit), key, 'none', grade) for bit, key, label, grade in INLET_BITS)
POSITIVE_BIT_ROWS = tuple(
    (str(bit), key, label, grade) for bit, key, label, grade in POSITIVE_BITS)
SCALAR_ROWS = (
    ('request', '4', 'modulation', 'u8/2', 'conflict celsius'),
    ('request', '5', 'dhw_water_flow', 'u8/10', 'litres_per_minute'),
    ('request', '6', 'temperature_logical6', 'u8/2', 'celsius'),
    ('request', '7', 'temperature_logical7', 'u8/2', 'celsius'),
    ('request', '8', 'temperature_logical8', 'u8/2', 'celsius'),
    ('positive', '4', 'dhw_setpoint', 'u8/2', 'celsius'),
    ('positive', '5', 'return_temperature', 'u8/2', 'celsius'),
    ('positive', '6', 'adjustment', 'signed8', 'named domain -1 0 1 2'),
)
CONTROL_ROWS = (
    ('request_all_zero', 'scalars 0 and modulation unit_conflict'),
    ('positive_all_zero', 'adjustment 0 not -1'),
    ('request_scalar_01', 'modulation 0.5 unit_conflict, flow 0.1, temperatures 0.5'),
    ('positive_adjustment_ff', 'adjustment -1'),
    ('positive_adjustment_02', 'adjustment 2'),
    ('positive_adjustment_03', 'adjustment 3 unlabelled'),
    ('request_through_logical6', 'temperature_logical6 0.5 and later temperatures absent'),
    ('positive_missing_logical6', 'adjustment absent'),
)
REQUIRED_SENTENCES = (
    'This page specifies the pure helper interpret_b512_op06_fields(context, logical_image).',
    'The hypothetical signature is the ab13/an13 helper API.',
    'AN14 is the ordinary companion of the AN13 helper description and does not depend on production code.',
    'Inputs are caller-selected logical images, not physical packets.',
    'Positions 0, 1 and 2 must be 181, 18 and 6 before any typed value is attached.',
    'Request fields use positions through 9. Positive fields use positions through 6.',
    'Logical 3 request bits 0..3 are task-active, heat-demand, loading-active and loading-pump-fault.',
    'Request bits 4..7 are four independent unnamed sensor-condition bits and acquire no semantic label.',
    'Logical 4 is u8/2 modulation with formal unit celsius and unit_conflict true.',
    'Logical 5 is u8/10 litres per minute.',
    'Logical 6, 7 and 8 are u8/2 degrees Celsius.',
    'Logical 9 bits 0 and 1 are two distinct unnamed inlet-condition flags. Bits 2..7 are reserved.',
    'Positive logical 3 bits 0..5 are loading-disabled, internal-test-active, ready, frost-protection-active, legionella-demand and reset. Bits 6 and 7 are reserved.',
    'Positive logical 4 and 5 are DHW setpoint and return temperature as u8/2 celsius.',
    'Positive logical 6 is signed8 adjustment with named numeric domain -1, 0, 1 and 2. Every other raw adjustment value stays unlabelled.',
    'Declared defaults of false and adjustment -1 are metadata and are not materialized for missing cells.',
    'A present positive adjustment byte 0 is numeric 0 and stays distinct from the metadata default -1.',
    'A request whose cells stop at logical 6 keeps temperature_logical6 and omits later temperatures and inlet flags.',
    'A positive image that omits logical 6 does not create adjustment -1.',
    'Request bytes 1 at logical 4..8 yield modulation 0.5 with unit_conflict, flow 0.1 and temperatures 0.5.',
    'Positive adjustment byte 255 is -1, byte 2 is 2, and byte 3 is unlabelled.',
    'Reserved bit changes remain in the raw cell.',
    'Bytes past the direction window stay raw and unmodelled and are not decoded with the other direction.',
    'Family and candidate variant are explicit caller selections and are not inferred.',
    'Malformed context is reported before a prefix failure. prefix_ok remains an independent boolean.',
    'Native qualification, physical adaptation, requested-versus-actual actuation and support are Unknown.',
    'Physical qualification, presence, freshness and execution stay Unknown on every result, including a fully decoded image.',
    'The helper does not send, poll, open a control path, or mutate a status cache.',
    'Partial results keep raw cells and independently decoded fields and do not replace last-known-good state.',
    'Admission is fail closed.',
    'eBUS MCP compatibility and GraphQL parity are unchanged.',
    'Nothing in this contract is stable before Helianthus 1.0.',
    'These examples are synthetic and do not qualify a physical device.',
    'The public native B512 contract comes first. Its OP06 rows are candidate layouts and are unconfirmed on the wire. This page does not add native qualification.',
)
FORBIDDEN = (
    'divide flow by 2',
    'flow_sensor_fault',
    'adjustment_codec": "uint8"',
    'materialize_missing": true',
    'require_prefix": false',
    'preserve_reserved_raw": false',
)
HEADINGS = {
    '### Request logical 3 bits': REQUEST_BIT_ROWS,
    '### Request logical 9 inlet bits': INLET_ROWS,
    '### Positive logical 3 bits': POSITIVE_BIT_ROWS,
    '### Scalar cells': SCALAR_ROWS,
    '### Control outcomes': CONTROL_ROWS,
}


def ctx(direction='request', family='synthetic-dhw-family-a',
        variant='synthetic-variant-a'):
    return {'family': family, 'variant': variant, 'direction': direction}


def _window(length, position, value):
    image = [181, 18, 6] + [0] * (length - 3)
    image[position] = value
    return image


def case_inputs():
    """Finite synthetic inputs. Expected results are published in the fixture."""
    rows = []

    def add(name, context, image, error=False):
        rows.append({'name': name, 'context': context, 'image': image,
                     'error': error})

    add('request_all_zero', ctx(), _window(10, 3, 0))
    add('positive_all_zero', ctx('positive'), _window(7, 3, 0))
    for bit in range(8):
        add('request_bit_%d' % bit, ctx(), _window(10, 3, 1 << bit))
    for bit in range(2):
        add('request_inlet_bit_%d' % bit, ctx(), _window(10, 9, 1 << bit))
    for bit in range(2, 8):
        add('request_reserved_bit_%d' % bit, ctx(), _window(10, 9, 1 << bit))
    for bit in range(6):
        add('positive_bit_%d' % bit, ctx('positive'), _window(7, 3, 1 << bit))
    for bit in (6, 7):
        add('positive_reserved_bit_%d' % bit, ctx('positive'),
            _window(7, 3, 1 << bit))
    add('request_scalar_01', ctx(), [181, 18, 6, 0, 1, 1, 1, 1, 1, 0])
    add('request_modulation_only', ctx(), _window(10, 4, 1))
    add('request_flow_only', ctx(), _window(10, 5, 1))
    add('request_temperature6_only', ctx(), _window(10, 6, 1))
    add('request_temperature7_only', ctx(), _window(10, 7, 1))
    add('request_temperature8_only', ctx(), _window(10, 8, 1))
    add('positive_setpoint_only', ctx('positive'), _window(7, 4, 1))
    add('positive_return_only', ctx('positive'), _window(7, 5, 1))
    add('positive_adjustment_ff', ctx('positive'), _window(7, 6, 255))
    add('positive_adjustment_02', ctx('positive'), _window(7, 6, 2))
    add('positive_adjustment_03', ctx('positive'), _window(7, 6, 3))
    add('positive_adjustment_00', ctx('positive'), _window(7, 6, 0))
    add('positive_adjustment_01', ctx('positive'), _window(7, 6, 1))
    add('positive_adjustment_80', ctx('positive'), _window(7, 6, 128))
    add('positive_adjustment_7f', ctx('positive'), _window(7, 6, 127))
    add('request_through_logical6', ctx(), [181, 18, 6, 0, 0, 0, 1])
    add('positive_missing_logical6', ctx('positive'), [181, 18, 6, 0, 0, 0])
    add('request_hole_logical7', ctx(),
        [181, 18, 6, 0, 0, 0, 1, None, 0, 0])
    add('request_unmodelled_logical4', ctx(),
        [181, 18, 6, 0, {'raw': 1, 'modelled': False}, 1, 0, 0, 0, 0])
    add('request_extra_position10', ctx(), _window(10, 3, 0) + [171])
    add('request_family_b', ctx(family='synthetic-dhw-family-b'), _window(10, 3, 0))
    add('request_variant_b', ctx(variant='synthetic-variant-b'), _window(10, 3, 0))
    add('request_family_c', ctx(family='synthetic-dhw-family-c'), _window(10, 3, 0))
    add('request_variant_c', ctx(variant='synthetic-variant-c'), _window(10, 3, 0))
    add('positive_direction_on_long_zero', ctx('positive'), _window(10, 3, 0))
    add('request_direction_on_short_zero', ctx(), _window(7, 3, 0))
    scalar = [181, 18, 6, 0, 1, 1, 1, 1, 1, 0]
    for index, bad in ((0, 180), (1, 17), (2, 5)):
        image = list(scalar)
        image[index] = bad
        add('prefix_position%d_mismatch' % index, ctx(), image)
    for index in range(3):
        image = list(scalar)
        image[index] = None
        add('prefix_position%d_missing' % index, ctx(), image)
    add('length_0', ctx(), [])
    add('length_1', ctx(), [181])
    add('length_2', ctx(), [181, 18])
    add('length_3', ctx(), [181, 18, 6])
    add('length_4', ctx(), [181, 18, 6, 0])
    add('missing_family', {'variant': 'synthetic-variant-a', 'direction': 'request'},
        list(scalar))
    add('empty_family', ctx(family=''), list(scalar))
    add('missing_variant', {'family': 'synthetic-dhw-family-a', 'direction': 'request'},
        list(scalar))
    add('empty_variant', ctx(variant=''), list(scalar))
    add('variant_integer_zero',
        {'family': 'synthetic-dhw-family-a', 'variant': 0, 'direction': 'request'},
        list(scalar))
    add('family_integer_zero',
        {'family': 0, 'variant': 'synthetic-variant-a', 'direction': 'request'},
        list(scalar))
    add('missing_direction',
        {'family': 'synthetic-dhw-family-a', 'variant': 'synthetic-variant-a'},
        list(scalar))
    add('direction_reply', ctx(direction='reply'), list(scalar))
    add('direction_integer_zero',
        {'family': 'synthetic-dhw-family-a', 'variant': 'synthetic-variant-a',
         'direction': 0}, list(scalar))
    add('empty_family_bad_prefix', ctx(family=''), [0, 0, 0])
    add('image_unicode', ctx(), 'synthetic', error=True)
    add('image_integer', ctx(), 181, error=True)
    add('context_list', [], [181, 18, 6], error=True)
    add('bool_cell', ctx(), [181, 18, 6, True], error=True)
    add('cell_out_of_range', ctx(), [181, 18, 6, 256], error=True)
    add('negative_cell', ctx(), [181, 18, 6, -1], error=True)
    return rows


REQUIRED_NAMES = tuple(row['name'] for row in case_inputs())


def parse_image(image):
    if isinstance(image, memoryview):
        image = image.tobytes()
    if isinstance(image, (bytes, bytearray)):
        return [{'state': 'present', 'raw': byte, 'modelled': True} for byte in image]
    if type(image) not in (list, tuple):
        raise TypeError('logical image')
    return [_parse_cell(item) for item in image]


def _parse_cell(item):
    if item is None:
        return {'state': 'missing', 'raw': None, 'modelled': False}
    if type(item) is int and 0 <= item <= 255:
        return {'state': 'present', 'raw': item, 'modelled': True}
    if (type(item) is dict and set(item) == {'raw', 'modelled'}
            and item['modelled'] is False and type(item['raw']) is int
            and 0 <= item['raw'] <= 255):
        return {'state': 'unmodelled', 'raw': item['raw'], 'modelled': False}
    raise TypeError('logical image cell')


def _context_gate(context):
    if type(context) is not dict:
        raise TypeError('context')
    copied = copy.deepcopy(context)
    family = copied.get('family')
    variant = copied.get('variant')
    if 'family' not in copied or type(family) is not str or family == '':
        return copied, 'context'
    if 'variant' not in copied or type(variant) is not str or variant == '':
        return copied, 'context'
    if 'direction' not in copied or type(copied.get('direction')) is not str:
        return copied, 'context'
    if copied['direction'] not in ('request', 'positive'):
        return copied, 'direction'
    return copied, None


def _prefix_ok(cells):
    if len(cells) < 3:
        return False
    return all(cells[index]['state'] == 'present' and cells[index]['raw'] == expected
               for index, expected in enumerate(PREFIX))


def _ratio(raw, divisor):
    value = Fraction(int(raw), int(divisor))
    negative = value < 0
    value = abs(value)
    whole = value.numerator // value.denominator
    remainder = value.numerator % value.denominator
    if remainder == 0:
        text = str(whole)
    else:
        digits = []
        while remainder and len(digits) < 20:
            remainder *= 10
            digits.append(str(remainder // value.denominator))
            remainder %= value.denominator
        text = str(whole) + '.' + ''.join(digits).rstrip('0')
    if negative and text != '0':
        return '-' + text
    return text


def _field(key, position, raw, scale, numeric, semantic_label, semantic_grade,
           unit=None, quantity=None, formal_unit=None, unit_conflict=False,
           bit=None, value=None):
    return {
        'key': key, 'position': position, 'bit': bit, 'raw': raw,
        'numeric': numeric, 'value': value, 'scale': scale, 'unit': unit,
        'quantity': quantity, 'formal_unit': formal_unit,
        'unit_conflict': unit_conflict, 'semantic_label': semantic_label,
        'unlabelled': semantic_label is None,
        'numeric_grade': 'Hypothesis', 'semantic_grade': semantic_grade,
        'native_grade': 'Unknown',
    }


def _bit_fields(fields, position, raw, specs):
    for bit, key, label, grade in specs:
        fields[key] = _field(
            key, position, raw, 'bit', '1' if raw & (1 << bit) else '0',
            label, grade, bit=bit, value=bool(raw & (1 << bit)))


def _ratio_field(fields, cells, position, key, divisor, scale, unit,
                 unit_conflict=False, formal_unit=None):
    if position >= len(cells) or cells[position]['state'] != 'present':
        return
    raw = cells[position]['raw']
    fields[key] = _field(
        key, position, raw, scale, _ratio(raw, divisor), key, 'Hypothesis',
        unit=unit, quantity=key, formal_unit=formal_unit,
        unit_conflict=unit_conflict)


def _signed(raw):
    return raw - 256 if raw >= 128 else raw


def _attach(fields, cells, direction):
    if direction == 'request':
        if 3 < len(cells) and cells[3]['state'] == 'present':
            _bit_fields(fields, 3, cells[3]['raw'], REQUEST_BITS)
        _ratio_field(fields, cells, 4, 'modulation', 2, 'u8/2', 'celsius',
                     True, 'celsius')
        _ratio_field(fields, cells, 5, 'dhw_water_flow', 10, 'u8/10',
                     'litres_per_minute')
        for position, key in ((6, 'temperature_logical6'),
                              (7, 'temperature_logical7'),
                              (8, 'temperature_logical8')):
            _ratio_field(fields, cells, position, key, 2, 'u8/2', 'celsius')
        if 9 < len(cells) and cells[9]['state'] == 'present':
            _bit_fields(fields, 9, cells[9]['raw'], INLET_BITS)
        return
    if 3 < len(cells) and cells[3]['state'] == 'present':
        _bit_fields(fields, 3, cells[3]['raw'], POSITIVE_BITS)
    _ratio_field(fields, cells, 4, 'dhw_setpoint', 2, 'u8/2', 'celsius')
    _ratio_field(fields, cells, 5, 'return_temperature', 2, 'u8/2', 'celsius')
    if 6 < len(cells) and cells[6]['state'] == 'present':
        raw = cells[6]['raw']
        number = _signed(raw)
        label = ADJUSTMENT_LABELS.get(number)
        fields['adjustment'] = _field(
            'adjustment', 6, raw, 'signed8', str(number), label,
            'Hypothesis' if label is not None else 'Unknown',
            quantity='adjustment', value=None)


def interpret_b512_op06_fields(context, logical_image):
    """Pure B512 OP06 logical-image helper. Returns a new result."""
    cells = parse_image(logical_image)
    copied, context_reason = _context_gate(context)
    known = context_reason is None
    if known:
        last = REQUEST_LAST if copied['direction'] == 'request' else POSITIVE_LAST
        revised = []
        for index, cell in enumerate(cells):
            cell = dict(cell)
            if index > last and cell['state'] == 'present':
                cell['state'] = 'unmodelled'
                cell['modelled'] = False
            revised.append(cell)
        cells = revised
        partial = any(index >= len(cells) or cells[index]['state'] != 'present'
                      for index in range(last + 1))
        extra = any(index > last and cell['state'] == 'unmodelled'
                    for index, cell in enumerate(cells))
    else:
        cells = [dict(cell) for cell in cells]
        partial = False
        extra = False
    if context_reason:
        reason = context_reason
    elif not _prefix_ok(cells):
        reason = 'prefix'
    else:
        reason = None
    fields = {}
    if reason is None:
        _attach(fields, cells, copied['direction'])
    return {
        'context': copied,
        'raw_cells': [{'position': index, 'state': cell['state'], 'raw': cell['raw']}
                      for index, cell in enumerate(cells)],
        'prefix_ok': _prefix_ok(cells),
        'admission': 'fields' if reason is None else 'raw_only',
        'reason': reason,
        'fields': fields,
        'partial': partial,
        'extra': extra,
        'qualification': dict(QUALIFICATION),
    }


def publish_expect(result):
    fields = result['fields']
    return {
        'admission': result['admission'],
        'reason': result['reason'],
        'prefix_ok': result['prefix_ok'],
        'partial': result['partial'],
        'extra': result['extra'],
        'field_keys': sorted(fields),
        'true_keys': sorted(key for key, field in fields.items() if field['value'] is True),
        'numeric': {key: field['numeric'] for key, field in sorted(fields.items())
                    if field['scale'] != 'bit'},
        'labels': {key: field['semantic_label'] for key, field in sorted(fields.items())},
        'unit_conflict_keys': sorted(key for key, field in fields.items()
                                     if field['unit_conflict']),
        'semantic_grades': {key: field['semantic_grade']
                            for key, field in sorted(fields.items())},
        'numeric_grades': {key: field['numeric_grade']
                           for key, field in sorted(fields.items())},
        'native_grades': {key: field['native_grade']
                          for key, field in sorted(fields.items())},
        'cell_states': {str(cell['position']): cell['state']
                        for cell in result['raw_cells']},
        'cell_raw': [cell['raw'] for cell in result['raw_cells']],
        'qualification': result['qualification'],
    }


def markdown_table(page, heading):
    lines = page.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None
    rows = []
    seen = False
    for line in lines[start + 1:]:
        if not line.strip():
            if rows:
                break
            continue
        if not line.startswith('|'):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and all(cell and set(cell) <= set('-: ') for cell in cells):
            seen = True
            continue
        if seen:
            rows.append(tuple(cells))
    return rows


def page_policy(page):
    blocks = re.findall(r'```json\n(.*?)\n```', page, re.S)
    if len(blocks) != 1:
        return None
    return json.loads(blocks[0])


def contract_problems(page, fixture):
    problems = []
    policy = page_policy(page)
    if policy != POLICY:
        problems.append('policy')
    normalized = ' '.join(page.split())
    for sentence in REQUIRED_SENTENCES:
        if sentence not in normalized:
            problems.append('prose:' + sentence[:48])
    for phrase in FORBIDDEN:
        if phrase in page:
            problems.append('forbidden')
            break
    for heading, expected in HEADINGS.items():
        if markdown_table(page, heading) != list(expected):
            problems.append('table:' + heading)
    if [row['name'] for row in fixture.get('examples', [])] != list(REQUIRED_NAMES):
        problems.append('names')
    by_name = {row['name']: row for row in case_inputs()}
    for example in fixture.get('examples', []):
        name = example.get('name')
        source = by_name.get(name)
        if source is None or example.get('context') != source['context']:
            problems.append('example:' + str(name))
            continue
        if example.get('image') != source['image']:
            problems.append('example:' + name)
            continue
        if source['error']:
            if example.get('expect') != {'outcome': 'type_error'}:
                problems.append('example:' + name)
            continue
        try:
            result = interpret_b512_op06_fields(source['context'], source['image'])
        except (TypeError, ValueError):
            problems.append('example:' + name)
            continue
        if example.get('expect') != publish_expect(result):
            problems.append('example:' + name)
    links = re.findall(r'\]\(([^)]+)\)', page)
    if not links:
        problems.append('links')
    for target in links:
        if '://' in target or not (PAGE.parent / target.split('#')[0]).is_file():
            problems.append('links')
            break
    return problems


class B512Op06Views(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.examples = {row['name']: row for row in cls.fixture['examples']}

    def test_contract_text_and_fixture_agree(self):
        self.assertEqual(contract_problems(self.page, self.fixture), [])
        self.assertEqual(set(self.fixture), {'examples'})
        self.assertGreater(len(self.examples), 0)

    def test_relative_links_resolve_locally(self):
        links = re.findall(r'\]\(([^)]+)\)', self.page)
        self.assertGreaterEqual(len(links), 3)
        for target in links:
            self.assertNotIn('://', target)
            self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)

    def _run(self, name):
        row = self.examples[name]
        return interpret_b512_op06_fields(row['context'], row['image'])

    def test_every_published_row(self):
        self.assertEqual([row['name'] for row in self.fixture['examples']],
                         list(REQUIRED_NAMES))
        for row in self.fixture['examples']:
            with self.subTest(example=row['name']):
                source = next(item for item in case_inputs() if item['name'] == row['name'])
                self.assertEqual(row['context'], source['context'])
                self.assertEqual(row['image'], source['image'])
                if source['error']:
                    self.assertEqual(row['expect'], {'outcome': 'type_error'})
                    with self.assertRaises(TypeError):
                        interpret_b512_op06_fields(row['context'], row['image'])
                    continue
                result = interpret_b512_op06_fields(row['context'], row['image'])
                self.assertEqual(set(result), RESULT_KEYS)
                self.assertEqual(result['qualification'], QUALIFICATION)
                self.assertIsNot(result['context'], row['context'])
                self.assertEqual(result['context'], row['context'])
                self.assertEqual(row['expect'], publish_expect(result))
                for field in result['fields'].values():
                    self.assertEqual(set(field), FIELD_KEYS)
                    self.assertEqual(field['numeric_grade'], 'Hypothesis')
                    self.assertEqual(field['native_grade'], 'Unknown')
                    self.assertEqual(field['unlabelled'], field['semantic_label'] is None)

    def test_request_and_positive_zero_controls(self):
        request = self._run('request_all_zero')
        positive = self._run('positive_all_zero')
        self.assertEqual(set(request['fields']), REQUEST_KEYS)
        self.assertEqual(set(positive['fields']), POSITIVE_KEYS)
        self.assertTrue(request['fields']['modulation']['unit_conflict'])
        self.assertEqual(request['fields']['modulation']['formal_unit'], 'celsius')
        self.assertEqual(request['fields']['modulation']['numeric'], '0')
        self.assertEqual(request['fields']['dhw_water_flow']['numeric'], '0')
        self.assertEqual(request['fields']['dhw_water_flow']['scale'], 'u8/10')
        for key in ('temperature_logical6', 'temperature_logical7', 'temperature_logical8'):
            self.assertEqual(request['fields'][key]['numeric'], '0')
        self.assertFalse(any(field['value'] for field in request['fields'].values()
                             if field['scale'] == 'bit'))
        self.assertEqual(positive['fields']['adjustment']['numeric'], '0')
        self.assertEqual(positive['fields']['adjustment']['semantic_label'], 'in_range')
        self.assertNotEqual(positive['fields']['adjustment']['numeric'], '-1')
        self.assertFalse(request['partial'])
        self.assertFalse(positive['partial'])
        self.assertEqual(request['admission'], 'fields')
        self.assertTrue(request['prefix_ok'])

    def test_each_request_bit_toggles_alone(self):
        """Bits 0..7: stuck or cross-wired request bits, including unnamed labels."""
        for bit, key, label, grade in REQUEST_BITS:
            with self.subTest(bit=bit, key=key):
                row = self.examples['request_bit_%d' % bit]
                self.assertEqual(row['image'][3], 1 << bit)
                result = self._run(row['name'])
                self.assertEqual(set(result['fields']), REQUEST_KEYS)
                self.assertTrue(result['fields'][key]['value'])
                self.assertEqual(result['fields'][key]['semantic_label'], label)
                self.assertEqual(result['fields'][key]['semantic_grade'], grade)
                self.assertNotIn('loading_disabled', result['fields'])
                for other_bit, other_key, _label, _grade in REQUEST_BITS:
                    if other_bit != bit:
                        self.assertFalse(result['fields'][other_key]['value'])

    def test_each_inlet_bit_toggles_alone(self):
        """Inlet bits 0 and 1: merged flags or invented inlet names."""
        for bit, key, label, grade in INLET_BITS:
            with self.subTest(bit=bit):
                row = self.examples['request_inlet_bit_%d' % bit]
                self.assertEqual(row['image'][9], 1 << bit)
                result = self._run(row['name'])
                self.assertTrue(result['fields'][key]['value'])
                self.assertIsNone(result['fields'][key]['semantic_label'])
                self.assertEqual(result['fields'][key]['semantic_grade'], grade)
                other = INLET_BITS[1 - bit][1]
                self.assertFalse(result['fields'][other]['value'])
                self.assertEqual(set(result['fields']), REQUEST_KEYS)

    def test_reserved_request_and_positive_bits_stay_raw(self):
        """Reserved masks: raw bits cleared or promoted to named conditions."""
        for bit in range(2, 8):
            with self.subTest(request_reserved=bit):
                row = self.examples['request_reserved_bit_%d' % bit]
                self.assertEqual(row['image'][9], 1 << bit)
                result = self._run(row['name'])
                self.assertEqual(result['raw_cells'][9]['raw'], 1 << bit)
                self.assertEqual(set(result['fields']), REQUEST_KEYS)
                self.assertFalse(result['fields']['unnamed_inlet_condition_0']['value'])
                self.assertFalse(result['fields']['unnamed_inlet_condition_1']['value'])
        for bit in (6, 7):
            with self.subTest(positive_reserved=bit):
                row = self.examples['positive_reserved_bit_%d' % bit]
                self.assertEqual(row['image'][3], 1 << bit)
                result = self._run(row['name'])
                self.assertEqual(result['raw_cells'][3]['raw'], 1 << bit)
                self.assertEqual(set(result['fields']), POSITIVE_KEYS)
                for _bit, key, _label, _grade in POSITIVE_BITS:
                    self.assertFalse(result['fields'][key]['value'])

    def test_each_positive_bit_toggles_alone(self):
        """Positive bits 0..5: request names applied to the positive image."""
        for bit, key, label, grade in POSITIVE_BITS:
            with self.subTest(bit=bit, key=key):
                row = self.examples['positive_bit_%d' % bit]
                self.assertEqual(row['image'][3], 1 << bit)
                result = self._run(row['name'])
                self.assertTrue(result['fields'][key]['value'])
                self.assertEqual(result['fields'][key]['semantic_label'], label)
                self.assertEqual(result['fields'][key]['semantic_grade'], grade)
                self.assertNotIn('task_active', result['fields'])
                for other_bit, other_key, _label, _grade in POSITIVE_BITS:
                    if other_bit != bit:
                        self.assertFalse(result['fields'][other_key]['value'])

    def test_scalar_divisor_and_unit_conflict(self):
        """Flow /2, dropped unit conflict, or temperature scale applied to flow."""
        result = self._run('request_scalar_01')
        self.assertEqual(self.examples['request_scalar_01']['expect']['numeric'], {
            'modulation': '0.5', 'dhw_water_flow': '0.1',
            'temperature_logical6': '0.5', 'temperature_logical7': '0.5',
            'temperature_logical8': '0.5'})
        self.assertEqual(result['fields']['modulation']['numeric'], '0.5')
        self.assertTrue(result['fields']['modulation']['unit_conflict'])
        self.assertEqual(result['fields']['modulation']['formal_unit'], 'celsius')
        self.assertEqual(result['fields']['modulation']['quantity'], 'modulation')
        self.assertEqual(result['fields']['dhw_water_flow']['numeric'], '0.1')
        self.assertNotEqual(result['fields']['dhw_water_flow']['numeric'], '0.5')
        self.assertEqual(result['fields']['dhw_water_flow']['unit'], 'litres_per_minute')
        for key in ('temperature_logical6', 'temperature_logical7', 'temperature_logical8'):
            self.assertEqual(result['fields'][key]['numeric'], '0.5')
            self.assertFalse(result['fields'][key]['unit_conflict'])
        only = {
            'request_modulation_only': 'modulation',
            'request_flow_only': 'dhw_water_flow',
            'request_temperature6_only': 'temperature_logical6',
            'request_temperature7_only': 'temperature_logical7',
            'request_temperature8_only': 'temperature_logical8',
        }
        expected = {
            'modulation': '0.5', 'dhw_water_flow': '0.1',
            'temperature_logical6': '0.5', 'temperature_logical7': '0.5',
            'temperature_logical8': '0.5'}
        for name, key in only.items():
            with self.subTest(example=name):
                fields = self._run(name)['fields']
                self.assertEqual(fields[key]['numeric'], expected[key])
                for other, other_expected in expected.items():
                    if other != key:
                        self.assertEqual(fields[other]['numeric'], '0')
        flow = self._run('request_flow_only')['fields']['modulation']
        self.assertTrue(flow['unit_conflict'])
        self.assertEqual(flow['numeric'], '0')

    def test_positive_scalars_are_not_the_request_map(self):
        """Swapped layouts: setpoint decoded as modulation or flow."""
        setpoint = self._run('positive_setpoint_only')['fields']
        ret = self._run('positive_return_only')['fields']
        self.assertEqual(setpoint['dhw_setpoint']['numeric'], '0.5')
        self.assertNotIn('modulation', setpoint)
        self.assertNotIn('dhw_water_flow', setpoint)
        self.assertEqual(setpoint['return_temperature']['numeric'], '0')
        self.assertEqual(ret['return_temperature']['numeric'], '0.5')
        self.assertEqual(ret['dhw_setpoint']['numeric'], '0')
        self.assertFalse(setpoint['dhw_setpoint']['unit_conflict'])

    def test_adjustment_domain_and_sign(self):
        """Unsigned adjustment, or a label invented for raw 3."""
        expected = {
            'positive_adjustment_ff': ('-1', 'at_minimum', 'Hypothesis', False),
            'positive_adjustment_02': ('2', 'modulation_regulator_not_active',
                                       'Hypothesis', False),
            'positive_adjustment_03': ('3', None, 'Unknown', True),
            'positive_adjustment_00': ('0', 'in_range', 'Hypothesis', False),
            'positive_adjustment_01': ('1', 'at_maximum', 'Hypothesis', False),
            'positive_adjustment_80': ('-128', None, 'Unknown', True),
            'positive_adjustment_7f': ('127', None, 'Unknown', True),
        }
        for name, (numeric, label, grade, unlabelled) in expected.items():
            with self.subTest(example=name):
                field = self._run(name)['fields']['adjustment']
                self.assertEqual(field['numeric'], numeric)
                self.assertNotEqual(field['numeric'], '255')
                self.assertEqual(field['semantic_label'], label)
                self.assertEqual(field['semantic_grade'], grade)
                self.assertEqual(field['native_grade'], 'Unknown')
                self.assertEqual(field['unlabelled'], unlabelled)
                self.assertEqual(field['scale'], 'signed8')
                self.assertEqual(self.examples[name]['expect']['numeric']['adjustment'],
                                 numeric)

    def test_partial_request_and_missing_adjustment(self):
        """Filled tails: later temperatures, inlet flags, or default adjustment -1."""
        short = self._run('request_through_logical6')
        self.assertEqual(short['fields']['temperature_logical6']['numeric'], '0.5')
        for absent in ('temperature_logical7', 'temperature_logical8',
                       'unnamed_inlet_condition_0', 'unnamed_inlet_condition_1'):
            self.assertNotIn(absent, short['fields'])
        self.assertTrue(short['partial'])
        self.assertEqual(short['admission'], 'fields')
        self.assertEqual(self.examples['request_through_logical6']['expect']['numeric'],
                         {'modulation': '0', 'dhw_water_flow': '0',
                          'temperature_logical6': '0.5'})
        hole = self._run('request_hole_logical7')
        self.assertEqual(hole['fields']['temperature_logical6']['numeric'], '0.5')
        self.assertNotIn('temperature_logical7', hole['fields'])
        self.assertEqual(hole['fields']['temperature_logical8']['numeric'], '0')
        self.assertEqual(hole['raw_cells'][7]['state'], 'missing')
        self.assertIsNone(hole['raw_cells'][7]['raw'])
        missing = self._run('positive_missing_logical6')
        self.assertNotIn('adjustment', missing['fields'])
        self.assertNotIn('-1', [field['numeric'] for field in missing['fields'].values()])
        self.assertTrue(missing['partial'])
        self.assertEqual(missing['fields']['dhw_setpoint']['numeric'], '0')
        self.assertEqual(missing['fields']['return_temperature']['numeric'], '0')
        unmodelled = self._run('request_unmodelled_logical4')
        self.assertNotIn('modulation', unmodelled['fields'])
        self.assertEqual(unmodelled['raw_cells'][4]['state'], 'unmodelled')
        self.assertEqual(unmodelled['raw_cells'][4]['raw'], 1)
        self.assertEqual(unmodelled['fields']['dhw_water_flow']['numeric'], '0.1')
        extra = self._run('request_extra_position10')
        self.assertTrue(extra['extra'])
        self.assertFalse(extra['partial'])
        self.assertEqual(extra['raw_cells'][10]['raw'], 171)
        self.assertEqual(extra['raw_cells'][10]['state'], 'unmodelled')
        self.assertEqual(set(extra['fields']), REQUEST_KEYS)

    def test_identity_axes_vary_one_at_a_time(self):
        base = self._run('request_all_zero')
        family = self._run('request_family_b')
        variant = self._run('request_variant_b')
        self.assertEqual(family['fields'], base['fields'])
        self.assertEqual(family['context']['family'], 'synthetic-dhw-family-b')
        self.assertNotEqual(family['context']['family'], base['context']['family'])
        self.assertEqual(variant['fields'], base['fields'])
        self.assertEqual(variant['context']['variant'], 'synthetic-variant-b')
        self.assertNotEqual(variant['context']['variant'], base['context']['variant'])
        outside = self._run('request_family_c')
        other_variant = self._run('request_variant_c')
        self.assertEqual(set(outside['fields']), REQUEST_KEYS)
        self.assertEqual(outside['context']['family'], 'synthetic-dhw-family-c')
        self.assertNotIn('synthetic-dhw-family-c', POLICY['example_families'])
        self.assertEqual(set(other_variant['fields']), REQUEST_KEYS)
        self.assertNotIn('synthetic-variant-c', POLICY['example_variants'])
        long = self._run('positive_direction_on_long_zero')
        self.assertEqual(set(long['fields']), POSITIVE_KEYS)
        self.assertNotIn('modulation', long['fields'])
        self.assertNotIn('temperature_logical7', long['fields'])
        self.assertEqual(long['fields']['adjustment']['numeric'], '0')
        for position in (7, 8, 9):
            self.assertEqual(long['raw_cells'][position]['state'], 'unmodelled')
            self.assertEqual(long['raw_cells'][position]['raw'], 0)
        short = self._run('request_direction_on_short_zero')
        self.assertIn('temperature_logical6', short['fields'])
        self.assertNotIn('temperature_logical7', short['fields'])
        self.assertNotIn('adjustment', short['fields'])
        self.assertTrue(short['partial'])

    def test_each_prefix_byte_and_length(self):
        """Prefix bypass, or a short image treated as a complete zero image."""
        for index, bad in ((0, 180), (1, 17), (2, 5)):
            with self.subTest(prefix=index):
                mismatch = self._run('prefix_position%d_mismatch' % index)
                missing = self._run('prefix_position%d_missing' % index)
                self.assertEqual(mismatch['raw_cells'][index]['raw'], bad)
                self.assertFalse(mismatch['prefix_ok'])
                self.assertEqual(mismatch['fields'], {})
                self.assertEqual(mismatch['reason'], 'prefix')
                self.assertEqual(mismatch['admission'], 'raw_only')
                self.assertEqual(mismatch['raw_cells'][4]['raw'], 1)
                self.assertFalse(missing['prefix_ok'])
                self.assertEqual(missing['fields'], {})
                self.assertEqual(missing['raw_cells'][index]['state'], 'missing')
                self.assertEqual(missing['raw_cells'][5]['raw'], 1)
        lengths = {
            'length_0': (False, 'prefix', 'raw_only', True, 0),
            'length_1': (False, 'prefix', 'raw_only', True, 0),
            'length_2': (False, 'prefix', 'raw_only', True, 0),
            'length_3': (True, None, 'fields', True, 0),
            'length_4': (True, None, 'fields', True, 8),
        }
        for name, (prefix, reason, admission, partial, count) in lengths.items():
            with self.subTest(example=name):
                result = self._run(name)
                self.assertEqual(result['prefix_ok'], prefix)
                self.assertEqual(result['reason'], reason)
                self.assertEqual(result['admission'], admission)
                self.assertEqual(result['partial'], partial)
                self.assertEqual(len(result['fields']), count)
                self.assertNotIn('modulation', result['fields'])
        flags = self._run('length_4')
        self.assertEqual(set(flags['fields']), {item[1] for item in REQUEST_BITS})
        self.assertTrue(all(field['value'] is False for field in flags['fields'].values()))

    def test_context_failures_do_not_decode(self):
        """A scalar image still yields no typed value when identity is unusable."""
        for name, reason in (
            ('missing_family', 'context'),
            ('empty_family', 'context'),
            ('missing_variant', 'context'),
            ('empty_variant', 'context'),
            ('variant_integer_zero', 'context'),
            ('family_integer_zero', 'context'),
            ('missing_direction', 'context'),
            ('direction_integer_zero', 'context'),
            ('direction_reply', 'direction'),
        ):
            with self.subTest(example=name):
                result = self._run(name)
                self.assertEqual(result['fields'], {})
                self.assertEqual(result['reason'], reason)
                self.assertEqual(result['admission'], 'raw_only')
                self.assertTrue(result['prefix_ok'])
                self.assertEqual(result['raw_cells'][4]['raw'], 1)
                self.assertEqual(result['raw_cells'][4]['state'], 'present')
                self.assertFalse(result['partial'])
                self.assertFalse(result['extra'])
        both = self._run('empty_family_bad_prefix')
        self.assertEqual(both['reason'], 'context')
        self.assertFalse(both['prefix_ok'])
        self.assertEqual(both['fields'], {})

    def test_direction_reply_is_not_positive(self):
        result = self._run('direction_reply')
        self.assertNotIn('dhw_setpoint', result['fields'])
        self.assertNotIn('adjustment', result['fields'])
        self.assertEqual(result['reason'], 'direction')

    def test_same_scalar_image_changes_only_direction(self):
        image = [181, 18, 6, 0, 1, 1, 1, 1, 1, 0]
        request = interpret_b512_op06_fields(ctx(), image)
        positive = interpret_b512_op06_fields(ctx('positive'), image)
        self.assertEqual(request['fields']['dhw_water_flow']['numeric'], '0.1')
        self.assertEqual(request['fields']['modulation']['numeric'], '0.5')
        self.assertNotIn('return_temperature', request['fields'])
        self.assertEqual(positive['fields']['dhw_setpoint']['numeric'], '0.5')
        self.assertEqual(positive['fields']['return_temperature']['numeric'], '0.5')
        self.assertEqual(positive['fields']['adjustment']['numeric'], '1')
        self.assertEqual(positive['fields']['adjustment']['semantic_label'], 'at_maximum')
        self.assertNotIn('dhw_water_flow', positive['fields'])
        self.assertEqual(positive['raw_cells'][7]['state'], 'unmodelled')
        self.assertEqual(positive['raw_cells'][7]['raw'], 1)
        self.assertEqual(positive['raw_cells'][9]['raw'], 0)

    def test_containers_are_copied_and_bytes_match_lists(self):
        image = bytearray([181, 18, 6, 0, 1, 1, 1, 1, 1, 0])
        context = ctx()
        context['status_cache'] = {'generation': 1}
        result = interpret_b512_op06_fields(context, image)
        image[4] = 9
        context['status_cache']['generation'] = 2
        context['family'] = 'changed'
        self.assertEqual(result['raw_cells'][4]['raw'], 1)
        self.assertEqual(result['context']['status_cache'], {'generation': 1})
        self.assertEqual(result['context']['family'], 'synthetic-dhw-family-a')
        self.assertEqual(context['status_cache'], {'generation': 2})
        listed = interpret_b512_op06_fields(ctx(), [181, 18, 6, 0, 1, 1, 1, 1, 1, 0])
        viewed = interpret_b512_op06_fields(
            ctx(), memoryview(bytes([181, 18, 6, 0, 1, 1, 1, 1, 1, 0])))
        self.assertEqual(result['fields'], listed['fields'])
        self.assertEqual(viewed['fields'], listed['fields'])
        self.assertEqual(viewed['raw_cells'], listed['raw_cells'])
        hole = [{'raw': 1, 'modelled': False}]
        parsed = interpret_b512_op06_fields(ctx(), [181, 18, 6, 0, hole[0], 0, 0, 0, 0, 0])
        hole[0]['raw'] = 9
        self.assertEqual(parsed['raw_cells'][4]['raw'], 1)

    def test_qualification_is_not_promoted(self):
        result = self._run('request_scalar_01')
        result['qualification']['physical'] = 'Proven'
        again = self._run('request_scalar_01')
        self.assertEqual(again['qualification'], QUALIFICATION)
        self.assertEqual(self._run('length_0')['qualification'], QUALIFICATION)

    def test_grades_stay_independent(self):
        unnamed = self._run('request_all_zero')['fields']['unnamed_sensor_condition_4']
        self.assertEqual(unnamed['numeric_grade'], 'Hypothesis')
        self.assertEqual(unnamed['semantic_grade'], 'Unknown')
        self.assertEqual(unnamed['native_grade'], 'Unknown')
        self.assertIsNone(unnamed['semantic_label'])
        named = self._run('request_all_zero')['fields']['task_active']
        self.assertEqual(named['semantic_grade'], 'Hypothesis')
        self.assertEqual(named['native_grade'], 'Unknown')
        unlabelled = self._run('positive_adjustment_03')['fields']['adjustment']
        self.assertEqual(unlabelled['numeric'], '3')
        self.assertEqual(unlabelled['numeric_grade'], 'Hypothesis')
        self.assertEqual(unlabelled['semantic_grade'], 'Unknown')
        self.assertEqual(unlabelled['native_grade'], 'Unknown')

    def test_executed_file_mutants(self):
        """Disposable copies only. Each mutant must be rejected."""
        page = self.page
        fixture = json.loads(FIXTURE.read_text())
        self.assertEqual(contract_problems(page, fixture), [])

        def rejected(name, new_page, new_fixture, code):
            directory = tempfile.TemporaryDirectory(prefix='an14-mutant-')
            try:
                path = Path(directory.name)
                (path / 'page.md').write_text(new_page)
                (path / 'fixture.json').write_text(json.dumps(new_fixture))
                found = contract_problems((path / 'page.md').read_text(),
                                          json.loads((path / 'fixture.json').read_text()))
            finally:
                directory.cleanup()
            self.assertIn(code, found, name)
            return name

        killed = []
        flow = page.replace('"flow_divisor": 10', '"flow_divisor": 2', 1)
        killed.append(rejected('flow-divisor', flow, fixture, 'policy'))
        killed.append(rejected('flow-prose', page + '\ndivide flow by 2\n', fixture, 'forbidden'))
        swapped = page.replace(
            '| 0 | task_active | task_active | Hypothesis |',
            '| 0 | loading_disabled | loading_disabled | Hypothesis |', 1)
        killed.append(rejected('table-layout-swap', swapped, fixture, 'table:### Request logical 3 bits'))
        labelled_policy = page_policy(page)
        labelled_policy['request_bits'][4]['semantic_label'] = 'flow_sensor_fault'
        labelled = re.sub(
            r'```json\n.*?\n```',
            '```json\n' + json.dumps(labelled_policy, indent=2) + '\n```',
            page, count=1, flags=re.S)
        killed.append(rejected('unnamed-label', labelled, fixture, 'policy'))
        unsigned = page.replace('"adjustment_codec": "signed8"',
                                '"adjustment_codec": "uint8"', 1)
        killed.append(rejected('unsigned-adjustment', unsigned, fixture, 'policy'))
        filled = page.replace('"materialize_missing": false',
                              '"materialize_missing": true', 1)
        killed.append(rejected('fill-missing', filled, fixture, 'policy'))
        dropped = page.replace('"preserve_reserved_raw": true',
                               '"preserve_reserved_raw": false', 1)
        killed.append(rejected('drop-reserved', dropped, fixture, 'policy'))
        ignored = page.replace('"require_prefix": true', '"require_prefix": false', 1)
        killed.append(rejected('ignore-prefix', ignored, fixture, 'policy'))
        policy = page_policy(page)
        policy['request_bits'], policy['positive_bits'] = (
            policy['positive_bits'], policy['request_bits'])
        encoded = json.dumps(policy, indent=2)
        rewritten = re.sub(r'```json\n.*?\n```', '```json\n' + encoded + '\n```',
                           page, count=1, flags=re.S)
        killed.append(rejected('json-layout-swap', rewritten, fixture, 'policy'))

        def mutate(example_name, change):
            clone = json.loads(json.dumps(fixture))
            for example in clone['examples']:
                if example['name'] == example_name:
                    change(example)
            return clone

        killed.append(rejected(
            'fixture-flow',
            page,
            mutate('request_scalar_01', lambda example: example['expect']['numeric'].__setitem__(
                'dhw_water_flow', '0.5')),
            'example:request_scalar_01'))
        killed.append(rejected(
            'fixture-default-adjustment',
            page,
            mutate('positive_missing_logical6', lambda example: example['expect']['numeric'].__setitem__(
                'adjustment', '-1')),
            'example:positive_missing_logical6'))
        killed.append(rejected(
            'fixture-unsigned',
            page,
            mutate('positive_adjustment_ff', lambda example: example['expect']['numeric'].__setitem__(
                'adjustment', '255')),
            'example:positive_adjustment_ff'))
        killed.append(rejected(
            'fixture-reserved-raw',
            page,
            mutate('request_reserved_bit_2', lambda example: example['expect']['cell_raw'].__setitem__(
                9, 0)),
            'example:request_reserved_bit_2'))
        killed.append(rejected(
            'fixture-native-promoted',
            page,
            mutate('request_all_zero', lambda example: example['expect']['qualification'].__setitem__(
                'physical', 'Proven')),
            'example:request_all_zero'))
        self.assertEqual(len(killed), 14)
        self.assertEqual(len(set(killed)), 14)


if __name__ == '__main__':
    unittest.main()
