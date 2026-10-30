# B516 local OP14 cycle candidate

This page describes a **Hypothesis** about local software behavior for a
requester in the energy-manager family. It assigns no gateway change, producer
integration, installed support, or physical qualification. Nothing here grants
execution or admission through eBUS MCP or GraphQL; their contracts are unchanged.

The [B516 energy protocol page](../protocols/vaillant/ebus-vaillant-B516-energy.md),
section “Sub-ID 0x14 - current electrical power (candidate)”, grades the
candidate layout **Hypothesis**. It preserves a status byte, binary32 word0, and an uninterpreted word1. Sign, unit, answering targets and cadence remain
**Unknown**. The local tuples below are synthetic software inputs, not telegrams
or evidence of those physical properties. Raw float bytes are space-separated
and little-endian; markers are independent synthetic variant markers, not native status meanings.

## Individually graded rules

Each row is a local **Hypothesis**; constants and alternatives are intentionally
explicit. The unittest is a bounded candidate transition oracle, not a runtime.

| Rule | Value | Grade |
|---|---|---|
| slots | 9 | Hypothesis |
| sentinel | 4294967295 | Hypothesis |
| threshold | 2 | Hypothesis |
| modulus | 4294967296 | Hypothesis |
| gates | registration_and_capability | Hypothesis |
| positive_only | false | Hypothesis |
| partial_sum | retain | Hypothesis |
| scheduler_arguments | 1,60 | Hypothesis |

Registration and capability are independent gates per slot (indices 0 through
8). An admitted attempt copies prior into previous before processing. A skip
sets new to 4294967295, but whether it updates previous or changed is **Unknown**.
An admitted read or parse failure sets new to 4294967295, retaining the raw input
and variant marker beside the previous value. Previous is last-known-good only
when the supplied prior was good; a prior sentinel remains a sentinel.

For a determined new value, changed is `previous == 4294967295 or
((new - previous) % 4294967296) >= 2`. This is unsigned subtraction: the
12-to-11 decrease exposes delta 4294967295 and changes. Signed subtraction
would miss it; absolute difference would produce one and also miss it.
Successful contributions sum modulo 4294967296; failures do not inherently
withhold a partial sum. Failure count adds failed admitted attempts modulo
4294967296 and resets on a cycle without such failures. Skips are not failures.

There is no extra positive-only conversion guard: zero is accepted. Negative
and NaN conversion results are **Unknown**, rather than rejected by an invented
positive-only rule or coerced to a number. Other unprovided conversions, outcomes,
slot identities and malformed inputs remain **Unknown**. The large wrap vector
injects a u32 directly; 4294967294 is not exactly representable as binary32.
No conversion to that integer is claimed. No real-time scheduler runs here.
Arguments 1/60 establish neither physical cadence, native units nor freshness.

The oracle returns Unknown publication without a successful contribution;
publication with unknown contributions and every other unprovided branch remain
Unknown. A partial sum is a local candidate result, never qualified telemetry.
Raw alternatives (status and word1 interpretation, signed/absolute delta, and
negative/NaN conversion) are not resolved by these synthetic examples. There is
no native Proven conclusion. **Proven** is limited to the declared representation
and arithmetic predicates checked by the synthetic tests.

## Synthetic steps

Each row carries the local Hypothesis grade above. Unknown is an unresolved
field, not a sentinel. The only identity axis claimed is local slot; no device,
address, source, destination or firmware identity is inferred.

| id | slot | registered | capable | outcome | prior | raw | marker | previous | new | diagnostic | changed | contribution | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| delta_one | 0 | true | true | success | 10 | 00 00 30 41 | 00 | 10 | 11 | success | false | 11 | 0 |
| delta_two | 1 | true | true | success | 10 | 00 00 40 41 | 00 | 10 | 12 | success | true | 12 | 0 |
| prior_sentinel | 2 | true | true | success | 4294967295 | 00 00 00 00 | 00 | 4294967295 | 0 | success | true | 0 | 0 |
| read_failure | 3 | true | true | read_failure | 10 | Unknown | A1 | 10 | 4294967295 | read_failure | true | 0 | 1 |
| parse_failure | 4 | true | true | parse_failure | 10 | AA | B2 | 10 | 4294967295 | parse_failure | true | 0 | 1 |
| unregistered | 5 | false | true | success | 10 | 00 00 40 41 | C3 | Unknown | 4294967295 | skip_registration | Unknown | 0 | 0 |
| incapable | 6 | true | false | success | 10 | 00 00 40 41 | D4 | Unknown | 4294967295 | skip_capability | Unknown | 0 | 0 |
| decrease_one | 7 | true | true | success | 12 | 00 00 30 41 | 00 | 12 | 11 | success | true | 11 | 0 |
| ninth_slot | 8 | true | true | success | 10 | 00 00 40 41 | 00 | 10 | 12 | success | true | 12 | 0 |
| negative | 0 | true | true | success | 10 | 00 00 80 BF | E5 | 10 | Unknown | Unknown | Unknown | Unknown | 0 |
| nan | 1 | true | true | success | 10 | 00 00 C0 7F | F6 | 10 | Unknown | Unknown | Unknown | Unknown | 0 |
| unsupported_step | 2 | true | true | unprovided | 10 | Unknown | 17 | 10 | Unknown | Unknown | Unknown | Unknown | 0 |
| wrap_large | 0 | true | true | success | 10 | injected_u32:4294967294 | 00 | 10 | 4294967294 | success | true | 4294967294 | 0 |
| wrap_small | 1 | true | true | success | 10 | 00 00 40 40 | 00 | 10 | 3 | success | true | 3 | 0 |

## Injected cycles

| id | steps | counter_before | sum | counter_after | publication |
|---|---|---|---|---|---|
| partial | delta_one,read_failure | 4 | 11 | 5 | true |
| sum_wrap | wrap_large,wrap_small | 2 | 1 | 0 | true |
| counter_wrap | read_failure | 4294967295 | 0 | 0 | Unknown |
| clean | delta_two | 7 | 12 | 0 | true |
| skip | unregistered | 7 | 0 | 0 | Unknown |
| conversion_unknown | negative | 7 | 0 | 0 | Unknown |

The [fixture](fixtures/ai25_b516_local_cycle.json) preserves these inputs and
expected outputs. Tests compare both tables and fixture against independent
constants, then check transitions, gate independence, slot range and arithmetic.
All checks use injected steps; no polling, live operation or protocol write is assigned.
