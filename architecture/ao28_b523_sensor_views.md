# B523 selected sensor and status API results

This software API companion defines the bounded selected interpretation for
functional-module families. It adds no native qualification or catalog entry.
The [public B523 native contract](../protocols/vaillant/ebus-vaillant-B523.md#candidate-layouts)
comes first: its candidate sensor layouts are unconfirmed on the wire, response
position adaptation is unresolved, and the reserved sensor carrier has no known
physical meaning. The detailed logical selections below are **Hypothesis**.
They neither establish a physical adaptation nor resolve the signed-selector
32768 materialisation conflict. Native support, effects and persistence remain
**Unknown**. A successful software result grants no permission to act.

## Pure library boundary

Package `vaillant`, standard library only:

```go
func Ab27Ao27Interpret(ab27ao27Input json.RawMessage) (json.RawMessage, error)
```

This is a contract for a pure library function, not its implementation. It has
no global cache, generic catalog, metadata listing, registration, runtime call
site, wire codec or request encoder. This page has no dependency on AO27 or a
code merge. Existing eBUS MCP compatibility and GraphQL parity are unaffected;
no transport or surface is introduced. All new Go declarations, fields, locals,
helpers and tests in a companion implementation use `ab27ao27` or exported
`Ab27Ao27`; Go tests start `TestAb27Ao27`. Fixture IDs also use `ab27ao27`.
Literal JSON and protocol field labels retain their names.

## JSON admission and selection

Input is an object with `context`, `fields`, and optional `arguments`.
`context` contains `primary:181`, `secondary:35`, integer `operation`, `direction`
and explicit `view`; preserve every supplied context key, including opaque
`family`, `variant` and nested unknown values. `fields` maps names to arrays of
integer bytes in 0..255. The selected array is `logical_object`; other fields
and tails are preserved without interpretation. Its first three positions are
opaque, not an asserted prefix. Never decode an operation or identity from them,
or select by family, field name resemblance or payload length.

The positive direction and explicit `status-zero-valid` or
`status-zero-valid-or-low` view select the software layouts for operations 3, 6
and 7. Unknown operation, direction or view yields raw-only `state:"Unknown"`
and `fields:{}`. A view selects interpretation, never family applicability.
Changing primary or secondary is not evidence of applicability: the finite
context cases assert preservation and nonqualification only; they do not specify
selection for a different service. Opaque family and variant never qualify it.

Reject malformed JSON, duplicate object keys at any depth, wrong JSON kinds and
invalid byte elements, including booleans, fractions, strings, null, negative
integers and integers above 255. Return an error and no successful result.
Absent differs from explicit zero; empty arrays differ from missing fields.
`arguments`, when supplied, is an independently copied object containing only
explicitly described scalar flags/integers. No argument is defined by this
sensor selection; the finite cases cover absent and empty arguments. They do not
invent a flag or an admission rule for an unspecified argument.

## Result shapes and grades

The output object has `context` (unchanged deep copy), `raw` (independent copy of
all supplied fields), optional `arguments` (independent copy if supplied),
`state`, `fields`, `physical:"Unknown"` and `qualified:false`. No result, earlier
call, later call or input may share mutable nested memory with another. Mutating
input after a call or mutating returned context, raw, arguments or fields must
not affect any other result. JSON round trips preserve states and presence,
including absent arguments, explicit zero, empty fields and errors versus success.

Selected complete results use `state:"Hypothesis"`; missing accessed bytes give
`state:"partial"`, retaining every complete independent sensor, PWM and status.
An explicit Unknown branch remains `Unknown`. Unknown siblings cannot erase
complete fields and defaults never fill missing data. Per-field `raw` retains
the unsigned word carrier, PWM byte or selected two-bit status; the output `raw`
object additionally retains the exact original arrays. Each complete semantic
field has `state:"Hypothesis"`. Numeric fields may additionally carry
`calculation:"Proven"` for exact arithmetic; this never replaces the family
grade. Incomplete or unmapped fields remain `Unknown` with available raw bytes
and no `number`; unit-conflict and unknown-order fields likewise have no number.
`label`, `flags`, `reserved` and `candidate_domain` are present only when their
contract defines them. No flags or candidate domain are invented here. An
explicit outside-domain carrier in a future defined selection may retain its
number with `candidate_domain:false`; this is not native qualification.

For every sensor occurrence, test unsigned carrier 32768 (`00 80` in byte order)
**before** signed conversion. Its field is `{ "raw":32768,
"state":"Hypothesis", "label":"replacement" }`, with no temperature number
and no unavailable assertion. All other words use the full signed LE16 carrier
divided by 16 Celsius: `10 00` is +1, `F0 FF` is -1, `FF 7F` is 2047.9375,
`01 80` is -2047.9375 and `00 00` is zero. These numbers are exact calculations,
not physical support. OP03 PWM `FF` is 127.5 percent (raw / 2), without clipping
or importing an actor-command domain.

Status pairs start at bits 0/2/4/6 in sensor order. Codes 1, 2 and 3 label
`open-circuit`, `closed-circuit` and `high-level`. Code 0 is `valid-value` only
under `status-zero-valid`, and `valid-value-or-low-level` only under
`status-zero-valid-or-low`. Preserve the last status byte's reserved bits in
place, without assigning meaning. OP07 logical byte 11 remains opaque and
independent of S12 starting at 12.

## Finite machine-readable contract table

The JSON table is normative for the bounded software cases. `sensors` pairs are
name/logical-position; `status` pairs are byte-position/ordered sensor names;
`reserved` gives byte-position/bit-positions. Extents are accessed logical
minimums, not wire lengths. Every sensor occurrence receives all six `words`;
every status pair receives all four values under both views; every reserved bit
is toggled separately. Partial cases cover every shorter length. Fixture rows
contain complete synthetic inputs and explicit expected assertions, not complete
serialized outputs. `field`/`result` is one selected output-field assertion;
`complete_sensors` and `numeric_zero_sensors` assert retained sibling sets,
`complete_pwm` and `complete_status` the retained complete PWM and status fields;
`reserved` and `opaque` assert retained raw evidence. `preserve_*` assertions
require exact input copies, not inferred values. Context-only rows make no
unstated decoding claim. Error rows retain input text because parsing would lose
duplicate keys. The standard-library suite checks this table and every fixture
row against separate constants; it does not supply another interpreter or invoke
an unavailable production function. Production error, aliasing, serialization
and mutation behavior requires the companion library's tests.

<!-- ab27ao27-contract:start -->
```json
{
  "api": {
    "package": "vaillant",
    "signature": "Ab27Ao27Interpret(ab27ao27Input json.RawMessage) (json.RawMessage, error)",
    "dependencies": "standard library only"
  },
  "selection": {
    "primary": 181,
    "secondary": 35,
    "direction": "positive",
    "views": [
      "status-zero-valid",
      "status-zero-valid-or-low"
    ],
    "field": "logical_object",
    "prefix": "opaque",
    "physical": "Unknown",
    "qualified": false
  },
  "layouts": [
    {
      "operation": 3,
      "extent": 18,
      "sensors": [
        [
          "S1",
          3
        ],
        [
          "S2",
          5
        ],
        [
          "S3",
          7
        ],
        [
          "S4",
          9
        ],
        [
          "S5",
          11
        ],
        [
          "S6",
          13
        ]
      ],
      "pwm": 15,
      "status": [
        [
          16,
          [
            "S1",
            "S2",
            "S3",
            "S4"
          ]
        ],
        [
          17,
          [
            "S5",
            "S6"
          ]
        ]
      ],
      "reserved": [
        17,
        [
          4,
          5,
          6,
          7
        ]
      ]
    },
    {
      "operation": 6,
      "extent": 19,
      "sensors": [
        [
          "S1",
          3
        ],
        [
          "S2",
          5
        ],
        [
          "S3",
          7
        ],
        [
          "S4",
          9
        ],
        [
          "S5",
          11
        ],
        [
          "S6",
          13
        ],
        [
          "S7",
          15
        ]
      ],
      "status": [
        [
          17,
          [
            "S1",
            "S2",
            "S3",
            "S4"
          ]
        ],
        [
          18,
          [
            "S5",
            "S6",
            "S7"
          ]
        ]
      ],
      "reserved": [
        18,
        [
          6,
          7
        ]
      ]
    },
    {
      "operation": 7,
      "extent": 18,
      "sensors": [
        [
          "S8",
          3
        ],
        [
          "S9",
          5
        ],
        [
          "S10",
          7
        ],
        [
          "S11",
          9
        ],
        [
          "S12",
          12
        ],
        [
          "S13",
          14
        ]
      ],
      "opaque": 11,
      "status": [
        [
          16,
          [
            "S8",
            "S9",
            "S10",
            "S11"
          ]
        ],
        [
          17,
          [
            "S12",
            "S13"
          ]
        ]
      ],
      "reserved": [
        17,
        [
          4,
          5,
          6,
          7
        ]
      ]
    }
  ],
  "words": [
    {
      "bytes": [
        0,
        128
      ],
      "raw": 32768,
      "label": "replacement"
    },
    {
      "bytes": [
        16,
        0
      ],
      "raw": 16,
      "number": 1
    },
    {
      "bytes": [
        240,
        255
      ],
      "raw": 65520,
      "number": -1
    },
    {
      "bytes": [
        255,
        127
      ],
      "raw": 32767,
      "number": 2047.9375
    },
    {
      "bytes": [
        1,
        128
      ],
      "raw": 32769,
      "number": -2047.9375
    },
    {
      "bytes": [
        0,
        0
      ],
      "raw": 0,
      "number": 0
    }
  ],
  "status_labels": {
    "status-zero-valid": [
      "valid-value",
      "open-circuit",
      "closed-circuit",
      "high-level"
    ],
    "status-zero-valid-or-low": [
      "valid-value-or-low-level",
      "open-circuit",
      "closed-circuit",
      "high-level"
    ]
  },
  "pwm": {
    "bytes": [
      255
    ],
    "number": 127.5,
    "unit": "percent"
  },
  "grades": {
    "semantic": "Hypothesis",
    "calculation": "Proven",
    "native_support": "Unknown",
    "effects": "Unknown",
    "persistence": "Unknown"
  },
  "errors": [
    "malformed-json",
    "duplicate-root",
    "duplicate-context",
    "duplicate-fields",
    "duplicate-arguments",
    "root-array",
    "context-array",
    "fields-array",
    "arguments-array",
    "byte-negative",
    "byte-overflow",
    "byte-fraction",
    "byte-bool",
    "byte-string",
    "byte-null",
    "field-scalar",
    "operation-string"
  ],
  "scope": {
    "wire_codec": false,
    "request_encoder": false,
    "runtime_call_site": false,
    "catalog": false,
    "qualification": false
  },
  "case_families": [
    "word",
    "status",
    "reserved",
    "pwm",
    "opaque",
    "partial",
    "tail",
    "selection",
    "context",
    "raw-field",
    "arguments",
    "error"
  ],
  "json_shapes": {
    "input_required": [
      "context",
      "fields"
    ],
    "input_optional": [
      "arguments"
    ],
    "context_required": [
      "primary",
      "secondary",
      "operation",
      "direction",
      "view"
    ],
    "output_required": [
      "context",
      "raw",
      "state",
      "fields",
      "physical",
      "qualified"
    ],
    "output_optional": [
      "arguments"
    ],
    "field_required": [
      "raw",
      "state"
    ],
    "field_optional": [
      "number",
      "label",
      "flags",
      "reserved",
      "candidate_domain",
      "calculation"
    ],
    "complete_state": "Hypothesis",
    "partial_state": "partial",
    "unknown_state": "Unknown",
    "replacement_number_present": false,
    "incomplete_number_present": false,
    "physical": "Unknown",
    "qualified": false,
    "copy": "independent deep copies",
    "unknown_selection_fields": {},
    "undefined_arguments": []
  }
}
```
<!-- ab27ao27-contract:end -->

The [synthetic tuples](fixtures/ao28_b523_sensor_views.json) and
[finite contract checks](../tests/test_ao28_b523_sensor_views.py) are mandatory
focused ship evidence. The repository full gate uses an explicit suite list and
does not automatically run this new suite. Full Gate D, independent committed
review, publication checks and transport classification remain separate ship
requirements. No shared registration is changed by this companion.
