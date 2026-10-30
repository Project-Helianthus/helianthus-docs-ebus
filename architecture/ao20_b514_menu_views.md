# B514 selected menu and pressure software API results

This bounded software API companion records the Release 0.7 slice tracked by
issue #940, with Refs #736; it does not close the parent. The
[public native B514 contract](../protocols/vaillant/ebus-vaillant-B514.md#candidate-sub-commands)
comes first for native claims: its subcommands are candidate layouts, its OP06
states depend on profile, and it establishes no native qualification for the
selections below. The supplied issue contract defines these finite software
views. They are **Hypothesis** family interpretations. Physical support,
adaptation, peer effects and persistence remain **Unknown**. Arithmetic may be
**Proven** without changing that family grade. A candidate label grants no
permission. No device model is selected or qualified.

The pure standard-library function in package `vaillant` is exactly:

```go
Ab19Ao19Interpret(ab19ao19Input json.RawMessage) (json.RawMessage, error)
```

The input is an object containing `context`, `fields`, and optionally
`arguments`. Context has integer `primary=181`, `secondary=20`, integer
`operation`, string `direction`, and explicit string `view`. Every additional
context key, including opaque `family` and `variant` values, survives unchanged.
Fields are named byte arrays; each element must be a JSON integer in 0..255
(booleans, fractions, strings and null are not byte integers). Arguments, when
supplied, are copied independently. This slice specifies no nonempty argument
vocabulary; it grants no flag, command or integer-argument behavior. A nonempty
argument vocabulary needs an explicit contract before admission.

Malformed JSON, duplicate keys at any object depth, missing required members,
wrong JSON kinds or invalid bytes return an error with no successful result.
Reject duplicates before a map decoder could discard them. Absent versus zero,
and missing versus empty, remain distinct through JSON round trips. A valid but
unrecognized operation, direction or view returns structured raw-only `Unknown`;
primary/secondary outside this identity likewise cannot select these views.
Never infer selection from a field name, payload length, family or prefix.

The result has `context` (unchanged deep copy), `raw` (independent copy of all
supplied fields), optional `arguments` only when supplied, `state`, semantic
`fields`, `physical="Unknown"`, and `qualified=false`. Each result field retains
`raw` and `state`; semantic fields carry `grade="Hypothesis"`. Optional `number`,
`label`, `flags`, `reserved`, or `candidate_domain` exist only where defined.
An exact numeric calculation additionally carries `calculation="Proven"`.
No flags, reserved bits or outside-domain predicates are defined in this slice;
never synthesize them. In a contract that explicitly defines an outside-domain
carrier it may retain its number with `candidate_domain=false`.

Here `complete` means every selected field has its required bytes, including
unmapped or conflicting fields; it proves no effect. `partial` means bytes for
at least one selected field are missing. Preserve complete independent fields,
and retain the supplied fragment for each incomplete field. `Unknown` is the
explicit raw-only branch and must not become `partial`. Field states are
`mapped`, `unmapped`, `invalid`, `unit-conflict`, or `incomplete` as shown below.
Incomplete, unmapped, unit-conflict and unknown-order fields have no number.
Unknown siblings cannot erase valid fields. Input mutation, returned nested
mutation, sibling fields and later calls must never share mutable storage.

| Operation / positive view | Input field | Software interpretation (Hypothesis) |
|---|---|---|
| 6 / `generic-result` | isolated `feedback` | 1 in-progress; 255 unsupported; 0, 2 and other unmapped values have no label |
| 6 / `specific-a-result` | isolated `feedback` | 1 not-successful; 3..255 invalid; 0 and 2 unmapped |
| 6 / `specific-b-result` | isolated `feedback` | 1 not-successful; 3..255 invalid; 0 and 2 unmapped |
| 7 / `progress` | isolated `feedback` | 0 idle; 1 progress; 2 passed; 3 warning; 4 combustion-error; 5 gas-type-error; 6 aborted; 255 unsupported; all others unmapped |
| 8 / `pressure` | `logical_object` | extent 13; fields below; no command builder |

Isolated feedback uses its first byte; additional bytes and unknown named fields
remain raw. Empty and missing feedback are distinct raw inputs with incomplete
semantic feedback. OP08 feedback has no supplied enum, so remains unmapped;
feedback alone has no completed-effect assertion. OP02's twenty-row union and
OP05's 128 typed rows remain Unknown, regardless of their supplied bytes.

| Logical position | Width | Field | Result and boundary |
|---|---:|---|---|
| 0..2 | 3 | opaque prefix | preserve; no prefix assertion, operation or identity decoding |
| 3 | 1 | feedback | raw/unmapped; no borrowed OP07 enum |
| 4 | 2 | pressure | LEu16 carrier only, no physical converter or pressure unit |
| 6 | 2 | minimum | independent LEu16 carrier only |
| 8 | 2 | maximum | independent LEu16 carrier only |
| 10 | 1 | step | raw unit-conflict: constant 1 mbar versus default 0; no number or silent normalization |
| 11 | 2 | flow | LEu16 / 100, l/min; exact carrier arithmetic Proven |

Carrier numbers 1, 256 and 4660 below are not converted pressure readings.
The flow bytes `[100,0]` give 1 l/min; `[100,1]` give 3.56 l/min. Length 12 is
partial: flow has only one byte and no number, while all earlier complete words
remain useful. Extra tails survive without changing the selected extent.

There is no cache, catalog, metadata listing, registration, pending API import,
runtime call site, active request or transport change. eBUS MCP compatibility
and GraphQL parity remain unchanged. This page has no dependency on AO19 code
or a code merge. All new implementation symbols must start `ab19ao19` or exported
`Ab19Ao19`; Go tests start `TestAb19Ao19`. Existing symbols and literal JSON and
protocol field labels keep their names. No Entries/Lookup API or second family
schema is introduced. Nothing is stable before Helianthus 1.0.

The finite machine-readable contract below and the
[synthetic tuple fixture](fixtures/ao20_b514_menu_views.json) describe expected
projections (`state`, semantic `fields`, `physical`, `qualified`). Runtime output
must additionally preserve the complete context, raw fields and optional
arguments as specified above. Error vectors specify required runtime rejection;
they are not evidence that an implementation has executed. The
[standard-library unittest](../tests/test_ao20_b514_menu_views.py) checks the page
and fixture against independent finite constants, including negative mutations.
It does not implement a decoder or establish runtime conformance of the Go API.
The focused suite is a separate mandatory ship check because the repository's
full gate uses an explicit list. Independent committed-change review, full Gate
D, publication checks and applicable transport classification remain required.

<!-- ab19ao19 finite contract: exactly one JSON block -->
```json
{
  "contract": {
    "api": "Ab19Ao19Interpret(ab19ao19Input json.RawMessage) (json.RawMessage, error)",
    "package": "vaillant",
    "dependencies": "standard library",
    "input": {
      "required": [
        "context",
        "fields"
      ],
      "optional": [
        "arguments"
      ],
      "context": {
        "primary": 181,
        "secondary": 20,
        "operation": "integer",
        "direction": "string",
        "view": "explicit string"
      },
      "fields": "object of integer byte arrays, each element 0..255",
      "arguments": "object; no nonempty argument vocabulary is specified by this slice"
    },
    "output": {
      "required": [
        "context",
        "raw",
        "state",
        "fields",
        "physical",
        "qualified"
      ],
      "optional": [
        "arguments"
      ],
      "physical": "Unknown",
      "qualified": false,
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
        "grade",
        "calculation"
      ],
      "semantic_grade": "Hypothesis",
      "exact_calculation": "Proven"
    },
    "selection": [
      [
        6,
        "positive",
        "generic-result"
      ],
      [
        6,
        "positive",
        "specific-a-result"
      ],
      [
        6,
        "positive",
        "specific-b-result"
      ],
      [
        7,
        "positive",
        "progress"
      ],
      [
        8,
        "positive",
        "pressure"
      ]
    ],
    "op06": {
      "generic-result": {
        "1": "in-progress",
        "255": "unsupported"
      },
      "specific-a-result": {
        "1": "not-successful",
        "invalid": [
          3,
          255
        ]
      },
      "specific-b-result": {
        "1": "not-successful",
        "invalid": [
          3,
          255
        ]
      },
      "unmapped": [
        0,
        2
      ]
    },
    "op07": {
      "0": "idle",
      "1": "progress",
      "2": "passed",
      "3": "warning",
      "4": "combustion-error",
      "5": "gas-type-error",
      "6": "aborted",
      "255": "unsupported",
      "unmapped": [
        7,
        254
      ]
    },
    "op08": {
      "field": "logical_object",
      "extent": 13,
      "opaque_positions": [
        0,
        1,
        2
      ],
      "layout": [
        [
          "feedback",
          3,
          1,
          "unmapped"
        ],
        [
          "pressure",
          4,
          2,
          "LEu16 carrier"
        ],
        [
          "minimum",
          6,
          2,
          "LEu16 carrier"
        ],
        [
          "maximum",
          8,
          2,
          "LEu16 carrier"
        ],
        [
          "step",
          10,
          1,
          "unit-conflict"
        ],
        [
          "flow",
          11,
          2,
          "LEu16 / 100 l/min"
        ]
      ],
      "pressure_unit": "Unknown",
      "step_conflict": {
        "constant": 1,
        "unit": "mbar",
        "default": 0
      }
    },
    "rules": {
      "unknown_selection": "raw-only Unknown; no guessed view or identity",
      "identity_mismatch": "raw-only Unknown",
      "raw_preservation": "all context keys, raw fields, opaque prefix and tails; arguments if supplied",
      "partial": "retain complete independent fields; never decode a truncated word",
      "number_omission": [
        "incomplete",
        "unmapped",
        "unit-conflict",
        "unknown-order"
      ],
      "outside_domain": "an explicitly defined carrier may keep number with candidate_domain=false; none defined here",
      "isolation": "deep independent context, raw and arguments; calls and sibling fields share no mutable storage",
      "presence": "missing, empty and explicit zero remain distinct through JSON round trips",
      "errors": "malformed JSON, duplicate object keys at every depth, wrong JSON kinds, invalid bytes: error and no successful result",
      "unknown_sibling": "cannot erase complete independent fields",
      "qualification": "never inferred from family, variant, selection or arithmetic",
      "effects": "feedback alone proves no completed effect; physical adaptation, peer effects and persistence Unknown",
      "op02": "twenty-row union Unknown",
      "op05": "128 typed rows Unknown",
      "non_goals": [
        "command builder",
        "global cache",
        "generic catalog",
        "metadata listing",
        "registration",
        "pending API import",
        "runtime call site"
      ],
      "parity": "no eBUS MCP or GraphQL surface change"
    }
  },
  "cases": [
    {"id":"ab19ao19_op06_generic_0","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[0]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_generic_1","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[1],"state":"mapped","grade":"Hypothesis","label":"in-progress"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_generic_2","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[2]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[2],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_generic_3","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[3]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[3],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_generic_255","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[255]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[255],"state":"mapped","grade":"Hypothesis","label":"unsupported"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_a_0","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[0]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_a_1","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[1],"state":"mapped","grade":"Hypothesis","label":"not-successful"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_a_2","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[2]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[2],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_a_3","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[3]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[3],"state":"invalid","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_a_255","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[255]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[255],"state":"invalid","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_b_0","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[0]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_b_1","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[1],"state":"mapped","grade":"Hypothesis","label":"not-successful"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_b_2","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[2]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[2],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_b_3","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[3]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[3],"state":"invalid","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op06_specific_b_255","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[255]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[255],"state":"invalid","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_0","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[0]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[0],"state":"mapped","grade":"Hypothesis","label":"idle"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_1","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[1],"state":"mapped","grade":"Hypothesis","label":"progress"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_2","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[2]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[2],"state":"mapped","grade":"Hypothesis","label":"passed"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_3","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[3]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[3],"state":"mapped","grade":"Hypothesis","label":"warning"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_4","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[4]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[4],"state":"mapped","grade":"Hypothesis","label":"combustion-error"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_5","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[5]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[5],"state":"mapped","grade":"Hypothesis","label":"gas-type-error"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_6","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[6]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[6],"state":"mapped","grade":"Hypothesis","label":"aborted"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_7","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[7]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[7],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_254","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[254]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[254],"state":"unmapped","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_op07_255","input":{"context":{"primary":181,"secondary":20,"operation":7,"direction":"positive","view":"progress","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[255]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[255],"state":"mapped","grade":"Hypothesis","label":"unsupported"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_pressure_control","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_pressure_low","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,2,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[2,0],"state":"mapped","number":2,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_pressure_high","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,1,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,1],"state":"mapped","number":257,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_minimum_low","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,1,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[1,1],"state":"mapped","number":257,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_minimum_high","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,2,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,2],"state":"mapped","number":512,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_maximum_low","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,53,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[53,18],"state":"mapped","number":4661,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_maximum_high","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,19,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,19],"state":"mapped","number":4916,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_flow_low","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,200,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[200,0],"state":"mapped","number":2,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_flow_high","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,1]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,1],"state":"mapped","number":3.56,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_prefix_0","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[255,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_prefix_1","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,255,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_prefix_2","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,255,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_step_one","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,1,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[1],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_pressure_feedback","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,6,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[6],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_tail_and_sibling","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0,255,0],"unmodelled":[0,255]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_length_0","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"pressure":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_3","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"pressure":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_4","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_5","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1],"state":"incomplete","grade":"Hypothesis"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_6","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_7","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_8","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_9","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_10","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_11","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_length_12","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100]}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_missing_object","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{}},"expected":{"state":"partial","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"pressure":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"minimum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"maximum":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"step":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"flow":{"raw":[],"state":"incomplete","grade":"Hypothesis"}}}},
    {"id":"ab19ao19_explicit_zero","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,0,0,0,0,0,0,0,0,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[0,0],"state":"mapped","number":0,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,0],"state":"mapped","number":0,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[0,0],"state":"mapped","number":0,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[0,0],"state":"mapped","number":0,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_unknown_primary","input":{"context":{"primary":180,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_secondary","input":{"context":{"primary":181,"secondary":21,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_direction","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"negative","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_view","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"other","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_operation","input":{"context":{"primary":181,"secondary":20,"operation":9,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_op2","input":{"context":{"primary":181,"secondary":20,"operation":2,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_unknown_op5","input":{"context":{"primary":181,"secondary":20,"operation":5,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_opaque_family","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":{"opaque":[0,"candidate"]},"variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_opaque_variant","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":{"opaque":[0,"candidate"]}},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}},
    {"id":"ab19ao19_wrong_view_generic-result","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_wrong_view_specific-a-result","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"specific-a-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_wrong_view_specific-b-result","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"specific-b-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_feedback_missing","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{}},"expected":{"state":"partial","fields":{"feedback":{"raw":[],"state":"incomplete","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_feedback_empty","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[]}},"expected":{"state":"partial","fields":{"feedback":{"raw":[],"state":"incomplete","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_feedback_tail","input":{"context":{"primary":181,"secondary":20,"operation":6,"direction":"positive","view":"generic-result","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1,255],"other":[6]}},"expected":{"state":"complete","fields":{"feedback":{"raw":[1,255],"state":"mapped","grade":"Hypothesis","label":"in-progress"}},"physical":"Unknown","qualified":false}},
    {"id":"ab19ao19_arguments_empty","input":{"context":{"primary":181,"secondary":20,"operation":8,"direction":"positive","view":"pressure","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"logical_object":[17,34,51,0,1,0,0,1,52,18,0,100,0]},"arguments":{}},"expected":{"state":"complete","physical":"Unknown","qualified":false,"fields":{"feedback":{"raw":[0],"state":"unmapped","grade":"Hypothesis"},"pressure":{"raw":[1,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"},"minimum":{"raw":[0,1],"state":"mapped","number":256,"grade":"Hypothesis","calculation":"Proven"},"maximum":{"raw":[52,18],"state":"mapped","number":4660,"grade":"Hypothesis","calculation":"Proven"},"step":{"raw":[0],"state":"unit-conflict","grade":"Hypothesis"},"flow":{"raw":[100,0],"state":"mapped","number":1,"grade":"Hypothesis","calculation":"Proven"}}}}
  ],
  "error_cases": [
    {"id":"ab19ao19_malformed","json":"{\"context\":","expected":"error; no successful result"},
    {"id":"ab19ao19_duplicate_top","json":"{\"context\":{},\"context\":{},\"fields\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_duplicate_context","json":"{\"context\":{\"view\":\"pressure\",\"view\":\"progress\"},\"fields\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_duplicate_fields","json":"{\"context\":{},\"fields\":{\"feedback\":[0],\"feedback\":[1]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_duplicate_arguments","json":"{\"context\":{},\"fields\":{},\"arguments\":{\"x\":0,\"x\":1}}","expected":"error; no successful result"},
    {"id":"ab19ao19_wrong_root","json":"[]","expected":"error; no successful result"},
    {"id":"ab19ao19_wrong_context","json":"{\"context\":[],\"fields\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_wrong_fields","json":"{\"context\":{},\"fields\":[]}","expected":"error; no successful result"},
    {"id":"ab19ao19_wrong_arguments","json":"{\"context\":{},\"fields\":{},\"arguments\":[]}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_negative","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[-1]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_overflow","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[256]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_fraction","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[0.5]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_boolean","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[true]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_null","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[null]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_string","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[\"0\"]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_object","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[{}]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_byte_nested","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":6,\"direction\":\"positive\",\"view\":\"generic-result\"},\"fields\":{\"feedback\":[[]]}}","expected":"error; no successful result"},
    {"id":"ab19ao19_wrong_array","json":"{\"context\":{},\"fields\":{\"feedback\":0}}","expected":"error; no successful result"},
    {"id":"ab19ao19_missing_context","json":"{\"fields\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_missing_fields","json":"{\"context\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_null_fields","json":"{\"context\":{},\"fields\":null}","expected":"error; no successful result"},
    {"id":"ab19ao19_operation_string","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":\"8\",\"direction\":\"positive\",\"view\":\"pressure\"},\"fields\":{}}","expected":"error; no successful result"},
    {"id":"ab19ao19_operation_bool","json":"{\"context\":{\"primary\":181,\"secondary\":20,\"operation\":true,\"direction\":\"positive\",\"view\":\"pressure\"},\"fields\":{}}","expected":"error; no successful result"}
  ]
}
```
