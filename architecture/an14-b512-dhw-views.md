# B512 OP06 request and positive field views

**Proven — software contract.** This page specifies the pure helper interpret_b512_op06_fields(context, logical_image). The hypothetical signature is the ab13/an13 helper API. AN14 is the ordinary companion of the AN13 helper description and does not depend on production code. It is an application contract for caller-selected logical images. It does not implement a sender, a poll, a control path, or a transport parser.

See the [public native B512 contract](../protocols/vaillant/ebus-vaillant-b512.md). The public native B512 contract comes first. Its OP06 rows are candidate layouts and are unconfirmed on the wire. This page does not add native qualification. The finite synthetic examples below do not upgrade that evidence.

**Hypothesis — candidate field map.** Family and candidate variant are explicit caller selections and are not inferred. Direction is the caller-selected string `request` or `positive`. Inputs are caller-selected logical images, not physical packets. Positions 0, 1 and 2 must be 181, 18 and 6 before any typed value is attached. Those three values are the logical prefix bytes `0xB5`, `0x12` and `0x06`. Request fields use positions through 9. Positive fields use positions through 6.

## Caller input

`context` is a mapping. `logical_image` is a sequence of cells. `bytes`, `bytearray` and `memoryview` are present modelled bytes. A list or tuple may contain an integer `0..255` (present modelled byte), `null` (missing cell), or `{"raw": <byte>, "modelled": false}` (explicit unmodelled cell). Any other container or cell raises `TypeError` and yields no result. Booleans are not integers. No cell is coerced.

Required context fields are `family`, `variant` and `direction`. `family` and `variant` are nonempty strings. They are synthetic selection labels, not a device-model catalog and not an allowlist: any nonempty string is retained and does not by itself admit or reject bytes. `direction` must be the string `request` or `positive`. The string `reply` is not an alias. A missing key, an empty string, or a non-string (including integer zero) is malformed context. An unknown direction string is a direction failure. Malformed context is reported before a prefix failure. prefix_ok remains an independent boolean.

The helper deep-copies context and copies every raw cell before interpretation. Later mutation of the caller mapping, a status cache stored inside it, the byte container, or an unmodelled-cell mapping does not change the result. Extra context keys are retained and select no field.

## Request cells

Logical 3 request bits 0..3 are task-active, heat-demand, loading-active and loading-pump-fault. Request bits 4..7 are four independent unnamed sensor-condition bits and acquire no semantic label. Logical 4 is u8/2 modulation with formal unit celsius and unit_conflict true. The conflict stays visible: quantity `modulation` and formal unit `celsius` are both retained. Logical 5 is u8/10 litres per minute. Logical 6, 7 and 8 are u8/2 degrees Celsius. Which of those three temperature cells corresponds to which candidate DHW or tank quantity is Unknown. Logical 9 bits 0 and 1 are two distinct unnamed inlet-condition flags. Bits 2..7 are reserved.

### Request logical 3 bits

| Bit | Key | Semantic label | Semantic grade |
| --- | --- | --- | --- |
| 0 | task_active | task_active | Hypothesis |
| 1 | heat_demand | heat_demand | Hypothesis |
| 2 | loading_active | loading_active | Hypothesis |
| 3 | loading_pump_fault | loading_pump_fault | Hypothesis |
| 4 | unnamed_sensor_condition_4 | none | Unknown |
| 5 | unnamed_sensor_condition_5 | none | Unknown |
| 6 | unnamed_sensor_condition_6 | none | Unknown |
| 7 | unnamed_sensor_condition_7 | none | Unknown |

### Request logical 9 inlet bits

| Bit | Key | Semantic label | Semantic grade |
| --- | --- | --- | --- |
| 0 | unnamed_inlet_condition_0 | none | Unknown |
| 1 | unnamed_inlet_condition_1 | none | Unknown |

## Positive cells

Positive logical 3 bits 0..5 are loading-disabled, internal-test-active, ready, frost-protection-active, legionella-demand and reset. Bits 6 and 7 are reserved. Positive logical 4 and 5 are DHW setpoint and return temperature as u8/2 celsius. Positive logical 6 is signed8 adjustment with named numeric domain -1, 0, 1 and 2. Every other raw adjustment value stays unlabelled. The hypothesis labels inside that domain are `at_minimum` for -1, `in_range` for 0, `at_maximum` for 1, and `modulation_regulator_not_active` for 2. They cite the candidate native wording and do not raise native grade.

### Positive logical 3 bits

| Bit | Key | Semantic label | Semantic grade |
| --- | --- | --- | --- |
| 0 | loading_disabled | loading_disabled | Hypothesis |
| 1 | internal_test_active | internal_test_active | Hypothesis |
| 2 | ready | ready | Hypothesis |
| 3 | frost_protection_active | frost_protection_active | Hypothesis |
| 4 | legionella_demand | legionella_demand | Hypothesis |
| 5 | reset | reset | Hypothesis |

### Scalar cells

| Direction | Position | Key | Scale | Unit state |
| --- | --- | --- | --- | --- |
| request | 4 | modulation | u8/2 | conflict celsius |
| request | 5 | dhw_water_flow | u8/10 | litres_per_minute |
| request | 6 | temperature_logical6 | u8/2 | celsius |
| request | 7 | temperature_logical7 | u8/2 | celsius |
| request | 8 | temperature_logical8 | u8/2 | celsius |
| positive | 4 | dhw_setpoint | u8/2 | celsius |
| positive | 5 | return_temperature | u8/2 | celsius |
| positive | 6 | adjustment | signed8 | named domain -1 0 1 2 |

## Defaults, partial cells and admission

Declared defaults of false and adjustment -1 are metadata and are not materialized for missing cells. A present positive adjustment byte 0 is numeric 0 and stays distinct from the metadata default -1. A request whose cells stop at logical 6 keeps temperature_logical6 and omits later temperatures and inlet flags. A positive image that omits logical 6 does not create adjustment -1. Reserved bit changes remain in the raw cell. Bytes past the direction window stay raw and unmodelled and are not decoded with the other direction. An explicit unmodelled cell keeps its raw byte and produces no typed field.

Admission is fail closed. The result is `raw_only` when context or direction is unusable, or when the prefix does not match. `prefix_ok` is false when any of positions 0..2 is missing, unmodelled, or not the required byte. A passed prefix with a known direction admits independent partial fields: each present modelled cell inside the direction window is typed, and each missing or unmodelled cell is omitted. `partial` is true only for a known direction whose window `0..last` is not entirely present and modelled. `extra` is true when a byte past that window is retained as unmodelled. Unknown direction does not reclassify the tail and does not choose either layout.

The result retains `context`, `raw_cells` (`position`, `state`, `raw`), `prefix_ok`, `admission`, `reason`, `fields`, `partial`, `extra` and `qualification`. `reason` is `context`, `direction`, `prefix`, or null. Each typed field carries its own `numeric_grade`, `semantic_grade` and `native_grade`. Numeric grade is Hypothesis for an attached field. Semantic grade is Hypothesis for a named bit, named scalar, or labelled adjustment, and Unknown for an unnamed condition or an unlabelled adjustment. Native grade is Unknown on every field. These three grades are not collapsed. Qualification of physical support, presence, freshness, execution, family inference, physical adaptation, requested-versus-actual actuation and support is Unknown on every result. Physical qualification, presence, freshness and execution stay Unknown on every result, including a fully decoded image. Native qualification, physical adaptation, requested-versus-actual actuation and support are Unknown.

## Pure boundary

The helper does not send, poll, open a control path, or mutate a status cache. Partial results keep raw cells and independently decoded fields and do not replace last-known-good state. There is no route, writer, or presence assertion. eBUS MCP compatibility and GraphQL parity are unchanged. This helper is not an MCP tool and adds no GraphQL field. Nothing in this contract is stable before Helianthus 1.0. It adds no namespace and no authorization gate.

## Normative policy

The following policy is normative. The [synthetic example package](fixtures/an14_b512_dhw_views.json) publishes the finite rows. Example families and variants are the labels used in that package. They are not an admission catalog.

```json
{
  "signature": "interpret_b512_op06_fields(context, logical_image)",
  "context_fields": [
    "family",
    "variant",
    "direction"
  ],
  "directions": [
    "request",
    "positive"
  ],
  "prefix": [
    181,
    18,
    6
  ],
  "request_last_position": 9,
  "positive_last_position": 6,
  "require_prefix": true,
  "preserve_reserved_raw": true,
  "preserve_unmodelled": true,
  "materialize_missing": false,
  "admit_any_nonempty_family": true,
  "admit_any_nonempty_variant": true,
  "infer_family": false,
  "flow_divisor": 10,
  "modulation_divisor": 2,
  "temperature_divisor": 2,
  "modulation_formal_unit": "celsius",
  "modulation_unit_conflict": true,
  "adjustment_codec": "signed8",
  "adjustment_named_domain": [
    -1,
    0,
    1,
    2
  ],
  "adjustment_labels": {
    "-1": "at_minimum",
    "0": "in_range",
    "1": "at_maximum",
    "2": "modulation_regulator_not_active"
  },
  "unlabelled_semantic_grade": "Unknown",
  "defaults_metadata": {
    "bits": false,
    "adjustment": -1
  },
  "native_grade": "Unknown",
  "software_contract": "Proven",
  "layout_grade": "Hypothesis",
  "example_families": [
    "synthetic-dhw-family-a",
    "synthetic-dhw-family-b"
  ],
  "example_variants": [
    "synthetic-variant-a",
    "synthetic-variant-b"
  ],
  "request_bits": [
    {
      "bit": 0,
      "key": "task_active",
      "semantic_label": "task_active",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 1,
      "key": "heat_demand",
      "semantic_label": "heat_demand",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 2,
      "key": "loading_active",
      "semantic_label": "loading_active",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 3,
      "key": "loading_pump_fault",
      "semantic_label": "loading_pump_fault",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 4,
      "key": "unnamed_sensor_condition_4",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    },
    {
      "bit": 5,
      "key": "unnamed_sensor_condition_5",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    },
    {
      "bit": 6,
      "key": "unnamed_sensor_condition_6",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    },
    {
      "bit": 7,
      "key": "unnamed_sensor_condition_7",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    }
  ],
  "request_inlet_bits": [
    {
      "bit": 0,
      "key": "unnamed_inlet_condition_0",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    },
    {
      "bit": 1,
      "key": "unnamed_inlet_condition_1",
      "semantic_label": null,
      "semantic_grade": "Unknown"
    }
  ],
  "request_reserved_bits": [
    2,
    3,
    4,
    5,
    6,
    7
  ],
  "positive_bits": [
    {
      "bit": 0,
      "key": "loading_disabled",
      "semantic_label": "loading_disabled",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 1,
      "key": "internal_test_active",
      "semantic_label": "internal_test_active",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 2,
      "key": "ready",
      "semantic_label": "ready",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 3,
      "key": "frost_protection_active",
      "semantic_label": "frost_protection_active",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 4,
      "key": "legionella_demand",
      "semantic_label": "legionella_demand",
      "semantic_grade": "Hypothesis"
    },
    {
      "bit": 5,
      "key": "reset",
      "semantic_label": "reset",
      "semantic_grade": "Hypothesis"
    }
  ],
  "positive_reserved_bits": [
    6,
    7
  ],
  "request_scalars": [
    {
      "position": 4,
      "key": "modulation",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "modulation",
      "unit": "celsius",
      "formal_unit": "celsius",
      "unit_conflict": true,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 5,
      "key": "dhw_water_flow",
      "scale": "u8/10",
      "divisor": 10,
      "quantity": "dhw_water_flow",
      "unit": "litres_per_minute",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 6,
      "key": "temperature_logical6",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "temperature_logical6",
      "unit": "celsius",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 7,
      "key": "temperature_logical7",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "temperature_logical7",
      "unit": "celsius",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 8,
      "key": "temperature_logical8",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "temperature_logical8",
      "unit": "celsius",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    }
  ],
  "positive_scalars": [
    {
      "position": 4,
      "key": "dhw_setpoint",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "dhw_setpoint",
      "unit": "celsius",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 5,
      "key": "return_temperature",
      "scale": "u8/2",
      "divisor": 2,
      "quantity": "return_temperature",
      "unit": "celsius",
      "formal_unit": null,
      "unit_conflict": false,
      "semantic_grade": "Hypothesis"
    },
    {
      "position": 6,
      "key": "adjustment",
      "scale": "signed8",
      "named_domain": [
        -1,
        0,
        1,
        2
      ],
      "semantic_grade": "Hypothesis"
    }
  ]
}
```

## Control outcomes

These examples are synthetic and do not qualify a physical device. The package holds every finite row: raw cells, selection context, partial and malformed outcomes, and separate numeric, semantic and native grades. All-zero complete request and positive images with prefix 181, 18, 6 are the controls. Request bytes 1 at logical 4..8 yield modulation 0.5 with unit_conflict, flow 0.1 and temperatures 0.5. Positive adjustment byte 255 is -1, byte 2 is 2, and byte 3 is unlabelled. Each request bit, each inlet bit, each named positive bit, each reserved bit, each prefix byte, each identity field and the listed lengths vary alone.

### Control outcomes

| Example | Expected numeric or state |
| --- | --- |
| request_all_zero | scalars 0 and modulation unit_conflict |
| positive_all_zero | adjustment 0 not -1 |
| request_scalar_01 | modulation 0.5 unit_conflict, flow 0.1, temperatures 0.5 |
| positive_adjustment_ff | adjustment -1 |
| positive_adjustment_02 | adjustment 2 |
| positive_adjustment_03 | adjustment 3 unlabelled |
| request_through_logical6 | temperature_logical6 0.5 and later temperatures absent |
| positive_missing_logical6 | adjustment absent |

The [focused standard-library tests](../tests/test_an14_b512_dhw_views.py) compare this prose, the policy and the package with independent literals. They exercise a local reference of this page, not companion production code. Full repository CI, Gate D, independent committed-change review, publication checks and applicable transport classification remain later ship requirements.
