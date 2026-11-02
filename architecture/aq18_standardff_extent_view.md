# Standard FF body extents and retained raw remainders

## Scope and evidence

Read the [public native FF contract](../protocols/ebus-services/ebus-service-FFh.md)
first, especially services FF04 and FF06. Its structural distinctions remain
authoritative; this page adds only a pre-1.0 local API contract. **Proven** here
means exact local arithmetic, never native service completion. Body meaning,
target correlation, physical receipt, support, effects, persistence and delivery
remain **Unknown**. Candidate meaning remains **Hypothesis** independently of
calculation grade and qualification. No family is qualified by selecting a view.

AQ18 is an ordinary companion to AQ17, with no code-merge dependency or unmerged
registry entry required. AL21/22 retains completeness metadata; AJ28 retains
liveness/reset prose. This callable span evaluator adds no emitter, decoder,
lifecycle reducer, executor, automatic caller or qualification path. It defines
no new eBUS MCP or GraphQL behavior and requires no provider registration.

## Callable boundary and input

Package `ebus_standard_catalog` exports, using only the Go standard library:

```go
func Ab17Aq17Evaluate(ab17Aq17Input json.RawMessage) (json.RawMessage, error)
```

This is a pure field evaluator, not another Entries/Lookup catalog or schema.
There is no initialization side effect, persistent cache or pending helper.
Input and output storage cannot alter another call or a later result. The
compound declaration stem is `ab17aq17` / exported `Ab17Aq17`; this page creates
no Go package or declarations beyond documenting the supplied signature.

The input is exactly one JSON object containing `context`, `fields` and optional
`arguments`, each an object when supplied. Preserve unknown extra input keys
unchanged, including nested values. The supported view requires
`arguments.declared_length`.

| Input location | Contract |
|---|---|
| `context.primary`, `context.secondary` | Integers 0..255 when present |
| `context.operation` | Integer 0..255 when present; absence is distinct from explicit zero; null is not a number and is rejected |
| `context.direction`, `context.view` | Selectors `positive` and `body-extent` for the supported views |
| Opaque family/variant keys in `context` | Retained independently; no supplied family/variant mapping or qualification |
| Named members of `fields` | Initialized byte arrays of integers 0..255; explicit opaque `[]` differs from missing |
| `fields.body` | Variable-length isolated raw body, with no fixed width; missing remains partial, never synthesized as `[]` |
| `arguments.declared_length` | Required integer 0..255 for a supported view; never inferred from available bytes |

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional or out-of-range bytes or integer arguments, and
missing required arguments. Return an error with no successful result. Never
coerce strings, null or Booleans into numbers. Unknown extra keys remain opaque;
their valid explicit null, zero, false and empty values retain their distinctions
from absence. Reject invalid input even if its context would be unsupported.

Only these combinations apply formulas:

| Primary | Secondary | Operation | Direction | View |
|---:|---:|---|---|---|
| 255 | 4 | absent | `positive` | `body-extent` |
| 255 | 6 | absent | `positive` | `body-extent` |

Any other valid combination returns raw-only **Unknown**, without applying a
formula. In particular, explicit operation zero is unsupported; null is an input
error. Opaque family/variant values do not supply additional supported views.

## Result and partial boundaries

Return one JSON object retaining `context`, raw `fields`, `arguments` when
present, and extra keys independently, alongside `state`, `results`,
`physical: "Unknown"` and `qualified: false`. Each field result retains `raw`
and `state`, plus applicable arithmetic values. Semantic outputs may have
`number`, `label`, `flags`, `reserved`, `unmodeled`, `candidate_domain` or
`alternatives` only when applicable; none of the missing address/flag definitions
is decoded here. No semantic number or label is invented for Unknown conversion.

`complete` denotes local representation only. An unresolved semantic label can
coexist with complete raw arithmetic; it does not establish native completeness.
An FF04 body of length one is partial, even though its minimum predicates can
be calculated completely. Truncation or an FF06 incomplete tail likewise stays
partial. Unsupported context is `Unknown`. A minimum result alone never makes
a successful or qualified reply.

Missing, short or overlong fixed-width fields, if encountered by a selected
field evaluator, retain their raw form and have per-field incomplete state;
complete independent siblings remain available. This span view introduces no
fixed-width sibling decoder. For missing `body`, retain absence and return
partial without an available length or available pair count. Explicit `body: []`
has available length zero. Preserve every initialized byte: the bounded span is
the prefix up to the declaration; any suffix beyond it remains raw and unmodeled,
without repairing the declaration. Partial results retain useful arithmetic
that is independently known, including declared counts when body data is absent.

Candidate meaning stays `Hypothesis`; exact calculations may additionally carry
`calculation: "Proven"`. Never replace a candidate grade with its calculation
grade. Qualification, freshness and physical support are separate from both.

## FF04 minimum arithmetic

Let `declared` be `arguments.declared_length` and `available` the initialized
body length. The declared interval 1..10 includes one, which cannot hold both
follow-block and status overhead. This view does not decode either byte.

| Result | Exact rule |
|---|---|
| `declared_minimum_satisfied` | `declared >= 2` |
| `initialized_minimum_satisfied` | `available >= 2`; unavailable when body is missing |
| `bounded_minimum` | Both minima true, `declared <= 10`, and `available >= declared` |

For missing body, bounded minimum cannot be established; do not invent available
bytes or a true minimum. A true bounded minimum establishes only the local
minimum arithmetic. Address definitions, flags, body meaning and successful
reply status remain Unknown.

| Declared | Available | Declared minimum | Initialized minimum | Bounded minimum | Interpretation |
|---:|---:|---|---|---|---|
| 1 | 1 | false | false | false | Partial/raw, never complete |
| 2 | 2 | true | true | true | Minimum only; semantic state Unknown |
| 10 | 2 | true | true | false | Partial; declared span unavailable |
| 0 | 0 | false | false | false | Partial; no peer inference |

Values above ten cannot satisfy bounded minimum, even with all bytes present;
they do not extend the stated interval or establish native structure.

## FF06 pair arithmetic

The declared whole-pair form is `1 + 2n`, for integer `n >= 0`. Preserve declared
and available lengths separately; no extra initialized byte repairs a declaration.

| Result | Exact rule |
|---|---|
| `declared_pair_count` | `floor((declared - 1) / 2)` when `declared >= 1`; absent for zero |
| `declared_incomplete_tail` | `declared >= 1` and `(declared - 1) % 2 == 1` |
| `available_pair_count` | `floor((min(available, declared) - 1) / 2)` when that bounded span has at least one byte; otherwise absent |
| `whole_declared_span` | `declared >= 1`, `available >= declared`, and no declared incomplete tail |

Missing data supplies no available count and cannot establish a whole span.
These are arithmetic predicates, not service decoding or a new normative maximum.
Full service meaning remains Unknown.

| Declared | Available | Declared pairs | Available pairs | Incomplete tail | Whole declared span |
|---:|---:|---:|---:|---|---|
| 0 | 0 | absent | absent | false | false |
| 1 | 1 | 0 | 0 | false | true |
| 2 | 2 | 0 | 0 | true | false |
| 3 | 3 | 1 | 1 | false | true |
| 4 | 4 | 1 | 1 | true | false |
| 5 | 5 | 2 | 2 | false | true |
| 5 | 3 | 2 | 1 | false | false |
| 3 | 4 | 1 | 1 | false | true |

The last row retains the fourth byte as raw remainder, without adding a pair.
Even declarations never become whole pairs by using available bytes instead.

## Synthetic result examples

These shapes show retained input and local results; they are not wire captures.
A complete valid local FF06 input:

```json
{"context":{"primary":255,"secondary":6,"direction":"positive","view":"body-extent"},"fields":{"body":[0,17,34,51]},"arguments":{"declared_length":3},"extra":{"zero":0,"enabled":false,"note":null,"empty":[]}}
```

Its result retains the entire input, including the extra fourth byte:

```json
{"context":{"primary":255,"secondary":6,"direction":"positive","view":"body-extent"},"fields":{"body":[0,17,34,51]},"arguments":{"declared_length":3},"extra":{"zero":0,"enabled":false,"note":null,"empty":[]},"state":"complete","results":{"body":{"raw":[0,17,34,51],"state":"complete","declared_length":3,"available_length":4,"declared_pair_count":1,"available_pair_count":1,"declared_incomplete_tail":false,"whole_declared_span":true,"unmodeled":[51],"calculation":"Proven"}},"physical":"Unknown","qualified":false}
```

The counts do not assign meaning to the bytes. No semantic label is asserted.
Independent partial and Unknown cases:

| Input variation | Retained result |
|---|---|
| FF04, declared 1, body `[0]` | Partial, raw `[0]`; all three minimum predicates false; meaning Unknown |
| FF04, declared 2, body `[0,0]` | Local minimum satisfied only; semantic state Unknown, physical Unknown, qualified false |
| FF04, declared 10, body `[0,0]` | Partial, raw retained; both minima true, bounded minimum false |
| FF06, declared 5, body `[0,17,34]` | Partial; declared pairs 2, available pairs 1, tail false, whole span false |
| FF06, declared 3, body absent | Partial; declared pairs 1 retained, available length/count absent; no whole-span success |
| FF06, declared 3, body `[]` | Partial; available length 0, available count absent, whole span false; raw `[]` retained |
| Same valid bytes, explicit operation 0 | Raw-only Unknown; no pair or minimum formulas applied |
| Same valid bytes, direction other than `positive` | Raw-only Unknown; no formula or qualification |
| Same bytes, operation null or duplicate nested key | Error; no successful result |

Calling FF04 length one complete, decoding unprovided fields, accepting an even
FF06 declaration as whole pairs, repairing declared counts from available bytes,
or equating minimum arithmetic with a qualified reply violates this contract.
Zero-length, truncated, mismatched and unsupported inputs imply neither peer
absence nor ACK nor executable support. Native completion and execution do not
follow from any result on this page.
