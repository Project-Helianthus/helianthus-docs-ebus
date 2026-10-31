# B509 diagnostic fields: local API contract

This architecture contract describes a pure library representation, independently
of a runtime implementation. Start with the public native
[B509 contract](../protocols/vaillant/ebus-vaillant-B509.md) and
[service overview](../protocols/vaillant/ebus-vaillant.md): native OP34/OP35
layouts remain Unknown there. The named logical fields below are Hypothesis;
no byte offsets, physical response adaptation or native qualification follow.
The selector is a software input, never proof of device support.

## API and JSON shapes

Package `vaillant` exposes exactly
`Ab17Ap17Evaluate(ab17ap17Input json.RawMessage) (json.RawMessage, error)`
using only the Go standard library. This is a pure function: no initialization
side effect, persistent cache, generic catalog, listing API or runtime caller.
No Go implementation or Python runtime feature is introduced by this page.

Input: `{ "context": {...}, "fields": {...}, "arguments": {...} }`.
Context and fields are required objects; arguments is an optional object.
Context includes primary=181, secondary=9, an operation, direction and explicit
view from the table. Missing, explicit null and zero context values remain
distinct and yield raw-only Unknown when they do not select a supported view.
Family, variant and other context keys are opaque and preserved verbatim.

| Operation (hex / decimal) | Direction | View | Required logical fields | Arguments |
|---|---|---|---|---|
| 34 / 52 | request | diagnostic-get | address: 4 bytes; count: 1 byte | none required |
| 34 / 52 | positive | diagnostic-get | address: 4 bytes; data: opaque array | requested_address: optional u32 |
| 35 / 53 | request | diagnostic-put | address: 4 bytes; data: opaque array | none required |
| 35 / 53 | positive | diagnostic-put | status: 1 byte | none required |

Every fields value is an array of integral bytes 0..255. No relay vector is
introduced. Arguments contain only typed scalars declared for the selected
view plus opaque unknown extra keys, preserved unchanged. The only declared
argument here is requested_address; no argument is required by these four views.
A declared u8/u16/u32 must be an integer in 0..255/65535/4294967295;
Boolean, null, string and array are separate kinds, never coerced. Unknown
argument keys can contain JSON values including false, null, zero and arrays.

Reject malformed JSON, duplicate keys at any depth, non-JSON numeric constants,
wrong kinds, fractions, out-of-range bytes or declared arguments, and any missing
required argument with an error and no successful result. Validation of byte
kinds/ranges precedes unsupported-selector admission. Unknown selector values
apply no formula. Missing, short or overlong fixed-width arrays are incomplete,
not successful zero quantities; opaque data has minimum length zero and no
stated maximum. An absent data key differs from a present empty array.

Output: `{ "context": {...}, "raw": {...}, "arguments": {...},
"state": "complete|partial|Unknown", "fields": {...},
"physical": "Unknown", "qualified": false }`.
Arguments is omitted exactly when absent on input. Context and supplied arguments
are unchanged. Raw is a deep independent copy of fields. Semantic field results
contain raw when present, state and grade, plus only applicable number, label,
flags, reserved, unmodeled, candidate_domain or alternatives. No missing field
gets synthetic raw bytes, a number or a label. Data additionally records length.
The formal table below and scenario file fix the local JSON spelling.

## Arithmetic and transitions

| Quantity | Rule | Local result | Native grade |
|---|---|---|---|
| address | b0 + 256*b1 + 65536*b2 + 16777216*b3 | [120,86,52,18] = 305419896 | Hypothesis; calculation Proven |
| count | b0 | [0] = 0; [255] = 255 | Hypothesis; calculation Proven |
| data | unchanged bytes through end-of-data | unmodeled=true; length=len(data); [] is complete | Hypothesis |
| status | b0; candidate_domain=(0 <= b0 <= 6) | 0,6 in domain; 7,255 outside; no label | Hypothesis; calculation Proven |

Address bytes written as hexadecimal `78 56 34 12` are JSON decimal
`[120,86,52,18]`; their little-endian result is 305419896.
Requested count and actual data length are independent. Neither proves peer
capacity or correlation. The ten-byte diagnostic recommendation is not a maximum:
eleven fabricated bytes remain complete opaque data. OP35 request has no count;
no count is synthesized from OP34 or from data length. A supplied
arguments.requested_address is retained as context only on a positive OP34
result. Positive address and requested address can differ; correlation is Unknown
and no echo validation is invented. Status 0 has no known success meaning;
all individual status meanings remain Unknown. Out-of-domain status still retains
its calculated number and candidate_domain=false, with no invented label.

An incomplete independent field sets overall state=partial; complete siblings
survive with their raw values and calculations. Otherwise a supported view is
complete as a local representation only. An unresolved candidate branch can
coexist with complete siblings. Unsupported primary, secondary, operation,
direction or view yields state=Unknown, fields={}, preserving context, raw and
arguments without formulas. There is no persistent state; callers may retain
last-known-good siblings, but this function cannot manufacture freshness or
replace missing values with earlier results.

Candidate family/behavior grades stay Hypothesis even when calculation=Proven.
Physical association, acceptance, support, freshness, effects, persistence and
delivery remain Unknown, qualified=false. Every distinction survives JSON round
trips. Mutating input storage or returned nested storage cannot affect another
result or later call. Each result owns independent context, raw, arguments and
semantic raw storage. This is an API requirement, not runtime verification here.

OP13 Boolean mapping, OP51 identity details, memory access, request construction,
write authority and native effects are outside this view. No active executor,
registration, scan change, peer communication or automatic qualification follows.
eBUS MCP compatibility and GraphQL parity are unchanged: neither surface gains
a caller or schema in this documentation slice. No new namespace is introduced;
nothing is stable before Helianthus 1.0.

## Formal table

The table is a machine-readable local contract, checked against independent
constants and bounded scenario transitions by the supplemental unittest.

```json
{
  "signature": "Ab17Ap17Evaluate(ab17ap17Input json.RawMessage) (json.RawMessage, error)",
  "package": "vaillant",
  "primary": 181,
  "secondary": 9,
  "views": [
    [
      52,
      "request",
      "diagnostic-get",
      {
        "address": 4,
        "count": 1
      },
      {}
    ],
    [
      52,
      "positive",
      "diagnostic-get",
      {
        "address": 4,
        "data": "opaque"
      },
      {
        "requested_address": "optional u32"
      }
    ],
    [
      53,
      "request",
      "diagnostic-put",
      {
        "address": 4,
        "data": "opaque"
      },
      {}
    ],
    [
      53,
      "positive",
      "diagnostic-put",
      {
        "status": 1
      },
      {}
    ]
  ],
  "address_weights": [
    1,
    256,
    65536,
    16777216
  ],
  "status_domain": [
    0,
    6
  ],
  "opaque_minimum": 0,
  "opaque_maximum": null,
  "recommendation": 10,
  "physical": "Unknown",
  "qualified": false,
  "grade": "Hypothesis",
  "calculation": "Proven",
  "unsupported_state": "Unknown",
  "incomplete_state": "partial",
  "complete_state": "complete",
  "correlation": "Unknown",
  "status_labels": {},
  "count_data_relation": "independent",
  "input_keys": [
    "context",
    "fields",
    "arguments"
  ],
  "result_keys": [
    "context",
    "raw",
    "arguments",
    "state",
    "fields",
    "physical",
    "qualified"
  ],
  "argument_kinds": {
    "requested_address": "u32"
  },
  "errors": [
    "malformed JSON",
    "duplicate key anywhere",
    "wrong kind",
    "fraction",
    "out of range",
    "missing required argument"
  ],
  "copy": "deep independent",
  "context": "unchanged",
  "arguments": "unchanged if supplied"
}
```

## Synthetic evidence and verification boundary

[Owned scenarios](fixtures/ap18_b509_diagnostic_fields.json) contain synthetic
families only. [Supplemental tests](../tests/test_ap18_b509_diagnostic_fields.py)
check the page, scenario shapes, arithmetic, partial transitions and negative
admission vectors with independent constants. Their bounded oracles are test
logic, not a production evaluator. They do not invoke a pending Go API or prove
its parser, copy isolation or runtime behavior. Full repository CI and fresh
independent committed-change review remain required; the fixed Gate D list does
not discover this supplemental suite automatically. Run it explicitly at ship.
