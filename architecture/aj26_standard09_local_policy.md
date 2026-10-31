# Separate standard 09 local policies (AJ26)

This bounded pre-1.0 software candidate is **Hypothesis**. It defines separate
refresh, forwarding and client verification decisions, not runtime behavior.
Nothing here is stable before 1.0. Refs #833; partial child of #736, which stays
open. The supplied issue contract is the source of the local candidate rules.

## Native evidence boundary

Consult the public native contract first:
[secondary channel](../protocols/weishaupt/kromschroeder-5000.md#4-secondary-channel-09020903)
and [standard profiles](../protocols/vaillant/ebus-vaillant.md#standard-ebus-protocols).
Those family-specific accounts do not establish the local refresh, forwarding
or verification policy below. Native behavior remains **Unknown** for this
candidate. No primary capture or device observation is supplied. No protocol
fact is promoted from these synthetic checks. **Proven** is reserved for claims
with supporting native evidence; it is not the grade of this candidate.
Physical qualification is independently **Unknown**.

## Optional refresh

After successful identification, an optional 0902 refresh sets address `0000`
and count `09`. Stop at the first success or after two attempts. Failure retains
identification success and any partial last-known-good state, including raw
values. It does not replace those values with absence or fabricate fresh data.
No active request, polling default or execution is introduced.

| Refresh input | Attempts | Identification | Optional refresh |
| --- | --- | --- | --- |
| fail, success | 2 | success | success |
| success | 1 | success | success |
| fail, fail, success | 2 | success | failed |

The trailing synthetic success in the last row is never consumed. Physical
effect, periodicity and service-mode meaning are **Unknown**.

## Forwarding

All hexadecimal selectors below are synthetic values, not a probe list.
Keep variant, direct/scheduled path, request/reply direction, operation,
destination and remaining data selector separate. A selector pass alone grants
no admission. Both variants retain all structural predicates below, combined
with logical AND. An unknown variant, path or direction fails closed locally.

| Variant | Operation | Destination | Selector predicate |
| --- | --- | --- | --- |
| A | 0902 | 35 | pass |
| A | 0902 | 15 | fail |
| A | 0903 | 15 | pass |
| A | 0903 | 35 | fail |
| B | any | any | absent |

A's predicate applies on direct and scheduled paths; remaining data selectors
are unconstrained by that predicate. B lacks that predicate only: it is not
universal admission and does not assert support for any operation or target.
The scenario oracle's `selector=true` for B means no selector veto.

| Structural field | Required predicate |
| --- | --- |
| extent | 5 <= extent <= 21 |
| nn | nn + 5 == extent |
| request_length | request_length <= 16 |
| reply_length | reply_length <= 21 |
| role_ok | true |
| state_ok | true |
| capacity_ok | true |

Extent and NN describe the current synthetic frame. Request and reply lengths
are separate envelope bounds of the synthetic transaction, checked in both
directions. Role, state and capacity are abstract local predicate results;
their internal rules are unprovided and **Unknown**. This is no authorization
gate. Local no-match length `0` establishes neither transmission nor ACK; both
remain **Unknown**. Retain that raw length rather than inferring a bus result.

## Separate client and verification

A separate client candidate explicitly sets 0902 low address, high address and
count before consuming returned raw data. Do not infer blocksize or extra
endian rules: both are **Unknown**. Preserve low/high fields separately.
A 0903 client candidate iterates address/data pairs and optionally verifies with
0902. Each pair retains its own address, raw data and outcome; partial successes
and last-known-good data survive a later failure. No aggregate success may
hide a mismatch or an unverified pair.

| Positive 0903 | Verify requested | 0902 comparison | Result |
| --- | --- | --- | --- |
| true | true | mismatch | positive_unverified |
| true | true | match | synthetic_verified |
| true | false | match | positive_unverified |
| false | true | match | not_positive |

A positive 0903 alone is not verification. Matching data satisfies only the
synthetic comparison, never physical execution, controller receipt or native
qualification. Verify=false retains the positive/unverified distinction.

## Scope and checks

[Scenarios](fixtures/aj26_standard09_local_policy.json) use synthetic tuples only.
[Standard-library checks](../tests/test_aj26_standard09_local_policy.py) compare
page tables and scenarios to independent transition and arithmetic expectations.
No memory client, writer, authorization gate or forwarder is implemented. eBUS
MCP compatibility and GraphQL parity are unaffected because no runtime or API is changed.
The candidate preserves existing naming and release boundaries.
No authorization gate is introduced before 0.9; any roadmap discussion belongs to 0.11.
Full ship gates and transport qualification are separate later requirements;
these checks establish no physical result.
