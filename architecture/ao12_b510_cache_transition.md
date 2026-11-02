# B510 capability-cache query transition API companion

Refs #934; partial child of #736. This Release 0.7 software API contract is
independently authorable; it has no AO11 dependency and needs no code merge to
validate its finite documentation table. Nothing is stable before Helianthus 1.0.

## Evidence and scope

Read the [public native B510 contract](../protocols/vaillant/ebus-vaillant-B510.md)
first. Its candidate feedback and bit interpretation remain **Hypothesis**. It
establishes neither native qualification nor physical capability from feedback.
The local count below is an explicit software argument, **not packet length**.
This companion specifies the supplied query-transition hypothesis; it does not
add wire evidence, assert an operation number, or qualify a device family.
In particular, this view has no operation-zero association, even though the
native page separately discusses a candidate operation-zero query.

Only a pure library contract is defined here: no global cache, generic catalog,
metadata listing, Entries/Lookup API, registration, scheduler, polling, pending
API import or runtime call site. Initialization and reset may independently
overwrite a cache, but their values and persistence are Unknown. Native timing,
physical capability and effects remain Unknown. A candidate label grants no
permission. Existing eBUS MCP compatibility and GraphQL parity are unaffected;
there is no endpoint or application-schema change.

## Function and JSON boundary

```go
package vaillant

func Ab11Ao11Interpret(ab11ao11Input json.RawMessage) (json.RawMessage, error)
```

Use the standard library. All new Go declarations, fields, locals, helpers,
fixture IDs and tests use the `ab11ao11` / exported `Ab11Ao11` prefix; Go tests
start `TestAb11Ao11`. Existing library symbols and literal JSON labels retain
their names. This docs repository supplies no production Go implementation.

The input is one JSON object with `context`, `fields`, and optional `arguments`.
Context is an object with the selectors below; opaque `family`, `variant` and
every other supplied context key survive unchanged, including nested values.
Fields is an object of named byte arrays: each element is a JSON integer in
0..255 (Boolean, null, string and fractional values are not bytes). Unknown
field names and all their bytes survive. Arguments, if present, is an object
with only Boolean `parsed` and nonnegative integer `count`; neither defaults.
Count is not narrowed to eight bits. Empty arrays, missing keys and explicit
zero remain distinct after JSON round trips.

| Selector | Required value | Other or absent value |
|---|---|---|
| primary | 181 | raw-only Unknown |
| secondary | 16 | raw-only Unknown |
| operation | absent | any supplied operation: raw-only Unknown |
| direction | local | raw-only Unknown |
| view | capability-query | raw-only Unknown |

A view selects software interpretation only. Names, family labels and byte
lengths never select a view or establish family applicability. Wrong JSON kinds,
malformed/trailing JSON, duplicate keys at any depth and invalid byte elements
return an error with no successful result. For well-typed JSON, missing required
inputs, invalid widths, negative count, unsupported argument names or an invalid
bit carrier return structured raw-only Unknown and never an update. Validation
of JSON kinds and bytes precedes selection, so unselected input cannot hide an
invalid byte or duplicate key. Wrong selector scalar kinds are errors; unknown
selector values of the correct kind are raw-only Unknown.

| Field | Width | Candidate domain | Preservation |
|---|---:|---|---|
| prior | 1 byte | 0..255 | previous cell, including zero |
| feedback | 1 byte | 0..255 | only 1 permits replacement |
| bit_six | 1 byte | 0 or 64 | already supplied raw bit 6, no extraction implied |

## Output and transitions

Output has `context`, `raw`, `state`, `fields`, `physical: "Unknown"` and
`qualified: false`; `arguments` exists exactly when supplied. Context, raw and
arguments are independent deep copies of their respective input objects.
`raw` preserves every supplied field, including unmodelled tails. Each semantic
field's `raw` is separately copied; mutation of any returned nested object or
input cannot change another result field, another result, or a later call.
The finite records below show the expected semantic projection; add the exact
input context, fields as raw, and arguments when present to obtain the complete
expected output. Error records have no output at all.

| Result field | raw source | state | Optional value |
|---|---|---|---|
| cache_cell | prior array | Hypothesis | number: updated or retained byte |
| freshness | feedback array | Hypothesis for fresh; otherwise Unknown | label: fresh or Unknown |
| rule | bit_six array | Hypothesis for replace/retain; otherwise Unknown | label: replace, retain or Unknown |

For selected, complete, valid input, parsed=false or feedback other than 1
retains prior, with freshness Unknown and rule retain. This failure rule takes
precedence even at count zero. Otherwise count zero retains prior with rule
Unknown, freshness Unknown and overall state Unknown. Otherwise count 1 or 2
replaces prior with 0; count greater than 2 replaces it with bit_six (0 or 64).
These replacements have freshness fresh and rule replace. Other complete
branches have overall state Hypothesis. The retained value and query freshness
are separate properties; retained data is never declared fresh.

Every cache-cell interpretation remains Hypothesis, including an exactly
represented numeric byte. A separately exact numeric calculation may carry
`calculation: "Proven"`, but cannot promote its semantic grade; this transition
needs no calculation tag. No flags, reserved, candidate_domain or additional
numeric fields are defined by this view. An outside-domain carrier can have a
number plus candidate_domain=false only where a contract explicitly supplies
that number; this view instead rejects the invalid carrier as raw-only Unknown.

Raw-only Unknown has `fields: {}` and contains no interpreted number. Generic
partial handling preserves every complete independent semantic field and uses
state partial when another field is incomplete. Incomplete, unmapped,
unit-conflict or unknown-order fields never have numbers; unknown siblings must
not erase valid independent fields. Here all three semantic fields share the
required transition inputs, so missing required input is explicitly raw-only
Unknown, not partial; an unknown extra raw field alone causes no partial state.
An explicit Unknown branch stays Unknown. State, error and presence distinctions
must survive JSON round trips. No successful call establishes native support.

## Finite machine-readable contract

The JSON contract and JSON-lines case table are normative software examples,
using only synthetic family/variant values and bytes. The companion fixture
contains the same parsed contract and cases. The standard-library unittest
checks both against fixed expected records and independent numeric constants;
it does not implement or execute the production Go interpreter. Runtime error,
aliasing and partial-state conformance remain implementation acceptance work.

<!-- ab11ao11-contract -->
```json
{
  "api": "Ab11Ao11Interpret(ab11ao11Input json.RawMessage) (json.RawMessage, error)",
  "package": "vaillant",
  "implementation": "standard library; pure; no global cache or runtime call site",
  "selection": {
    "primary": 181,
    "secondary": 16,
    "operation": "absent",
    "direction": "local",
    "view": "capability-query"
  },
  "input": {
    "context": "object; preserve every key and opaque family/variant value",
    "fields": "object of integer byte arrays (0..255)",
    "arguments": "object; parsed Boolean; count nonnegative integer; no other keys"
  },
  "required_fields": {
    "prior": {
      "width": 1,
      "domain": "0..255"
    },
    "feedback": {
      "width": 1,
      "domain": "0..255"
    },
    "bit_six": {
      "width": 1,
      "domain": [
        0,
        64
      ]
    }
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
    "states": [
      "Hypothesis",
      "partial",
      "Unknown"
    ],
    "physical": "Unknown",
    "qualified": false
  },
  "result_fields": {
    "cache_cell": {
      "raw": "prior",
      "state": "Hypothesis",
      "number": "updated or retained byte"
    },
    "freshness": {
      "raw": "feedback",
      "state": "Hypothesis or Unknown",
      "label": "fresh or Unknown"
    },
    "rule": {
      "raw": "bit_six",
      "state": "Hypothesis or Unknown",
      "label": "replace or retain or Unknown"
    }
  },
  "errors": [
    "malformed JSON",
    "duplicate object keys at any depth",
    "invalid byte elements",
    "wrong JSON kinds"
  ],
  "raw_only": [
    "unselected context",
    "missing required input",
    "invalid width",
    "bit_six outside domain",
    "negative count",
    "unknown argument"
  ],
  "grades": {
    "semantic": "Hypothesis",
    "calculation": "Proven only for independently exact calculation; absent here",
    "physical": "Unknown",
    "native_timing": "Unknown",
    "qualified": false
  },
  "copy": "context, raw, arguments and result-field raw are independent deep copies across inputs, outputs and calls",
  "partial": "preserve complete independent fields; incomplete, unmapped, unit-conflict or unknown-order fields have no number; explicit Unknown stays Unknown",
  "presence": "missing differs from empty and explicit zero; preserve through JSON round trips",
  "selection_policy": "never infer from name, payload length or family; no operation zero association"
}
```
<!-- /ab11ao11-contract -->

<!-- ab11ao11-cases -->
```jsonl
{"id":"ab11ao11_count_0","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":0}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[1],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Unknown","label":"Unknown"}}}}
{"id":"ab11ao11_count_1","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":1}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":0},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_count_2","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":2}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":0},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_count_3","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_count_255","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":255}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_count_256","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":256}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_bit_zero","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[0]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":0},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[0],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_prior_zero","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[0],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[0],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_prior_other","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[42],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[42],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_parse_failure","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":false,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[1],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_feedback_0","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[0],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[0],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_feedback_2","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[2],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[2],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_feedback_255","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[255],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[255],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_failure_count_zero","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":false,"count":0}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":165},"freshness":{"raw":[1],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_tail","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64],"unmodelled":[0,255,64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_opaque_family","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":{"opaque":[1,0]},"variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_opaque_variant","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":["opaque",null]},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_opaque_extra","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant","extra":{"retained":true}},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_selector_primary_180","input":{"context":{"primary":180,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_selector_secondary_17","input":{"context":{"primary":181,"secondary":17,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_selector_operation_0","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant","operation":0},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_selector_operation_1","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant","operation":1},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_selector_direction_reply","input":{"context":{"primary":181,"secondary":16,"direction":"reply","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_selector_view_other","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"other","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_primary","input":{"context":{"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_secondary","input":{"context":{"primary":181,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_direction","input":{"context":{"primary":181,"secondary":16,"view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_view","input":{"context":{"primary":181,"secondary":16,"direction":"local","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_prior_empty","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_prior_wide","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[0,64],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_prior_missing","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_prior_negative","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[-1],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_overflow","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[256],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_fraction","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[1.5],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_bool","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[true],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":["1"],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[null],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_prior_wrong_kind","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":1,"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_empty","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_feedback_wide","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[0,64],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_feedback_missing","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_feedback_negative","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[-1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_overflow","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[256],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_fraction","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1.5],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_bool","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[true],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":["1"],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[null],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_feedback_wrong_kind","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":1,"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_empty","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_bit_six_wide","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[0,64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_bit_six_missing","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_bit_six_negative","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[-1]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_overflow","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[256]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_fraction","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[1.5]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_bool","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[true]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":["1"]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[null]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_six_wrong_kind","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":1},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_bit_invalid","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[1]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_parsed","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_count","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_missing_context","input":{"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_context_null","input":{"context":null,"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_context_array","input":{"context":[],"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_context_string","input":{"context":"x","fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_missing_fields","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_fields_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":null,"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_fields_array","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":[],"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_fields_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":"x","arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_missing_arguments","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_arguments_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":null},"error":true,"expected":null}
{"id":"ab11ao11_arguments_array","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":[]},"error":true,"expected":null}
{"id":"ab11ao11_arguments_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":"x"},"error":true,"expected":null}
{"id":"ab11ao11_negative_count","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":-1}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_extra_argument","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3,"extra":1}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_parsed_integer","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":1,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_parsed_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":null,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_count_bool","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":true}},"error":true,"expected":null}
{"id":"ab11ao11_count_fraction","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":1.5}},"error":true,"expected":null}
{"id":"ab11ao11_count_string","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":"3"}},"error":true,"expected":null}
{"id":"ab11ao11_count_null","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":null}},"error":true,"expected":null}
{"id":"ab11ao11_malformed","input_json":"{","error":true,"expected":null}
{"id":"ab11ao11_duplicate_root","input_json":"{\"context\":{},\"context\":{}}","error":true,"expected":null}
{"id":"ab11ao11_duplicate_context","input_json":"{\"context\":{\"view\":\"capability-query\",\"view\":\"other\"}}","error":true,"expected":null}
{"id":"ab11ao11_duplicate_fields","input_json":"{\"fields\":{\"prior\":[0],\"prior\":[165]}}","error":true,"expected":null}
{"id":"ab11ao11_duplicate_arguments","input_json":"{\"arguments\":{\"count\":1,\"count\":3}}","error":true,"expected":null}
{"id":"ab11ao11_root_array","input_json":"[]","error":true,"expected":null}
{"id":"ab11ao11_kind_primary","input":{"context":{"primary":"181","secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_kind_secondary","input":{"context":{"primary":181,"secondary":"16","direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_kind_operation","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant","operation":null},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_kind_direction","input":{"context":{"primary":181,"secondary":16,"direction":1,"view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_kind_view","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":null,"family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":true,"expected":null}
{"id":"ab11ao11_absent_family","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_absent_variant","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[165],"state":"Hypothesis","number":64},"freshness":{"raw":[1],"state":"Hypothesis","label":"fresh"},"rule":{"raw":[64],"state":"Hypothesis","label":"replace"}}}}
{"id":"ab11ao11_zero_primary","input":{"context":{"primary":0,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_zero_secondary","input":{"context":{"primary":181,"secondary":0,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":true,"count":3}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_arguments_empty","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[165],"feedback":[1],"bit_six":[64]},"arguments":{}},"error":false,"expected":{"state":"Unknown","physical":"Unknown","qualified":false,"fields":{}}}
{"id":"ab11ao11_retained_other_prior","input":{"context":{"primary":181,"secondary":16,"direction":"local","view":"capability-query","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"prior":[42],"feedback":[1],"bit_six":[64]},"arguments":{"parsed":false,"count":3}},"error":false,"expected":{"state":"Hypothesis","physical":"Unknown","qualified":false,"fields":{"cache_cell":{"raw":[42],"state":"Hypothesis","number":42},"freshness":{"raw":[1],"state":"Unknown","label":"Unknown"},"rule":{"raw":[64],"state":"Hypothesis","label":"retain"}}}}
{"id":"ab11ao11_trailing","input_json":"{} {}","error":true,"expected":null}
{"id":"ab11ao11_duplicate_opaque","input_json":"{\"context\":{\"family\":{\"x\":1,\"x\":2}}}","error":true,"expected":null}
```
<!-- /ab11ao11-cases -->

## Validation boundary

The focused suite is registered in `scripts/ci_local.sh` with
`python3 -m unittest discover -s tests -p 'test_ao12_b510_cache_transition.py' -v`.
Later shipment requires independent committed-change review,
full repository CI, Gate D with its provisioned references, publication checks
and applicable transport classification. Documentation checks cannot certify
Go error handling, deep-copy isolation, eBUS MCP or GraphQL runtime behavior.
