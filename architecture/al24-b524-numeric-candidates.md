# AL24: B524 numeric candidates outside edit admission

The public [native B524 contract](../protocols/vaillant/ebus-vaillant-b524.md)
comes first for wire facts: OP02 and OP06 are distinct namespaces, and the
request instance remains part of selector identity. The public
[type declarations](../types/ebusd-csv.md) define UCH/1 as unsigned byte,
UIN/2 as little-endian unsigned 16-bit, and EXP/4 as little-endian binary32.
Widths here describe isolated fields, not complete messages or qualified codecs
for an installed device.

This page specifies a finite library representation contract, not an implemented
runtime API. **Hypothesis:** all twenty range/step mappings below, including their
selector-to-codec association. **Proven:** the declared representation shape and
synthetic arithmetic only. **Unknown:** physical applicability, units and native
qualification. Grades do not establish presence, freshness or execution.
Nothing is stable before Helianthus 1.0.

## Immutable exact caller context

```text
Ab56Entries() -> []Ab56Tuple
Ab56NewView(context Ab56Context) -> (*Ab56View, error)
(*Ab56View).Ab56Lookup(key Ab56Key) -> (Ab56Entry, bool)
```

These are the companion contract signatures, not newly routed methods.
`Ab56Entries` returns the twenty identity-free tuples, each carrying opcode,
group, instance, register, codec, width, minimum, maximum, step and candidate
grade. Store those tuples once; do not manufacture native identity rows.

`Ab56Context` has the seven mandatory fields below. `Ab56Key` has those same
fields plus the four selector fields. The separately prefixed software,
hardware, API version and API revision fields extend the catalog identity;
version and revision are independent, never an interchangeable pair.

| Field | Domain |
| --- | --- |
| ab56_family | nonempty opaque caller string |
| ab56_software | nonempty opaque caller string |
| ab56_hardware | nonempty opaque caller string |
| ab56_api_version | nonempty opaque caller string |
| ab56_api_revision | nonempty opaque caller string |
| ab56_variant | nonempty opaque caller string |
| ab56_candidate_set | nonempty opaque caller string |
| ab56_opcode | explicit integer byte |
| ab56_group | explicit integer byte |
| ab56_instance | explicit integer byte |
| ab56_register | explicit unsigned 16-bit integer |

All seven strings are uninterpreted metadata, with no native default or
qualification effect. Variant and candidate-set are separate tokens. Comparison
is exact, without trimming, case folding, wildcard syntax or fallback. In
particular a token spelling `*` is only a literal token, never a wildcard.
Synthetic family labels in the examples are not native profiles or firmware
allowlists. Any complete caller context may index the same finite candidates;
this is metadata indexing only.

`Ab56NewView` returns no view and an error if any identity string is missing,
null, empty or not a string. On success it captures an immutable owned copy of
the exact context; it never mutates global data. A view does not embed a native
identity or expand the catalog into per-caller rows.

`Ab56Lookup` succeeds only when all seven key strings exactly match that view
and all four selector fields exactly match a finite tuple. Missing, null,
ill-typed or out-of-range key fields, a context mismatch, or an unmatched
selector yield an absent entry and `false`; there is no partial match or fallback.
Booleans are not selector integers. A successful entry contains an owned copy
of the full key and tuple, including explicit codec and width. Mutating a caller
context, a returned list, a tuple or an entry cannot affect the view, global
tuples, another result or another view. Return fresh independent memory on every
call, including nested fields.

## Finite candidate tuples

Every row is OP02 and Hypothesis; no row is admitted. The already allocated
exact system bound OP02/GG00/II00/RR0001 is excluded from this residual set.
No semantic labels, other codebooks or full-family coverage are added here.

| OP | GG | II | RR | Codec | Width | Min | Max | Step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02 | 00 | 00 | 0003 | UIN | 2 | 0 | 12 | 1 |
| 02 | 00 | 00 | 0080 | EXP | 4 | -10.0 | 10.0 | 1.0 |
| 02 | 01 | 00 | 0001 | UIN | 2 | 0 | 1 | 1 |
| 02 | 01 | 00 | 0003 | UIN | 2 | 0 | 2 | 1 |
| 02 | 02 | 01 | 0002 | UIN | 2 | 0 | 4 | 1 |
| 02 | 02 | 01 | 0004 | EXP | 4 | 15.0 | 80.0 | 1.0 |
| 02 | 02 | 01 | 0005 | UCH | 1 | 0 | 1 | 1 |
| 02 | 02 | 01 | 0006 | UCH | 1 | 0 | 1 | 1 |
| 02 | 02 | 02 | 0002 | UIN | 2 | 0 | 4 | 1 |
| 02 | 02 | 02 | 0004 | EXP | 4 | 15.0 | 80.0 | 1.0 |
| 02 | 02 | 02 | 0005 | UCH | 1 | 0 | 1 | 1 |
| 02 | 02 | 02 | 0006 | UCH | 1 | 0 | 1 | 1 |
| 02 | 02 | 09 | 0002 | UIN | 2 | 0 | 4 | 1 |
| 02 | 02 | 09 | 0004 | EXP | 4 | 15.0 | 80.0 | 1.0 |
| 02 | 02 | 09 | 0005 | UCH | 1 | 0 | 1 | 1 |
| 02 | 02 | 09 | 0006 | UCH | 1 | 0 | 1 | 1 |
| 02 | 03 | 00 | 0001 | UIN | 2 | 0 | 2 | 1 |
| 02 | 03 | 00 | 0002 | EXP | 4 | 15.0 | 30.0 | 0.5 |
| 02 | 03 | 00 | 0005 | EXP | 4 | 5.0 | 30.0 | 1.0 |
| 02 | 03 | 00 | 0006 | UIN | 2 | 0 | 2 | 1 |

There are twenty distinct selectors: two in GG00, two in GG01, twelve in GG02
and four in GG03. GG02/II01, II02 and II09 remain separate, with four rows
each. Listing an instance claims no new slot presence or active configuration.
Unlisted instances, inactive or unknown slots, OP06 and date/time candidates
never inherit numeric admission.

## Admission and evidence boundary

A metadata hit is not a runtime `LookupB524Bound` result. Each entry has
candidate grade `Hypothesis`, physical qualification `Unknown`, presence
`Unknown`, freshness `Unknown`, writable `Unknown`, execution `Unknown`,
`admitted=false` and `runtime_bound=null`. Candidate data alone cannot set
presence, fresh state, a writable flag or admitted=true, or return an admitted
edit bound. Neither a hit nor arithmetic membership supplies edit permission.

This metadata API accepts no telegram bytes or cached state. Callers retain
their raw bytes and independently useful decoded fields on partial failure,
alongside their separate last-known-good state. A lookup miss cannot erase that
evidence or make retained state fresh. No cache updater or decoder is specified.

The [small synthetic example set](fixtures/al24_b524_numeric_candidates.json)
is not a second full dictionary or native profile. For GG03/II00/RR0002,
inclusive range 15..30 with step 0.5 includes 15, 15.5 and 30; it excludes
15.25 arithmetically. These four arithmetic results are Proven under the
declared decimal model; the candidate remains Hypothesis and unadmitted.

The following normative assertions are checked independently of the examples.

<!-- al24-policy:begin -->
```json
{
  "tuple_count": 20,
  "context_match": "exact_all_fields",
  "identity_defaults": false,
  "wildcard_fallback": false,
  "missing_identity": "constructor_error_or_lookup_miss",
  "memory": "independent_deep_copies",
  "candidate_grade": "Hypothesis",
  "arithmetic_grade": "Proven",
  "physical_qualification": "Unknown",
  "presence": "Unknown",
  "freshness": "Unknown",
  "writable": "Unknown",
  "execution": "Unknown",
  "admitted": false,
  "runtime_bound": null,
  "op06_inheritance": false,
  "date_time_admission": false,
  "inactive_unknown_slot_admission": false,
  "raw_and_last_known_good": "caller_retains_on_failure"
}
```
<!-- al24-policy:end -->

## Companion and verification boundary

The catalog prerequisite must merge before this page. This page adds no
cross-repository runtime import. Prerequisite merge status is Unknown here.
The tests check this declared page contract and synthetic examples without
importing another repository. Their local reference model is not the companion
implementation: no companion code result, native effect or full parity is
claimed before its own checks.

Existing eBUS MCP compatibility and GraphQL parity are preserved by this
documentation-only slice. Navigation and runtime integration are carried
elsewhere. No transmit route, polling default, automatic native qualification,
write admission or authorization gate is added. Independent committed-change
review, full CI and publication checks remain merge requirements; no transport
or hardware smoke result is claimed. Refs #1035 and partial parent #736; the
parent stays open.
