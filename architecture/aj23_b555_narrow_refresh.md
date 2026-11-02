# AJ23: timer narrowing and distinct refresh identities

Refs #830; partial child of #736. This is a bounded local software candidate,
graded **Hypothesis**, with physical qualification **Unknown**. No timer
scheduler, cache writer or consumer is implemented. No native code is assigned
to an unnamed kind. Nothing here is a stable pre-1.0 API or an execution grant.

The [public native B555 contract](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md)
comes first for wire claims, particularly its selector correspondence, multi-slot
qualification and open questions. The supplied issue facts support only the
local candidate below; they do not extend native support to another family.
A4/A5/A6 here name local refresh/write paths in that context. Do not infer
native module aliases, cadence, acceptance, writable capability or persistence.
No raw installation capture is provided. All examples in the
[scenario file](fixtures/aj23_b555_narrow_refresh.json) are synthetic.

## Separate local contracts

These labels are fixture-local placeholders, not native kind names or codes.
Each kind has a separate carrier, cache and consumer contract. Their internal
layouts, actual native identifiers and module admission rule remain Unknown.

| Kind | Carrier | Cache | Consumer | Native code | Grade |
|---|---|---|---|---|---|
| local-1 | carrier-1 | cache-1 | consumer-1 | Unknown | Hypothesis |
| local-2 | carrier-2 | cache-2 | consumer-2 | Unknown | Hypothesis |
| local-3 | carrier-3 | cache-3 | consumer-3 | Unknown | Hypothesis |
| local-4 | carrier-4 | cache-4 | consumer-4 | Unknown | Hypothesis |
| local-5 | carrier-5 | cache-5 | consumer-5 | Unknown | Hypothesis |

Module admission differs by software variant. The fixture's variant-alpha and
variant-beta use separate opaque predicates; neither predicate's definition or
result is supplied. Unknown admission stays closed. Local N equals transmitted
count only for the ordinary sender; other sender counts stay Unknown.

## Arithmetic candidate

Integer64 retains low 16 bits, including negative operands; it does not saturate.
For ordinary finite floating operands in the defined conversion domain, narrow
float64 to float32, widen to float64, multiply by 10, truncate to u32, then retain
low 16 bits. Nonfinite and out-of-domain conversion remain Unknown.

| Integer64 input | Low 16 |
|---|---|
| 65535 | 65535 |
| 65536 | 0 |
| -1 | 65535 |

| Float input | Widened float32 | Multiplied by 10 | u32 | Low 16 |
|---|---|---|---|---|
| 1.29 | 1.2899999618530273 | 12.899999618530273 | 12 | 12 |
| 6553.6 | 6553.60009765625 | 65536.0009765625 | 65536 | 0 |
| 1.3 | 1.2999999523162842 | 12.999999523162842 | 12 | 12 |

Skipping float32 would give 13 for 1.3, contrary to this candidate.
Preserve the generic setter marker separately from the full 32-bit OR return:
`00010000 | 00000001 = 00010001`. The return must not narrow to 16 bits.
Local commit and persistence are separate; persistence remains Unknown.

## A6 transitions

Count is local callback context, not evidence of sender count equivalence.
For nonzero count, full and partial callbacks select distinct dirty states.
For zero count, preserve the 500-argument attempt separately from the later
root/full request. An attempt does not establish success; neither a request nor
a local commit establishes persistence. Zero count does not fabricate a dirty
callback outcome.

| Count predicate | Callback | Attempt argument | Attempt success | Request | Dirty |
|---|---|---|---|---|---|
| zero | full | 500 | Unknown | root/full | Unknown |
| zero | partial | 500 | Unknown | root/full | Unknown |
| nonzero | full | none | Unknown | none | full |
| nonzero | partial | none | Unknown | none | partial |

Retain raw evidence and partial last-known-good state on incomplete outcomes.
The fixture retains both raw items but only the previously good item as useful
state; it does not turn a pending item into a committed or persisted value.
Unknown qualification or admission never opens control execution.

## Refresh and identity boundaries

A4 and A5 refresh variants include DHW, circulation and ventilation, while
heating and cooling remain separately scoped. This local inventory establishes
no observed requester behavior for any of those scopes.

| Service | Scope | Direction | Grade |
|---|---|---|---|
| A4 | DHW | read-refresh | Hypothesis |
| A4 | circulation | read-refresh | Hypothesis |
| A4 | ventilation | read-refresh | Hypothesis |
| A4 | heating | read-refresh | Hypothesis |
| A4 | cooling | read-refresh | Hypothesis |
| A5 | DHW | read-refresh | Hypothesis |
| A5 | circulation | read-refresh | Hypothesis |
| A5 | ventilation | read-refresh | Hypothesis |
| A5 | heating | read-refresh | Hypothesis |
| A5 | cooling | read-refresh | Hypothesis |

Identity is the full tuple `(variant, timer_kind, model_index, read_instance,
a6_module)`. Model index 255, read instance 0 and the input-derived A6 module
are independent axes. Neither 255 nor 0 supplies the output module. The fixture
varies each axis individually; its module 7 is synthetic input, not a native
mapping. Cache/consumer selection must retain the whole tuple without merging
partial outcomes. A 3600-second timer argument establishes neither TTL nor
actual cadence; both remain Unknown.

## Compatibility and verification boundary

No eBUS MCP or GraphQL surface changes here. Any eventual projection must keep
identical identities, raw/partial outcomes and grades across both surfaces;
runtime compatibility and parity remain Unknown without implementation checks.
The test-only struct oracle checks arithmetic, all page tables and the scenarios
independently. Synthetic success proves only local checks, never native behavior
or physical qualification. No active requests, polling defaults or control
execution follow. Full documentation gates, independent committed-change review,
publication audit, full CI and transport classification remain later ship gates.
