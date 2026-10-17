# Shared energy calendar policy proposal

This is a proposed gateway application contract for energy ingest, register
acquisition and public projection. It selects a shared calendar policy; it does
not establish new B516 wire evidence or claim implemented runtime behavior.
Nothing in this proposal is stable before Helianthus 1.0.

## Sources and status

The native authority comes first: [B516 energy statistics](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B516-energy.md),
sections 3, 4.3–4.5 and 6.1, documents packed absolute calendar components and
their evidence limits. A civil date is not an instant or a time-zone identifier.
The [energy merge contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/energy-merge.md)
documents application keying, the process-calendar assumption, source precedence,
relative monthly acquisition, projection, freshness and the pending retention
companion. Its implementation statements corroborate application behavior, not
native protocol semantics.

| Claim | Evidence status | Application consequence |
| --- | --- | --- |
| The native page's worked reply date can be decoded as absolute components | Proven for the worked evidence only | Preserve the decoded components and raw evidence; do not generalize device support |
| Year selectors identify absolute years; totals ignore the date | Hypothesis, following the merge contract's explicit qualification of the native page | Do not promote these interpretations through this calendar proposal |
| Controller IANA zone and agreement with the configured calendar | Unknown unless independently established | Configuration chooses application behavior; it does not prove controller agreement |
| One shared injected location and the transitions below | Proposed gateway policy, not a Proven implementation | Requires implementation and focused validation before runtime acceptance |

Proven/Hypothesis/Unknown describe evidence. They do not confer qualification,
acquisition eligibility, admission or trust. Existing admission and native
validation remain prerequisites; this proposal grants none of them. It introduces
no authorization gate and no device write.

## Decision and fields

Inject one immutable calendar context into all three consumers at startup. It
contains a resolved IANA location and the shared clock dependency. No consumer
may consult its own process-local zone, infer a zone from a controller label, or
substitute UTC when location resolution fails. At an operation's reference UTC
instant `t`, derive `R = date(t in location)`. Separate operations can naturally
have different references when they straddle a boundary; all consumers using the
same context and instant must derive the same reference.

| Field | Meaning and required treatment |
| --- | --- |
| Controller civil date `(year, month, day)` | Absolute decoded components, validated for their period. Never construct UTC midnight and convert it to obtain another date. Preserve the original date even if admission rejects it. Unused key components remain zero |
| Calendar location | One explicit injected IANA identifier, such as `Europe/Berlin`, loaded once with available zone rules; fixed offsets and ambiguous abbreviations are not substitutes |
| Reference date `R` | Derived from the shared clock instant in that location; supplies day/year admission, relative month resolution, retention eligibility and live projection |
| Evidence instant | UTC wall-clock instant of the observation, retained with native provenance; not a replacement for the controller civil date |
| Monotonic observation marker | Process-local elapsed-time basis for original age, freshness and same-source ingest ordering. Wall-clock corrections cannot make old evidence fresh or reverse ingest order |
| Calendar context generation | Internal identity of the startup context, including the loaded zone rules; binds an acquisition and derived caches. It is not a new public field or evidence identity |

For omitted configuration, the compatibility default is the process's local
IANA location resolved once at startup and explicitly injected into all consumers.
This preserves the documented calendar where that location can be resolved; it
does not establish that the controller uses it. An explicitly configured `UTC`
is valid, but UTC is never an implicit error fallback. If the process location
cannot be resolved to an IANA location, require an explicit valid location before
starting dated energy processing. Reject an empty explicit value, unknown name,
fixed-offset expression or unavailable zone rules. Do not replace the last
accepted context with an invalid candidate. Lifetime processing is independent
of dated-calendar readiness and retains its existing admission rules.

When the controller zone is unknown, continue under the accepted configured
calendar while reporting agreement as Unknown. Do not guess from telegram dates,
alter the controller clock, relax strict matching or claim qualification. A
known disagreement requires an explicit configuration correction, not automatic
date shifting. This policy guarantees agreement among application consumers;
controller alignment remains a separate acceptance obligation.

## Consumers and invariants

| Consumer | Proposed reference and key rule | Preserved behavior |
| --- | --- | --- |
| Broadcast ingest | Capture `R` once. Admit a valid daily civil date only when it equals `R`; key it by those unchanged components. Admit a valid absolute year only for `R.year` or its predecessor | Monthly broadcasts remain unconsumed. Missing/invalid dates and mismatches do not mutate stored points or revision |
| Register acquisition | Capture the context generation and `R` once for the acquisition. Resolve current month to `(R.year, R.month, 0)` and previous month by civil calendar subtraction | Relative monthly reads bypass scheduler/shadow caches. Lifetime reads retain their normal cache policy and no date |
| Live projection | Derive `R` for each live accessor call using the same context. Select today, current/previous month and current/previous year from absolute stored keys | GraphQL, live MCP, portal and inventory use the shared provider. No envelope or public shape change |

The complete dated key remains `(channel, usage, period, year, month, day)`.
Usage canonicalization, period and channel are unaffected. A year key has zero
month/day; a month key has zero day. Lifetime remains `(channel, usage, all)`
without a reference year. Its compatibility projection, including competition
with dated register points, remains exactly the merge contract's lifetime truth
table; a calendar change cannot turn it into a dated annual total.

Register precedence over broadcast is unchanged even when the register point is
stale. Within one source and process epoch, only a strictly later monotonic
ingest wins; equal ingests are rejected. Across restart, use the restored-evidence
ordering rule below. Failed or rejected observations retain partial
last-known-good state and its original age. Calendar projection, cache rebuild,
rollover and configuration rejection never count as a new observation. Preserve
the documented 45-minute freshness threshold; use monotonic elapsed duration,
not subtraction of UTC evidence instants. Do not change its existing threshold
edge convention through this proposal.

Apply the merge contract's existing day pruning and pending companion's
month/year retention rules against the shared reference, without expanding their
acceptance or claiming the companion is merged. Projection never prunes. Future
absolute windows retained across rollback remain stored; pruned history is not
recreated by a later clock change.

## Transition and cache contract

| Transition | Required result |
| --- | --- |
| Day/month/year boundary during relative acquisition | Before accepting each reply, compare the current shared civil date with the captured date. On any date change, including rollback, discard that reply and stop the remaining acquisition; keep already accepted points under their original keys. The next poll captures a new reference |
| DST jump or repeated hour within one civil day | Same reference date and keys. A relative read need not abort solely for an offset change; elapsed freshness keeps advancing through both transitions |
| Wall clock rolls backward within one day | Keep keys, monotonic ingest ordering and original age. A backward date change invokes the acquisition guard above |
| Live read after a boundary without an accepted merge | Recompute projection against the new shared `R`, retaining absolute stored keys and original age |
| Captured MCP snapshot or GraphQL subscription event | Preserve the projection as of capture/event time. A captured MCP snapshot retains the documented five-minute TTL; a subscription event remains frozen. Do not reinterpret either under a later reference |
| Location configuration or zone-rule update while running | Reject hot replacement; continue with the accepted immutable context. Changes to process zone settings cannot silently change energy policy. Applying a different context requires restart |
| Restart with a different location or loaded rules | Stop old acquisitions; discard derived relative-window caches and cached live projections. Rebuild against the new context. Never relabel retained absolute points or reuse relative-month replies from the old context; preserve lifetime values and original provenance |
| Evidence restored after restart | A process-local monotonic marker cannot be compared across processes. For the same key and source, treat the first otherwise admissible observation ingested in the new process epoch as causally newer than the restored point, regardless of either marker's numeric value. Once accepted, use the new observation's current-epoch marker for subsequent same-source ordering; restoring an older-epoch point cannot overwrite a current-epoch observation. Source precedence remains unchanged, so a broadcast cannot replace a restored register point. Preserve original UTC evidence and retained values, but mark age Unknown/stale unless a trusted existing persistence mechanism preserves elapsed age. Do not reset restored points to fresh or synthesize monotonic age from a corrected wall clock |

Any derived cache is scoped to the calendar context and reference date; an old
generation or date cannot satisfy a new live projection or relative acquisition.
This adds no persistence/recovery scheme. Values surviving restart depend on
existing persistence support; the proposal requires no store clearing or replay.
Captured artifacts stay frozen rather than being upgraded into live caches.

## Before/after truth table

All instants below are synthetic UTC inputs for civil-date arithmetic. Unless
stated otherwise, the controller-calendar scenario and the proposed location
are `Europe/Berlin`, while the current process calendar is UTC. `D` is the valid
controller daily date, `M` its current month and `P` its previous month.
`I/A/Pj` mean ingest, acquisition and live projection. Ingest does not consume
monthly broadcasts: equality of monthly references below concerns reference
derivation, not new broadcast support. Existing same-source ordering and source
admission are assumed satisfied in these examples.

| Scenario and synthetic UTC instant(s) | Before: documented process-calendar I / A / Pj | After: shared references and dated keys |
| --- | --- | --- |
| Process/controller disagreement: `2028-06-14T22:30Z`; `D=2028-06-15` | I rejects D as process day is June 14; A resolves June/May; Pj selects June 14 today | All use June 15. I accepts `(2028,6,15)` and Pj selects that same day; A resolves M `(2028,6,0)`, P `(2028,5,0)` exactly as Pj |
| Month rollover: `2028-04-30T22:30Z`; `D=2028-05-01` | I rejects D; A resolves April/March; Pj selects April 30 and April/March | All use May 1. I/Pj day `(2028,5,1)`; A/Pj months `(2028,5,0)` and `(2028,4,0)` |
| Year rollover: `2027-12-31T23:30Z`; `D=2028-01-01` | I rejects D; A resolves December/November; Pj selects year 2027 and previous 2026 | All use January 1. I/Pj day `(2028,1,1)`; A/Pj months `(2028,1,0)` and `(2027,12,0)`; I year admission and Pj years agree on `(2028,0,0)` and `(2027,0,0)` |
| DST forward: `2028-03-26T00:30Z` → `2028-03-26T01:30Z` (local 01:30 → 03:30) | All use March 26 for both instants; the missing local hour supplies no distinct date key | All use March 26. I/Pj day `(2028,3,26)`; A/Pj months `(2028,3,0)`, `(2028,2,0)`; age increases by one hour |
| DST back: `2028-10-29T00:30Z` → `2028-10-29T01:30Z` (local 02:30 repeats) | All use October 29 for both instants; process calendar masks the repeated local hour | All use October 29. I/Pj day `(2028,10,29)`; A/Pj months `(2028,10,0)`, `(2028,9,0)`; distinct evidence instants, age increases by one hour |
| Clock rollback across New Year: wall reading `2027-12-31T23:05Z` → `2027-12-31T22:55Z`, with monotonic time advancing | Process reference stays December 31 in all three consumers; no process-date acquisition guard triggers | Shared date January 1 → December 31. I/Pj keys `(2028,1,1)` → `(2027,12,31)`; A/Pj M January → December, P December → November. Abort spanning acquisition; retained future windows survive, original age increases |
| Unknown controller zone, injected `Europe/Berlin`, `2028-06-14T22:30Z`, valid decoded D June 15 | Process-based I rejects D, A uses June/May, Pj today June 14; controller agreement is Unknown | All use June 15, with the same keys as the first row. Agreement with the actual controller calendar stays Unknown; a different decoded day is rejected unchanged |

For the rollback row, the earlier reference's year eligibility is 2028/2027;
the later reference's is 2027/2026. Acquisition and projection compute previous
month by calendar subtraction, never by a fixed elapsed duration. At the two
month/year rollover rows, an acquisition spanning the local boundary aborts
even though the UTC process date has not yet changed. In every row lifetime is
undated, register precedence holds, and no date calculation renews evidence age.

## Acceptance boundary

The tables are a reasoned contract review, not executed gateway tests or device
qualification. B03/C07/C11/F02–F04 characterize or retain existing behavior;
they do not select this missing shared policy. Implementation still needs to
inject and validate the context, exercise every transition including invalid
configuration and restart, establish controller alignment where possible, and
prove monotonic freshness and cache isolation across public consumers. Existing
MCP envelopes, GraphQL parity, admission/trust and partial last-known-good state
must remain intact. Receipts, idempotency, principal boundaries and recovery
redesign remain outside this slice; G5 D1–D5/O8 remain J01–J17-owned. This page
does not close the parent acceptance or claim runtime, full-CI, hardware or
release success.
