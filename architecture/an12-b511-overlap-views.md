# B511 variant-specific logical overlays

**Proven — software contract.** AN12 defines `ab11an11.view(context, logical_image)`, a pure view of one caller-selected B511 logical image. The hypothetical signature is the ab11an11 helper API. This page does not import companion code and does not wait for a code change. Pair with AN11. This ordinary companion has no dependency on the code.

The public native contract comes first: [B511 operating-data classes](../protocols/vaillant/ebus-vaillant-b511.md#operating-data-classes-candidate). That section is **Hypothesis**, unconfirmed on the wire. This page does not repeat that family page and does not add native qualification. Native candidate codecs on that page are not imported.

## Pure helper boundary

`ab11an11.view(context, logical_image)` returns one result. It does not send, poll, open a control path, or store last-known-good state. A partial result keeps the complete raw image and every independent field that is already available. It does not replace caller state. No decoder is attached to existing runtime routes. eBUS MCP compatibility and GraphQL parity are unchanged. This helper is not an MCP tool and adds no GraphQL field. Nothing in this contract is stable before Helianthus 1.0. It adds no namespace and no authorization gate.

Family, variant, operation, direction and alternative are explicit caller selections. The helper does not infer them from image length, from list order, or from a prefix byte. Unknown variants are preserved. Caller buffers are copied before interpretation. Later mutation of the caller image or context does not change the result.

## Logical image

A logical image retains the three prefix positions 0, 1 and 2. No physical prefix insertion or removal is defined. No transmission shape is defined. Positions are 0-based view coordinates. Both OP00 alternatives occupy 12 logical positions, indexes 0 through 11. The OP07 base alternative occupies 8 logical positions, indexes 0 through 7. The OP07 extended alternative occupies 9 logical positions, indexes 0 through 8. Logical 8 on the extended alternative is the ninth position.

These are distinct view alternatives. Response length does not select the alternative, the variant, or the operation.

`bytes`, `bytearray` and `memoryview` are sequences of present bytes. A list or tuple may contain an integer 0..255, null for a missing cell, or `{"raw": <byte>, "modelled": false}` for an unmodelled cell. Any other container or cell raises `TypeError`. Booleans are not integers. No other field is inferred from its order in a list. A hole at logical 8 does not move a later byte into the pressure field.

## Context

Required keys are `family`, `variant`, `operation`, `direction`, `alternative` and `select_room_setpoint`. The first five are non-empty strings. `select_room_setpoint` is a boolean. An empty family, empty variant, empty operation, empty alternative, missing key, or non-boolean room selection is malformed context and is reported before direction. Admitted direction is the exact string `positive`. Admitted operations are `OP00` and `OP07`. Admitted OP00 alternatives are `reserved` and `fan`. Admitted OP07 alternatives are `base` and `extended`. Any other operation is an unknown operation. Any other alternative for the selected operation is an unknown overlay. Unknown overlays retain bytes and receive no invented labels. Other classes receive no invented offsets.

Example families are `synthetic-b511-family-a` and `synthetic-b511-family-b`. Example variants are `synthetic-variant-a`, `synthetic-variant-b` and `unknown-variant`. Any other non-empty family or variant is retained. These labels are not an admission catalog and not a device-model list.

## Hypothesis — OP00 flag byte

**Hypothesis.** Both positive alternatives require 12 logical positions for a complete extent. At logical 8 bit 7, the reserved alternative marks the bit reserved. The fan alternative names that bit fan-running. The reserved alternative does not name logical 8 bit 7 fan-running. OP00 logical 8 byte 80 hex yields fan true only under the fan alternative. Under the reserved alternative the same byte stays reserved raw 80 hex. All bits of the raw flag byte stay present, including the reserved bit. No other bit of that byte receives a name. A shorter image stays incomplete for both alternatives. A present flag byte on an incomplete image stays available.

## Hypothesis — OP07 overlap

**Hypothesis.** The base alternative is complete at 8 logical positions. The extended alternative is complete only when the ninth position, logical 8, is present and modelled. A length 8 image is complete only as the base alternative. The same length 8 image is incomplete as the extended alternative and retains byte 7. A missing ninth position stays visible.

Logical 7 is an overlap. The raw overlay of byte 7 is retained. The room-setpoint view is separate and is emitted only when `select_room_setpoint` is true. Its candidate scale is u8/2 degrees Celsius. OP07 extended byte 7 raw 40 hex yields room setpoint 32 degrees Celsius and retains overlay 40 hex. Overlapping structures stay separate and are not concatenated. Selecting the room-setpoint view does not remove the raw overlay or the pressure view.

Logical 8 on the extended alternative is building-circuit-pressure. The candidate codec is percent with inclusive domain 0..100. Byte 8 raw 100 yields percent 100. Byte 8 raw 101 stays raw and out of domain without clipping or bar conversion. The percent-labelled pressure is not converted to bar. Values inside the domain keep the percent unit. Values outside the domain keep the raw byte, withhold the numeric, and do not change the room setpoint. Bytes 7 and 8 are independent. Changing one does not change the other field.

## Result

The result returns the selected alternative, the available extent, the complete-logical-extent state, the raw flag byte, the optional named fan bit, the optional room setpoint, and the percent-labelled pressure with its domain state. It also returns the copied context, the complete raw cells, missing positions, per-field availability, and separate numeric, semantic and native grades.

Admission is fail closed. Malformed context, a non-positive direction, an unknown operation and an unknown overlay are raw-only. They keep the raw image and invent no fan label, room setpoint, pressure numeric, or offset for another class.

`layout_grade` on an applied alternative is Hypothesis. Native grade stays Unknown on every result and every field. Numeric grade and semantic grade are Hypothesis only for an applied fan bit, an applied in-domain room setpoint, and an applied in-domain percent. The reserved bit, an out-of-domain percent, a missing cell and a raw-only result stay Unknown for those grades. These grades are not collapsed. Other per-variant fields, other per-variant defaults, physical image adaptation, missing codecs, actual support, relationships to other class 07 reply shapes, presence, freshness and execution stay Unknown.

## Normative policy

The following policy is normative. The [synthetic example package](fixtures/an12_b511_overlap_views.json) publishes the finite rows. Example families and variants in that package are synthetic labels.

```json
{
  "signature": "ab11an11.view(context, logical_image)",
  "context_fields": [
    "family",
    "variant",
    "operation",
    "direction",
    "alternative",
    "select_room_setpoint"
  ],
  "direction": "positive",
  "operations": [
    "OP00",
    "OP07"
  ],
  "op00_alternatives": [
    "reserved",
    "fan"
  ],
  "op07_alternatives": [
    "base",
    "extended"
  ],
  "op00_required_extent": 12,
  "op07_base_required_extent": 8,
  "op07_extended_required_extent": 9,
  "prefix_positions": [
    0,
    1,
    2
  ],
  "insert_or_remove_prefix": false,
  "transmission_shape_defined": false,
  "select_alternative_from_length": false,
  "select_variant_from_length": false,
  "infer_operation_from_prefix": false,
  "infer_fields_from_list_order": false,
  "logical8_bit7": 7,
  "reserved_bit7_label": "reserved",
  "fan_bit7_label": "fan-running",
  "label_reserved_bit7_as_fan": false,
  "concatenate_overlapping_fields": false,
  "room_setpoint_position": 7,
  "room_setpoint_scale": "u8/2",
  "room_setpoint_divisor": 2,
  "room_setpoint_unit": "degrees_Celsius",
  "pressure_position": 8,
  "pressure_label": "building-circuit-pressure",
  "pressure_unit": "percent",
  "pressure_domain_min": 0,
  "pressure_domain_max": 100,
  "convert_percent_to_bar": false,
  "clip_out_of_domain": false,
  "hide_missing_ninth_position": false,
  "invent_offsets_for_other_classes": false,
  "other_class_offsets": {},
  "preserve_complete_raw_image": true,
  "preserve_unknown_variant": true,
  "detach_raw_buffers": true,
  "unknown_overlay_invents_labels": false,
  "software_contract": "Proven",
  "layout_grade": "Hypothesis",
  "native_grade": "Unknown",
  "runtime_route_decoder": false,
  "example_families": [
    "synthetic-b511-family-a",
    "synthetic-b511-family-b"
  ],
  "example_variants": [
    "synthetic-variant-a",
    "synthetic-variant-b",
    "unknown-variant"
  ]
}
```

## Finite examples

Decimal raw values are the byte integers. 128 is 80 hex. 64 is 40 hex. 129 is 81 hex. Prefix cells in these rows are 17, 34 and 51, which are 11, 22 and 33 hex. They are retained and are not a transmission shape. `none` means the view is absent. `missing` means the position was not supplied or is an explicit hole. `unmodelled` means the raw byte is retained and not typed.

| case | family | variant | operation | direction | alternative | room | length | byte7 | byte8 | admission | reason | extent | fan | flag | overlay | setpoint | pressure | domain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| op00_fan_80 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 12 | 0 | 128 | applied | none | complete | true | 128 | none | none | none | none |
| op00_reserved_80 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | reserved | false | 12 | 0 | 128 | applied | none | complete | reserved | 128 | none | none | none | none |
| op00_fan_len11 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 11 | 0 | 128 | applied | none | incomplete | true | 128 | none | none | none | none |
| op00_fan_len8 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 8 | 64 | missing | applied | none | incomplete | none | none | none | none | none | none |
| op00_fan_zero | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 12 | 0 | 0 | applied | none | complete | false | 0 | none | none | none | none |
| op00_fan_81 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 12 | 0 | 129 | applied | none | complete | true | 129 | none | none | none | none |
| op07_ext_40_100 | synthetic-b511-family-b | synthetic-variant-b | OP07 | positive | extended | true | 9 | 64 | 100 | applied | none | complete | none | none | 64 | 32.0 | 100 | in_domain |
| op07_ext_40_101 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | 64 | 101 | applied | none | complete | none | none | 64 | 32.0 | none | out_of_domain |
| op07_base_len8 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | base | true | 8 | 64 | missing | applied | none | complete | none | none | 64 | 32.0 | none | none |
| op07_ext_len8 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 8 | 64 | missing | applied | none | incomplete | none | none | 64 | 32.0 | none | missing |
| op07_ext_not_selected | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | false | 9 | 64 | 100 | applied | none | complete | none | none | 64 | not_selected | 100 | in_domain |
| op07_unknown_variant | synthetic-b511-family-a | unknown-variant | OP07 | positive | extended | true | 9 | 64 | 100 | applied | none | complete | none | none | 64 | 32.0 | 100 | in_domain |
| op07_split_42_100 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | 66 | 100 | applied | none | complete | none | none | 66 | 33.0 | 100 | in_domain |
| op07_pressure_0 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | 64 | 0 | applied | none | complete | none | none | 64 | 32.0 | 0 | in_domain |
| op07_room_half | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | 1 | 100 | applied | none | complete | none | none | 1 | 0.5 | 100 | in_domain |
| op07_room_ff | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | 255 | 100 | applied | none | complete | none | none | 255 | 127.5 | 100 | in_domain |
| op01_no_offsets | synthetic-b511-family-a | synthetic-variant-a | OP01 | positive | fan | true | 12 | 64 | 128 | raw_only | unknown_operation | not_admitted | none | none | none | none | none | none |
| direction_request | synthetic-b511-family-a | synthetic-variant-a | OP00 | request | fan | false | 12 | 0 | 128 | raw_only | direction | not_admitted | none | none | none | none | none | none |
| unknown_overlay | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | unknown-overlay | true | 9 | 64 | 100 | raw_only | unknown_overlay | not_admitted | none | none | none | none | none | none |
| op07_fan_mismatch | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | fan | true | 9 | 64 | 128 | raw_only | unknown_overlay | not_admitted | none | none | none | none | none | none |
| op00_extended_mismatch | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | extended | true | 12 | 64 | 100 | raw_only | unknown_overlay | not_admitted | none | none | none | none | none | none |
| empty_image | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 0 | missing | missing | applied | none | incomplete | none | none | none | none | none | none |
| unmodelled_byte7 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 9 | unmodelled | 100 | applied | none | incomplete | none | none | 64 | unmodelled | 100 | in_domain |
| op00_len13 | synthetic-b511-family-a | synthetic-variant-a | OP00 | positive | fan | false | 13 | 0 | 128 | applied | none | complete | true | 128 | none | none | none | none |
| op07_ext_len13 | synthetic-b511-family-a | synthetic-variant-a | OP07 | positive | extended | true | 13 | 64 | 100 | applied | none | complete | none | none | 64 | 32.0 | 100 | in_domain |

## Grade boundaries

Grades below belong to the named field on that row. Numeric, semantic and native grades stay separate.

| case | field | numeric_grade | semantic_grade | native_grade |
| --- | --- | --- | --- | --- |
| op00_fan_80 | fan_running | Hypothesis | Hypothesis | Unknown |
| op00_fan_len11 | fan_running | Hypothesis | Hypothesis | Unknown |
| op00_fan_zero | fan_running | Hypothesis | Hypothesis | Unknown |
| op00_fan_81 | fan_running | Hypothesis | Hypothesis | Unknown |
| op07_ext_40_100 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_ext_40_100 | pressure | Hypothesis | Hypothesis | Unknown |
| op07_ext_40_101 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_ext_40_101 | pressure | Unknown | Unknown | Unknown |
| op07_base_len8 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_ext_len8 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_ext_len8 | pressure | Unknown | Unknown | Unknown |
| op07_ext_not_selected | pressure | Hypothesis | Hypothesis | Unknown |
| op07_unknown_variant | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_unknown_variant | pressure | Hypothesis | Hypothesis | Unknown |
| op07_split_42_100 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_split_42_100 | pressure | Hypothesis | Hypothesis | Unknown |
| op07_pressure_0 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_pressure_0 | pressure | Hypothesis | Hypothesis | Unknown |
| op07_room_half | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_room_half | pressure | Hypothesis | Hypothesis | Unknown |
| op07_room_ff | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_room_ff | pressure | Hypothesis | Hypothesis | Unknown |
| unmodelled_byte7 | room_setpoint | Unknown | Unknown | Unknown |
| unmodelled_byte7 | pressure | Hypothesis | Hypothesis | Unknown |
| op00_len13 | fan_running | Hypothesis | Hypothesis | Unknown |
| op07_ext_len13 | room_setpoint | Hypothesis | Hypothesis | Unknown |
| op07_ext_len13 | pressure | Hypothesis | Hypothesis | Unknown |
| op00_reserved_80 | reserved_bit7 | Unknown | Unknown | Unknown |

## Negative rows

| case | outcome |
| --- | --- |
| empty_family | context |
| missing_alternative | context |
| room_flag_integer | context |
| hole_logical8 | applied |
| unmodelled_byte7 | applied |

## Bit preservation

Each bit 0..7 of logical 8 is preserved in the raw flag byte. Only bit 7 under the fan alternative is fan-running. The same bits under the reserved alternative stay reserved. On the extended OP07 alternative the single-bit values 1, 2, 4, 8, 16, 32 and 64 are in-domain percent, and 128 is out of domain. Room setpoint stays on byte 7 while those bits change.

These examples are synthetic and do not qualify a physical device.
