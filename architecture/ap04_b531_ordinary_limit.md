# B531 ordinary-slot sum and requested-state API

This architecture page specifies a local software contract for the Vaillant
family. The selector is a software input, never native qualification. These
synthetic scenarios establish no native B531 wire fact. Native semantics beyond
this finite contract are **Unknown**; consult the public
[eBUS native documentation](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md) before adding native claims.

## Function and selector

```go
func Ab03Ap03Evaluate(ab03ap03Input json.RawMessage) (json.RawMessage, error)
```

Package `vaillant`, Go standard library only. This is a pure library function:
no initialization side effect, persistent cache, generic catalog, listing API,
or runtime caller. No pending Go API is imported by this documentation slice.

The following table is the normative finite local contract. Each Value is JSON.

| Key | Value |
| --- | --- |
| signature | `"Ab03Ap03Evaluate(ab03ap03Input json.RawMessage) (json.RawMessage, error)"` |
| package | `"vaillant"` |
| primary | `181` |
| secondary | `49` |
| operation | `3` |
| direction | `"local"` |
| view | `"ordinary-limit"` |
| rows | `9` |
| slot_order | `[0,1,2,3,4,5,6,7,8]` |
| special_slot | `1` |
| admission | `"registered && capable && !failure"` |
| sum_slots | `"admitted except slot 1"` |
| sum_width | `"u64"` |
| scale | `1` |
| effective | `"token_sum < maximum_sum && limited != 0"` |
| requested_state | `"gate == 0 ? 0 : (effective known ? 1 + effective : Unknown)"` |
| candidate_grade | `"Hypothesis"` |
| calculation_grade | `"Proven"` |
| physical | `"Unknown"` |
| qualified | `false` |
| unknown_selectors | `"raw-only Unknown"` |
| incomplete_fields | `"partial; independent siblings retained"` |
| special_admitted | `"ordinary subtotals retained; effective Unknown"` |
| errors | `"error; no successful result"` |
| copies | `"deep independent input, output, and later results"` |
| argument_types | `{"rows":"array[9]","registered":"bool","capable":"bool","failure":"bool","token":"u32","maximum":"u32","limited":"u32"}` |
| output_required | `["context","raw","state","fields","physical","qualified"]` |
| output_optional | `["arguments"]` |
| unknown_number | `"absent"` |
| field_lengths | `{"gate":1}` |
| u8_max | `255` |
| u16_max | `65535` |
| u32_max | `4294967295` |
| duplicates | `"reject anywhere"` |
| context | `"preserve absent, null, zero, opaque keys distinctly"` |
| arguments | `"preserve unknown extra keys; preserve absence on raw-only result"` |

Only `(181, 49, 3, "local", "ordinary-limit")` selects this view: primary
181 and secondary 49 are the local B531 selector; operation 3 denotes OP03.
Any unknown or missing selector, including explicit null or a mismatched kind,
returns raw-only `Unknown`, without a formula. Absent, null, and zero context
members are distinct and survive JSON round trips. Opaque `family`, `variant`,
and other context members are copied verbatim and cannot qualify the selector.

## Input and validation

The input is exactly one JSON object with object `context`, object `fields`, and
optional object `arguments`. For the selected view, `arguments` is required and
contains `rows` and `limited`. Each of the nine ordered rows represents its array
index 0 through 8 and requires Boolean `registered`, `capable`, `failure`, and
u32 `token`, `maximum`. They are caller-resolved predicates; there is no decoding
of unspecified capability bits. Unknown argument keys are preserved verbatim,
including nested arrays, objects, null, strings, and Boolean false.

`fields` maps names to byte arrays of integral values 0..255. `gate` is exactly
one byte for a complete field. There is no relay vector in this view. Missing,
empty, short, or overlong `gate` arrays are incomplete, retained raw, and do not
invalidate independent slot sums. Unknown named byte fields are preserved raw
and unmapped with `state="Unknown"`; they acquire no invented number or label.

Reject malformed JSON, trailing values, duplicate keys anywhere (also inside
opaque objects), non-object envelopes/context/fields/arguments, missing required
arguments or row members, non-nine-row arrays, wrong kinds, fractions and
out-of-range arguments or bytes. Booleans are not integers; null, string, array,
and Boolean kinds are never coerced. u8/u16/u32, wherever applicable, have upper
bounds 255/65535/4294967295; only u8 and u32 are used here. Unknown selectors do
not demand view-specific required arguments, but JSON structure, duplicate-key,
and byte-kind validation still apply. No successful result accompanies an error.

## Results and transitions

The result object contains `context` unchanged; `raw`, a deep independent copy
of `fields`; `arguments` unchanged when supplied (otherwise absent); `state`;
semantic `fields`; `physical="Unknown"`; and `qualified=false`.

| Semantic field | Result shape |
| --- | --- |
| gate | raw byte array when present, state complete or incomplete, number only for exactly one byte |
| slots | raw rows, state complete, ordered per-slot raw values and admitted Boolean |
| admitted | raw rows, state complete, indices of all admitted slots including slot 1 |
| token_sum | raw ordinary admitted token values, state complete, u64 number |
| maximum_sum | raw ordinary admitted maximum values, state complete, u64 number |
| effective | raw limited and admitted rows, state complete with Boolean number or Unknown without number |
| requested_state | raw gate and effective evidence, state complete with integer number or Unknown without number |

Every candidate semantic field carries `grade="Hypothesis"`; exact arithmetic
also carries `calculation="Proven"`. A missing quantity has no invented raw value,
number, or label. An explicit empty raw array remains empty. An unmapped quantity
has `state="Unknown"`. Applicable labels, flags, reserved, unmodeled,
candidate_domain, or alternatives must be retained if declared; none are declared
for this view, so they must not be invented. In particular there is no additional
candidate-domain bound that would suppress a valid ordinary sum.

Admission independently requires all three predicates. Sum admitted ordinary
slot tokens and maxima independently as u64; do not scale by 10 or 86500.
Even nine maximum u32 contributors cannot overflow u64; at most eight are
ordinary here. Preserve admitted indices and every row's raw values, including
excluded rows. If slot 1 is admitted, its special formula is unspecified:
ordinary subtotals stay available, but whole effective is `Unknown`. Never fold
slot 1 into ordinary sums. A failed admission predicate on slot 1 removes this
uncertainty. No previous successful sibling is erased by an incomplete field;
no persistent last-known-good cache is introduced by this pure function.

Without an admitted slot 1, compute the strict comparison and limited predicate
shown in the normative table. An empty admitted set gives zero sums and false
effective; this is not a native no-device result. Gate 0 yields requested state
0 even if effective is Unknown. Every nonzero byte, including 2 and 128, is
truthy: return 1 + effective only when effective is known. A missing/incomplete
gate leaves requested_state Unknown while sums and effective remain available.

Top-level state is `partial` for incomplete independent byte fields, `Unknown`
for an unsupported selector, otherwise `complete` as local representation only.
An unresolved special-slot branch can coexist with complete siblings and a
complete envelope; it does not make the supplied bytes incomplete. Raw-only
unsupported results have an empty semantic `fields` object and no formula-derived quantities. Return/input
mutation must not affect another field's nested storage, another result, or any
later call. All context/raw/state distinctions survive JSON round trips.

## Independent synthetic scenarios

The [scenario file](fixtures/ap04_b531_ordinary_limit.json) includes full nine-row
inputs and explicit expected tuples ordered as `(admitted, token_sum,
maximum_sum, effective, requested_state, state)`. JSON string `"Unknown"` in an
expected tuple denotes absence of a semantic number, never Boolean false or 0.
Its shape expectations are assertion notation, not a new runtime namespace.

| Case | token sum | maximum sum | effective | requested state |
| --- | --- | --- | --- | --- |
| ordinary | 3 | 4 | true | 2 |
| equality | 4 | 4 | false | 1 |
| limited-zero | 3 | 4 | false | 1 |
| gate-zero | 3 | 4 | true | 0 |
| gate-high | 3 | 4 | true | 2 |
| wide | 8589934590 | 8589934590 | false | 1 |
| special | 3 | 4 | Unknown | Unknown |
| special-zero | 3 | 4 | Unknown | 0 |
| empty | 0 | 0 | false | 1 |

These are candidate family/behavior results graded **Hypothesis**; exact
arithmetic may additionally be **Proven**. Physical association, support,
freshness, effects, feedback, applied state, persistence, and delivery remain
**Unknown**. No result is feedback or applied state. No executor, registration,
scan-default change, peer communication, MCP or GraphQL surface is added; their
existing compatibility and parity are unchanged. Nothing here is stable before
Helianthus 1.0; no major or experimental namespace is introduced.

## Verification boundary

The standard-library unittest independently checks these tables, scenario
constants, schema/error vectors, copy/round-trip assertions on synthetic JSON,
and small bounded transition oracles. It is not a Python runtime implementation
or evidence that a Go function was invoked. Production invocation, rejection,
and allocation isolation require later implementation tests; this slice owns no
Go implementation. The suite runs in `scripts/ci_local.sh`; it can also run
directly:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap04_b531_ordinary_limit.py -v
```

Gate D uses a fixed test list that explicitly includes this suite.
Full repository CI with its prescribed read-only prerequisites, publication
checks, applicable transport classification, and fresh independent committed
change review remain ship requirements. This is partial work for #736; the
umbrella remains open. Focused checks establish no physical result.
