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

## Provenance and evidence status

**Proven:** the two committed, sanitized fixtures are publishable primary
evidence for the bytes they retain. Their stable SHA-256 values are
`030cbb4fb5cb37dc443e39bb081e5aeff45419e5faf4085fa1da6d2cfe455210`
(descriptions) and
`f54b0802e97bc8baaad3f899f132e633af2fa39c6a99835ad89feb2ee4a22533`
(register observations). Acquisition context is limited to B524
request/response metadata and the exact local controller profile recorded in
the fixture. Export software version and timestamp are **Unknown**.

**Hypothesis:** semantic names, device roles, and installation topology require
separate evidence. **Unknown:** any unretained current value, capture context,
or identity detail. The sanitized raw records are publishable evidence because
they retain only protocol-native metadata and exclude those details.

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
`validation_scope: raw_evidence_only`. Each codec has a fixed span width
(UCH 1, UIN 2, U32 4, EXP 4, HDA:3 3, HTI 3 bytes) that must equal the
description payload length divided by three; a decoded record that disagrees is
rejected.

### Basis of the codec labels

`codec_basis` records why a codec was named for a selector:

| `codec_basis` | Meaning | Evidence status |
| --- | --- | --- |
| `public_local_constraint_codec` | The register map's Wire column for the selector, scoped to the VRC720 family. It does not follow from this fixture's own bytes and does not extend to another family. | **Hypothesis** (a family-scoped catalog label; the retained spans are consistent with it) |
| `public_exact_selector_schema` | Used for the 13 HDA:3/HTI records and one U32 record. The date and time spans read as plain day, month, year-offset and hour, minute, second bytes. | **Hypothesis** (candidate). [ebus-vaillant-B524.md](ebus-vaillant-B524.md) says which codec applies to which date or time register is "not established" and notes BCD for some scalar date fields; [b524-op02-calendar-clock-selectors.csv](fixtures/b524-op02-calendar-clock-selectors.csv) lists the selectors as "candidate, unconfirmed on the wire". |
| `payload_length_inferred` | The codec was guessed from the span width only. | **Unknown**; always `unqualified` |

For the 13 HDA:3/HTI records `qualified` therefore means only that the spans
parse under the candidate codec; it is **Hypothesis**, not **Proven**. STEP stays
unknown (`step: null`). The validator requires the exact-selector-schema basis
for every qualified HDA:3/HTI record and never grants those records range
validation.

### Basis of the other state fields

- `presence_state` (`observed_present`, `observed_inactive`, `unknown`,
  `remote_identity_unqualified`) is the installation topology at acquisition,
  as interpreted for the source installation. Current values are omitted, so it
  cannot be re-derived from the fixture and is **Hypothesis** for any other
  installation. `remote_identity.qualification: unqualified` holds exactly for
  `presence_state: remote_identity_unqualified`, and such a record never carries
  a qualified codec.
- `acquisition_state` in the register-observation fixture links a row to its
  description: `matched` (the retained description answers the selector),
  `unavailable` (no description was returned) and `unqualified` (a description
  is retained but the source acquisition did not qualify it; in the retained
  fixture all 36 such rows have `decoded: null`). `unqualified` is retained
  raw evidence, not a failed read; it grants no codec or range. This is
  **Proven** for the retained rows only.
- `validation_scope` records the source installation's interpretation of how far
  a description could be used. It defines no display behavior and no edit
  validation for any consumer. The derivation is, **Proven** against the
  retained records: `format_range_and_step` if and only if the record is
  `observed_present` and has a qualified, selector-qualified
  `public_local_constraint_codec`; `display_only` for the other qualified
  selector-qualified codecs (inactive or unknown instances, and every HDA:3/HTI
  record); `raw_evidence_only` otherwise. A consumer derives presence from its
  own current evidence, not from this field. An application-side reuse contract
  lives in the repository's AGPL development tree and is linked from the
  repository README; the CC0 tree does not link into it.

## Observed local bound

**Proven (within the retained bytes):** the local DHW bivalence selector
`(02, 00, 00, 0001)` has raw description `0001000000A0C10000A0410000803F`. Under
its selector-qualified EXP codec (a **Hypothesis** codec basis, see above), the
observed bounds are `-20`, `20`, and `1`. This is a BASV0 profile observation.
Neither value applies to another software revision or installation configuration
without its own profile-qualified evidence.

**Hypothesis (corroborating implementation evidence):** an application bundle
observation reports `-20`, `50`, and `1` for the same selector on a BASV2
controller. No BASV2 bytes, software or hardware identity, or raw description
are retained here, so this is not a profile observation and cannot be falsified
from this repository. It resembles the register map's historical short-probe
range hint (`-20..50`, see
[ebus-vaillant-B524-register-map.md](ebus-vaillant-B524-register-map.md)),
which "must not provide input-validation authority". Neither the BASV2 figure
nor the hint qualifies a range for BASV0 or any other profile.

## Explicitly retained uncertainty

The `OP02/GG04/II01/RR000B` description has the same raw body as the qualified
`II00` U32 observation, but the II01 codec cannot be selected from width or
numeric order. It remains unqualified. Empty-looking descriptions at local
system selectors `006C`, `006D`, `006F`, and `0070` likewise remain raw
metadata; their zero-valued UCH interpretation does not establish a numeric
parameter or a text codec.

**Proven (within the retained bytes):** for local ventilation
`OP02/GG09/II00..II0A/RR0001`, the observed read body has width two for all
eleven instances, and the description spans are two bytes wide. The
profile-qualified UIN decoding is consistent with that numeric response
(**Hypothesis** codec basis, see above). A UCH-sized interpretation is rejected
for this profile.

**Unknown:** the observed instance state (`presence_state: unknown`) does not
establish ventilation equipment; there is no positive-presence predicate in this
evidence.

Remote entries retain their native group and optional remote-header metadata.
A disconnected or identity-unqualified remote entry is metadata evidence, not
proof that a device function exists. Unknown names are represented by JSON
`null`; a missing description or limit is represented by `null`, never by a
substituted default.

## Scope

This is a reusable native evidence record. It does not define application
profile selection, display behavior, edit validation, write behavior, or a
universal B524 topology. The `validation_scope` field records only the source
installation's interpretation and defines no display behavior; consumers must
apply their own explicit qualification contract; the AGPL development tree
holds one such contract, linked from the repository README.
