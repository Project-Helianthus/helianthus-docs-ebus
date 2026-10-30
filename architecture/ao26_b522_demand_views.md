# B522 candidate demand and scalar API results

This software API companion defines isolated candidate field results for the
recoVAIR family. It is a partial child of #736 (Refs #944); it grants no native
qualification and does not depend on AO25 merging. All examples are synthetic.
Nothing here is stable before Helianthus 1.0.

The public native contract is [B522](../protocols/vaillant/ebus-vaillant-B522.md).
It identifies candidate operation `00` but leaves wire confirmation and response
positions unresolved. This companion selects that operation in software; it
does not establish positions in a telegram. In particular, the native page's
candidate status names and `FF FF` unset inference do not allocate Boolean roles
or a sentinel in this API. These are separate, unresolved interpretations.

## Function and JSON envelope

```go
package vaillant

func Ab25Ao25Interpret(ab25ao25Input json.RawMessage) (json.RawMessage, error)
```

The standard-library function is a pure selected field/state interpreter. It has
no global cache, generic catalog, metadata listing, registration, pending API
import or runtime call site. All new Go identifiers use `ab25ao25` or exported
`Ab25Ao25`; Go test names start `TestAb25Ao25`. JSON labels retain their names.
This page describes the implementation obligation; its finite checks do not
execute a production interpreter or establish implementation conformance.

Input is an object with required `context` and `fields` objects and optional
`arguments` object. The exact software selector is primary 181, secondary 34,
integer operation 0, direction `request` or `positive`, and explicit view
`isolated-fields`. Required selector kinds are integers for primary, secondary
and operation and strings for direction and view. Other integer operations,
other selectors and unknown direction/view tokens return structured raw-only
`Unknown`, with an empty semantic `fields` object. Missing selectors also cannot
select a view. Never infer a view from a family, name, length or payload.

Family, variant and all extra context keys are opaque JSON values preserved
unchanged. Every supplied field, including an unrecognised field, is a byte
array of integer elements 0..255. Booleans, fractions, nulls and coercion from
strings are invalid byte elements. No scalar argument flags or integers are
allocated by this slice: omit `arguments` or supply `{}`; nonempty arguments
are rejected rather than guessed. Absent arguments remain absent in output.

Malformed JSON, duplicate keys at any nesting depth, invalid byte elements and
wrong JSON kinds produce an error with no successful result. Validate the
entire input even for unknown selection or unrecognised fields. Missing fields,
empty arrays and explicit `[0]` are distinct successful input states.

Output has `context`, `raw`, optional `arguments`, `state`, `fields`,
`physical: "Unknown"` and `qualified: false`. Context is an unchanged deep copy;
raw is an independent copy of all supplied fields, including unmodelled tails.
Arguments, when present, are copied independently. Each supplied selected field
has its own `raw`, `state` and `grade: "Hypothesis"`, with only the optional
`number`, `label`, `flags`, `reserved` or `candidate_domain` supplied by its
contract. `calculation: "Proven"` can accompany exact numeric arithmetic and
never replaces the semantic grade. These carriers have full domains, so no
`candidate_domain: false` is allocated here.

## Field and state rules

| Direction | Field | Width | Result | Grade |
|---|---|---|---|---|
| request | mode | 1 | 0..4 labels below; 1 label-conflict; 5..255 unmapped | Hypothesis |
| request | fan | 1 | raw u8 number 0..255, no enum or clipping | Hypothesis; calculation Proven |
| request | room_temperature | 1 | u8 / 2 Celsius, 0..127.5; FF is 127.5 | Hypothesis; calculation Proven |
| request | automatic | 1 | bit 0 disabled/enabled; reserved mask 254 | Hypothesis |
| positive | positive_flags | 1 | three independent unnamed Booleans in bit order 0,1,2; reserved mask 248 | Hypothesis |

| Mode | State | Candidate label |
|---|---|---|
| 0 | complete | no-heating-demand-to-source-or-circuits |
| 1 | label-conflict | no-source-demand-but-demand-from-sink |
| 2 | complete | source-heating-demand |
| 3 | complete | no-source-cooling-demand-but-demand-from-sink |
| 4 | complete | source-cooling-demand |
| 5..255 | unmapped | absent |

Mode 1 preserves the stated candidate; an unresolved competing label remains
Unknown. No competing text is invented and neither label is definitive.
Positive `08` has flags `[false,false,false]` and reserved `8`; it introduces
no fourth Boolean. Automatic `01` is enabled; `80` is disabled with reserved
`128`. Bit roles are unnamed and independent, without executable effects.

An empty selected byte field has state `incomplete`; an overlong field has
state `unknown-order`. Both preserve every supplied byte and omit numeric and
label results. Missing selected fields have no result entry; the aggregate is
`partial`. Complete independent siblings survive either condition. Unknown
fields and fields belonging only to another direction remain solely in `raw`;
they cannot erase valid siblings or fulfill a missing selected field. Aggregate
`complete` means all fields allocated for that direction have complete results;
label-conflict or unmapped results make it `partial`. Explicit unknown selection
always keeps aggregate `Unknown`, even with missing or empty fields.

No numeric value is present for incomplete, unmapped, unit-conflict or
unknown-order fields. This slice allocates no unit-conflict branch. A future
outside-domain carrier may retain its explicitly specified number with separate
`candidate_domain: false`; it cannot change these full carrier domains.
Heating priority, bypass behavior and `FF FF` unset remain candidates without
executable effects. Default zero never fills missing data.

All states and presence/error distinctions must survive JSON round trips.
Mutating nested caller input, returned context/raw/arguments, one semantic field
or a result from another call must not affect any sibling or later call.
Partial results preserve last-known independent evidence; this pure API owns no
persistent state. Semantic success, exact arithmetic and opaque family context
never imply native support, effects or persistence: those remain Unknown.
No output-control, UI label, scan default, executor or active request changes.
Existing eBUS MCP compatibility and GraphQL parity are unaffected; no new
transport or application surface is defined.

## Machine-readable finite case table

The JSON block is the normative finite table. `input` and `output` are full JSON
objects, not wire captures. `errors` hold serialized rejected inputs and require
no successful result. The companion fixture repeats the table; the standard
library unittest checks each independently against constants. It does not
implement another interpreter. Production invocation, memory isolation and
runtime error behavior require separate implementation evidence.

<!-- ab25ao25-contract-start -->
```json
{
  "id": "ab25ao25-demand-views",
  "provenance": "synthetic",
  "contract": {
    "api": "Ab25Ao25Interpret(ab25ao25Input json.RawMessage) (json.RawMessage, error)",
    "package": "vaillant",
    "implementation": "standard-library; pure; no runtime call site",
    "selection": {
      "primary": 181,
      "secondary": 34,
      "operation": 0,
      "view": "isolated-fields",
      "directions": {
        "request": [
          "mode",
          "fan",
          "room_temperature",
          "automatic"
        ],
        "positive": [
          "positive_flags"
        ]
      }
    },
    "grades": {
      "semantic": "Hypothesis",
      "calculation": "Proven",
      "physical": "Unknown",
      "qualified": false
    },
    "mode_labels": {
      "0": "no-heating-demand-to-source-or-circuits",
      "1": "no-source-demand-but-demand-from-sink",
      "2": "source-heating-demand",
      "3": "no-source-cooling-demand-but-demand-from-sink",
      "4": "source-cooling-demand"
    },
    "mode_1": {
      "state": "label-conflict",
      "competing_label": "Unknown"
    },
    "mode_unmapped": [
      5,
      255
    ],
    "fan": {
      "carrier": [
        0,
        255
      ],
      "enum": null
    },
    "room_temperature": {
      "carrier": [
        0,
        255
      ],
      "divisor": 2,
      "unit": "Celsius",
      "sentinel": null
    },
    "automatic": {
      "allocated_bits": [
        0
      ],
      "reserved_bits": [
        1,
        2,
        3,
        4,
        5,
        6,
        7
      ]
    },
    "positive_flags": {
      "allocated_bits": [
        0,
        1,
        2
      ],
      "reserved_bits": [
        3,
        4,
        5,
        6,
        7
      ],
      "roles": null
    },
    "width": 1,
    "empty_state": "incomplete",
    "overlong_state": "unknown-order",
    "missing": "absent result; partial aggregate",
    "arguments": "absent or empty object; no scalar arguments are allocated",
    "unknown_selection": {
      "state": "Unknown",
      "fields": {},
      "physical": "Unknown",
      "qualified": false
    },
    "copy_contract": [
      "context",
      "raw",
      "arguments",
      "result fields",
      "later calls"
    ],
    "error_contract": [
      "duplicate keys at any depth",
      "malformed JSON",
      "wrong JSON kinds",
      "noninteger bytes",
      "bytes outside 0..255"
    ],
    "non_executable_candidates": [
      "heating priority",
      "bypass behavior",
      "FF FF unset"
    ],
    "qualification": "No native support, effects or persistence inferred",
    "scope": "Synthetic software contract; no output-control, UI, scan or transport change"
  },
  "cases": [
    {"id":"ab25ao25-mode-0","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[0]},"state":"partial","fields":{"mode":{"raw":[0],"state":"complete","grade":"Hypothesis","label":"no-heating-demand-to-source-or-circuits"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-1","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[1]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[1]},"state":"partial","fields":{"mode":{"raw":[1],"state":"label-conflict","grade":"Hypothesis","label":"no-source-demand-but-demand-from-sink"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-2","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-3","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[3]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[3]},"state":"partial","fields":{"mode":{"raw":[3],"state":"complete","grade":"Hypothesis","label":"no-source-cooling-demand-but-demand-from-sink"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-4","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[4]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[4]},"state":"partial","fields":{"mode":{"raw":[4],"state":"complete","grade":"Hypothesis","label":"source-cooling-demand"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-5","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[5]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[5]},"state":"partial","fields":{"mode":{"raw":[5],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-255","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[255]},"state":"partial","fields":{"mode":{"raw":[255],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room-0","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"room_temperature":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"room_temperature":[0]},"state":"partial","fields":{"room_temperature":{"raw":[0],"state":"complete","grade":"Hypothesis","number":0,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room-1","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"room_temperature":[1]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"room_temperature":[1]},"state":"partial","fields":{"room_temperature":{"raw":[1],"state":"complete","grade":"Hypothesis","number":0.5,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room-16","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"room_temperature":[16]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"room_temperature":[16]},"state":"partial","fields":{"room_temperature":{"raw":[16],"state":"complete","grade":"Hypothesis","number":8,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room-153","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"room_temperature":[153]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"room_temperature":[153]},"state":"partial","fields":{"room_temperature":{"raw":[153],"state":"complete","grade":"Hypothesis","number":76.5,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room-255","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"room_temperature":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"room_temperature":[255]},"state":"partial","fields":{"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-0","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"fan":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"fan":[0]},"state":"partial","fields":{"fan":{"raw":[0],"state":"complete","grade":"Hypothesis","number":0,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-1","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"fan":[1]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"fan":[1]},"state":"partial","fields":{"fan":{"raw":[1],"state":"complete","grade":"Hypothesis","number":1,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-255","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"fan":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"fan":[255]},"state":"partial","fields":{"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-0","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[0]},"state":"partial","fields":{"automatic":{"raw":[0],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-1","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[1]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[1]},"state":"partial","fields":{"automatic":{"raw":[1],"state":"complete","grade":"Hypothesis","label":"enabled","reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-2","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[2]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[2]},"state":"partial","fields":{"automatic":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":2}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-4","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[4]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[4]},"state":"partial","fields":{"automatic":{"raw":[4],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":4}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-8","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[8]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[8]},"state":"partial","fields":{"automatic":{"raw":[8],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":8}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-16","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[16]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[16]},"state":"partial","fields":{"automatic":{"raw":[16],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":16}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-32","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[32]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[32]},"state":"partial","fields":{"automatic":{"raw":[32],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":32}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-64","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[64]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[64]},"state":"partial","fields":{"automatic":{"raw":[64],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":64}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-128","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[128]},"state":"partial","fields":{"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-255","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"automatic":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"automatic":[255]},"state":"partial","fields":{"automatic":{"raw":[255],"state":"complete","grade":"Hypothesis","label":"enabled","reserved":254}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-0","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[0]},"state":"complete","fields":{"positive_flags":{"raw":[0],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-1","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[1]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[1]},"state":"complete","fields":{"positive_flags":{"raw":[1],"state":"complete","grade":"Hypothesis","flags":[true,false,false],"reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-2","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[2]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[2]},"state":"complete","fields":{"positive_flags":{"raw":[2],"state":"complete","grade":"Hypothesis","flags":[false,true,false],"reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-4","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[4]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[4]},"state":"complete","fields":{"positive_flags":{"raw":[4],"state":"complete","grade":"Hypothesis","flags":[false,false,true],"reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-8","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[8]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[8]},"state":"complete","fields":{"positive_flags":{"raw":[8],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":8}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-16","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[16]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[16]},"state":"complete","fields":{"positive_flags":{"raw":[16],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":16}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-32","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[32]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[32]},"state":"complete","fields":{"positive_flags":{"raw":[32],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":32}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-64","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[64]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[64]},"state":"complete","fields":{"positive_flags":{"raw":[64],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":64}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-128","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[128]},"state":"complete","fields":{"positive_flags":{"raw":[128],"state":"complete","grade":"Hypothesis","flags":[false,false,false],"reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-255","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[255]},"state":"complete","fields":{"positive_flags":{"raw":[255],"state":"complete","grade":"Hypothesis","flags":[true,true,true],"reserved":248}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-complete","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"arguments":{}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false,"arguments":{}}},
    {"id":"ab25ao25-mode-empty","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-overlong","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[0,255],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[0,255],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[0,255],"state":"unknown-order","grade":"Hypothesis"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-missing","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-mode-zero","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[0],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[0],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[0],"state":"complete","grade":"Hypothesis","label":"no-heating-demand-to-source-or-circuits"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-empty","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-overlong","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[0,255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[0,255],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[0,255],"state":"unknown-order","grade":"Hypothesis"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-missing","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-fan-zero","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[0],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[0],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[0],"state":"complete","grade":"Hypothesis","number":0,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room_temperature-empty","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room_temperature-overlong","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[0,255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[0,255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[0,255],"state":"unknown-order","grade":"Hypothesis"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room_temperature-missing","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"automatic":[128]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-room_temperature-zero","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[0],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[0],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[0],"state":"complete","grade":"Hypothesis","number":0,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-empty","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[],"state":"incomplete","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-overlong","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[0,255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[0,255]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[0,255],"state":"unknown-order","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-missing","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255]},"state":"partial","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-automatic-zero","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[0]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[0]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[0],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":0}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-empty","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[]},"state":"partial","fields":{"positive_flags":{"raw":[],"state":"incomplete","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-overlong","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[0,255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[0,255]},"state":"partial","fields":{"positive_flags":{"raw":[0,255],"state":"unknown-order","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-positive-missing","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{},"state":"partial","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-selection-primary","input":{"context":{"primary":180,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":180,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-selection-secondary","input":{"context":{"primary":181,"secondary":35,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":35,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-selection-operation","input":{"context":{"primary":181,"secondary":34,"operation":1,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":1,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-selection-direction","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"other","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"other","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-selection-view","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"other","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"other","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-missing-selection-primary","input":{"context":{"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-missing-selection-secondary","input":{"context":{"primary":181,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-missing-selection-operation","input":{"context":{"primary":181,"secondary":34,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-missing-selection-direction","input":{"context":{"primary":181,"secondary":34,"operation":0,"view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-missing-selection-view","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-opaque-family","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":{"opaque":[1,"other-family"]},"variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":{"opaque":[1,"other-family"]},"variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-opaque-variant","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":{"opaque":[2,"other-variant"]}},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":{"opaque":[2,"other-variant"]}},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-opaque-extra","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant","extra":{"opaque":[3]}},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant","extra":{"opaque":[3]}},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-cross-request","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"positive_flags":[7]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"positive_flags":[7]},"state":"partial","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-cross-positive","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"positive","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128]},"state":"partial","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-unknown-sibling","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128],"unmodelled":[0,255]}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{"mode":[2],"fan":[255],"room_temperature":[255],"automatic":[128],"unmodelled":[0,255]},"state":"complete","fields":{"mode":{"raw":[2],"state":"complete","grade":"Hypothesis","label":"source-heating-demand"},"fan":{"raw":[255],"state":"complete","grade":"Hypothesis","number":255,"calculation":"Proven"},"room_temperature":{"raw":[255],"state":"complete","grade":"Hypothesis","number":127.5,"calculation":"Proven"},"automatic":{"raw":[128],"state":"complete","grade":"Hypothesis","label":"disabled","reserved":128}},"physical":"Unknown","qualified":false}},
    {"id":"ab25ao25-all-absent","input":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"fields":{}},"output":{"context":{"primary":181,"secondary":34,"operation":0,"direction":"request","view":"isolated-fields","family":"synthetic-family","variant":"synthetic-variant"},"raw":{},"state":"partial","fields":{},"physical":"Unknown","qualified":false}}
  ],
  "errors": [
    {"id":"ab25ao25-error-0","input_json":"{","error":true,"successful_result":false},
    {"id":"ab25ao25-error-1","input_json":"[]","error":true,"successful_result":false},
    {"id":"ab25ao25-error-2","input_json":"null","error":true,"successful_result":false},
    {"id":"ab25ao25-error-3","input_json":"{\"context\":{},\"context\":{},\"fields\":{}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-4","input_json":"{\"context\":{\"primary\":181,\"primary\":181},\"fields\":{}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-5","input_json":"{\"context\":{},\"fields\":{\"fan\":[0],\"fan\":[1]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-6","input_json":"{\"context\":{\"opaque\":{\"x\":1,\"x\":2}},\"fields\":{}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-7","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[-1]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-8","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[256]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-9","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[1.5]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-10","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[true]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-11","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[null]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-12","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[\"0\"]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-13","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[{}]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-14","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[[]]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-15","input_json":"{\"context\":null,\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-16","input_json":"{\"context\":[],\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-17","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":[]}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-18","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":null}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-19","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]},\"arguments\":null}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-20","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]},\"arguments\":[]}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-21","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]},\"arguments\":{\"enabled\":true}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-22","input_json":"{\"context\":{\"primary\":true,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-23","input_json":"{\"context\":{\"primary\":181,\"secondary\":\"34\",\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-24","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0.5,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-25","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":null,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-26","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":0,\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-27","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":[]},\"fields\":{\"fan\":[0]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-28","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":null}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-29","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":0}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-30","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":\"00\"}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-31","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":{}}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-32","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":1,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0],\"unmodelled\":[256]}}","error":true,"successful_result":false},
    {"id":"ab25ao25-error-33","input_json":"{\"context\":{\"primary\":181,\"secondary\":34,\"operation\":0,\"direction\":\"request\",\"view\":\"isolated-fields\"},\"fields\":{\"fan\":[0],\"unmodelled\":[256]}}","error":true,"successful_result":false}
  ]
}
```
<!-- ab25ao25-contract-end -->

The focused suite is a mandatory separate ship check. The full docs gate uses
an explicit list and does not automatically discover this new suite. No gate,
index, catalog or protocol page is changed by this companion.
