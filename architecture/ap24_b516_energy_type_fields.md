# B516 directional energy-type result API

This is a local software contract in package `vaillant`, independent of any
pending implementation. Its exact Go standard-library signature is:

```go
func Ab23Ap23Evaluate(ab23ap23Input json.RawMessage) (json.RawMessage, error)
```

The [public B516 native reference](../protocols/vaillant/ebus-vaillant-B516-energy.md#10-other-b516-sub-ids-candidate)
provides candidate energy-type context, not a numeric operation binding for this
view. No native fact is promoted here. The selector is software input, never
native qualification. Candidate interpretation stays **Hypothesis**, even when
arithmetic additionally has `calculation=Proven`. Physical association, support,
freshness, effects, persistence and delivery stay **Unknown**; `qualified=false`.
All scenarios use synthetic families and variants.

## Selection and directional formulas

Only `primary=181`, `secondary=22`, explicit `operation=null`, explicit
`view="energy-type"` and one of these directions select the local interpretation.
Absent operation and numeric zero do not match explicit null. Other context
values select raw-only `Unknown`, with no formula applied.

| operation | direction | view | value length | number | low_six | flag6 | flag7 | unmodeled_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| null | request | energy-type | 1 | value | absent | absent | absent | absent |
| null | read-positive | energy-type | 1 | absent | value & 63 | (value & 64) != 0 | (value & 128) != 0 | absent |
| null | write-positive | energy-type | 1 | absent | value & 63 | absent | absent | value & 192 |

The request's whole byte is an unmapped enum token: `number=value`,
`unmapped=true`, no label. Read flags have no borrowed meaning in requests or
write-positive results. Write-positive retains the high bits without naming
flags or requiring high-zero. No inference connects this byte to meter/clear
selectors or any OP10 statistics flag. Request defaults, full enum labels,
encoded operation and physical coordinates remain Unknown.

| value | request number | read low_six | read flag6 | read flag7 | write low_six | write unmodeled_high |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | false | false | 0 | 0 |
| 1 | 1 | 1 | false | false | 1 | 0 |
| 63 | 63 | 63 | false | false | 63 | 0 |
| 64 | 64 | 0 | true | false | 0 | 64 |
| 128 | 128 | 0 | false | true | 0 | 128 |
| 192 | 192 | 0 | true | true | 0 | 192 |
| 193 | 193 | 1 | true | true | 1 | 192 |
| 255 | 255 | 63 | true | true | 63 | 192 |

## Input and admission

The input is one JSON object with required object members `context` and `fields`,
and optional object member `arguments`. `context` retains all supplied keys,
including opaque `family`, `variant` and nested values, verbatim as JSON values.
Missing, explicit null, zero and Boolean false remain distinct after round trips;
opaque keys do not affect selection or qualification. Unknown selector values
are unsupported, rather than guessed. No numeric selector is coerced from a
Boolean, string or fractional number.

`fields` maps names to byte arrays: every element must be an integral JSON number
in 0..255, never Boolean, null, string or array. Only `value` is interpreted here;
its exact width is one byte. Missing, empty, short or overlong arrays are
incomplete fields, not admission errors; all supplied bytes remain in `raw`.
Unknown fields remain raw-only, including valid independent siblings when
`value` is incomplete. No second semantic sibling is defined by this view.

No typed arguments, required arguments, relay vectors, u16 or u32 quantities are
defined for this view. If supplied, `arguments` preserves unknown extra keys and
arbitrary JSON values, including null, false, zero, arrays and nested objects.
This does not confer a typed argument meaning or invent a required argument.
For any future explicitly typed quantity, u8/u16/u32 require integral numbers in
0..255/65535/4294967295 respectively; no such quantity is admitted as semantic
input here.

Reject malformed JSON, duplicate keys anywhere (including opaque nested
objects), wrong container/byte kinds, fractional bytes and out-of-range bytes:
return an error and no successful result. Validate the entire input before
selection, even when context is unsupported. Error text is not prescribed.
The JSON grammar excludes nonfinite numbers. Unknown context keys and argument
keys remain opaque; they are never mistaken for typed bytes.

## Result and state transitions

Output is one JSON object. `context` is unchanged; `raw` is a deep independent
copy of `fields`; `arguments` is present unchanged only if supplied. `physical`
is always `Unknown`, and `qualified` is always false.

| condition | result state | semantic fields |
| --- | --- | --- |
| supported selector and one byte | complete | value complete, grade Hypothesis |
| supported selector and missing/empty/overlong value | partial | value incomplete, grade Hypothesis |
| unsupported selector | Unknown | empty object; raw retained |
| invalid JSON or admission failure | error | no successful result |

`fields.value` retains its own `raw` when supplied; missing raw is omitted,
never replaced with null or zero. Its `state` is `complete` or `incomplete` and
its `grade` is `Hypothesis`. Request complete results add only `number` and
`unmapped`; read-positive adds `low_six`, `flag6`, `flag7`, `calculation=Proven`;
write-positive adds `low_six`, `unmodeled_high`, `calculation=Proven`.
There are no invented labels, reserved meanings, candidate-domain restrictions
or alternatives for this view. Incomplete/unmapped quantities gain no invented
number or label. Generally an explicitly declared calculation outside a candidate
domain would retain its number with `candidate_domain=false`; none is declared
here. An unresolved candidate branch may coexist with complete independent
siblings, and partial inputs never erase their last-known-good raw evidence.
This pure call has no persistent last-known-good store.

For example, the selected read-positive input `fields={"value":[193]}` produces
`fields={"value":{"raw":[193],"state":"complete","grade":"Hypothesis",
"low_six":1,"flag6":true,"flag7":true,"calculation":"Proven"}}`, alongside
the unchanged context, `raw={"value":[193]}`, `state="complete"`,
`physical="Unknown"`, `qualified=false`, and supplied arguments if any.
Every context/raw/state distinction survives JSON round trips. Input mutation,
returned nested storage mutation, and mutation of one result must not affect
another result or a later call; even output `raw` and field `raw` must not alias.

The API is a pure library function: no initialization side effect, persistent
cache, generic catalog, listing API or runtime caller. No executor, method
registration, scan-default change, peer communication or automatic qualification
is introduced. eBUS MCP compatibility and GraphQL parity impose no new surface
in this slice. No new major or experimental namespace is defined; nothing is
stable before Helianthus 1.0. No authorization gate before 0.9 is introduced;
roadmap wording, when needed, is 0.11.

## Machine-checkable local contract

The following JSON and the page tables are checked against independent constants
and bounded transition oracles in the standard-library unittest. The
[synthetic scenarios](fixtures/ap24_b516_energy_type_fields.json) include full
input/result objects and rejected JSON texts. These are specifications, not a
Python runtime implementation or evidence that a Go implementation passes.

```json
{
  "package": "vaillant",
  "signature": "Ab23Ap23Evaluate(ab23ap23Input json.RawMessage) (json.RawMessage, error)",
  "selector": {
    "primary": 181,
    "secondary": 22,
    "operation": null,
    "view": "energy-type",
    "directions": [
      "request",
      "read-positive",
      "write-positive"
    ]
  },
  "value_width": 1,
  "typed_arguments": {},
  "grades": {
    "candidate": "Hypothesis",
    "calculation": "Proven",
    "physical": "Unknown",
    "qualified": false
  },
  "states": {
    "supported": "complete",
    "incomplete": "partial",
    "unsupported": "Unknown"
  },
  "output_keys": [
    "context",
    "raw",
    "state",
    "fields",
    "physical",
    "qualified"
  ],
  "optional_output_keys": [
    "arguments"
  ],
  "errors": [
    "malformed-json",
    "duplicate-key",
    "wrong-kind",
    "nonintegral-number",
    "out-of-range"
  ],
  "unknowns": [
    "request-defaults",
    "enum-labels",
    "encoded-operation",
    "physical-coordinates",
    "meter-selector",
    "clear-selector",
    "OP10-statistics-flag",
    "support",
    "freshness",
    "effects",
    "persistence",
    "delivery"
  ]
}
```

The explicit supplemental ship command is
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap24_b516_energy_type_fields.py -v`.
Gate D uses a fixed list and does not automatically discover this suite. Full
repository CI, publication checks, fresh independent committed-change review
and applicable transport classification remain later ship requirements.
Refs [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736);
this partial slice does not close the umbrella.
