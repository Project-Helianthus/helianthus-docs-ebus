# AJ22: partial weekly refresh and zero-slot outcomes

Refs #829; partial child of #736. This is a bounded local software candidate,
not a runtime implementation. All rules below are **Hypothesis**. Native behavior
and every unprovided property remain **Unknown**; synthetic success is not
qualification or admission. Nothing here establishes a stable pre-1.0 contract.

## Native evidence boundary

The public native contract comes first:
[B555 timer protocol](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md),
sections 5.2–5.4.2. It keeps A4 count/status, A5 slot reads and A6 slot writes
separate. Its requester descriptions are candidates, not native proof for this
software contract. In particular, section 5.2.1 describes upfront rejection of
any excessive count; the partial refresh below instead checks each day as it is
visited. These are distinct candidates, not interchangeable observations.
Section 5.4.2 describes a zero-count A6 request carrying initial slot bytes;
zero *processed slots* here does not assert zero A6 wire requests. A6 dispatch
count, native zero-slot meaning and controller effects remain Unknown.

## Identity and scope

Use synthetic timer-family identities only. Preserve `(family, transport, zone,
channel)` separately, then day and slot separately within that identity. A4/A5
refresh is a read candidate; A6 preparation is a write candidate. Do not merge
these variants because they share a channel or day. Symbolic zone/channel values
in the fixture are opaque labels, not wire bytes or supported mappings. No
aggregate-day mappings, timer codecs, builders or runtime timer paths change.
The synthetic capacity of two is an arithmetic test bound, not a device limit.

## A6 preparation table

Five symbolic inputs are ordered as start hour, start minute, end hour, end
minute, setpoint. Retain them verbatim beside prepared slots. For each processed
non-heating slot only, replace its prepared setpoint with `FFFF`; no other input
changes. Heating is a positive control retaining the explicit input setpoint.
The candidate accepts only the fixture's counts 0 and 1 in this slice; other
preparation counts are unprovided, not a new limit.

| Count | Variant | Retained inputs | Processed slots | Prepared setpoint |
|---|---|---|---|---|
| 0 | non-heating | unchanged five | 0 | absent |
| 1 | non-heating | unchanged five | 1 | FFFF |
| 0 | heating | unchanged five | 0 | absent |
| 1 | heating | unchanged five | 1 | input |

## Weekly refresh transition table

A4 status admission precedes every A5 attempt. On admitted A4, visit days 0–6
in order; validate that day's count before reading its slots. Each admitted day
retains its raw symbolic slot results, including an empty result for count 0.
Do not inspect later counts early. Preserve the full supplied A4 input separately
from visited-day results. No result is erased on a later failure.

| Condition | A5 attempts | Retained days | Partial day | complete |
|---|---|---|---|---|
| A4 failure before day 0 | 0 | none | absent | false |
| overflow at day d | sum of counts before d | 0 through d-1 | day d, raw count, no slots | false |
| all seven days accepted | sum of seven counts | 0 through 6 | absent | true |

A partial-day record is evidence of the failed count check, not a completed day.
The fixture independently overflows each of seven positions, including day 2
with successful days 0/1 retained. Unvisited slot inputs are not acquired results.
A prior last-known-good week is retained separately on failure; it cannot make
the new partial buffer complete. Completion is local traversal only; admission
remains false even for a complete synthetic week. No retry, rollback or recovery
policy is invented. Mid-slot A5 failure behavior is unprovided and Unknown.

## Evidence table

| Property | Grade |
|---|---|
| software candidate | Hypothesis |
| native behavior | Unknown |
| physical schedule effects | Unknown |
| persistence | Unknown |
| atomicity | Unknown |
| A6 dispatch count | Unknown |
| mid-slot failure | Unknown |
| retry or rollback | Unknown |

Raw inputs, partial state, evidence grade and physical qualification are
independent. No API, GraphQL or eBUS MCP surface changes; parity and compatibility
are unaffected by this documentation slice, not newly runtime-tested.

## Offline acceptance

[Scenarios](fixtures/aj22_b555_week_refresh.json) contain synthetic inputs and
explicit expected outputs. The standard-library
[test](../tests/test_aj22_b555_week_refresh.py) independently calculates transitions
and arithmetic, checks both tables and scenarios, and rejects isolated corruptions
of expected outcomes and evidence grades. Mutation mappings describe future runtime
regressions; only the in-memory fixture/table corruptions exercised by the tests
are executed rejection checks. There is no runtime feature under test.

Identity controls independently vary family, transport, zone and channel; day
and slot controls vary their indices through all visited days and a two-slot day.
Preparation controls vary each of the five inputs, count and heating predicate;
read/write operation and variant swaps are rejected. The test module enumerates
which prospective production mutation each field's control would catch.
