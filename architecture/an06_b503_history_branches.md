# AN06: B503 history branch field view

This architecture contract specifies the hypothetical `ab05an05` pure helper
API, paired with AN05. It is independently authorable and introduces no native
qualification or runtime implementation. Nothing here is stable before
Helianthus 1.0. The [public native B503 contract](../protocols/vaillant/ebus-vaillant-B503.md)
is the authority for protocol claims: its category-form absent-entry example
is a candidate, and its marker meanings remain unconfirmed. This page adds
software choices only, not another native family description.

## Field API and ownership

```text
ab05an05.history_branch_view(context, marker, remainder, error, cells) -> HistoryBranchView
```

All arguments are caller-separated JSON-compatible fields, never a packet.
`context` contains opaque, nonempty `family` and `variant` tokens, B503
`operation` as an unsigned integer, and an opaque nonempty `direction` token.
Tokens are retained exactly; a different family, variant or direction is not
silently merged or treated as qualification. The examples use synthetic family
tokens only. Only operation 1 (OP01) selects these candidate branches; any other
operation or unavailable context yields `unknown-branch` with raw input intact.
No family or direction allowlist, family inference or physical admission follows.

`marker` is a caller-supplied unsigned byte or unavailable value. `remainder`
is an opaque seven-byte array used only for the no-item comparison; missing,
wrong-length and non-byte arrays cannot pass that comparison. `error` is an
optional already-decoded unsigned integer, with no wire-width assumption:
null means missing, an unsigned integer means present, and anything else is
malformed. Booleans are not integers for this API. Error raw form is this
supplied field; no error bytes or codec are reconstructed.

`cells` has exactly five entries in minute/hour/day/month/year order. Each
entry has `state`, opaque `raw`, and nullable `value`. Input states are `value`,
`replacement`, `missing`, or `malformed`; an unrecognized state is malformed.
For `value`, only an already-normalized unsigned integer is eligible for domain
checking. There is no decimal decoding here. A replacement cell may contain
raw `FF` (represented as `[255]`); raw `FF` alone never selects a state.
Missing/replacement selection precedes domain checking and removes any supplied
normalized value from the component result while retaining the original cell.
A missing or structurally invalid five-cell vector selects `unknown-branch`;
individual available cells are still retained and evaluated where selected.

The result is a deep independent value:

- `input`: a deep copy of all supplied fields, preserving even malformed data.
- `state`: exactly `no-item`, `error-without-complete-time`,
  `candidate-components`, or `unknown-branch`.
- `error`: `{state: present|missing|malformed, value: integer|null}`; a valid
  error survives every branch, even incomplete time and unknown context.
- `components`: five `{state, raw, value}` results in the declared order.
  States are `unselected`, `missing`, `replacement`, `malformed`,
  `out-of-domain`, or `candidate`. Only candidate and out-of-domain retain
  normalized unsigned values; every state retains its raw cell value.
- `complete`: true only when selected components are all candidate. This is
  software completeness, never a valid physical timestamp.
- `grades`: `{software: Proven, numeric: Proven|Unknown,
  semantic: Hypothesis|Unknown, native: Unknown}`. Numeric Proven describes
  software comparisons for selected components, including partial and malformed
  results; unselected numeric information is Unknown. Completeness and component
  presence remain separate from grades. Semantic Hypothesis
  applies to the three recognized local states; unknown-branch stays Unknown.

The helper allocates no shared mutable state and performs no I/O, clock lookup,
parsing, diagnostic command, persistence, forwarding or device execution.
Mutation of either caller fields or an earlier result cannot affect later
outputs, and a result cannot mutate its caller. There is no cache to overwrite
last-known-good data. Consumers retain independent useful fields on partial
failure; unknown or incomplete data does not admit physical actions. Existing
eBUS MCP compatibility and GraphQL parity are unchanged; no public endpoint,
namespace, authorization gate or transport behavior is added.

## Selection and partial results

Selection is operation/context first, then marker, then its branch fields.
Calendar inspection cannot override a no-item or unknown-marker selection.
For operation 1 and marker 0, exactly seven bytes each equal to 255 select
`no-item`; every other remainder selects `unknown-branch`. Both leave components
unselected regardless of calendar contents. Other markers outside 1 and 2 also
leave components unselected. A malformed marker cannot match an integer marker.

For marker 1 or 2, select each component independently: missing/replacement
first, then normalized unsigned validity, then the component's own domain.
Candidate domains are minute 0..59, hour 0..23, day 1..31, month 1..12 and
year 0..99, inclusive. One bad component cannot erase another component.
Marker 1 with a present error and incomplete components selects
`error-without-complete-time`. Marker 1 with complete components, or without
a present error, conservatively selects `unknown-branch`: this finite contract
does not assign that combination a new meaning. Marker 2 with five candidates
selects `candidate-components`; partial, malformed or unavailable fields select
`unknown-branch`, retaining candidate components and any present error.
The opaque remainder is ignored for markers 1 and 2 and is always retained.

These local selection choices and result design are **Proven software contract**.
No-item meaning, marker 1 error-only meaning, marker 2 component meaning and
component domains remain **Hypothesis**. Physical qualification, presence,
freshness and execution are not established by those grades. A complete vector
such as February day 31 is still a candidate, with joint validity **Unknown**.

## Unknowns and prohibited inference

Byte positions, the wire error-number codec and the decimal algorithm are
**Unknown**. Century, timezone, joint calendar validity, body freshness,
local/peer error identity, forwarding, persistence and reset effects are
**Unknown**. No conversion to an absolute timestamp, year expansion, native
error label or physical parser is authorized. Raw replacement FF is never a
date. Family tokens and numeric completeness do not qualify a native mapping.

## Executable declaration and finite examples

This declaration is an application contract for the test-local model, not a
packet schema. Changing a rule requires reviewing its independent examples.

```json history-branch-rules
{
  "selection_order": [
    "context-operation",
    "marker",
    "remainder-or-components",
    "component-presence",
    "component-domain"
  ],
  "no_item": {
    "operation": 1,
    "marker": 0,
    "remainder_length": 7,
    "every_byte": 255
  },
  "replacement": "retain-raw-without-normalization",
  "error": "retain-independently-of-time",
  "packet_offsets": "Unknown",
  "error_codec": "Unknown",
  "decimal_algorithm": "Unknown",
  "century": "Unknown",
  "domains": {
    "minute": [
      0,
      59
    ],
    "hour": [
      0,
      23
    ],
    "day": [
      1,
      31
    ],
    "month": [
      1,
      12
    ],
    "year": [
      0,
      99
    ]
  },
  "grades": {
    "software": "Proven",
    "candidate_semantics": "Hypothesis",
    "native": "Unknown"
  }
}
```

The [finite synthetic fixture](fixtures/an06_b503_history_branches.json) supplies
explicit input, raw forms and independent expected result fields. Its base
selection is synthetic family-a/variant-a, operation 1, direction reply.
The [standard-library checks](../tests/test_an06_b503_history_branches.py) validate
this declaration, all examples, field coverage, local links and copy isolation.
They exercise a test-local contract model, not the absent companion code.

| Example set | Independent expected outcome |
|---|---|
| no-item; remainder-0 through remainder-6 | Seven FF gives no-item; change any one byte to FE gives unknown-branch |
| error-only; error-all-missing; error-partial | Error 4660 survives replacement FF cells, missing cells and an out-of-domain minute; no complete time |
| upper; lower | 59/23/31/12/99 and 0/0/1/1/0 are five candidates |
| minute-high; hour-high | 60 or 24 is out-of-domain; independent day/month/year remain candidate |
| each component's low/high/missing/replacement/malformed/value variants | Raw and each independent state survive; missing/replacement wins over even supplied valid numbers |
| family; variant; direction; operation; unavailable-context | Exact context retained; non-OP01 or unavailable context stays unknown |
| marker-unknown; marker-missing; marker-malformed | No calendar selection despite otherwise complete cells |
| error-missing/error-zero/error-other/error-malformed | Presence and numeric value remain independent of calendar completeness |
| remainder-short/remainder-long/remainder-malformed/remainder-missing | No no-item admission |
| cells-missing/cells-short; impossible-joint-date | Retain partial fields; no joint validity inference |

No synthetic example is a capture or native evidence. AN05 is an ordinary
companion, not an import or dependency. Refs parent #736; this partial slice
leaves native qualification, companion implementation and runtime obligations
open. Full shipping CI and independent review remain separate requirements.
