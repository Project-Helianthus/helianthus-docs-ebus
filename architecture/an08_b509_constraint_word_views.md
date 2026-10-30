# B509 OP33 constraint word views

This page is a software contract for one pure helper. It selects the B509 OP33
positive alternative and interprets caller-supplied address strings and five
word slices. It is not a native family page. Native register-access material
stays on the [B509 register-access page](../protocols/vaillant/ebus-vaillant-B509.md).
This page does not restate that material. This page does not qualify a device.

The full finite example set is the
[constraint-word fixture](fixtures/an08_b509_constraint_word_views.json).
The examples are synthetic. They are not device observations, captures, or
installation records.

The signature below is hypothetical and is used consistently by this contract.
This documentation establishes the API contract before implementation.
Implementation must follow this contract. The checks use a local reference
helper and import no production module.

```text
interpret_b509_op33_positive_alternative(selection, addresses, words) -> view
```

Nothing here is a new major or experimental namespace. This software contract is not a stable interface before Helianthus 1.0. Roadmap wording for anything beyond this helper, if it is written later, is 0.11. This page does not open that work. This helper is not an authorization gate. This helper adds no GraphQL field and no MCP tool.

## Grades

Numeric word decoding is **Hypothesis**: signed little-endian 16-bit values
with no scale. The factor is a raw signed field under the same **Hypothesis**,
not a converter. Retaining a negative step, a zero factor, a default outside
the supplied bounds, and a minimum greater than the maximum is **Hypothesis**.
Those values stay candidate data.

These helper behaviors are **Proven** software contract: each word is decoded
on its own; raw bytes stay with that word; a missing or malformed word does
not clear its siblings; raw address equality is only a local byte comparison;
a mismatch does not grant requested edit bounds; the helper does not grant
edit bounds when the bytes match either; the call does not change a shared
cache or an admitted constraint store; OP32 does not share the OP33 word view;
returned raw bytes are detached copies.

These subjects stay **Unknown**: physical adaptation, exact packet association,
universal family applicability, the factor algorithm, writability, peer
enforcement, and native echo rules. Native qualification is **Unknown**.
Presence of a decoded candidate is not freshness, execution, or peer
acceptance.

## Normative keys

| key | value | numeric grade | semantic grade | native grade |
| --- | --- | --- | --- | --- |
| selected_family | B509 | none | Proven | Unknown |
| selected_variant | positive | none | Proven | Unknown |
| selected_operation | OP33 | none | Proven | Unknown |
| op32_token | OP32 | none | Proven | Unknown |
| op32_role | address-status-query | none | Hypothesis | Unknown |
| op32_result | not-shared-with-op33 | none | Proven | Unknown |
| word_signedness | signed | Hypothesis | Hypothesis | Unknown |
| word_endian | little-endian | Hypothesis | Hypothesis | Unknown |
| word_width_bytes | 2 | Hypothesis | Hypothesis | Unknown |
| word_scale | none | Hypothesis | Hypothesis | Unknown |
| factor_role | raw-signed-field | Hypothesis | Hypothesis | Unknown |
| min_above_max | retain-supplied-order | Hypothesis | Hypothesis | Unknown |
| negative_step | retain-candidate | Hypothesis | Hypothesis | Unknown |
| zero_factor | retain-candidate | Hypothesis | Hypothesis | Unknown |
| default_outside_bounds | retain-candidate | Hypothesis | Hypothesis | Unknown |
| partial_malformed | siblings-remain | none | Proven | Unknown |
| independent_word_decode | per-word | none | Proven | Unknown |
| address_mismatch_edit_bounds | not-granted | none | Proven | Unknown |
| edit_bounds_on_match | not-granted | none | Proven | Unknown |
| local_address_equality | raw-bytes-only | none | Proven | Unknown |
| returned_raw | detached-copy | none | Proven | Unknown |
| shared_cache | unchanged | none | Proven | Unknown |
| constraint_store | unchanged | none | Proven | Unknown |
| address_width | unspecified | Unknown | Proven | Unknown |
| packet_offsets | unspecified | Unknown | Proven | Unknown |
| native_echo | unresolved | Unknown | Unknown | Unknown |
| native_success | not-reported | Unknown | Proven | Unknown |
| native_qualification | unresolved | Unknown | Unknown | Unknown |
| universal_family_applicability | unresolved | Unknown | Unknown | Unknown |
| factor_algorithm | unresolved | Unknown | Unknown | Unknown |
| writability | unresolved | Unknown | Unknown | Unknown |
| peer_enforcement | unresolved | Unknown | Unknown | Unknown |
| physical_adaptation | unresolved | Unknown | Unknown | Unknown |
| packet_association | unresolved | Unknown | Unknown | Unknown |

In this table, numeric grade `none` means the row is not a numeric claim.

Unsigned conversion is outside this contract. Big-endian conversion is outside this contract. The factor is not a converter and does not scale the other words. Minimum greater than maximum is not rejected and is not reordered. One malformed word does not erase the other words. An address mismatch does not grant the requested edit bounds.

## Inputs

`selection` has four fields: `family`, `variant`, `operation`, and
`direction`. Each field is either a string or missing. Selection tokens are exact and case-sensitive. The selected tokens are family `B509`, variant
`positive`, and operation `OP33`. Direction is echoed and may be an empty
string. An empty direction is present. A missing direction is not.

This selection is the helper's input gate. It is not native proof that another
family lacks a similar operation. Universal family applicability is
**Unknown**.

`addresses.requested` and `addresses.returned` are opaque byte strings or
missing. The caller supplies them already separated. This contract defines no
address width and no packet offset. An empty string is present and has length
zero. Missing is a different state. Examples represent a byte string as a
sequence of integers from 0 through 255.

`words` has five independent slices in this order: `minimum`, `maximum`,
`default`, `step`, and `factor`. A slice is missing, or it is a present byte
sequence of any length. The caller supplies the field boundaries. The helper
does not search a packet for them.

## Outputs

Every call returns one view and changes no other state.

`result_kind` is one of `op33-positive-alternative`,
`op32-address-status-query`, `selection-incomplete`, or
`selection-not-admitted`.

- Operation `OP32` returns `op32-address-status-query` even when another
  selection field is missing. OP32 is an address-status query under
  **Hypothesis**. OP32 does not share the OP33 word view. `words` is null and
  `shares_op33_result` is false. This separation is **Proven** for the helper.
- Otherwise, a missing `family`, `variant`, `operation`, or `direction`
  returns `selection-incomplete`. `words` is null. The helper does not invent
  the selected tokens.
- Otherwise, a present token other than `B509`, `positive`, or `OP33` returns
  `selection-not-admitted`. `words` is null.
- The remaining input returns `op33-positive-alternative`. `words` contains
  one result for each of the five fields, and `shares_op33_result` is true.

The echoed `selection` contains only those four fields. Address comparison is
still returned for every result kind.

Each address is `present` or `missing`. A present address includes its
detached raw bytes and its length. `local_equal` is true only when both
addresses are present and the raw sequences are equal, including two empty
sequences. Native echo is `Unknown`. Native success is not reported. Empty address strings stay explicit, and native success is not invented.

`grants_requested_edit_bounds` is false for every result. `admitted_minimum`
and `admitted_maximum` are null. Matching bytes are not permission to edit.
Writability and peer enforcement remain **Unknown**. Admission is fail-closed.

A word state is `missing`, `malformed`, or `decoded`.

- Missing keeps a null raw sequence and a null number. Its numeric grade is
  **Unknown**.
- A present slice decodes only when it is exactly two byte values, each from
  0 through 255. Any other present slice, including length 0, 1, or 3, or a
  value outside that byte range, is `malformed`. Its raw sequence is kept.
  Its number is null. Its numeric grade is **Unknown**.
- A decoded word's number is the signed little-endian 16-bit interpretation
  of those two bytes, with scale null. Its numeric grade is **Hypothesis**.
  Its semantic grade is **Proven** for the helper's independent retention of
  that field. Its native grade is **Unknown**.

Returned raw bytes are detached copies. Changing the caller's sequence after
the call does not change the view, and changing the view does not change the
caller. A second call does not read or write the first call's view. The shared
cache and the admitted constraint store stay unchanged.

The view's native grade is **Unknown**. Its semantic grade is **Proven**. Its
numeric grade is **Hypothesis** when at least one word decoded, and
**Unknown** when the view has no decoded word.

## Published examples

The rows below repeat the acceptance examples. The fixture holds these rows
and the isolated variations of every selection field, every address byte,
address length and presence, and every word value, length, and presence.

| case | field | raw bytes | state | signed le16 | numeric grade | semantic grade | native grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| extremes | minimum | 00 80 | decoded | -32768 | Hypothesis | Proven | Unknown |
| extremes | maximum | FF 7F | decoded | 32767 | Hypothesis | Proven | Unknown |
| extremes | default | FF FF | decoded | -1 | Hypothesis | Proven | Unknown |
| extremes | step | 02 00 | decoded | 2 | Hypothesis | Proven | Unknown |
| extremes | factor | 00 00 | decoded | 0 | Hypothesis | Proven | Unknown |
| min10-max5 | minimum | 0A 00 | decoded | 10 | Hypothesis | Proven | Unknown |
| min10-max5 | maximum | 05 00 | decoded | 5 | Hypothesis | Proven | Unknown |
| min10-max5 | default | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| min10-max5 | step | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| min10-max5 | factor | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| factor-one-byte | minimum | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| factor-one-byte | maximum | 02 00 | decoded | 2 | Hypothesis | Proven | Unknown |
| factor-one-byte | default | 03 00 | decoded | 3 | Hypothesis | Proven | Unknown |
| factor-one-byte | step | 04 00 | decoded | 4 | Hypothesis | Proven | Unknown |
| factor-one-byte | factor | 02 | malformed | none | Unknown | Proven | Unknown |
| factor-two | minimum | 0A 00 | decoded | 10 | Hypothesis | Proven | Unknown |
| factor-two | maximum | 05 00 | decoded | 5 | Hypothesis | Proven | Unknown |
| factor-two | default | 07 00 | decoded | 7 | Hypothesis | Proven | Unknown |
| factor-two | step | 09 00 | decoded | 9 | Hypothesis | Proven | Unknown |
| factor-two | factor | 02 00 | decoded | 2 | Hypothesis | Proven | Unknown |
| negative-step | minimum | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| negative-step | maximum | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| negative-step | default | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| negative-step | step | FF FF | decoded | -1 | Hypothesis | Proven | Unknown |
| negative-step | factor | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| zero-factor | minimum | 04 00 | decoded | 4 | Hypothesis | Proven | Unknown |
| zero-factor | maximum | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| zero-factor | default | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| zero-factor | step | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| zero-factor | factor | 00 00 | decoded | 0 | Hypothesis | Proven | Unknown |
| default-outside | minimum | 00 00 | decoded | 0 | Hypothesis | Proven | Unknown |
| default-outside | maximum | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| default-outside | default | 64 00 | decoded | 100 | Hypothesis | Proven | Unknown |
| default-outside | step | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| default-outside | factor | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| address-mismatch | minimum | 0A 00 | decoded | 10 | Hypothesis | Proven | Unknown |
| address-mismatch | maximum | 14 00 | decoded | 20 | Hypothesis | Proven | Unknown |
| address-mismatch | default | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| address-mismatch | step | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| address-mismatch | factor | 01 00 | decoded | 1 | Hypothesis | Proven | Unknown |
| all-malformed | minimum | empty | malformed | none | Unknown | Proven | Unknown |
| all-malformed | maximum | 11 | malformed | none | Unknown | Proven | Unknown |
| all-malformed | default | 01 02 03 | malformed | none | Unknown | Proven | Unknown |
| all-malformed | step | 04 05 06 07 | malformed | none | Unknown | Proven | Unknown |
| all-malformed | factor | 08 | malformed | none | Unknown | Proven | Unknown |

## Address examples

| case | requested | returned | local equal | grants edit bounds | native success |
| --- | --- | --- | --- | --- | --- |
| base | 10 20 | 10 20 | true | false | none |
| both-empty | empty | empty | true | false | none |
| requested-missing | missing | 10 20 | false | false | none |
| returned-missing | 10 20 | missing | false | false | none |
| address-mismatch | 01 02 | 01 09 | false | false | none |

## Result examples

| case | result kind | shares op33 | words | direction | numeric grade | semantic grade | native grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | op33-positive-alternative | true | present | request | Hypothesis | Proven | Unknown |
| direction-response | op33-positive-alternative | true | present | response | Hypothesis | Proven | Unknown |
| direction-empty | op33-positive-alternative | true | present | empty | Hypothesis | Proven | Unknown |
| op32-extremes | op32-address-status-query | false | none | read | Unknown | Proven | Unknown |
| family-b510 | selection-not-admitted | false | none | request | Unknown | Proven | Unknown |
| family-missing | selection-incomplete | false | none | request | Unknown | Proven | Unknown |

## Unknowns

Physical adaptation, the packet that would carry these slices, whether any
other family uses the same helper selection, the algorithm that would turn
`factor` into a conversion, writability, and peer enforcement are
**Unknown**. A decoded candidate does not establish those claims.

## Companion

AN07 is a related companion. This page owns the B509 OP33 helper contract; it
neither defines nor requires the companion API.
