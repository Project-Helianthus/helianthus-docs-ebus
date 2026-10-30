# B531 capability state: local API contract

This is a software contract for the heat-pump energy-manager family, not a
native capability declaration. The [public B531 contract](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md)
is the native evidence boundary: its layouts remain candidate, unconfirmed on
the wire. Physical token meaning, family association, peer effect, support,
freshness, persistence and delivery remain **Unknown**. The synthetic selector
never qualifies a device. This partial slice references #736 and leaves it open.

## API and JSON shape

Package `vaillant` exposes exactly:

```go
func Ab01Ap01Evaluate(ab01ap01Input json.RawMessage) (json.RawMessage, error)
```

Only the Go standard library is required. This specifies a pure library
function, without initialization effects, persistent cache, generic catalog,
listing API or runtime caller. No Go implementation is supplied by this page.
New Go declarations, parameters, locals, struct fields and helpers use the
`ab01ap01` or exported `Ab01Ap01` prefix; Go test functions use `TestAb01Ap01`.
JSON labels and standard-library names keep their spelling.

The following machine-readable table fixes the local contract. Numeric JSON
operation 1 represents OP01; strings such as "01" are not coerced.

<!-- ab01ap01-contract -->
```json
{
  "signature": "Ab01Ap01Evaluate(ab01ap01Input json.RawMessage) (json.RawMessage, error)",
  "package": "vaillant",
  "selectors": {"primary": 181, "secondary": 49, "operation": 1, "direction": "local"},
  "views": {"capability": {"registered": "u32", "prior": "u32", "result": "u32"}, "select": {"rows": {"length": 9, "element": {"a": "u32", "b": "u32", "c": "u32"}}}},
  "limits": {"u8": 255, "u16": 65535, "u32": 4294967295},
  "output_keys": ["context", "raw", "state", "fields", "physical", "qualified"],
  "optional_output_keys": ["arguments"],
  "field_groups": ["raw_fields", "derived"],
  "physical": "Unknown",
  "qualified": false,
  "grade": "Hypothesis",
  "calculation": "Proven",
  "unsupported_state": "Unknown",
  "incomplete_state": "partial",
  "ordinary_state": "complete",
  "marker": 65535,
  "no_match": 9
}
```

Input is one JSON object: `context` and `fields` are required objects;
`arguments` is an optional object, but its view-specific required members must
be present for a supported view. Context contains the selectors above and an
explicit `view` of `capability` or `select`. Opaque `family`, `variant` and other
context keys are preserved verbatim, including nested objects. Missing, null,
zero and false context values remain distinct. Missing or unsupported selector
values produce raw-only Unknown, with no formulas. Present numeric selectors must be null or u8; direction and view must be
null or strings. Other kinds are errors. Null cannot select a formula. `family` and `variant` never select a formula.

Each supplied `fields` member is a byte array of integral values 0..255.
No named byte quantity, width, relay vector or byte-to-number formula is
specified for these two views: all such members remain raw-only Unknown,
including empty arrays. In particular, an arbitrary byte array cannot be
reinterpreted as `registered`, `prior`, `result` or a selector row. Argument
members for the selected view have exactly the types in the table; unknown
extra argument keys are retained without semantic interpretation. A row is an
object with required `a`, `b`, `c`; extra opaque row keys are retained.

Reject malformed JSON, duplicate keys at every nesting depth, non-object input,
wrong object/array/scalar kinds, missing required arguments, fractions, Boolean
numbers, negative numbers and out-of-range byte or typed argument values. Do
not coerce strings, Boolean, null or arrays to numbers. Reject non-JSON numeric
constants. On error return no successful JSON result. Validate the JSON and
supplied byte arrays even for an unsupported selector; do not require a
supported view's arguments when its selector is unsupported.

Output is an object with exactly the required keys in `output_keys`, plus
`arguments` iff supplied. `context` and optional `arguments` are unchanged as
JSON values; `raw` is a deep independent copy of `fields`. `fields.raw_fields`
contains one `{raw: <byte array>, state: "Unknown"}` per supplied byte field.
`fields.derived` contains only the results specified below, or is empty for an
unsupported selector. Every derived record has `raw`, `state`, `grade` and,
where exact, `calculation`, plus its applicable `number` or `flags`.
The marker uses `raw: []`; update and predicate records use the supplied
`{registered, prior, result}` object as raw; the selection record uses the
supplied rows as raw. These are software source values, not captured bytes.

Missing, unmapped and incomplete quantities get no invented number or label.
If a named quantity with a declared width is incomplete (absent, short or
overlong), retain its supplied raw value, mark its record incomplete, and
return aggregate `partial`, keeping complete independent siblings. This is the
generic partial policy; these views declare no fixed-width byte quantities,
so arbitrary raw lengths do not themselves trigger partial. No last-known-good
prior is discarded because another independent quantity is unresolved. There
is no implicit cached prior beyond the input. An unresolved candidate branch
can coexist with complete sibling results and aggregate `complete`.
Where a calculation has an explicitly declared candidate domain, retain an
out-of-domain calculation with `candidate_domain: false`; neither view declares
a restricted candidate domain beyond its typed input ranges. No reserved bits,
unmodeled interpretation, labels or alternatives are invented here.

Returned/input nested storage and results of separate calls are independent.
Mutation of any one must not affect another. All context, raw and state
distinctions survive JSON round trips; whitespace and object key order are
not part of the contract.

## Capability transitions

Allowed selector: primary 181, secondary 49, operation 1, direction `local`,
view `capability`. All derived records have grade **Hypothesis** and exact
calculation **Proven**. Arithmetic correctness never replaces the family grade.
`updated`, `cached_bit0` and `whole_nonzero` records have state `complete`,
including when their source outcome is Unknown. `marker` is independent and
always has state `complete`, number 65535 (`FFFF`).

| registered condition | result condition | prior condition | updated | outcome |
|---|---|---|---|---|
| zero | any | any | prior | skipped |
| nonzero | 0 | any | 0 | cleared |
| nonzero | 1 | zero | 1 | admitted |
| nonzero | 1 | nonzero | prior | retained |
| nonzero | other | any | prior | Unknown |

The `updated` record contains `number` and `outcome`. `cached_bit0` contains
`flags: {"cached_bit0": (updated & 1) != 0}`. `whole_nonzero` contains
`flags: {"whole_nonzero": updated != 0}`. Aggregate state is `complete`,
meaning local representation only. Whole `registered != 0` admits the update;
its bit zero does not control admission. Skipping is local API policy, not a
physical response. Unknown result values preserve the prior verbatim.

## Ordered selection

Allowed selector: primary 181, secondary 49, operation 1, direction `local`,
view `select`. Require exactly nine ordered rows of three independent u32
members. The derived `index` record has state `complete`, grade **Hypothesis**,
calculation **Proven**, and number given by the following table.

| row predicate | choice | no match |
|---|---|---|
| a != 0 and b != 0 and c != 0 | first matching local index, 0 through 8 | 9 |

The input order is local, not topology. A row (2,2,2) matches despite all bit
zero predicates being false. Independently zeroing any member makes it miss.
No family association, peer behavior or physical token meaning follows.

## Synthetic conformance

[Scenarios](fixtures/ap02_b531_capability_state.json) include complete result
examples, strict input failures, opaque raw siblings and unsupported selectors.
The [standard-library suite](../tests/test_ap02_b531_capability_state.py) checks
these tables with independent constants and bounded transition oracles. These
are document checks, not execution of the specified Go API. No executor, method
registration, scan-default change or peer communication is introduced. Existing
eBUS MCP compatibility and GraphQL parity remain requirements for a later
implementation; this page defines no new transport surface.

Nothing is stable before Helianthus 1.0. No new major or experimental namespace
or pre-0.9 authorization gate follows. Any roadmap reference uses 0.11.
