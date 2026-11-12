# B525 quality and configuration local API contract

This architecture contract defines a pure software representation for candidate
B525 data. The [public native contract](../protocols/vaillant/ebus-vaillant.md#b525-radio-diagnosis)
is the evidence boundary: its layouts are candidates. The local selector does
not qualify native behavior. All scenarios in the
[synthetic fixture](fixtures/ap26_b525_quality_config.json) are invented family
examples, without device observations. This partial slice refs #967 and #736;
the parent remains open.

## Signature and shapes

Package `vaillant` exposes exactly:

```go
func Ab25Ap25Evaluate(ab25ap25Input json.RawMessage) (json.RawMessage, error)
```

Use the Go standard library only. No initialization side effect, persistent
cache, generic catalog, listing API or runtime caller is defined. This page
specifies the contract independently of any pending implementation. Python is
only a documentation validator, never a runtime implementation.

Input is one JSON object: `context` object, `fields` object, and optional
`arguments` object. Context has numeric primary=181, secondary=37, numeric
operation, explicit string direction and view. Missing, explicit null and zero
context members remain distinct; an unsupported or missing selector gives
raw-only Unknown. Opaque family, variant and other context keys survive verbatim.
Arguments have no required or recognized typed members in these two views;
unknown extra keys of any JSON kind survive unchanged. In particular absent
arguments, `{}`, null-valued members, zero, empty arrays and Boolean false stay
distinct. Explicit null for the arguments object itself is a kind error.

All named fields are byte arrays of integral values 0..255; Boolean values are
not integers. Unknown field names retain byte arrays too. Scalar field lengths
must be exactly one; missing, short or overlong arrays are incomplete rather
than errors. Data accepts any finite array length including zero, with no
specified protocol maximum. Missing data is incomplete. No relay vector or
u16/u32 typed argument is defined in these views. If such types are added, their
bounds must be explicit; this contract introduces none.

Output is one JSON object containing `context` unchanged, `raw` as a deep
independent copy of input fields, `arguments` unchanged if supplied, `state`,
semantic `fields`, `physical="Unknown"` and `qualified=false`. Every semantic
field retains its original `raw` when present, and `state`; an absent field has
no `raw` key. Incomplete fields contain neither invented number nor label.
Unknown input fields remain only in top-level raw. Unsupported selectors
produce `state="Unknown"` and empty semantic `fields`, with no formula applied.
Independent complete siblings survive partial input. Candidate results have
`grade="Hypothesis"`; exact arithmetic additionally has
`calculation="Proven"`, without replacing the candidate grade. An unresolved
candidate branch can coexist with complete siblings; calculation outside an
explicit candidate domain would retain its value and `candidate_domain=false`.
No such domain restriction or unresolved branch is defined for these two views.

## Normative envelope and admission table

| member or condition | kind or policy | preservation |
| --- | --- | --- |
| input | object | context and fields required |
| context | object | unchanged; absent/null/zero distinct |
| fields | object of byte arrays | raw deep copy; unknown names retained |
| arguments | optional object; no typed members in these views | unchanged when supplied; unknown extra keys retained |
| output | object | context, raw, state, fields, physical, qualified; optional arguments |
| physical | string | Unknown |
| qualified | Boolean | false |
| candidate grade | string | Hypothesis |
| arithmetic calculation | string | Proven; never replaces grade |
| incomplete field | object | raw if present; state=incomplete; grade=Hypothesis; no number or label |
| duplicate keys | reject at every nesting depth | error; no successful result |
| byte kind | integer 0..255; Boolean excluded | reject null/string/fraction/out-of-range |
| selector kind | integer primary/secondary/operation; string direction/view | absent/null unsupported; wrong kinds error |
| storage | independent input/output/raw/semantic/call copies | nested mutation never propagates |
| validation precedence | admission before selector dispatch | invalid bytes error even for unsupported selector |

## Selector table

Operations are decimal JSON numbers; 24..27 denote hexadecimal 18..1B.
Every row is an independent identity, even where formulas coincide.

| primary | secondary | operation | direction | view |
| --- | --- | --- | --- | --- |
| 181 | 37 | 3 | positive | quality |
| 181 | 37 | 24 | request | configuration |
| 181 | 37 | 24 | positive | configuration |
| 181 | 37 | 25 | request | configuration |
| 181 | 37 | 25 | positive | configuration |
| 181 | 37 | 26 | request | configuration |
| 181 | 37 | 26 | positive | configuration |
| 181 | 37 | 27 | request | configuration |
| 181 | 37 | 27 | positive | configuration |

## Field formulas and transitions

The following normative tables use `b` for a single byte. Bit indices are zero
based. Quality exposes seven independent Boolean components, not a numeric
quality score. The declared CRC-okay Boolean never verifies a checksum.

| field | length | formula | metadata |
| --- | --- | --- | --- |
| rssi | 1 | b if b < 128 else b - 256 | number; unit=Unknown; grade=Hypothesis; calculation=Proven |
| quality | 1 | bit_i = bool(b & (1 << i)), i=0..6; crc_okay = bool(b & 128) | flags; verified_crc=false; grade=Hypothesis; calculation=Proven |
| configuration | 1 | read_write = bool(b & 1); unmodeled = b & 254 | default_read=0; grade=Hypothesis; calculation=Proven |
| data | 0..unspecified | copy every byte in order | opaque; grade=Hypothesis |

| condition | result state | semantic behavior |
| --- | --- | --- |
| supported; all required fields complete | complete | all independent results retained |
| supported; any required field absent or wrong length | partial | incomplete field retained; complete siblings retained |
| unsupported selector | Unknown | raw-only; no formulas |
| malformed JSON; duplicate key anywhere; wrong kind; fractional or out-of-range byte | error | error and no successful result |

Complete RSSI has `number` and `unit`; quality has `flags` with `bit0`..`bit6`
and `crc_okay`, plus `verified_crc=false`. Configuration has `flags.read_write`,
`unmodeled` and `default_read=0`. Complete data has `value`, an independently
owned byte array. Each complete field has `state="complete"`. Each incomplete
field has `state="incomplete"` and `grade="Hypothesis"`. The enclosing state is
local completeness only. Missing reply offsets remain Unknown.

Reject malformed JSON, duplicate keys at any nesting depth, non-object input,
missing or wrong-kind context/fields, and wrong-kind supplied arguments. Reject
wrong field kinds, fractions, negative bytes, bytes over 255, strings, Boolean
and null byte elements. Reject non-finite JSON numbers. Context selector kinds
are explicit: numeric selector slots accept JSON integers or remain unsupported
when absent/null; other kinds are errors. Direction/view accept strings or
remain unsupported when absent/null; other kinds are errors. Unknown numeric
selector values, including zero, are unsupported, never coerced. Any future
required argument must be present with its exact declared kind and bounds.
Validation errors take precedence over unsupported selector evaluation.

## Preservation and scope

Input mutation, mutation of returned nested context/raw/arguments/semantic data,
and later calls must never share storage. Preserve every distinction through
JSON round trips, including omitted keys versus explicit null, zero, false and
empty arrays. Raw and semantic copies must also be independent of each other.
The fixture records input/result pairs and rejected serialized inputs; bounded
oracles in the supplemental unittest assert these tables and transitions.

Configuration bit zero is a raw read/write choice with candidate default-read
metadata, never permission to write. Explicit empty data represents zero bytes;
it does not prove packet acceptance. Structure, unit, count, correlation,
atomicity, cipher, pairing and physical effect are Unknown. Spectrum, keys and
radio identifiers are outside this view. No radio action, active executor,
registration, scan-default change, peer communication or automatic qualification
is introduced. Physical association, support, freshness, effects, persistence
and delivery remain Unknown. Existing eBUS MCP compatibility and GraphQL parity
are unaffected because no transport or runtime API is registered here.

Nothing is stable before Helianthus 1.0. This adds no major or experimental
namespace and no authorization gate; roadmap wording is 0.11.

The explicit supplemental ship command is
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap26_b525_quality_config.py -v`.
Gate D has a fixed test list and does not automatically include this suite.
Full repository CI, publication checks, fresh independent committed-change
review and applicable transport classification remain required before shipping.
