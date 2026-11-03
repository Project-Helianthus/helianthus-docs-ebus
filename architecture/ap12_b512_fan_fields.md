# B512 fan and air-quality interpreter results

This local software API contract is **Proven** as a declaration, not an implemented
runtime or native qualification. The public [B512 candidate contract](../protocols/vaillant/ebus-vaillant-B512.md#candidate-sub-commands-op)
comes first: OP0B–OP0E are **Hypothesis**, unconfirmed on the wire. Named byte
fields here are isolated logical fields, never packet offsets. No OP01 or OP06
semantics are borrowed. Family and variant selectors are opaque software inputs;
they do not establish a device association. Physical support, freshness, effects,
persistence and delivery are **Unknown**. No action or physical feedback follows.

## API and JSON shape

```go
package vaillant

func Ab11Ap11Evaluate(ab11ap11Input json.RawMessage) (json.RawMessage, error)
```

The intended function uses only the Go standard library and is pure: no
initialization side effects, persistent cache, catalog, listing API or runtime
caller. There is no implementation in this documentation slice. This contract
introduces no eBUS MCP or GraphQL integration change; any future exposure must
preserve the same context, raw values, partial states and qualification boundary.

Input is exactly one JSON object with required `context` and `fields` objects and
optional `arguments` object. Context selects primary 181, secondary 18, an
operation, an explicit view and direction from the table. Unknown context keys,
including nested family and variant values, survive verbatim as JSON values.
Absent, explicit null, zero and Boolean false remain distinct. Null or missing
selector values are unsupported, not defaults. Non-null primary, secondary and
operation selectors must be integral u8; non-null view and direction must be
strings. Fields are named arrays of integral bytes 0..255. There is no relay
vector in these views: relay is one byte. Unknown named byte fields survive as
unmodeled raw fields; they cannot gain meaning from a neighboring operation.

No view declares a required or known argument. Optional `arguments` therefore
preserves unknown keys and their JSON kinds unchanged, including false, null,
strings and arrays. There is no coercion. A future required typed argument is not
implicitly admitted by this contract. Wherever typed u8/u16/u32 values are
specified, their integral bounds are respectively 0..255, 0..65535 and
0..4294967295. Arbitrary opaque JSON values are not typed argument declarations.

Reject malformed JSON, trailing JSON, duplicate object keys at every depth,
non-object envelopes/context/fields/arguments, non-array fields, Boolean bytes,
fractional bytes and out-of-range bytes with an error and no successful result.
Missing required context/fields objects are errors. Valid missing, empty, short
or overlong named arrays remain raw, but yield an incomplete semantic field.
Validate syntax and kinds before unsupported-selector fallback.

Output is one JSON object with `context` unchanged, `raw` a deep independent copy
of fields, `arguments` unchanged only if supplied, `state`, semantic `fields`,
`physical: "Unknown"` and `qualified: false`. Each semantic result retains `raw`
when present (omits it when absent), `state` and `grade: "Hypothesis"`; decoded
quantities also have `calculation: "Proven"`, `number` and `unit`. Digital uses a
Boolean `number`. Mappings use `label`; relay uses `flags` and `reserved`.
Incomplete and unmapped results have no invented number or label. Unknown fields
have `state: "Unknown"` and `unmodeled: true`. Missing results omit raw; empty
arrays retain raw `[]`. Extra bytes are never silently truncated.

An unsupported primary, secondary, operation, direction or view yields state
`Unknown`, raw only, and an empty semantic fields object; apply no formula. For
supported views, state is `partial` if any required logical field is incomplete,
otherwise `complete` as a local representation only. Unmapped status/digital
branches can coexist with complete siblings without turning into qualification.
Inputs and all returned nested storage are independent across results and calls.
Every distinction must survive JSON round trips; retain last-known-good sibling
results even when another field is incomplete. No persistent last-known cache is
introduced. Defaults are annotations, never fills for absent input.

## Allowed fields and directions

All rows have candidate grade Hypothesis. Arithmetic additionally has calculation
Proven; it never replaces the candidate grade. Empty request views are listed
separately below. Every listed field is independently required for completeness.
LEu16 = b0 + 256*b1. SignedLE16 subtracts 65536 when LEu16 >= 32768.
`s16/16` divides SignedLE16 by 16; `s16/256` divides it by 256.

| view | operation | direction | field | width | codec | unit | default |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fan | 11 | request | fan1 | 2 | leu16 | rpm | Unknown |
| fan | 11 | request | fan2 | 2 | leu16 | rpm | Unknown |
| fan | 11 | request | relay | 1 | relay | Unknown | Unknown |
| fan | 11 | positive | fan1 | 2 | leu16 | rpm | Unknown |
| fan | 11 | positive | fan2 | 2 | leu16 | rpm | Unknown |
| fan | 11 | positive | status | 1 | status | Unknown | Unknown |
| fan | 11 | positive | temperature1 | 2 | s16/16 | Celsius | Unknown |
| fan | 11 | positive | temperature2 | 2 | s16/16 | Celsius | Unknown |
| fan | 11 | positive | temperature3 | 2 | s16/16 | Celsius | Unknown |
| fan-control | 12 | request | pulse | 1 | u8 | Unknown | 0 |
| fan-control | 12 | request | p | 1 | u8 | Unknown | 0 |
| fan-control | 12 | request | i | 1 | u8 | Unknown | 0 |
| fan-control | 12 | request | d | 1 | u8 | Unknown | 0 |
| fan-control | 12 | request | fan_count | 1 | u8 | Unknown | 0 |
| fan-control | 12 | request | minimum_pwm | 2 | s16/256 | percent | 1.0 |
| fan-control | 12 | request | maximum_pwm | 2 | s16/256 | percent | 1.0 |
| fan-control | 12 | positive | feedback | 1 | feedback | Unknown | Unknown |
| digital-air | 13 | positive | digital | 1 | digital | Unknown | 0 |
| digital-air | 13 | positive | temperature1 | 2 | s16/16 | Celsius | 0 |
| digital-air | 13 | positive | temperature2 | 2 | s16/16 | Celsius | 0 |
| air-quality | 14 | positive | temperature | 2 | s16/16 | Celsius | 0 |
| air-quality | 14 | positive | humidity | 2 | leu16/16 | percent | 0 |
| air-quality | 14 | positive | air_quality | 2 | leu16 | Unknown | 0 |

`digital-air` / operation 13 / request and `air-quality` / operation 14 / request
have no semantic fields. Positive and request directions are distinct views.

Status maps 0 to idle, 1 to running and 255 to fault; all others are unmapped.
Feedback maps exactly 1 to accepted, every other byte to rejected. Digital maps
0 to false, 1 to true, all others to unmapped; 2 is never true. Relay bits 0 and 1
are independent: each 0 selects 15V, each 1 selects tray-heater-relay. Flags are
named bit0 and bit1. Preserve `reserved = byte & 252`; never decode bits 2..7 as
outputs. Reserved bits do not make a supported field incomplete.

PWM spans the entire signed domain -128..127.99609375 percent, with candidate
default 1.0. Do not clip at 0 or 100, and do not enforce minimum <= maximum.
Decoded PWM has `candidate_domain: true` over that entire domain. Other physical
candidate domains are Unknown, so no numerical candidate-domain predicate is
invented. If a future explicit candidate domain excludes a calculated value,
retain the number and calculation grade with `candidate_domain: false`.
Humidity has no 100 percent cap. Air quality has unit Unknown, never ppm.
Temperatures have no sentinel or established physical domain in this contract.

## Machine-readable declaration and synthetic scenarios

This declaration provides exact table and envelope values for independent
contract validation. [Synthetic scenarios](fixtures/ap12_b512_fan_fields.json)
retain input bytes and expected semantic projections. They are examples, not
physical observations or qualification records.

```json
{
  "signature": "Ab11Ap11Evaluate(ab11ap11Input json.RawMessage) (json.RawMessage, error)",
  "package": "vaillant",
  "primary": 181,
  "secondary": 18,
  "physical": "Unknown",
  "qualified": false,
  "grade": "Hypothesis",
  "calculation": "Proven",
  "arguments": {
    "required": [],
    "known": {},
    "unknown": "preserve"
  },
  "fields": [
    {
      "view": "fan",
      "operation": 11,
      "direction": "request",
      "name": "fan1",
      "width": 2,
      "codec": "leu16",
      "unit": "rpm",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "request",
      "name": "fan2",
      "width": 2,
      "codec": "leu16",
      "unit": "rpm",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "request",
      "name": "relay",
      "width": 1,
      "codec": "relay",
      "unit": "Unknown",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "fan1",
      "width": 2,
      "codec": "leu16",
      "unit": "rpm",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "fan2",
      "width": 2,
      "codec": "leu16",
      "unit": "rpm",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "status",
      "width": 1,
      "codec": "status",
      "unit": "Unknown",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "temperature1",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "temperature2",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": null
    },
    {
      "view": "fan",
      "operation": 11,
      "direction": "positive",
      "name": "temperature3",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": null
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "pulse",
      "width": 1,
      "codec": "u8",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "p",
      "width": 1,
      "codec": "u8",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "i",
      "width": 1,
      "codec": "u8",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "d",
      "width": 1,
      "codec": "u8",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "fan_count",
      "width": 1,
      "codec": "u8",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "minimum_pwm",
      "width": 2,
      "codec": "s16/256",
      "unit": "percent",
      "default": 1.0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "request",
      "name": "maximum_pwm",
      "width": 2,
      "codec": "s16/256",
      "unit": "percent",
      "default": 1.0
    },
    {
      "view": "fan-control",
      "operation": 12,
      "direction": "positive",
      "name": "feedback",
      "width": 1,
      "codec": "feedback",
      "unit": "Unknown",
      "default": null
    },
    {
      "view": "digital-air",
      "operation": 13,
      "direction": "positive",
      "name": "digital",
      "width": 1,
      "codec": "digital",
      "unit": "Unknown",
      "default": 0
    },
    {
      "view": "digital-air",
      "operation": 13,
      "direction": "positive",
      "name": "temperature1",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": 0
    },
    {
      "view": "digital-air",
      "operation": 13,
      "direction": "positive",
      "name": "temperature2",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": 0
    },
    {
      "view": "air-quality",
      "operation": 14,
      "direction": "positive",
      "name": "temperature",
      "width": 2,
      "codec": "s16/16",
      "unit": "Celsius",
      "default": 0
    },
    {
      "view": "air-quality",
      "operation": 14,
      "direction": "positive",
      "name": "humidity",
      "width": 2,
      "codec": "leu16/16",
      "unit": "percent",
      "default": 0
    },
    {
      "view": "air-quality",
      "operation": 14,
      "direction": "positive",
      "name": "air_quality",
      "width": 2,
      "codec": "leu16",
      "unit": "Unknown",
      "default": 0
    }
  ],
  "empty_views": [
    [
      "digital-air",
      13,
      "request"
    ],
    [
      "air-quality",
      14,
      "request"
    ]
  ],
  "mappings": {
    "status": {
      "0": "idle",
      "1": "running",
      "255": "fault"
    },
    "feedback": {
      "1": "accepted",
      "other": "rejected"
    },
    "digital": {
      "0": false,
      "1": true,
      "other": "unmapped"
    },
    "relay": {
      "0": "15V",
      "1": "tray-heater-relay",
      "reserved_mask": 252
    }
  },
  "pwm_domain": [
    -128,
    127.99609375
  ],
  "rules": {
    "input_required": [
      "context",
      "fields"
    ],
    "input_optional": [
      "arguments"
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
    "arguments_presence": "same_as_input",
    "raw_presence": "omit_if_absent_preserve_if_present",
    "unknown_fields": "raw_and_unmodeled",
    "unknown_selectors": "raw_only_Unknown",
    "invalid_input": "error_no_result",
    "duplicate_keys": "reject_at_every_depth",
    "numeric_kinds": "integral_not_boolean_no_coercion",
    "bounds": {
      "u8": [
        0,
        255
      ],
      "u16": [
        0,
        65535
      ],
      "u32": [
        0,
        4294967295
      ]
    },
    "supported_complete": "complete",
    "any_incomplete": "partial",
    "unmapped_sibling": "complete",
    "storage": "deep_independent_across_calls",
    "defaults": "annotations_never_fill",
    "minimum_maximum_order": "not_enforced",
    "pwm_clip": null,
    "humidity_cap": null,
    "family_grade": "Hypothesis",
    "calculation_grade": "Proven",
    "physical": "Unknown",
    "qualified": false
  }
}
```

For example, fan words `[2,1]` and `[4,3]` produce 258 and 772 rpm independently.
Temperatures `[16,0]` and `[240,255]` produce 1 and -1 Celsius. Relay `[4]`
keeps reserved 4 with both flags 15V. PWM `[0,1]`, `[0,128]`, `[255,127]`
produces 1, -128 and 127.99609375 percent respectively. Humidity `[64,6]`
and `[80,6]` produces 100 and 101 percent. Air quality `[255,255]` produces
65535 with unit Unknown. These calculations do not establish native support.

The supplemental unittest validates this declaration, tables and synthetic
transitions using standard-library bounded oracles. It does not execute a Go
runtime API. Its explicit ship command is
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap12_b512_fan_fields.py -v`.
The fixed full-CI list does not automatically discover this suite. Full repository
CI, independent committed-change review and publication checks remain required.
No transport or hardware invocation is introduced. This is partial work for
helianthus-docs-ebus#736; the umbrella remains open. Nothing is stable before
Helianthus 1.0; no new major or experimental namespace is introduced.
