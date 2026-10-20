# B524 BASV0 parameter-description profile v1

This profile is a sanitized, read-only metadata observation for the native B524
selector namespace. It is identified as `basv0_sw0217_hw8803_api1`; its local
identity is EID `BASV0`, software raw `0217`, hardware raw `8803`, API version
raw `1` and API revision raw `1`. **Hypothesis (derived):** `software_raw`,
`hardware_raw`, `api_version_raw`, and `api_revision_raw` come from the
acquisition session, not the retained description bytes. The API values are
recorded separately as read from system-information registers `0006h` and
`0007h`, respectively; those read bytes are not retained. These identity claims
cannot be re-derived from the retained artifact; falsifying them requires a new
acquisition. They identify the observation context, not a product article,
installation, or every controller carrying an EID `BASV0`, and do not establish
codec qualification.

The machine-readable record is
[b524-basv0-description-profile-v1.json][source-1]. It retains `(OP, GG, II,
RR)`, local or remote identity scope, raw description bytes, access flags when
observed, and the explicit qualification of any codec or limits. It contains no
current register values, network endpoints, serial numbers, capture time,
contributor identity, or acquisition fingerprint.

## Provenance and evidence status

The SHA-256 values authenticate the two derived JSON artifacts only:
`23f8f3a95315920b4746b7d7e70b648e73c1da8bb2734450e9ac34e77b6ae1cb`
(descriptions) and
`70a9194788779a7d1e47ef05a83e1d583b83b72cc8643b744b44ee5f5570db86` (register
observations). **Proven** applies only to facts within the retained description
bytes. Native headers (source, destination, direction) and response payloads
were not retained by the sanitized export. Consequently,
`observed_payload_width`, `response_state`, and `presence_state` are
**Hypothesis** (derived, non-reproducible from the retained artifact) facts of
the acquisition session; falsifying them requires a new acquisition. The
description fixture's `observed_read_payload_width` has the same evidence limit.

**Hypothesis:** semantic names, device roles, and installation topology require
separate evidence. **Unknown:** any unretained current value, capture context,
or identity detail. The sanitized raw records are publishable evidence because
they retain only protocol-native metadata and exclude those details.

[b524-basv0-register-observations-v1.json][source-2] separately retains every
bounded scalar selector without retaining its current value. `echo_payload`,
`status_only`, and `transport_error` remain distinct; in particular, a
status-only `00` is not promoted to a register value or device function. Its
explicit `description: null` is retained when no description was available.

## Native description format

For a local OP02 selector, the corresponding description request is OP01. For a
remote OP06 selector, it is OP07. A description response begins with `GG, RRlo,
RRhi`; the remaining bytes split into equal-width `MIN`, `MAX`, and `STEP`
spans. The echoed fields and equal spans establish response structure. They do
not select a codec, prove the requested instance, prove a present device, or
authorize a write.

**Hypothesis (derived, non-reproducible from the retained artifact):** for a
selector carried in both register-map namespaces, the retained fields alone
cannot distinguish the request opcode; the published fixture bytes are pinned by
the page-cited SHA-256, so a reassignment cannot be published silently, and the
local-only qualification rule rejects a qualified remote claim because no
retained evidence ties a remote description to a codec.

The response does not echo the instance byte `II`, and the fixture retains no
request bytes, so the retained material cannot prove which instance a
description answers; the semantic selector is the only link. A qualified decoded
range is therefore accepted only where it is identical across every retained
described instance of the selector `(OP, GG, RR)`: the raw limits and
description length must be byte-identical for all instances that retain a
description. An instance without a description is absent evidence and takes no
part in the comparison. The validator rejects a qualified claim in an instance-
divergent family. The retained fixture has no such family (all 340 are
instance-invariant over their described instances). Divergent spans, if a later
profile retains any, are raw evidence only. The validator also requires every
catalog record, with or without description bytes, to have a
register-observation record for its selector.

Of the 40 selector families with qualified records, 21 retain only one
described instance. Those 21 satisfy cross-instance invariance trivially
(vacuously): there is no second described instance to compare. Neither a
single-instance pass nor agreement across multiple retained instances recovers
the omitted request bytes or proves the request-to-instance association.
Selector qualification does not establish those missing bytes or prove the
codec; its evidence basis remains separate, as described below. The comparison
concerns retained description ranges within each `(OP, GG, RR)` family, not
instance presence or behavior at unobserved instances.

The fixture records the raw three spans even when no codec is qualified. A
decoded record with `codec_provenance: selector_qualified` can be marked
`qualified`; a length-inferred codec remains `unqualified`. Selector-qualified
codec acceptance is validator vocabulary, distinct from the evidence grade of
the codec basis or decoded limits. Each codec has a fixed span width (`UCH` 1,
`UIN` 2, `U32` 4, `EXP` 4, `DATE_DMY_U8X3` 3, `TIME_HMS_U8X3` 3 bytes) that
must equal the description payload length divided by three; a decoded record
that disagrees is rejected.

### Basis of the codec labels

`codec_basis` records why a codec was named for a selector:

| `codec_basis` | Evidence status |
| --- | --- |
| `public_local_constraint_codec` | **Hypothesis** |
| `public_exact_selector_schema` | **Hypothesis** |
| `payload_length_inferred` | **Unknown** |

`public_local_constraint_codec` names the register map's Wire column for the
selector, scoped to the VRC720 family. This family-scoped catalog label does not
follow from this fixture's own bytes or extend to another family; the retained
spans are consistent with it.

`public_exact_selector_schema` covers the 13 plain-byte calendar/clock records
and one U32 record. The date and time spans read as day, month, year-offset and
hour, minute, second bytes. These are candidate layouts:
[ebus-vaillant-B524.md][source-3] says which codec applies to which date or time
register is "not established" and notes BCD for some scalar date fields. The
[b524-op02-calendar-clock-selectors.csv][source-4] list calls the selectors
"candidate, unconfirmed on the wire".

`payload_length_inferred` guesses the codec from the span width only and is
always `unqualified`.

The validator pins every codec that claims selector provenance to its selector,
whether or not the record is qualified (qualification governs only reuse
authority, not what the cited source contains); a retained fixture has no
unqualified record that claims selector provenance. A
`public_local_constraint_codec` must equal the register map's Wire column for
that `(OP, GG, RR)` (u8 UCH, u16 UIN, u32 U32, f32 EXP) and a selector with no
Wire entry is rejected; an exact-selector-schema codec must equal the codec the
calendar/clock selector list implies (date `DATE_DMY_U8X3`, time
`TIME_HMS_U8X3`). The fourteen exact-schema selectors are listed below as
`(OP, GG, II, RR)`; OP02 and OP06 remain distinct namespaces:

- `(02, 00, 00, 002C)`
- `(02, 00, 00, 0034)`
- `(02, 00, 00, 0035)`
- `(02, 00, 00, 00DA)`
- `(02, 00, 00, 00DB)`
- `(02, 00, 00, 00F2)`
- `(02, 00, 00, 00F3)`
- `(02, 00, 00, 00F4)`
- `(02, 00, 00, 00F5)`
- `(02, 01, 00, 0009)`
- `(02, 01, 00, 000A)`
- `(02, 01, 00, 0010)`
- `(02, 01, 00, 0011)`
- `(02, 04, 00, 000B)`

Eight of these selectors (`GG00 RR002C`, `RR00F2..RR00F5`,
`GG01 RR0010/RR0011`, and the U32 `GG04 RR000B`) are absent from the
calendar/clock list; for them the register map's Wire column is the pin. The
validator accepts the exact-selector-schema basis only for these fourteen
selectors, requires every one of them to keep it, and rejects it anywhere else;
decoded numeric limits must be numbers, never booleans. A calendar value must
be a valid date (year offset 0-99 from 2000) and a clock value a valid time
(hour 0-23, minute and second 0-59) before `qualified` is kept.

**Hypothesis (candidate layouts).** Each calendar or clock byte is a plain
unsigned integer. The codec names describe the retained layouts:

| Codec | Bytes per span | Candidate layout |
| --- | --- | --- |
| `UCH` | 1 | Unsigned integer |
| `UIN` | 2 | Unsigned integer, little-endian |
| `U32` | 4 | Unsigned integer, little-endian |
| `EXP` | 4 | Floating point, little-endian |
| `DATE_DMY_U8X3` | 3 | Day, month, year offset from 2000 |
| `TIME_HMS_U8X3` | 3 | Hour, minute, second |

These neutral date and time codecs are not the packed-BCD `HDA:3`/`HTI` types in
[types/ebusd-csv.md][source-5]. For example, the date maximum `1F0C63` reads as
2099-12-31 and the time maximum `173B3B` as 23:59:59 under these candidate
layouts; neither span is valid packed BCD.

For the 13 DATE_DMY_U8X3/TIME_HMS_U8X3 records `qualified` therefore means only
that the spans parse under the candidate codec; it is **Hypothesis**, not
**Proven**. STEP stays unknown (`step: null`). The validator requires the
exact-selector-schema basis for every qualified DATE_DMY_U8X3/TIME_HMS_U8X3
record and never grants those records range validation.

### Basis of the other state fields

- `presence_state` (`observed_present`, `observed_inactive`, `unknown`,
  `remote_identity_unqualified`) is the installation topology at acquisition, as
  interpreted for the source installation: **Hypothesis** (derived,
  non-reproducible from the retained artifact). Native headers and response
  payloads were not retained, so falsifying this state requires a new
  acquisition. Current values and request bytes are omitted, so the sanitized
  fixtures cannot independently establish instance presence. This source-
  installation interpretation follows the recorded instance; description-range
  invariance does not qualify it. It cannot be re-derived from the fixture and
  is **Hypothesis** for any other installation.
  `remote_identity.qualification: unqualified` holds exactly for
  `presence_state: remote_identity_unqualified`, and such a record never carries
  a qualified codec.
- `acquisition_state` in the register-observation fixture links a row to its
  description: `matched` (the retained description answers the selector),
  `unavailable` (no description was returned) and `unqualified` (a description
  is retained but the source acquisition did not qualify it; in the retained
  fixture all 36 such rows have `decoded: null`, and the validator requires
  that). `unqualified` is retained raw evidence, not a failed read; it grants no
  codec or range. This is **Hypothesis** (derived, non-reproducible from the
  retained artifact) for the acquisition session. Native headers and response
  payloads were not retained, so falsifying the acquisition outcome requires a
  new acquisition; the retained links alone do not prove it.
- This fixture carries no validation-scope field. How far a description may be
  used is an application decision, not wire evidence, so the classification the
  source installation applied is kept outside this CC0 tree, in an overlay under
  the repository's AGPL development tree that the validator loads when present.
  A consumer derives presence from its own current evidence, not from
  `presence_state`. The application-side reuse contract lives in the same AGPL
  tree and is linked from the repository README; the CC0 tree does not link into
  it.

## Observed local bound

**Proven (within the retained bytes):** the local DHW bivalence selector `(02,
00, 00, 0001)` has raw description `0001000000A0C10000A0410000803F`.

**Hypothesis (codec basis):** under its selector-qualified EXP codec, the
decoded minimum, maximum, and step are `-20`, `20`, and `1`; the retained
maximum bytes alone prove only `0000A041`. This is a BASV0 profile observation.
None of these decoded limits applies to another software revision or
installation configuration without its own profile-qualified evidence.

**Hypothesis (corroborating implementation evidence):** an application bundle
observation reports `-20`, `50`, and `1` for the same selector on a BASV2
controller. No BASV2 bytes, software or hardware identity, or raw description
are retained here, so this is not a profile observation and cannot be falsified
from this repository. It resembles the register map's historical short-probe
range hint (`-20..50`; its legend in
[ebus-vaillant-B524-register-map.md][source-6] says the hint "requires a
matching complete OP01/OP07 description before validating edits").
[ebus-vaillant-B524.md][source-7] says the historical short probe "must not
provide input-validation authority". Neither the BASV2 figure nor the hint
qualifies a range for BASV0 or any other profile.

## Explicitly retained uncertainty

The `OP02/GG04/II01/RR000B` description has the same raw body as the qualified
`II00` U32 observation, but the II01 codec cannot be selected from width or
numeric order. It remains unqualified. Empty-looking descriptions at local
system selectors `006C`, `006D`, `006F`, and `0070` likewise remain raw
metadata; their zero-valued UCH interpretation does not establish a numeric
parameter or a text codec.

**Hypothesis (derived, non-reproducible from the retained artifact):** for local
ventilation `OP02/GG09/II00..II0A/RR0001`, the observed read body has width two
for all eleven instances. Native headers and response payloads were not
retained, so falsifying that width requires a new acquisition. **Proven (within
the retained description bytes):** the description spans are two bytes wide.
The profile-qualified UIN decoding is consistent with the derived response width
(**Hypothesis** codec basis, see above). A UCH-sized interpretation is rejected
for this profile.

**Unknown:** the observed instance state (`presence_state: unknown`) does not
establish ventilation equipment; there is no positive-presence predicate in this
evidence.

Remote entries retain their native group and optional remote-header metadata; an
`observed_remote_header` entry must retain its group, address and firmware
fields, which the schema and validator require, and all entries of one remote
(OP, GG, II) slot must retain the same identity qualification and, when
observed, the same address and firmware, which the validator checks. The
retained fixture is homogeneous in all slots (six observed-header slots, the
rest unqualified). The register-observation fixture likewise retains one
presence state per remote slot, and a qualified codec width must equal the
observed read payload width in both fixtures; the validator rejects either
contradiction. A disconnected or identity-unqualified remote entry is metadata
evidence, not proof that a device function exists. Unknown names are represented
by JSON `null`; a missing description or limit is represented by `null`, never
by a substituted default.

## Scope

This is a reusable native evidence record. It does not define application
profile selection, display behavior, edit validation, write behavior, or a
universal B524 topology. Consumers must apply their own explicit qualification
contract; the AGPL development tree holds one such contract, linked from the
repository README.

[source-1]:
  fixtures/b524-basv0-description-profile-v1.json
[source-2]:
  fixtures/b524-basv0-register-observations-v1.json
[source-3]:
  ebus-vaillant-B524.md
[source-4]:
  fixtures/b524-op02-calendar-clock-selectors.csv
[source-5]:
  ../../types/ebusd-csv.md
[source-6]:
  ebus-vaillant-B524-register-map.md
[source-7]:
  ebus-vaillant-B524.md
