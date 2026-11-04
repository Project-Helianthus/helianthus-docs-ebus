# Standard 09 body views

> AGPL-3.0 architecture contract for the `ab25an25` pure helper. This page
> defines a software view. It does not restate the native service family, does
> not add native qualification, and does not import a code change.

Nothing in this helper is stable before Helianthus 1.0. The page adds no major
namespace and no experimental namespace. It adds no authorization gate. No
authorization gate is introduced before 0.9. Roadmap wording for a later gate,
if one is ever written, is 0.11 and is outside this contract.

This page is the ordinary AN26 companion of AN25. It has no dependency on a
code change. It adds no MCP tool and no GraphQL field. Existing eBUS MCP
compatibility and GraphQL parity are unchanged because both faces gain nothing
here.

Protocol background is the public native contract
[Service 0x09](../protocols/ebus-services/ebus-service-09h.md). Native physical
offsets and the relevance of a positive prefix remain Unknown. The helper does
not copy that family page and does not newly qualify it.

## Scope

`ab25an25` exposes three pure views over an explicitly selected positive
logical object whose service token is `0900`, `0901`, `0902`, or `0903`.

The views do not perform a memory operation. They do not open a read client or
a write client. They do not poll. They do not run a verification sequence.
They do not strip a universal header. They do not read or write a stored
last-known-good record. On every non-represented admission they return the
supplied raw bytes and synthesize no replacement body, address, or count.

A caller that still holds an older raw object keeps that object outside this
helper. The helper's result is only the current input plus the admission below.

The same inputs always produce the same outputs. The helper has no clock, no
network, and no stored installation identity.

## Grades

Grades are independent. A Proven arithmetic result is not a Proven meaning, and
neither is native qualification, presence, freshness, or execution.

| Grade | What it covers in this helper | What it does not cover |
| --- | --- | --- |
| Proven | Software admission, the pure-helper boundary, little-endian uint16 arithmetic on exactly two supplied bytes, and preservation of a u8 count in `0..255` | Wire qualification, peer acceptance, physical support |
| Hypothesis | Layout meaning, address meaning, count meaning, and the `0902` candidate recommendation maximum `10` | A license to execute or to label a memory space |
| Unknown | Native physical offsets, positive-prefix relevance, execution support, physical support, peer acceptance, and response support | A default success or a default rejection |

Software admission is fail-closed. Incomplete, unknown, and unmatched inputs
stay raw. None of them is a successful execution.

## Signatures

These signatures are hypothetical. They are the names used by this contract.
They are not a claim that a library package already exports them.

```
ab25an25.ViewStandard09Body(selection, object)
ab25an25.ViewStandard09Address(selection, delimited)
ab25an25.ViewStandard09Count(selection, count)
```

`selection` and the object's identity carry `family`, `profile_variant`,
`service`, and `direction`. The address and count views take the same selection
plus a separate identity record with those four fields. `delimited` is the
address field the caller has already cut out. `count` is one integer.

## Inputs

`family` is a device-family token supplied by the caller. Examples use the
synthetic token `ebus-module`. The helper does not publish a model name and
does not treat the token as a qualified native family list.

`profile_variant` is a caller token. Examples use the synthetic token
`standard-09`. Equality with the selection is the whole profile rule. Which
tokens exist on a device is Unknown.

`service` is one of `0900`, `0901`, `0902`, and `0903` for a defined view.
`direction` is the token `positive` for a defined view. Any other service or
direction stays unviewed.

`object_state` is `complete`, `incomplete`, or `unknown`.

`logical_bytes` is an ordered sequence of integer byte values `0..255`. The
helper does not expand escapes and does not search a surrounding frame.

The address view's only byte input is `delimited`. A decoy packet and a decoy
offset are not view inputs. The helper must not slice them.

The count view's only numeric input is one integer `0..255`.

Match is exact on every identity field that this contract lists: `family`,
`profile_variant`, `service`, and `direction`. A mismatch is `unmatched`. The
helper then keeps the raw bytes, sets no typed body, and sets execution to
`not_executed`.

Admission order for the body view is closed:

1. If any identity field differs between `selection` and the object, admission is `unmatched`.
2. If `object_state` is `incomplete`, admission is `incomplete`.
3. If `object_state` is `unknown`, admission is `unknown`.
4. If `direction` is not `positive`, or `service` is outside the four tokens, admission is `unknown`.
5. Otherwise apply the service rule. A prefix failure on `0900`, `0901`, or `0903` is `incomplete`.

Address and count use the same identity match, then the same positive-service
gate, then their own width or domain rule. Count on `0901` or `0903` is
`inapplicable`. That is not a global rejection of the byte: `rejected` stays
false and the raw integer is kept.

## Body views

Meaning of every represented layout below is Hypothesis. Execution stays
`not_executed`. `mutation_success` stays false. `native_success_claim` stays
false. `peer_acceptance`, `physical_support`, `native_physical_offset`, and
`positive_prefix_relevance` stay Unknown.

`0900` and `0903`, when the identity matches and the object is complete, use
constants at logical positions 0 and 1. Position 0 is byte `09`. Position 1 is
`00` for `0900` and `03` for `0903`. Opaque data starts at position 2. Zero
data bytes are a representable local object. They do not imply peer acceptance
or response support. A shorter sequence, or any other two leading bytes, stays
raw with admission `incomplete`. No maximum data length is inferred. The
unknown maximum is not a claim that every length is native.

`0901` declares only those two constants: byte `09` then byte `01`. It has no
typed data field. Bytes after the constants are an unresolved raw extension,
including a zero-length extension. An extension is not a newly typed body.

`0902` opaque data starts at position 0. The view does not infer PB or SB
constants. The bytes `09 02` inside that data are ordinary bytes. They are not
stripped. A zero-length sequence is a representable empty data view and carries
no native success claim.

No service inherits another service's prefix rule. In particular, a helper that
removes two leading bytes from every service is outside this contract.

## Address view

The address view is optional and separate. It consumes an already delimited
field. It invents no packet offset. It labels no physical memory space.
`packet_offset` and `address_space` stay null. Meaning is Hypothesis.
Arithmetic on the supplied bytes is Proven. Physical support and execution
stay Unknown.

`0900` and `0901` require exactly two bytes and expose one little-endian
uint16: `low + (high * 256)`. The synthetic field `34 12` is low `52` and high
`18`, and the integer is `4660`. One byte, zero bytes, or three bytes stay
raw with admission `incomplete` and no integer.

`0902` and `0903` require exactly two bytes and expose separate `low_u8` and
`high_u8` values. The same synthetic field stays low `52` and high `18`. The
view does not also emit `4660` and does not treat that integer as an
equivalent address. A wrong width stays raw and incomplete.

Changing the low byte, the high byte, or the width changes the result by
itself. The other bytes and the other identity fields stay as supplied.

## Count view

`0900` and `0902` preserve a u8 count in the formal domain `0..255`. The values
`0`, `10`, `11`, and `255` stay distinct. The helper does not clip and does
not reject the object globally.

`0902` also carries a candidate recommendation maximum of `10`. That candidate
conflicts with the formal full-byte domain. The conflict is Hypothesis. For
`0902`, a value above `10` keeps its raw value and its preserved value, and
records `value_outside_candidate_recommendation`. Value `11` stays raw `11`
with that conflict. It is not clipped to `10`. Values `0` and `10` stay inside
the candidate and still remain distinct from `11` and from `255`.

`0900` does not attach the `0902` conflict record. `0901` and `0903` do not
grow a count field. Their count admission is `inapplicable`, the raw integer
is kept, and `rejected` is false.

## States

Body and address admissions are only `represented`, `incomplete`, `unknown`,
and `unmatched`. Count admissions are those of a count plus `inapplicable`.
`execution` is only `not_executed`. There is no success state.

`represented` means a local view exists. It does not mean a device accepted a
mutation, a peer answered, or a physical access occurred.

`local_representation` is true only for `represented`. `typed_data` is
`opaque` only when a body rule defines opaque data (`0900`, `0902`, `0903`).
For `0901` it is null. `data` is the opaque byte copy, or null when the
service has no typed data or the admission is not `represented`.
`unresolved_tail` is the `0901` extension copy, or null for every other
service and for every non-represented `0901` result.

Returned byte sequences are new sequences. Later mutation of the caller's
buffer does not change them, and two calls do not share a sequence.

## Examples

Synthetic tokens only. Hex bytes in this table are the logical sequence.
Grades on a represented numeric address or count are Proven arithmetic,
Hypothesis meaning, and Unknown native support. Body rows have no numeric
claim (`not_applicable`), Hypothesis meaning, and Unknown native support.
Every row has execution `not_executed`.

| Id | Service | Bytes or field | Local result |
| --- | --- | --- | --- |
| body-0900-aa55 | `0900` | `09 00 AA 55` | opaque data `AA 55` |
| body-0903-aa55 | `0903` | `09 03 AA 55` | opaque data `AA 55` |
| body-0902-aa55-kept | `0902` | `09 02 AA 55` | opaque data is all four bytes |
| body-0901-constants-only | `0901` | `09 01` | no typed data; unresolved tail empty |
| body-0901-unresolved-aa | `0901` | `09 01 AA` | no typed data; unresolved tail `AA` |
| body-0900-truncated | `0900` | `09` | raw, incomplete |
| body-0901-truncated | `0901` | `09` | raw, incomplete |
| body-0903-truncated | `0903` | `09` | raw, incomplete |
| body-0900-prefix-mismatch | `0900` | `08 00 AA 55` | raw, incomplete |
| body-0901-prefix-mismatch | `0901` | `09 00` | raw, incomplete |
| body-0903-prefix-mismatch | `0903` | `09 02 AA 55` | raw, incomplete |
| body-0902-empty | `0902` | empty | empty data view; no native success claim |
| body-0900-prefix-only | `0900` | `09 00` | empty opaque data; not a successful mutation |
| address-0900-3412 | `0900` | `34 12` | little-endian `4660` |
| address-0901-3412 | `0901` | `34 12` | little-endian `4660` |
| address-0902-3412 | `0902` | `34 12` | low `52`, high `18`; no combined integer |
| address-0903-3412 | `0903` | `34 12` | low `52`, high `18`; no combined integer |
| count-0902-0 | `0902` | `0` | value `0`, inside the candidate |
| count-0902-10 | `0902` | `10` | value `10`, inside the candidate |
| count-0902-11 | `0902` | `11` | raw `11`, conflict, not clipped |
| count-0902-255 | `0902` | `255` | value `255`, conflict, distinct from `11` |

The machine-readable fixture
`architecture/fixtures/an26_standard09_body_views.json` repeats these rows and
the single-field variants. Identity variants change one of family, profile,
service, or direction and stay `unmatched` or, when both sides share a
non-positive direction, `unknown`.

## Unknowns

- Native physical offsets of any byte in these views.
- Whether a positive prefix is relevant on the wire.
- Whether any peer accepts a local object, including a zero-length one.
- Whether any peer supports a response.
- Execution support and physical support.
- The native maximum length of opaque data. This page infers none.
- Which family tokens and profile tokens a device implements.
- Service-mode policy. This helper does not decide it.
- Equivalence between a split byte pair and a little-endian integer. This page
  does not create that equivalence.

## Normative denials

- universal prefix removal: denied
- inferring 0902 PB/SB: denied
- prefix-only positive implies successful mutation: denied
- clipping 11 to 10: denied
- inventing a packet offset: denied
- address-space equivalence: denied
- accepting a mismatched service: denied

## Machine-readable rules

The block is the parameter set the focused checks execute. Prose denials stay
in force beside it.

```json
{
  "contract_id": "an26-standard09-body-views",
  "helper": "ab25an25",
  "signatures": [
    "ab25an25.ViewStandard09Body(selection, object)",
    "ab25an25.ViewStandard09Address(selection, delimited)",
    "ab25an25.ViewStandard09Count(selection, count)"
  ],
  "match_fields": ["family", "profile_variant", "service", "direction"],
  "universal_prefix_removal": false,
  "infer_0902_pb_sb": false,
  "prefix_only_positive_means_successful_mutation": false,
  "clip_count_11_to_10": false,
  "invent_packet_offset": false,
  "address_space_equivalence": false,
  "accept_mismatched_service": false,
  "empty_opaque_is_representable": true,
  "reject_outside_candidate": false,
  "body_rules": {
    "0900": {"kind": "constants_then_opaque", "pb": 9, "sb": 0, "data_start": 2},
    "0901": {"kind": "constants_only", "pb": 9, "sb": 1},
    "0902": {"kind": "opaque_from_start", "data_start": 0, "strip_prefix": false},
    "0903": {"kind": "constants_then_opaque", "pb": 9, "sb": 3, "data_start": 2}
  },
  "address_rules": {
    "0900": {"form": "leu16", "endian": "little", "width": 2, "packet_offset": null, "address_space": null},
    "0901": {"form": "leu16", "endian": "little", "width": 2, "packet_offset": null, "address_space": null},
    "0902": {"form": "split_u8", "width": 2, "packet_offset": null, "address_space": null, "leu16_equivalent": false},
    "0903": {"form": "split_u8", "width": 2, "packet_offset": null, "address_space": null, "leu16_equivalent": false}
  },
  "count_rules": {
    "0900": {"domain": "u8-0-255", "preserve": true, "candidate_recommendation_maximum": null, "clip_above": null},
    "0902": {"domain": "u8-0-255", "preserve": true, "candidate_recommendation_maximum": 10, "clip_above": null}
  },
  "grades": {
    "software_admission": "Proven",
    "arithmetic": "Proven",
    "meaning": "Hypothesis",
    "native": "Unknown"
  }
}
```
