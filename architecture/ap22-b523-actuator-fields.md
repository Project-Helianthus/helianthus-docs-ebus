# B523 relay and mixer interpretation API

This architecture contract defines a pure local representation for functional-module
families. The native evidence boundary is the public
[B523 contract](../protocols/vaillant/ebus-vaillant-b523.md#candidate-layouts),
including its [conflicting setpoint evidence](../protocols/vaillant/ebus-vaillant-b523.md#open-questions).
Those layouts are candidates, unconfirmed on the wire. The following software
selectors and grades do not establish a native contract or physical support.
The synthetic [scenario file](fixtures/ap22_b523_actuator_fields.json) and
[standard-library checks](../tests/test_ap22_b523_actuator_fields.py) specify this
contract independently of a runtime implementation.

## Callable and input

Package `vaillant` exposes exactly this API, with the Go standard library:

```go
func Ab21Ap21Evaluate(ab21ap21Input json.RawMessage) (json.RawMessage, error)
```

This is a library specification. There is no initialization side effect,
persistent cache, generic catalog, listing API or runtime caller. New Go names
use `ab21ap21` or exported `Ab21Ap21`; Go test functions use `TestAb21Ap21`.
Existing package names, JSON labels and standard-library symbols retain their
spelling. No Go implementation is provided by this page.

The input is one JSON object: required `context` object and `fields` object,
plus optional `arguments` object. Every field value, including an unknown field,
is an array of integral u8 bytes. The relay vector is one named array with its
route's exact length; other named fields have length one. Length mismatch,
including missing, empty, short and overlong arrays, is an incomplete field,
not a malformed byte. Wrong kinds, fractional or out-of-range bytes are errors.
A Boolean is never an integer. Objects, strings, null and arrays retain their
JSON kinds without coercion. Unknown argument and context keys preserve any
JSON value verbatim. There are no u16/u32 arguments in these views; the scalar
limits below specify the type vocabulary, not additional arguments.

`context.primary=181` and `secondary=35` identify the B523 selector; `operation`
is integral u8, `direction` and `view` are explicit strings. Missing or null
selectors are unsupported, remaining distinct from zero. A wrong non-null kind
is an error. `family`, context `variant` and all other context keys are opaque.
Only `arguments.variant` selects the mixer-request representation; it is required
and is exactly the string `two-circuit` or `three-circuit`. Context variant cannot
substitute for it. Unknown extra argument keys remain unchanged. Valid arguments
are checked before route admission; required variant applies only to the mixer
request route. Unknown selector combinations apply no formulas and return
raw-only `Unknown`, even if field lengths happen to match another route.

| OP | Direction | View | Fields with exact lengths | Required arguments |
|---|---|---|---|---|
| 1 | request | relay-six | relays:6, pwm1:1 | none |
| 1 | positive-feedback | relay-six | feedback:1 | none |
| 5 | request | relay-twelve | relays:12, pwm1:1, pwm2:1 | none |
| 5 | positive-feedback | relay-twelve | feedback:1 | none |
| 2 | request | mixer | circuit:1, mode:1, setpoint:1 | variant:two-circuit/three-circuit |
| 2 | positive-feedback | mixer | feedback:1, movement:1 | none |

There are no other allowed routes, operations or direction aliases. The
`positive-feedback` direction describes a payload to interpret; its feedback
value can still be rejected.

## Result, errors and copies

A successful result is an object containing `context` unchanged, `raw` as a deep
independent copy of `fields`, `arguments` unchanged iff supplied, `state`, semantic
`fields`, `physical="Unknown"` and `qualified=false`. Each known semantic field
retains its own independent `raw`, `state` and applicable `number`, `label`,
`alternatives`, `candidate_domain`, `items`, `relevant`, `unit`, `maximum` or
`setpoint_relevant`. Relay-vector `items` retain each slot's raw byte as a
one-byte array. Candidate results carry `grade="Hypothesis"`; exact arithmetic
may additionally carry `calculation="Proven"`. Calculation grade never replaces
family grade. Missing fields omit `raw`; an empty field retains `raw=[]`.
Incomplete results use `state="incomplete"` with no number or label. Unmapped
quantities use `state="Unknown"` without invented number or label. Unknown field
names remain in top-level raw only; their semantics are Unknown. No flags,
reserved meanings or configuration bitfields are modeled or invented.

Top-level state is `partial` if any required independent field is incomplete,
`Unknown` for unsupported selectors (with semantic `fields={}`), otherwise
`complete` as a local representation only. A competing unresolved candidate or
an ignored byte does not make a complete sibling incomplete. A missing mode
makes setpoint `relevant="Unknown"`, while both setpoint candidates survive if
its byte is complete. A missing variant is an error, not partial input.

Malformed JSON, duplicate keys at any nesting depth, wrong kinds, fractions,
out-of-range numbers or missing required arguments return an error and no
successful result. Integral u8/u16/u32 ranges are 0..255, 0..65535 and
0..4294967295. No successful partial result accompanies an admission error.
Valid independent siblings survive field-length incompleteness. Evaluation does
not mutate input; mutation of input, context, raw, argument objects, semantic
raw or returned alternatives cannot affect other result storage or a later
call. Preserve every absence/null/zero/raw/state distinction across JSON round
trips. There is no persistent last-result store; any last-known-good sibling
retention described here is within the current pure result, never fabricated
freshness or cross-call state.

## Candidate fields

All rows below are Hypothesis family interpretations. These duration and
movement labels do not start a clock, command an actuator or prove an effect.

| Relay minimum | Relay maximum | Label | Quantity |
|---|---|---|---|
| 0 | 0 | off | none |
| 1 | 253 | on-for-seconds-then-off | raw seconds |
| 254 | 254 | on | none |
| 255 | 255 | unchanged | none |

PWM always retains two ordered alternatives, `numeric` and `behavior`, for each
channel independently. Numeric arithmetic is `raw/2` percent with
`candidate_domain=true` for 0..250; outside that domain retain the calculation
and set `candidate_domain=false`. The behavior branch calculates `raw/2` percent
only for 0..200, otherwise labels `unchanged` with no number. Both numeric
calculations additionally carry Proven. Never clip to 100, merge branches or
select one automatically.

| PWM raw | Numeric percent | Numeric candidate domain | Behavior |
|---|---|---|---|
| 200 | 100 | true | 100 percent |
| 201 | 100.5 | true | unchanged |
| 250 | 125 | true | unchanged |
| 255 | 127.5 | false | unchanged |

Circuit 0/1 is `circuit-1`/`circuit-2` for both variants. Circuit 2 is `circuit-3`
only for `three-circuit`; all remaining values are `ignored`. Context family or
variant never admits circuit 2 into the two-circuit argument variant.

| Mode | Label | Setpoint relevant |
|---|---|---|
| 0 | stop/pump-off/close | false |
| 1 | heating-regulation | true |
| 2 | cooling-regulation | true |
| 3 | pump-off/open | false |
| 4 | pump-on/close | false |
| 5 | pump-on/open | false |
| 6..255 | ignored | false |

Setpoint always retains ordered `signed` and `conflicting` alternatives, even
when irrelevant. Signed interpretation is `signed8(raw)*0.5` Celsius, where
`signed8(raw)=raw` below 128 and `raw-256` otherwise: full range -64..63.5.
The conflicting example is raw 190 (BE) giving 95 Celsius with a stated clamp
95. For every other raw byte this conflicting conversion is Unknown: no general
unsigned formula is defined. Its `clamp=95` remains descriptive; no clipping
algorithm is inferred. The signed calculation additionally carries Proven;
the conflicting example retains Hypothesis only. Neither branch is selected.
Mode 0 marks both alternatives irrelevant without deleting raw or calculations.

| Setpoint raw | Signed Celsius | Conflicting Celsius | Clamp |
|---|---|---|---|
| 0 | 0 | Unknown | 95 |
| 127 | 63.5 | Unknown | 95 |
| 128 | -64 | Unknown | 95 |
| 190 | -33 | 95 | 95 |
| 255 | -0.5 | Unknown | 95 |

Movement uses signed8 percent: 0 is stopped, -1..-100 closing, +1..100 opening,
with magnitude 100 maximum. Outside these named intervals the result is Unknown
without a number or label; raw remains. Known calculations additionally carry
Proven. Configuration and physical movement stay Unknown.

| Movement raw | Signed percent | Label | Maximum |
|---|---|---|---|
| 156 | -100 | closing | true |
| 100 | 100 | opening | true |
| 155 | Unknown | Unknown | Unknown |
| 101 | Unknown | Unknown | Unknown |

| OP | Feedback 1 | Other feedback |
|---|---|---|
| 1 | accepted | rejected |
| 2 | accepted | rejected |
| 5 | accepted | rejected-or-unsupported |

Feedback always retains its raw byte. Acceptance labels cannot qualify physical
association, support, effects, freshness, persistence or delivery.

## Exact structural contract

The following JSON supplies normative shape, route and transition declarations;
the tables and scenario tuples are checked against independent constants.

```json
{
  "signature": "Ab21Ap21Evaluate(ab21ap21Input json.RawMessage) (json.RawMessage, error)",
  "package": "vaillant",
  "library": "Go standard library",
  "context": {
    "primary": 181,
    "secondary": 35,
    "operation": "integral u8",
    "direction": [
      "request",
      "positive-feedback"
    ],
    "view": [
      "relay-six",
      "relay-twelve",
      "mixer"
    ],
    "opaque": "preserve verbatim; never qualify"
  },
  "routes": [
    [
      1,
      "request",
      "relay-six",
      {
        "relays": 6,
        "pwm1": 1
      },
      {}
    ],
    [
      1,
      "positive-feedback",
      "relay-six",
      {
        "feedback": 1
      },
      {}
    ],
    [
      5,
      "request",
      "relay-twelve",
      {
        "relays": 12,
        "pwm1": 1,
        "pwm2": 1
      },
      {}
    ],
    [
      5,
      "positive-feedback",
      "relay-twelve",
      {
        "feedback": 1
      },
      {}
    ],
    [
      2,
      "request",
      "mixer",
      {
        "circuit": 1,
        "mode": 1,
        "setpoint": 1
      },
      {
        "variant": [
          "two-circuit",
          "three-circuit"
        ]
      }
    ],
    [
      2,
      "positive-feedback",
      "mixer",
      {
        "feedback": 1,
        "movement": 1
      },
      {}
    ]
  ],
  "input": {
    "root": "object",
    "required": [
      "context",
      "fields"
    ],
    "fields": "object of arrays of integral u8; missing or nonexact length is incomplete",
    "arguments": "optional object; variant required only for mixer request; unknown keys preserved",
    "duplicates": "reject at every depth",
    "kinds": "no coercion; Boolean is not integer",
    "numbers": {
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
    "context-presence": "missing, null, zero remain distinct; absent/null selectors are unsupported; opaque kinds unchanged"
  },
  "result": {
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
    "states": [
      "complete",
      "partial",
      "Unknown"
    ],
    "copy": "context, raw, arguments and field raw are independent; no shared mutable storage across calls",
    "grades": {
      "family": "Hypothesis",
      "arithmetic": "Proven",
      "physical": "Unknown"
    },
    "unsupported": "raw-only Unknown; fields={}; no formulas",
    "partial": "nonexact field length; complete independent siblings survive",
    "incomplete": "state=incomplete; raw omitted only when input field absent; no number or label",
    "unmapped": "state=Unknown; raw retained; no invented number or label",
    "arguments": "preserve iff supplied"
  },
  "relay": [
    [
      0,
      0,
      "off"
    ],
    [
      1,
      253,
      "on-for-seconds-then-off"
    ],
    [
      254,
      254,
      "on"
    ],
    [
      255,
      255,
      "unchanged"
    ]
  ],
  "pwm": {
    "numeric": {
      "formula": "raw/2",
      "domain": [
        0,
        250
      ],
      "outside": "retain calculation; candidate_domain=false"
    },
    "behavior": {
      "domain": [
        0,
        200
      ],
      "formula": "raw/2",
      "otherwise": "unchanged"
    },
    "selection": "none"
  },
  "mixer": {
    "circuits": {
      "two-circuit": [
        0,
        1
      ],
      "three-circuit": [
        0,
        1,
        2
      ]
    },
    "circuit-labels": [
      "circuit-1",
      "circuit-2",
      "circuit-3"
    ],
    "modes": [
      "stop/pump-off/close",
      "heating-regulation",
      "cooling-regulation",
      "pump-off/open",
      "pump-on/close",
      "pump-on/open"
    ],
    "other": "ignored",
    "setpoint-relevant": [
      1,
      2
    ],
    "signed": {
      "formula": "signed8(raw)*0.5",
      "range": [
        -64,
        63.5
      ]
    },
    "conflicting": {
      "raw": 190,
      "number": 95,
      "clamp": 95,
      "other": "Unknown"
    },
    "selection": "none"
  },
  "movement": [
    [
      -128,
      -101,
      "Unknown"
    ],
    [
      -100,
      -1,
      "closing"
    ],
    [
      0,
      0,
      "stopped"
    ],
    [
      1,
      100,
      "opening"
    ],
    [
      101,
      127,
      "Unknown"
    ]
  ],
  "feedback": {
    "1": {
      "1": "accepted",
      "other": "rejected"
    },
    "2": {
      "1": "accepted",
      "other": "rejected"
    },
    "5": {
      "1": "accepted",
      "other": "rejected-or-unsupported"
    }
  },
  "errors": [
    "malformed-json",
    "duplicate-key",
    "wrong-kind",
    "fraction",
    "out-of-range",
    "missing-required-argument"
  ],
  "invariants": {
    "side-effects": false,
    "persistent-cache": false,
    "generic-catalog": false,
    "listing-api": false,
    "runtime-caller": false,
    "native-qualification": false,
    "mcp": "compatibility preserved; no registration",
    "graphql": "same raw/context/state/alternatives/grades; no new resolver"
  }
}
```

## Compatibility and verification boundary

This contract adds no active executor, method registration, scan-default change,
peer communication or automatic qualification. Existing eBUS MCP compatibility
is preserved. Any future GraphQL projection must preserve the same context,
raw, arguments, state, alternatives and grades without choosing candidates or
qualifying support; there is no new resolver here. No new major or experimental
namespace is introduced. Nothing is stable before Helianthus 1.0.

The standard-library suite checks specification tables, bounded transitions and
synthetic JSON witnesses. It does not execute a Go function or demonstrate
runtime copy/error behavior. The focused unittest is an explicit supplemental
ship command: the fixed Gate D list does not discover it automatically. Full
repository CI, the prescribed Gate D references, publication checks and fresh
independent committed-change review remain later ship requirements. This is
partial work: Refs #965 and #736; the umbrella remains open. No transport or
physical support qualification follows from these local checks.
