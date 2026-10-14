# B524 BASV0 parameter-description profile v1

This profile is a sanitized, read-only metadata observation for the native B524
selector namespace. It is identified as `basv0_sw0217_hw8803_api1`; its local
identity is EID `BASV0`, software raw value `0217`, hardware raw value `8803`,
API version `1` and revision `1` (encoded together as raw `API1`). These fields identify the observation context. They do
not identify a product article, installation, or every controller carrying an
EID `BASV0`.

The machine-readable record is
[b524-basv0-description-profile-v1.json](fixtures/b524-basv0-description-profile-v1.json).
It retains `(OP, GG, II, RR)`, local or remote identity scope, raw description
bytes, access flags when observed, and the explicit qualification of any codec
or limits. It contains no current register values, network endpoints, serial
numbers, capture time, contributor identity, or acquisition fingerprint.

[b524-basv0-register-observations-v1.json](fixtures/b524-basv0-register-observations-v1.json)
separately retains every bounded scalar selector without retaining its current
value. `echo_payload`, `status_only`, and `transport_error` remain distinct;
in particular, a status-only `00` is not promoted to a register value or device
function. Its explicit `description: null` is retained when no description was
available.

## Native description format

For a local OP02 selector, the corresponding description request is OP01. For
a remote OP06 selector, it is OP07. A description response begins with `GG,
RRlo, RRhi`; the remaining bytes split into equal-width `MIN`, `MAX`, and
`STEP` spans. The echoed fields and equal spans establish response structure.
They do not select a codec, prove the requested instance, prove a present
device, or authorize a write.

The fixture records the raw three spans even when no codec is qualified. A
decoded record with `codec_provenance: selector_qualified` can be marked
`qualified`; a length-inferred codec remains `unqualified` and has
`validation_scope: raw_evidence_only` or `display_only`.

## Observed local bound

The local selector `(02, 00, 00, 0001)` has raw description
`0001000000A0C10000A0410000803F`. Under its selector-qualified EXP codec, the
observed bounds are `-20`, `20`, and `1`. This is a BASV0 profile observation.
The separate BASV2 observation has `-20`, `50`, and `1`; neither value applies
to another software revision or installation configuration without its own
profile-qualified evidence.

## Explicitly retained uncertainty

The `OP02/GG04/II01/RR000B` description has the same raw body as the qualified
`II00` U32 observation, but the II01 codec cannot be selected from width or
numeric order. It remains unqualified. Empty-looking descriptions at local
system selectors `006C`, `006D`, `006F`, and `0070` likewise remain raw
metadata; their zero-valued UCH interpretation does not establish a numeric
parameter or a text codec.

For local ventilation `OP02/GG09/RR0001`, the observed read body has width two.
The profile-qualified UIN decoding is supported for that numeric response. The
observed unknown instance state still does not establish ventilation equipment;
there is no positive-presence predicate in this evidence. A UCH-sized
interpretation is rejected for this profile.

Remote entries retain their native group and optional remote-header metadata.
A disconnected or identity-unqualified remote entry is metadata evidence, not
proof that a device function exists. Unknown names are represented by JSON
`null`; a missing description or limit is represented by `null`, never by a
substituted default.

## Scope

This is a reusable native evidence record. It does not define application
profile selection, display behavior, edit validation, write behavior, or a
universal B524 topology. Those consumers must apply their own explicit
qualification contract.
