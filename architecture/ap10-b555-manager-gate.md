# B555 manager-gate local API

This architecture contract defines a pure Go standard-library function in package
`vaillant`:

```go
func Ab09Ap09Evaluate(ab09ap09Input json.RawMessage) (json.RawMessage, error)
```

The function has no initialization side effect, persistent cache, catalog, listing
API or runtime caller. It changes no state and builds no request. This page defines
a local representation; it does not register a method or change eBUS MCP behavior
or GraphQL parity. It adds neither an API version nor an experimental namespace.

## Evidence boundary

The public [native B555 contract](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#31-sub-command-inventory-candidate)
comes first for wire claims. Its candidate OP00 reply layout and unresolved reply
adaptation do not qualify this software selector. No new native fact follows
from this page. All examples are synthetic and use opaque family labels.
Candidate family and behavior results are Hypothesis. Exact Boolean arithmetic
additionally has calculation=Proven; it never replaces the family grade.
Physical association, support, freshness, effects, persistence and delivery are
Unknown. There is no automatic qualification or live action.

## Input and admission

Input is exactly one JSON object with required object members `context` and
`fields`, and optional object `arguments`. Required view arguments must still be
present for the supported selector. All duplicate keys anywhere (including opaque
objects), malformed JSON, wrong kinds, fractions and out-of-range typed values
produce an error with no successful result. Booleans are not numbers. Null is
accepted only where explicitly allowed. Integral numeric values are accepted
regardless of JSON numeric notation; nonintegral numbers are rejected.

| Selector member | Accepted value | Kind |
|---|---|---|
| primary | 181 | integer |
| secondary | 85 | integer |
| operation | 0 | integer |
| direction | local | string |
| view | manager-gate | string |

This is the only allowed operation/direction/view. Missing selector members,
explicit null and well-typed unsupported selector values return raw-only Unknown,
with no formula applied. Wrong non-null selector kinds are errors. Missing, null
and zero context values remain distinct. Unknown context keys, including opaque
`family` and `variant`, survive verbatim and do not confer native qualification.
Unknown top-level members have no semantic meaning. `fields` maps names to arrays
of integral bytes in 0..255; unknown named arrays survive as raw-only Unknown.
No relay vector is defined for this view. A missing, empty or overlong `reply`
is incomplete, not a JSON admission error. Its valid independent siblings survive.

| Argument | Kind | Range / values | Required for supported view |
|---|---|---|---|
| controller_type | u8 | 0..255 | yes |
| spn | u16 | 0..65535 | yes |
| family_match | Boolean or null | true / false / null | yes |

Unknown argument keys are preserved, including nested objects and arrays. Typed
arguments are validated when supplied even for unsupported selectors. Missing
required arguments are errors for the supported selector. There is no u32
argument in this view; where a u32 is declared its integral range is 0..4294967295.
No Boolean, string, null or array is coerced to another kind.

## Result and formulas

A successful result is a JSON object with `context` unchanged, `raw` as a deep
independent copy of `fields`, `arguments` unchanged if supplied (omitted otherwise),
`state`, semantic `fields`, `physical` equal to `Unknown` and `qualified` false.

| Result path | Presence / shape |
|---|---|
| context | required; unchanged object |
| raw | required; deep independent fields copy |
| arguments | unchanged object if supplied; otherwise omitted |
| state | complete / partial / Unknown |
| fields | required; object of semantic field results |
| physical | required; Unknown |
| qualified | required; false |
| fields.reply.raw | retained if present; omitted if missing |
| fields.reply.state | complete / incomplete / Unknown |
| fields.reply.grade | Hypothesis for supported selector |
| fields.reply.calculation | Proven only for complete supported reply |
| fields.reply.labels | eligible: manager eligibility predicate; first_bit_policy: first-bit caller predicate; complete supported reply only |
| fields.family_role | raw omitted; state complete; grade Hypothesis; label family-role; number 21; supported selector only |
| fields.route_role | raw omitted; state complete; grade Hypothesis; label route-role; number 8; supported selector only |

There is no invented number or label for an absent, unmapped or incomplete value.
Each semantic field retains its own raw value when present; missing raw is omitted,
so missing and empty remain distinguishable through JSON round trips.

| Result member | Formula / value | Grade |
|---|---|---|
| fields.reply.flags.bit0 | (reply[0] & 1) != 0 | Hypothesis; calculation=Proven |
| fields.reply.flags.bit1 | (reply[0] & 2) != 0 | Hypothesis; calculation=Proven |
| fields.reply.reserved | reply[0] & 252 | Hypothesis; calculation=Proven |
| fields.reply.eligible | controller_type == 2 && spn == 385 && family_match == true && bit0 && bit1 | Hypothesis; calculation=Proven |
| fields.reply.first_bit_policy | bit0 | Hypothesis; calculation=Proven |
| fields.reply.family_applicability | Unknown if family_match is null; otherwise supplied Boolean | Hypothesis |
| fields.family_role.number | 21 (0x15) | Hypothesis |
| fields.route_role.number | 8 (0x08) | Hypothesis |

`first_bit_policy` is labelled `first-bit caller predicate`; `eligible` is labelled
`manager eligibility predicate`. They are independent caller policies, not actual
manager state. Both role fields have raw omitted, state=complete, grade=Hypothesis,
and labels `family-role` and `route-role` respectively. Neither constant is an
action target. Role numbers are complete independent siblings even when reply is
incomplete. The exact family prefix, reply adaptation and actual manager state
remain Unknown. No candidate_domain, alternatives or unmodeled calculation is
defined for this view; none should be invented.

For a one-byte reply, `fields.reply` has raw, state=complete, grade=Hypothesis,
calculation=Proven, flags, reserved, eligible, first_bit_policy and
family_applicability. The two predicate labels above are retained in `labels`.
For an incomplete reply it has state=incomplete, grade=Hypothesis, retained raw
when present and eligible=false; flags, reserved, labels, calculation,
first_bit_policy and family_applicability are omitted rather than invented.

| Condition | Result state | Reply state | Roles | Formulas |
|---|---|---|---|---|
| supported, one byte | complete | complete | complete | applied |
| supported, missing reply | partial | incomplete | complete | none |
| supported, empty reply | partial | incomplete | complete | none |
| supported, two or more bytes | partial | incomplete | complete | none |
| unsupported selector | Unknown | Unknown | omitted | none |

Unsupported results retain context, raw and optional arguments; each present raw
field has state=Unknown and its raw value, with no numbers, labels or role fields.
Null family applicability may coexist with complete reply and role fields. Complete
means complete local representation only. Unknown extra byte-array fields remain
raw-only Unknown and do not invalidate known siblings or change overall state.
There is no persistent last-known-good state: every call preserves its supplied raw
and valid independent siblings, never borrows a prior call's data. Input mutation,
returned nested-storage mutation and another call cannot affect each other.

## Synthetic transitions

The tuples below use controller_type=2, spn=385 and family_match=true.

| Reply byte (decimal) | bit0 | bit1 | reserved | eligible | first_bit_policy |
|---|---|---|---|---|---|
| 0 | false | false | 0 | false | false |
| 1 | true | false | 0 | false | true |
| 2 | false | true | 0 | false | false |
| 3 | true | true | 0 | true | true |
| 128 | false | false | 128 | false | false |
| 131 | true | true | 128 | true | true |

With reply 3, controller_type=3, spn=384, family_match=false or family_match=null
independently makes eligible=false. Null leaves family applicability Unknown.
The [scenario file](fixtures/ap10_b555_manager_gate.json) includes independent
selector, argument, raw, malformed-input and storage-preservation cases.
The standard-library suite checks these tables with independent constants and
bounded test-only oracles; it supplies no runtime implementation.

The supplemental ship command is
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap10_b555_manager_gate.py -v`.
It must be run explicitly: the fixed full Gate D list does not discover this suite.
Focused results do not constitute full CI or independent committed-change review.
