"""Synthetic AN12 B511 logical-overlay contract. Not a native codec.

Each identity field names the production mutation its assertion catches:
family — caller family dropped or replaced by a constant;
variant — unknown variant replaced, or variant taken from image length;
operation — OP00 and OP07 views swapped, or another class given an invented offset;
direction — a non-positive direction admitted as positive;
alternative — reserved bit 7 labelled fan-running, or alternative taken from length;
select_room_setpoint — room numeric emitted when false, or withheld when true;
length — length 8 reported complete for the extended alternative, or OP00 complete below 12;
byte 8 bit 0 — raw flag or percent loses value 1;
byte 8 bit 1 — raw flag or percent loses value 2;
byte 8 bit 2 — raw flag or percent loses value 4;
byte 8 bit 3 — raw flag or percent loses value 8;
byte 8 bit 4 — raw flag or percent loses value 16;
byte 8 bit 5 — raw flag or percent loses value 32;
byte 8 bit 6 — raw flag or percent loses value 64, or bit 6 is named fan-running;
byte 8 bit 7 — fan false under the fan alternative, fan true under reserved, or 128 clipped or converted;
byte 7 — room setpoint follows byte 8, or the raw overlay is dropped when room is selected;
byte 8 — pressure follows byte 7, or percent is converted to bar.
"""
import copy
from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import shutil
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/an12-b511-overlap-views.md'
FIXTURE = ROOT / 'architecture/fixtures/an12_b511_overlap_views.json'
PREFIX = (0x11, 0x22, 0x33)
QUALIFICATION = {
    'other_per_variant_fields': 'Unknown',
    'other_per_variant_defaults': 'Unknown',
    'physical_image_adaptation': 'Unknown',
    'missing_codecs': 'Unknown',
    'actual_support': 'Unknown',
    'other_class07_reply_shapes': 'Unknown',
    'presence': 'Unknown',
    'freshness': 'Unknown',
    'execution': 'Unknown',
}
POLICY = {
    'signature': 'ab11an11.view(context, logical_image)',
    'context_fields': [
        'family', 'variant', 'operation', 'direction', 'alternative',
        'select_room_setpoint',
    ],
    'direction': 'positive',
    'operations': ['OP00', 'OP07'],
    'op00_alternatives': ['reserved', 'fan'],
    'op07_alternatives': ['base', 'extended'],
    'op00_required_extent': 12,
    'op07_base_required_extent': 8,
    'op07_extended_required_extent': 9,
    'prefix_positions': [0, 1, 2],
    'insert_or_remove_prefix': False,
    'transmission_shape_defined': False,
    'select_alternative_from_length': False,
    'select_variant_from_length': False,
    'infer_operation_from_prefix': False,
    'infer_fields_from_list_order': False,
    'logical8_bit7': 7,
    'reserved_bit7_label': 'reserved',
    'fan_bit7_label': 'fan-running',
    'label_reserved_bit7_as_fan': False,
    'concatenate_overlapping_fields': False,
    'room_setpoint_position': 7,
    'room_setpoint_scale': 'u8/2',
    'room_setpoint_divisor': 2,
    'room_setpoint_unit': 'degrees_Celsius',
    'pressure_position': 8,
    'pressure_label': 'building-circuit-pressure',
    'pressure_unit': 'percent',
    'pressure_domain_min': 0,
    'pressure_domain_max': 100,
    'convert_percent_to_bar': False,
    'clip_out_of_domain': False,
    'hide_missing_ninth_position': False,
    'invent_offsets_for_other_classes': False,
    'other_class_offsets': {},
    'preserve_complete_raw_image': True,
    'preserve_unknown_variant': True,
    'detach_raw_buffers': True,
    'unknown_overlay_invents_labels': False,
    'software_contract': 'Proven',
    'layout_grade': 'Hypothesis',
    'native_grade': 'Unknown',
    'runtime_route_decoder': False,
    'example_families': ['synthetic-b511-family-a', 'synthetic-b511-family-b'],
    'example_variants': [
        'synthetic-variant-a', 'synthetic-variant-b', 'unknown-variant',
    ],
}
AXES = {
    'families': [
        'synthetic-b511-family-a', 'synthetic-b511-family-b', 'unknown-family',
    ],
    'variants': [
        'synthetic-variant-a', 'synthetic-variant-b', 'unknown-variant',
    ],
    'operations': ['OP00', 'OP07', 'OP01'],
    'directions': ['positive', 'request'],
    'alternatives': ['reserved', 'fan', 'base', 'extended', 'unknown-overlay'],
    'lengths': [8, 9, 12],
    'select_room_setpoint': [False, True],
    'byte8_bits': [0, 1, 2, 3, 4, 5, 6, 7],
}
BIT_ROWS = [
    {'bit': 0, 'raw': 1, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 1},
    {'bit': 1, 'raw': 2, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 2},
    {'bit': 2, 'raw': 4, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 4},
    {'bit': 3, 'raw': 8, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 8},
    {'bit': 4, 'raw': 16, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 16},
    {'bit': 5, 'raw': 32, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 32},
    {'bit': 6, 'raw': 64, 'fan': False, 'pressure_domain': 'in_domain', 'pressure_numeric': 64},
    {'bit': 7, 'raw': 128, 'fan': True, 'pressure_domain': 'out_of_domain', 'pressure_numeric': None},
]
SENTENCES = (
    'AN12 defines `ab11an11.view(context, logical_image)`, a pure view of one caller-selected B511 logical image.',
    'The hypothetical signature is the ab11an11 helper API.',
    'Pair with AN11. This ordinary companion has no dependency on the code.',
    'This page does not repeat that family page and does not add native qualification.',
    'A logical image retains the three prefix positions 0, 1 and 2.',
    'No physical prefix insertion or removal is defined. No transmission shape is defined.',
    'These are distinct view alternatives. Response length does not select the alternative, the variant, or the operation.',
    'Family, variant, operation, direction and alternative are explicit caller selections.',
    'Unknown variants are preserved.',
    'The reserved alternative does not name logical 8 bit 7 fan-running.',
    'OP00 logical 8 byte 80 hex yields fan true only under the fan alternative.',
    'Under the reserved alternative the same byte stays reserved raw 80 hex.',
    'Both positive alternatives require 12 logical positions for a complete extent.',
    'A length 8 image is complete only as the base alternative.',
    'The same length 8 image is incomplete as the extended alternative and retains byte 7.',
    'A missing ninth position stays visible.',
    'OP07 extended byte 7 raw 40 hex yields room setpoint 32 degrees Celsius and retains overlay 40 hex.',
    'Overlapping structures stay separate and are not concatenated.',
    'Byte 8 raw 100 yields percent 100.',
    'Byte 8 raw 101 stays raw and out of domain without clipping or bar conversion.',
    'The percent-labelled pressure is not converted to bar.',
    'Bytes 7 and 8 are independent.',
    'No other field is inferred from its order in a list.',
    'A hole at logical 8 does not move a later byte into the pressure field.',
    'Other classes receive no invented offsets.',
    'Unknown overlays retain bytes and receive no invented labels.',
    'An empty family, empty variant, empty operation, empty alternative, missing key, or non-boolean room selection is malformed context and is reported before direction.',
    'Native grade stays Unknown on every result and every field.',
    'No decoder is attached to existing runtime routes.',
    'eBUS MCP compatibility and GraphQL parity are unchanged.',
    'A partial result keeps the complete raw image and every independent field that is already available.',
    'Nothing in this contract is stable before Helianthus 1.0.',
    'These examples are synthetic and do not qualify a physical device.',
    'Each bit 0..7 of logical 8 is preserved in the raw flag byte.',
    'Only bit 7 under the fan alternative is fan-running.',
)


def ctx(operation='OP00', alternative='fan', family='synthetic-b511-family-a',
        variant='synthetic-variant-a', direction='positive', room=False):
    return {
        'family': family,
        'variant': variant,
        'operation': operation,
        'direction': direction,
        'alternative': alternative,
        'select_room_setpoint': room,
    }


def expect(**kwargs):
    base = {
        'admission': 'applied',
        'reason': None,
        'selected_alternative': 'fan',
        'family': 'synthetic-b511-family-a',
        'variant': 'synthetic-variant-a',
        'operation': 'OP00',
        'direction': 'positive',
        'available_extent': 12,
        'required_extent': 12,
        'complete_logical_extent': True,
        'extent_state': 'complete',
        'missing_positions': [],
        'fan_running': None,
        'fan_label': None,
        'raw_flag_byte': None,
        'reserved_label': None,
        'overlay_raw': None,
        'overlay_state': None,
        'room_numeric': None,
        'room_availability': None,
        'room_unit': None,
        'pressure_numeric': None,
        'pressure_raw': None,
        'pressure_unit': None,
        'pressure_domain': None,
        'pressure_availability': None,
        'concatenated': None,
        'layout_grade': 'Hypothesis',
        'fan_grades': None,
        'room_grades': None,
        'pressure_grades': None,
    }
    base.update(kwargs)
    return base


HHU = ['Hypothesis', 'Hypothesis', 'Unknown']
UUU = ['Unknown', 'Unknown', 'Unknown']


_MISSING_ALTERNATIVE = ctx()
del _MISSING_ALTERNATIVE['alternative']
_ROOM_FLAG_INTEGER = ctx()
_ROOM_FLAG_INTEGER['select_room_setpoint'] = 1


def _case(name, context, length, cells=(), holes=(), unmodelled=(), table=True, **expected):
    return {
        'name': name,
        'context': context,
        'length': length,
        'cells': [[index, value] for index, value in cells],
        'holes': list(holes),
        'unmodelled': [[index, value] for index, value in unmodelled],
        'table': table,
        'expect': expect(**expected),
    }


CASES = [
    _case('op00_fan_80', ctx(), 12, ((8, 128),),
          selected_alternative='fan', fan_running=True, fan_label='fan-running',
          raw_flag_byte=128, fan_grades=HHU),
    _case('op00_reserved_80', ctx(alternative='reserved'), 12, ((8, 128),),
          selected_alternative='reserved', raw_flag_byte=128, reserved_label='reserved'),
    _case('op00_fan_len11', ctx(), 11, ((8, 128),),
          available_extent=11, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=[11], fan_running=True, fan_label='fan-running',
          raw_flag_byte=128, fan_grades=HHU),
    _case('op00_fan_len8', ctx(), 8, ((7, 64),),
          available_extent=8, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=[8, 9, 10, 11]),
    _case('op00_fan_zero', ctx(), 12, ((8, 0),),
          fan_running=False, fan_label='fan-running', raw_flag_byte=0, fan_grades=HHU),
    _case('op00_fan_81', ctx(), 12, ((8, 129),),
          fan_running=True, fan_label='fan-running', raw_flag_byte=129, fan_grades=HHU),
    _case('op07_ext_40_100', ctx('OP07', 'extended', 'synthetic-b511-family-b',
                                'synthetic-variant-b', room=True),
          9, ((7, 64), (8, 100)),
          selected_alternative='extended', family='synthetic-b511-family-b',
          variant='synthetic-variant-b', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op07_ext_40_101', ctx('OP07', 'extended', room=True), 9, ((7, 64), (8, 101)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=None, pressure_raw=101,
          pressure_unit='percent', pressure_domain='out_of_domain',
          pressure_availability='out_of_domain', pressure_grades=UUU),
    _case('op07_base_len8', ctx('OP07', 'base', room=True), 8, ((7, 64),),
          selected_alternative='base', operation='OP07', available_extent=8,
          required_extent=8, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU),
    _case('op07_ext_len8', ctx('OP07', 'extended', room=True), 8, ((7, 64),),
          selected_alternative='extended', operation='OP07', available_extent=8,
          required_extent=9, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=[8], overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=None, pressure_raw=None,
          pressure_unit=None, pressure_domain='missing',
          pressure_availability='missing', pressure_grades=UUU),
    _case('op07_ext_not_selected', ctx('OP07', 'extended', room=False), 9,
          ((7, 64), (8, 100)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=64, overlay_state='present',
          pressure_numeric=100, pressure_raw=100, pressure_unit='percent',
          pressure_domain='in_domain', pressure_availability='present',
          pressure_grades=HHU),
    _case('op07_unknown_variant', ctx('OP07', 'extended', variant='unknown-variant', room=True),
          9, ((7, 64), (8, 100)),
          selected_alternative='extended', variant='unknown-variant', operation='OP07',
          available_extent=9, required_extent=9, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op07_split_42_100', ctx('OP07', 'extended', room=True), 9, ((7, 66), (8, 100)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=66, overlay_state='present',
          room_numeric=33.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op07_pressure_0', ctx('OP07', 'extended', room=True), 9, ((7, 64), (8, 0)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=0, pressure_raw=0, pressure_unit='percent',
          pressure_domain='in_domain', pressure_availability='present',
          pressure_grades=HHU),
    _case('op07_room_half', ctx('OP07', 'extended', room=True), 9, ((7, 1), (8, 100)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=1, overlay_state='present',
          room_numeric=0.5, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op07_room_ff', ctx('OP07', 'extended', room=True), 9, ((7, 255), (8, 100)),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, overlay_raw=255, overlay_state='present',
          room_numeric=127.5, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op01_no_offsets', ctx('OP01', 'fan', room=True), 12, ((7, 64), (8, 128)),
          selected_alternative='fan', operation='OP01', admission='raw_only',
          reason='unknown_operation', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None),
    _case('direction_request', ctx(direction='request'), 12, ((8, 128),),
          direction='request', admission='raw_only', reason='direction',
          required_extent=None, complete_logical_extent=False,
          extent_state='not_admitted', layout_grade=None),
    _case('unknown_overlay', ctx('OP07', 'unknown-overlay', room=True), 9,
          ((7, 64), (8, 100)),
          selected_alternative='unknown-overlay', operation='OP07',
          available_extent=9, admission='raw_only', reason='unknown_overlay',
          required_extent=None, complete_logical_extent=False,
          extent_state='not_admitted', layout_grade=None),
    _case('op07_fan_mismatch', ctx('OP07', 'fan', room=True), 9, ((7, 64), (8, 128)),
          selected_alternative='fan', operation='OP07', available_extent=9,
          admission='raw_only', reason='unknown_overlay', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None),
    _case('op00_extended_mismatch', ctx('OP00', 'extended', room=True), 12,
          ((7, 64), (8, 100)),
          selected_alternative='extended', available_extent=12, admission='raw_only',
          reason='unknown_overlay', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None),
    _case('empty_family', ctx(family=''), 12, ((8, 128),), table=False,
          family='', admission='raw_only', reason='context', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None, selected_alternative='fan'),
    _case('missing_alternative', _MISSING_ALTERNATIVE, 12, ((8, 128),), table=False,
          admission='raw_only', reason='context', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None, selected_alternative=None),
    _case('room_flag_integer', _ROOM_FLAG_INTEGER, 12, ((8, 128),), table=False,
          admission='raw_only', reason='context', required_extent=None,
          complete_logical_extent=False, extent_state='not_admitted',
          layout_grade=None),
    _case('empty_image', ctx(), 0, (),
          available_extent=0, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=list(range(12))),
    _case('hole_logical8', ctx('OP07', 'extended', room=True), 12, ((7, 64), (9, 100)),
          holes=(8,), table=False,
          selected_alternative='extended', operation='OP07', available_extent=12,
          required_extent=9, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=[8], overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_domain='missing', pressure_availability='missing',
          pressure_grades=UUU),
    _case('unmodelled_byte7', ctx('OP07', 'extended', room=True), 9, ((8, 100),),
          unmodelled=((7, 64),),
          selected_alternative='extended', operation='OP07', available_extent=9,
          required_extent=9, complete_logical_extent=False, extent_state='incomplete',
          missing_positions=[7], overlay_raw=64, overlay_state='unmodelled',
          room_numeric=None, room_availability='unmodelled', room_unit=None,
          room_grades=UUU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
    _case('op00_len13', ctx(), 13, ((8, 128), (12, 9)),
          available_extent=13, fan_running=True, fan_label='fan-running',
          raw_flag_byte=128, fan_grades=HHU),
    _case('op07_ext_len13', ctx('OP07', 'extended', room=True), 13,
          ((7, 64), (8, 100), (12, 9)),
          selected_alternative='extended', operation='OP07', available_extent=13,
          required_extent=9, overlay_raw=64, overlay_state='present',
          room_numeric=32.0, room_availability='present', room_unit='degrees_Celsius',
          room_grades=HHU, pressure_numeric=100, pressure_raw=100,
          pressure_unit='percent', pressure_domain='in_domain',
          pressure_availability='present', pressure_grades=HHU),
]


def materialize(case, context=None):
    context = copy.deepcopy(case['context'] if context is None else context)
    length = case['length']
    image = []
    for index in range(length):
        image.append(PREFIX[index] if index < 3 else 0)
    for index, value in case['cells']:
        image[index] = value
    for index in case['holes']:
        image[index] = None
    for index, value in case['unmodelled']:
        image[index] = {'raw': value, 'modelled': False}
    return context, image


def parse_image(image):
    if isinstance(image, memoryview):
        image = image.tobytes()
    if isinstance(image, (bytes, bytearray)):
        return [{'position': index, 'state': 'present', 'raw': byte}
                for index, byte in enumerate(image)]
    if not isinstance(image, (list, tuple)):
        raise TypeError('image')
    cells = []
    for index, cell in enumerate(image):
        if cell is None:
            cells.append({'position': index, 'state': 'missing', 'raw': None})
            continue
        if isinstance(cell, bool) or isinstance(cell, int):
            if isinstance(cell, bool) or not 0 <= cell <= 255:
                raise TypeError('cell')
            cells.append({'position': index, 'state': 'present', 'raw': cell})
            continue
        if isinstance(cell, dict) and set(cell) == {'raw', 'modelled'} and cell['modelled'] is False:
            raw = cell['raw']
            if isinstance(raw, bool) or not isinstance(raw, int) or not 0 <= raw <= 255:
                raise TypeError('cell')
            cells.append({'position': index, 'state': 'unmodelled', 'raw': raw})
            continue
        raise TypeError('cell')
    return cells


def context_problem(context):
    required = ('family', 'variant', 'operation', 'direction', 'alternative',
                'select_room_setpoint')
    if any(key not in context for key in required):
        return 'context'
    for key in required[:-1]:
        if not isinstance(context[key], str) or context[key] == '':
            return 'context'
    if not isinstance(context['select_room_setpoint'], bool):
        return 'context'
    return None


def _grades(numeric, semantic):
    return {
        'numeric_grade': numeric,
        'semantic_grade': semantic,
        'native_grade': 'Unknown',
    }


def _at(cells, index):
    if index < 0 or index >= len(cells):
        return None
    return cells[index]


def ab11an11_view(context, logical_image, policy=None):
    """Policy-driven reference for the hypothetical ab11an11 helper."""
    policy = POLICY if policy is None else policy
    if not isinstance(context, Mapping) or isinstance(context, (str, bytes, bytearray)):
        raise TypeError('context')
    cells = parse_image(logical_image)
    raw_cells = [dict(cell) for cell in cells]
    if policy.get('insert_or_remove_prefix') and len(cells) >= 3:
        cells = []
        for index, cell in enumerate(raw_cells[3:]):
            moved = dict(cell)
            moved['position'] = index
            cells.append(moved)
        raw_cells = [dict(cell) for cell in cells]
    ctx = copy.deepcopy(context)
    reason = context_problem(ctx)
    if reason is None and ctx['direction'] != policy['direction']:
        reason = 'direction'
    if reason is None and policy.get('infer_operation_from_prefix'):
        prefix = _at(cells, 2)
        if prefix and prefix['state'] == 'present' and prefix['raw'] in (0x00, 0x07):
            ctx['operation'] = 'OP00' if prefix['raw'] == 0x00 else 'OP07'
    if reason is None and policy.get('select_variant_from_length'):
        ctx['variant'] = 'length-%d' % len(raw_cells)
    if reason is None and policy.get('select_alternative_from_length'):
        extent = len(cells)
        if extent >= 12:
            ctx['alternative'] = 'fan'
        elif extent >= 9:
            ctx['alternative'] = 'extended'
        else:
            ctx['alternative'] = 'base'
    operation = ctx.get('operation')
    alternative = ctx.get('alternative')
    applied = False
    if reason is None:
        if operation not in policy['operations']:
            reason = 'unknown_operation'
        elif operation == 'OP00' and alternative not in policy['op00_alternatives']:
            reason = 'unknown_overlay'
        elif operation == 'OP07' and alternative not in policy['op07_alternatives']:
            reason = 'unknown_overlay'
        else:
            applied = True
            reason = None
    if (not applied and reason == 'unknown_operation'
            and policy.get('invent_offsets_for_other_classes')):
        applied = True
        reason = None
        operation = 'OP07'
        alternative = 'base'
        ctx['operation'] = operation
        ctx['alternative'] = alternative
    if applied and operation == 'OP00':
        required = policy['op00_required_extent']
    elif applied and operation == 'OP07' and alternative == 'extended':
        required = policy['op07_extended_required_extent']
    elif applied and operation == 'OP07' and alternative == 'base':
        required = policy['op07_base_required_extent']
    else:
        required = None
    missing = []
    if required is not None:
        for index in range(required):
            cell = _at(cells, index)
            if cell is None or cell['state'] != 'present':
                missing.append(index)
    if (policy.get('hide_missing_ninth_position') and alternative == 'extended'
            and missing == [policy['pressure_position']]):
        missing = []
    complete = applied and required is not None and not missing
    fields = {}
    raw_flag = None
    fan_running = None
    if applied and operation == 'OP00':
        flag = _at(cells, policy['pressure_position'])
        if flag and flag['state'] == 'present':
            raw_flag = flag['raw']
            bit = policy['logical8_bit7']
            named = bool(raw_flag & (1 << bit))
            if alternative == 'fan' or (
                    alternative == 'reserved' and named
                    and policy.get('label_reserved_bit7_as_fan')):
                fan_running = named
                fields['fan_running'] = {
                    'key': 'fan_running',
                    'position': policy['pressure_position'],
                    'bit': bit,
                    'raw': raw_flag,
                    'value': named,
                    'semantic_label': policy['fan_bit7_label'],
                    'availability': 'present',
                }
                fields['fan_running'].update(_grades('Hypothesis', 'Hypothesis'))
            elif alternative == 'reserved':
                fields['reserved_bit7'] = {
                    'key': 'reserved_bit7',
                    'position': policy['pressure_position'],
                    'bit': bit,
                    'raw': raw_flag,
                    'value': None,
                    'semantic_label': policy['reserved_bit7_label'],
                    'availability': 'reserved',
                }
                fields['reserved_bit7'].update(_grades('Unknown', 'Unknown'))
    overlay = None
    room = None
    pressure = None
    if applied and operation == 'OP07':
        overlay_cell = _at(cells, policy['room_setpoint_position'])
        if overlay_cell is None:
            overlay = {
                'position': policy['room_setpoint_position'],
                'raw': None,
                'state': 'missing',
            }
        else:
            overlay = {
                'position': policy['room_setpoint_position'],
                'raw': overlay_cell['raw'],
                'state': overlay_cell['state'],
            }
        fields['raw_overlay'] = dict(overlay)
        if ctx.get('select_room_setpoint') is True:
            room = {
                'key': 'room_setpoint',
                'position': policy['room_setpoint_position'],
                'raw': None if overlay_cell is None else overlay_cell['raw'],
                'numeric': None,
                'scale': policy['room_setpoint_scale'],
                'unit': None,
                'availability': 'missing',
            }
            room.update(_grades('Unknown', 'Unknown'))
            if overlay_cell and overlay_cell['state'] == 'present':
                room['numeric'] = overlay_cell['raw'] / policy['room_setpoint_divisor']
                room['unit'] = policy['room_setpoint_unit']
                room['availability'] = 'present'
                room.update(_grades('Hypothesis', 'Hypothesis'))
            elif overlay_cell and overlay_cell['state'] == 'unmodelled':
                room['availability'] = 'unmodelled'
            fields['room_setpoint'] = room
        if alternative == 'extended':
            source = _at(cells, policy['pressure_position'])
            if (policy.get('infer_fields_from_list_order')
                    and (source is None or source['state'] != 'present')):
                for cell in cells:
                    if (cell['position'] > policy['pressure_position']
                            and cell['state'] == 'present'):
                        source = cell
                        break
            pressure = {
                'key': policy['pressure_label'],
                'position': policy['pressure_position'],
                'raw': None,
                'numeric': None,
                'unit': None,
                'domain': 'missing',
                'availability': 'missing',
            }
            pressure.update(_grades('Unknown', 'Unknown'))
            if source and source['state'] == 'present':
                raw = source['raw']
                low = policy['pressure_domain_min']
                high = policy['pressure_domain_max']
                pressure['raw'] = raw
                pressure['position'] = source['position']
                if low <= raw <= high:
                    pressure['numeric'] = raw
                    pressure['unit'] = policy['pressure_unit']
                    pressure['domain'] = 'in_domain'
                    pressure['availability'] = 'present'
                    pressure.update(_grades('Hypothesis', 'Hypothesis'))
                    if policy.get('convert_percent_to_bar'):
                        pressure['numeric'] = raw / 10
                        pressure['unit'] = 'bar'
                elif policy.get('clip_out_of_domain'):
                    pressure['numeric'] = high if raw > high else low
                    pressure['unit'] = policy['pressure_unit']
                    pressure['domain'] = 'in_domain'
                    pressure['availability'] = 'present'
                    pressure.update(_grades('Hypothesis', 'Hypothesis'))
                else:
                    pressure['unit'] = policy['pressure_unit']
                    pressure['domain'] = 'out_of_domain'
                    pressure['availability'] = 'out_of_domain'
            fields['pressure'] = pressure
    concatenated = None
    if (policy.get('concatenate_overlapping_fields') and room and pressure
            and room.get('numeric') is not None and pressure.get('numeric') is not None):
        concatenated = '%s/%s' % (room['numeric'], pressure['numeric'])
        room = None
        pressure = None
        fields.pop('room_setpoint', None)
        fields.pop('pressure', None)
    selected = alternative if isinstance(alternative, str) else None
    return {
        'context': ctx,
        'selected_alternative': selected,
        'admission': 'applied' if applied else 'raw_only',
        'reason': reason,
        'available_extent': len(raw_cells),
        'required_extent': required,
        'complete_logical_extent': complete,
        'extent_state': 'complete' if complete else (
            'incomplete' if applied else 'not_admitted'),
        'missing_positions': missing,
        'raw_cells': raw_cells,
        'raw_flag_byte': raw_flag,
        'fan_running': fan_running,
        'raw_overlay': overlay,
        'room_setpoint': room,
        'pressure': pressure,
        'concatenated': concatenated,
        'fields': fields,
        'qualification': dict(QUALIFICATION),
        'software_contract': 'Proven',
        'layout_grade': policy['layout_grade'] if applied else None,
        'native_grade': 'Unknown',
        'runtime_route_decoder': False,
    }


def project(result):
    fan = result['fields'].get('fan_running')
    reserved = result['fields'].get('reserved_bit7')
    room = result['room_setpoint']
    pressure = result['pressure']
    overlay = result['raw_overlay']

    def grades(field):
        if field is None:
            return None
        return [field['numeric_grade'], field['semantic_grade'], field['native_grade']]

    return {
        'admission': result['admission'],
        'reason': result['reason'],
        'selected_alternative': result['selected_alternative'],
        'family': result['context'].get('family'),
        'variant': result['context'].get('variant'),
        'operation': result['context'].get('operation'),
        'direction': result['context'].get('direction'),
        'available_extent': result['available_extent'],
        'required_extent': result['required_extent'],
        'complete_logical_extent': result['complete_logical_extent'],
        'extent_state': result['extent_state'],
        'missing_positions': result['missing_positions'],
        'fan_running': result['fan_running'],
        'fan_label': None if fan is None else fan['semantic_label'],
        'raw_flag_byte': result['raw_flag_byte'],
        'reserved_label': None if reserved is None else reserved['semantic_label'],
        'overlay_raw': None if overlay is None else overlay['raw'],
        'overlay_state': None if overlay is None else overlay['state'],
        'room_numeric': None if room is None else room['numeric'],
        'room_availability': None if room is None else room['availability'],
        'room_unit': None if room is None else room['unit'],
        'pressure_numeric': None if pressure is None else pressure['numeric'],
        'pressure_raw': None if pressure is None else pressure['raw'],
        'pressure_unit': None if pressure is None else pressure['unit'],
        'pressure_domain': None if pressure is None else pressure['domain'],
        'pressure_availability': None if pressure is None else pressure['availability'],
        'concatenated': result['concatenated'],
        'layout_grade': result['layout_grade'],
        'fan_grades': grades(fan),
        'room_grades': grades(room),
        'pressure_grades': grades(pressure),
    }


def cell_token(case, index):
    if index in case['holes']:
        return 'missing'
    for raw_index, _value in case['unmodelled']:
        if raw_index == index:
            return 'unmodelled'
    if index >= case['length']:
        return 'missing'
    for raw_index, value in case['cells']:
        if raw_index == index:
            return str(value)
    if index < 3:
        return str(PREFIX[index])
    return '0'


def display_token(value):
    if value is None:
        return 'none'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return str(value)


def table_line(case):
    exp = case['expect']
    fan = exp['reserved_label'] or display_token(exp['fan_running'])
    setpoint = exp['room_numeric']
    if exp['room_availability'] == 'unmodelled':
        setpoint = 'unmodelled'
    elif exp['room_availability'] is None and exp['operation'] == 'OP07' and exp['admission'] == 'applied':
        setpoint = 'not_selected'
    return '| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
        case['name'], exp['family'], exp['variant'], exp['operation'], exp['direction'],
        exp['selected_alternative'], display_token(case['context']['select_room_setpoint']),
        case['length'], cell_token(case, 7), cell_token(case, 8), exp['admission'],
        display_token(exp['reason']), exp['extent_state'], fan,
        display_token(exp['raw_flag_byte']), display_token(exp['overlay_raw']),
        display_token(setpoint), display_token(exp['pressure_numeric']),
        display_token(exp['pressure_domain']),
    )


def grade_line(case, field):
    exp = case['expect']
    grades = exp['fan_grades'] if field == 'fan_running' else (
        exp['room_grades'] if field == 'room_setpoint' else exp['pressure_grades'])
    if grades is None:
        return None
    return '| %s | %s | %s | %s | %s |' % (
        case['name'], field, grades[0], grades[1], grades[2])


def slug(heading):
    return re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')


def load_policy(page):
    return json.loads(re.search(r'```json\n(.*?)\n```', page, re.S)[1])


def behavior_failures(policy, case):
    context, image = materialize(case)
    result = ab11an11_view(context, image, policy)
    actual = project(result)
    failures = []
    for key, expected in case['expect'].items():
        if actual[key] != expected:
            failures.append('%s %s %r != %r' % (case['name'], key, actual[key], expected))
    if policy.get('preserve_complete_raw_image', True) and not policy.get('insert_or_remove_prefix'):
        if result['raw_cells'] != parse_image(image):
            failures.append('%s raw image changed' % case['name'])
    if set(result['fields']) & {'flow_temperature', 'modulation', 'bar_pressure', 'concatenated'}:
        failures.append('%s invented field' % case['name'])
    if result['native_grade'] != 'Unknown' or result['qualification'] != QUALIFICATION:
        failures.append('%s grade promotion' % case['name'])
    if result['software_contract'] != 'Proven' or result['runtime_route_decoder'] is not False:
        failures.append('%s contract promotion' % case['name'])
    return failures


class B511OverlapViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.package = json.loads(FIXTURE.read_text())

    def test_policy_page_links_and_package(self):
        self.assertEqual(load_policy(self.page), POLICY)
        self.assertEqual(self.package['policy'], POLICY)
        self.assertEqual(self.package['identity_axes'], AXES)
        self.assertEqual(self.package['bit_rows'], BIT_ROWS)
        self.assertEqual([item['name'] for item in self.package['examples']],
                         [case['name'] for case in CASES])
        for published, case in zip(self.package['examples'], CASES):
            self.assertEqual(published['context'], case['context'])
            self.assertEqual(published['length'], case['length'])
            self.assertEqual(published['cells'], case['cells'])
            self.assertEqual(published['holes'], case['holes'])
            self.assertEqual(published['unmodelled'], case['unmodelled'])
            self.assertEqual(published['expect'], case['expect'])
        for sentence in SENTENCES:
            self.assertIn(sentence, self.page)
        for case in CASES:
            if case['table']:
                self.assertIn(table_line(case), self.page)
            for field in ('fan_running', 'room_setpoint', 'pressure'):
                line = grade_line(case, field)
                if line and case['table']:
                    self.assertIn(line, self.page)
        self.assertIn('| empty_family | context |', self.page)
        self.assertIn('| missing_alternative | context |', self.page)
        self.assertIn('| room_flag_integer | context |', self.page)
        self.assertIn('| hole_logical8 | applied |', self.page)
        self.assertIn('| unmodelled_byte7 | applied |', self.page)
        self.assertIn(
            '| op00_reserved_80 | reserved_bit7 | Unknown | Unknown | Unknown |',
            self.page)
        for link in re.findall(r'\]\(([^)]+)\)', self.page):
            path, _, anchor = link.partition('#')
            target = (PAGE.parent / path).resolve()
            self.assertTrue(target.is_file(), link)
            if anchor:
                headings = re.findall(r'^#+ (.+)$', target.read_text(), re.M)
                self.assertIn(anchor, [slug(heading) for heading in headings], link)
        self.assertFalse(POLICY['select_alternative_from_length'])
        self.assertFalse(POLICY['select_variant_from_length'])
        self.assertFalse(POLICY['label_reserved_bit7_as_fan'])
        self.assertFalse(POLICY['concatenate_overlapping_fields'])
        self.assertFalse(POLICY['convert_percent_to_bar'])
        self.assertFalse(POLICY['clip_out_of_domain'])
        self.assertFalse(POLICY['hide_missing_ninth_position'])
        self.assertFalse(POLICY['invent_offsets_for_other_classes'])
        self.assertEqual(POLICY['pressure_unit'], 'percent')
        self.assertEqual(POLICY['reserved_bit7_label'], 'reserved')
        self.assertEqual(POLICY['other_class_offsets'], {})
        self.assertEqual(POLICY['op00_required_extent'], 12)
        self.assertEqual(POLICY['op07_base_required_extent'], 8)
        self.assertEqual(POLICY['op07_extended_required_extent'], 9)
        self.assertEqual(POLICY['room_setpoint_divisor'], 2)
        self.assertEqual(POLICY['pressure_domain_max'], 100)

    def test_published_examples_match_independent_literals(self):
        self.assertGreaterEqual(len(CASES), 20)
        for case in CASES:
            with self.subTest(case=case['name']):
                context, image = materialize(case)
                result = ab11an11_view(context, image, POLICY)
                self.assertEqual(behavior_failures(POLICY, case), [])
                self.assertEqual(project(result), case['expect'])
                self.assertIsInstance(result['fields'], dict)
                self.assertIsNot(result['context'], context)
                if case['name'] == 'op00_fan_80':
                    self.assertEqual(result['fan_running'], True)
                    self.assertEqual(result['raw_flag_byte'], 0x80)
                    self.assertEqual(result['raw_cells'][0]['raw'], 0x11)
                    self.assertEqual(result['raw_cells'][5]['raw'], 0)
                    self.assertEqual(result['raw_cells'][8]['raw'], 0x80)
                    self.assertTrue(result['complete_logical_extent'])
                    self.assertEqual(result['required_extent'], 12)
                if case['name'] == 'op00_reserved_80':
                    self.assertIsNone(result['fan_running'])
                    self.assertEqual(result['raw_flag_byte'], 0x80)
                    self.assertEqual(result['fields']['reserved_bit7']['semantic_label'], 'reserved')
                    self.assertNotEqual(
                        result['fields']['reserved_bit7']['semantic_label'], 'fan-running')
                    self.assertTrue(result['complete_logical_extent'])
                if case['name'] == 'op07_ext_40_101':
                    self.assertEqual(result['room_setpoint']['numeric'], 32)
                    self.assertEqual(result['raw_overlay']['raw'], 0x40)
                    self.assertIsNone(result['pressure']['numeric'])
                    self.assertEqual(result['pressure']['raw'], 101)
                    self.assertEqual(result['pressure']['unit'], 'percent')
                    self.assertNotEqual(result['pressure']['unit'], 'bar')
                    self.assertNotEqual(result['pressure']['numeric'], 100)
                    self.assertNotEqual(result['pressure']['numeric'], 10)
                    self.assertIsNone(result['concatenated'])
                if case['name'] == 'op07_base_len8':
                    self.assertTrue(result['complete_logical_extent'])
                    self.assertEqual(result['raw_overlay']['raw'], 0x40)
                    self.assertIsNone(result['pressure'])
                if case['name'] == 'op07_ext_len8':
                    self.assertFalse(result['complete_logical_extent'])
                    self.assertEqual(result['missing_positions'], [8])
                    self.assertEqual(result['raw_overlay']['raw'], 0x40)
                    self.assertEqual(result['room_setpoint']['numeric'], 32)
                    self.assertEqual(result['pressure']['availability'], 'missing')
                if case['name'] == 'op07_unknown_variant':
                    self.assertEqual(result['context']['variant'], 'unknown-variant')
                if case['name'] == 'hole_logical8':
                    self.assertEqual(result['pressure']['availability'], 'missing')
                    self.assertIsNone(result['pressure']['numeric'])
                    self.assertNotEqual(result['pressure']['numeric'], 100)
                    self.assertEqual(result['raw_cells'][9]['raw'], 100)
                    self.assertEqual(result['raw_cells'][8]['state'], 'missing')
                    self.assertEqual(result['room_setpoint']['numeric'], 32)
                if case['name'] == 'op01_no_offsets':
                    self.assertIsNone(result['room_setpoint'])
                    self.assertIsNone(result['fan_running'])
                    self.assertEqual(result['raw_cells'][7]['raw'], 0x40)
                    self.assertEqual(result['fields'], {})

    def test_each_byte8_bit_and_separate_bytes(self):
        self.assertEqual([row['bit'] for row in BIT_ROWS], list(range(8)))
        for row in BIT_ROWS:
            bit = row['bit']
            raw = row['raw']
            self.assertEqual(raw, 1 << bit)
            with self.subTest(bit=bit):
                fan_case = _case('bit_fan', ctx(), 12, ((8, raw),))
                fan = ab11an11_view(*materialize(fan_case), POLICY)
                self.assertEqual(fan['raw_flag_byte'], raw)
                self.assertEqual(fan['fan_running'], row['fan'])
                self.assertEqual(fan['fan_running'], bit == 7)
                self.assertEqual(set(fan['fields']), {'fan_running'})
                self.assertEqual(fan['fields']['fan_running']['bit'], 7)
                reserved_case = _case('bit_reserved', ctx(alternative='reserved'), 12, ((8, raw),))
                reserved = ab11an11_view(*materialize(reserved_case), POLICY)
                self.assertIsNone(reserved['fan_running'])
                self.assertEqual(reserved['raw_flag_byte'], raw)
                self.assertEqual(reserved['fields']['reserved_bit7']['semantic_label'], 'reserved')
                self.assertNotIn('fan_running', reserved['fields'])
                pressure_case = _case(
                    'bit_pressure', ctx('OP07', 'extended', room=True), 9, ((7, 64), (8, raw)))
                pressure = ab11an11_view(*materialize(pressure_case), POLICY)
                self.assertEqual(pressure['room_setpoint']['numeric'], 32.0)
                self.assertEqual(pressure['raw_overlay']['raw'], 64)
                self.assertEqual(pressure['pressure']['domain'], row['pressure_domain'])
                self.assertEqual(pressure['pressure']['numeric'], row['pressure_numeric'])
                self.assertEqual(pressure['pressure']['raw'], raw)
                self.assertEqual(pressure['pressure']['unit'], 'percent')
                self.assertNotEqual(pressure['pressure']['unit'], 'bar')
        for byte7 in (0, 1, 64, 66, 255):
            for byte8 in (0, 1, 64, 100, 101, 128, 255):
                with self.subTest(byte7=byte7, byte8=byte8):
                    case = _case(
                        'split', ctx('OP07', 'extended', room=True), 9,
                        ((7, byte7), (8, byte8)))
                    result = ab11an11_view(*materialize(case), POLICY)
                    self.assertEqual(result['room_setpoint']['numeric'], byte7 / 2)
                    self.assertEqual(result['raw_overlay']['raw'], byte7)
                    self.assertEqual(result['pressure']['raw'], byte8)
                    self.assertEqual(result['pressure']['unit'], 'percent')
                    if 0 <= byte8 <= 100:
                        self.assertEqual(result['pressure']['numeric'], byte8)
                        self.assertEqual(result['pressure']['domain'], 'in_domain')
                    else:
                        self.assertIsNone(result['pressure']['numeric'])
                        self.assertEqual(result['pressure']['domain'], 'out_of_domain')
                        self.assertNotEqual(result['pressure']['numeric'], 100)
                        self.assertNotEqual(result['pressure'].get('unit'), 'bar')
                    self.assertIsNone(result['concatenated'])
                    self.assertNotIn('concatenated', result['fields'])

    def test_identity_axes_lengths_and_other_classes(self):
        base_image = materialize(CASES[0])[1]
        base = ab11an11_view(ctx(), base_image, POLICY)
        for family in AXES['families']:
            result = ab11an11_view(ctx(family=family), base_image, POLICY)
            self.assertEqual(result['context']['family'], family)
            self.assertEqual(result['fan_running'], True)
            self.assertEqual(result['raw_flag_byte'], 128)
        for variant in AXES['variants']:
            result = ab11an11_view(ctx(variant=variant), base_image, POLICY)
            self.assertEqual(result['context']['variant'], variant)
            self.assertNotEqual(result['context']['variant'], 'length-12')
            self.assertEqual(result['fan_running'], base['fan_running'])
        request = ab11an11_view(ctx(direction='request'), base_image, POLICY)
        self.assertEqual(request['reason'], 'direction')
        self.assertIsNone(request['fan_running'])
        self.assertEqual(request['raw_cells'][8]['raw'], 128)
        response = ab11an11_view(ctx(direction='response'), base_image, POLICY)
        self.assertEqual(response['admission'], 'raw_only')
        reserved = ab11an11_view(ctx(alternative='reserved'), base_image, POLICY)
        self.assertIsNone(reserved['fan_running'])
        self.assertEqual(reserved['selected_alternative'], 'reserved')
        self.assertEqual(reserved['raw_flag_byte'], base['raw_flag_byte'])
        switched = list(base_image)
        switched[2] = 0x07
        held = ab11an11_view(ctx(), switched, POLICY)
        self.assertEqual(held['context']['operation'], 'OP00')
        self.assertEqual(held['fan_running'], True)
        for operation in ('OP01', 'OP02', 'OP03', 'OP0A', 'OP10'):
            foreign = ab11an11_view(
                ctx(operation, 'fan', room=True), materialize(CASES[0])[1], POLICY)
            self.assertEqual(foreign['reason'], 'unknown_operation')
            self.assertEqual(foreign['fields'], {})
            self.assertIsNone(foreign['room_setpoint'])
            self.assertIsNone(foreign['pressure'])
            self.assertEqual(foreign['raw_cells'][8]['raw'], 128)
        for length in (0, 3, 7, 8, 9, 11, 12, 13):
            image = [PREFIX[index] if index < 3 else 0 for index in range(length)]
            if length > 8:
                image[8] = 128
            fan = ab11an11_view(ctx(), image, POLICY)
            self.assertEqual(fan['available_extent'], length)
            self.assertEqual(fan['complete_logical_extent'], length >= 12)
            self.assertEqual(fan['required_extent'], 12)
            extended = ab11an11_view(ctx('OP07', 'extended', room=True), image, POLICY)
            base_alt = ab11an11_view(ctx('OP07', 'base', room=True), image, POLICY)
            self.assertEqual(extended['complete_logical_extent'], length >= 9)
            self.assertEqual(base_alt['complete_logical_extent'], length >= 8)
            self.assertEqual(extended['required_extent'], 9)
            self.assertEqual(base_alt['required_extent'], 8)
            if length == 8:
                self.assertFalse(extended['complete_logical_extent'])
                self.assertTrue(base_alt['complete_logical_extent'])
                self.assertIn(8, extended['missing_positions'])
            if length > 8:
                self.assertIsNone(base_alt['pressure'])
                self.assertEqual(fan['selected_alternative'], 'fan')
                self.assertNotEqual(fan['selected_alternative'], 'base')

    def test_detached_buffers_and_type_errors(self):
        caller, payload_list = materialize(next(case for case in CASES if case['name'] == 'op07_ext_40_100'))
        caller['note'] = {'kept': 1}
        caller['actual_support'] = 'Proven'
        payload = bytearray(payload_list)
        snapshot = copy.deepcopy(caller)
        result = ab11an11_view(caller, payload, POLICY)
        payload[7] = 0
        payload[8] = 0
        caller['note']['kept'] = 9
        caller['variant'] = 'mutated'
        self.assertEqual(result['context']['note']['kept'], 1)
        self.assertEqual(result['context']['variant'], snapshot['variant'])
        self.assertEqual(result['raw_overlay']['raw'], 64)
        self.assertEqual(result['pressure']['numeric'], 100)
        self.assertEqual(result['qualification']['actual_support'], 'Unknown')
        self.assertEqual(payload[7], 0)
        result['raw_cells'][7]['raw'] = 1
        result['context']['note']['kept'] = 3
        self.assertEqual(caller['note']['kept'], 9)
        self.assertEqual(payload[7], 0)
        backed = bytearray(materialize(CASES[0])[1])
        viewed = ab11an11_view(ctx(), memoryview(backed), POLICY)
        backed[8] = 0
        self.assertEqual(viewed['raw_flag_byte'], 128)
        listed = materialize(CASES[0])[1]
        as_bytes = ab11an11_view(ctx(), bytes(listed), POLICY)
        self.assertEqual(as_bytes['fan_running'], True)
        unmodelled = {'raw': 64, 'modelled': False}
        image = materialize(CASES[25])[1]
        image[7] = unmodelled
        kept = ab11an11_view(ctx('OP07', 'extended', room=True), image, POLICY)
        unmodelled['raw'] = 1
        self.assertEqual(kept['raw_overlay']['raw'], 64)
        for image in (None, object(), 'image', 12):
            with self.assertRaises(TypeError):
                ab11an11_view(ctx(), image, POLICY)
        for bad in (None, [], 'context', bytearray()):
            with self.assertRaises(TypeError):
                ab11an11_view(bad, [0], POLICY)
        with self.assertRaises(TypeError):
            ab11an11_view(ctx(), [True], POLICY)
        with self.assertRaises(TypeError):
            ab11an11_view(ctx(), [256], POLICY)
        with self.assertRaises(TypeError):
            ab11an11_view(ctx(), [-1], POLICY)

    def test_executed_mutants_of_owned_copies(self):
        page = PAGE.read_text()
        fixture = FIXTURE.read_text()
        root = Path(os.environ.get('TMPDIR') or (ROOT / '.tmp'))
        scratch = root / 'an12-mutants'
        if scratch.exists():
            shutil.rmtree(scratch)
        scratch.mkdir(parents=True)
        try:
            mutations = (
                ('select_alternative_from_length', {'select_alternative_from_length': True},
                 'op00_reserved_80'),
                ('select_variant_from_length', {'select_variant_from_length': True},
                 'op07_unknown_variant'),
                ('label_reserved_bit7_as_fan', {'label_reserved_bit7_as_fan': True},
                 'op00_reserved_80'),
                ('concatenate_overlapping_fields', {'concatenate_overlapping_fields': True},
                 'op07_ext_40_100'),
                ('convert_percent_to_bar', {'convert_percent_to_bar': True},
                 'op07_ext_40_100'),
                ('clip_out_of_domain', {'clip_out_of_domain': True}, 'op07_ext_40_101'),
                ('hide_missing_ninth_position', {'hide_missing_ninth_position': True},
                 'op07_ext_len8'),
                ('invent_offsets_for_other_classes',
                 {'invent_offsets_for_other_classes': True}, 'op01_no_offsets'),
                ('insert_or_remove_prefix', {'insert_or_remove_prefix': True}, 'op00_fan_80'),
                ('infer_fields_from_list_order', {'infer_fields_from_list_order': True},
                 'hole_logical8'),
                ('infer_operation_from_prefix', {'infer_operation_from_prefix': True},
                 'op00_fan_80'),
                ('room_divisor', {'room_setpoint_divisor': 10}, 'op07_ext_40_100'),
                ('pressure_domain', {'pressure_domain_max': 101}, 'op07_ext_40_101'),
            )
            for name, patch, case_name in mutations:
                page_copy = scratch / (name + '.md')
                fixture_copy = scratch / (name + '.json')
                page_copy.write_text(_patch_page(page, patch))
                package = json.loads(fixture)
                package['policy'].update(patch)
                fixture_copy.write_text(json.dumps(package, indent=2) + '\n')
                copied_policy = load_policy(page_copy.read_text())
                self.assertEqual(copied_policy, json.loads(fixture_copy.read_text())['policy'])
                case = next(item for item in CASES if item['name'] == case_name)
                if name == 'infer_operation_from_prefix':
                    context, image = materialize(case)
                    image = list(image)
                    image[2] = 0x07
                    result = ab11an11_view(context, image, copied_policy)
                    self.assertNotEqual(result['context']['operation'], 'OP00')
                    self.assertIsNone(result['fan_running'])
                else:
                    self.assertNotEqual(behavior_failures(copied_policy, case), [])
            prose = scratch / 'prose.md'
            prose.write_text(page.replace(
                'The reserved alternative does not name logical 8 bit 7 fan-running.',
                'The reserved alternative names logical 8 bit 7 fan-running.',
                1))
            self.assertNotIn(SENTENCES[9], prose.read_text())
            shifted = json.loads(fixture)
            for example in shifted['examples']:
                if example['name'] == 'op00_reserved_80':
                    example['expect']['fan_running'] = True
            (scratch / 'fixture-fan.json').write_text(json.dumps(shifted, indent=2) + '\n')
            published = next(item for item in json.loads(
                (scratch / 'fixture-fan.json').read_text())['examples']
                if item['name'] == 'op00_reserved_80')
            literal = next(item for item in CASES if item['name'] == 'op00_reserved_80')
            self.assertNotEqual(published['expect'], literal['expect'])
        finally:
            shutil.rmtree(scratch)
        self.assertEqual(PAGE.read_text(), page)
        self.assertEqual(FIXTURE.read_text(), fixture)


def _patch_page(page, updates):
    match = re.search(r'```json\n(.*?)\n```', page, re.S)
    policy = json.loads(match.group(1))
    policy.update(updates)
    body = json.dumps(policy, indent=2)
    return page[:match.start(1)] + body + page[match.end(1):]


if __name__ == '__main__':
    unittest.main()
