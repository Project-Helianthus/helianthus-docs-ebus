# BASV0 B524 description-profile reuse

The BASV0 metadata fixture (the CC0 record is
[ebus-vaillant-b524-basv0-profile-v1.md][source-1]) is a candidate input to
application profile reuse. It may be selected only after the local EID, software
raw value, hardware raw value, API version, and revision match the fixture
identity. A selector match without that profile match must not reuse a bound or
codec. The bundled-baseline states (`not_verified`, `matches`, `differs`,
`unavailable`, `profile_mismatch`), the slot-identity rule and the recheck
behavior are defined once in [Application discovery and descriptions][source-2]
and apply unchanged to this fixture; this page does not restate them.

`DescribeParameter` and `DescribeDeviceParameter` echo group and register and
have equal-width limit spans. That proves response structure, not the value
codec. The consumer may use a decoded range only when the fixture labels it
`selector_qualified` and `qualified`; otherwise it must preserve the raw bytes
and expose no range-based validation authority. The
`public_local_constraint_codec` basis is itself a **Hypothesis** (a
VRC720-family register-map correspondence), so a consumer that uses a decoded
range on a `selector_qualified`, `qualified` record relies on that hypothesis.
Selector-qualified codec acceptance is validator vocabulary, distinct from the
evidence grade of the codec basis or decoded limits.

**Proven (within the retained bytes):** the BASV0 DHW bivalence maximum span is
`0000A041`. **Hypothesis (codec basis):** decoding it with EXP gives a maximum
of 20. **Hypothesis (corroborating implementation evidence):** an application
bundle observation reports a maximum of 50 for a BASV2 controller; no BASV2
bytes or identity are published, and it resembles the register map's historical
short-probe range hint (`-20..50`), which the register map's legend says
"requires a matching complete OP01/OP07 description before validating edits" and
which the B524 protocol page says "must not provide input-validation authority".
Selection must not substitute either value across profiles, software versions,
or installation configurations.

**Hypothesis (derived, non-reproducible from the retained artifact):** for the
BASV0 ventilation `OP02/GG09/II00..II0A/RR0001` observations, the
profile-qualified UIN decoder uses a two-byte response while presence remains
unknown. Native headers and response payloads were not retained, so falsifying
the width or presence state requires a new acquisition. Treating that response
as one-byte UCH, or treating an unknown slot as installed ventilation, is
unsupported. Remote descriptions whose identity is unqualified are
`raw_evidence_only`. They do not admit a device function or write path.

The profile itself has no current values and no write evidence. A consumer must
keep access flags distinct from write acceptance and use an independently
qualified, current interaction before attempting a write.

The application's plain-byte calendar and clock decoding consumes the neutral
`DATE_DMY_U8X3` and `TIME_HMS_U8X3` candidates. These are not the packed-BCD
`HDA:3`/`HTI` types documented in [types/ebusd-csv.md][source-3]. The
application-side classification never grants those candidates range validation.
Aligning the application codec labels with the documented types is tracked in
external issue #297 of the evidence-producing tool's repository.

## `validation_scope` and presence

**Proven** (against the retained fixture, and enforced by the validator in both
directions): `validation_scope` is a field of the source installation's
interpretation, kept only so the classification stays identical to the copy
bundled with the source application. It lives in the application overlay
[b524-basv0-validation-scope-v1.json][source-4] (schema
[b524-basv0-validation-scope-schema-v1.json][source-5]), keyed by selector, and
no longer in the CC0 description fixture. The validator loads the overlay when
present, requires one entry per description record and no entry without a
record, and enforces the derivation below. It is specific to that installation's
presence interpretation and is not reusable authority. Its derivation uses these
rules:

- `format_range_and_step`: `presence_state` is `observed_present`, and the codec
  is `qualified`, `selector_qualified`, with basis
  `public_local_constraint_codec`.
- `display_only`: the codec is qualified and selector-qualified, but presence is
  `observed_inactive` or `unknown`, or the basis is
  `public_exact_selector_schema` (every plain-byte calendar/clock record).
- `raw_evidence_only`: otherwise, with no description, no decoded codec, or an
  unqualified codec.

A consumer must derive presence from its own current evidence, never from the
fixture's `presence_state` or the overlay's `validation_scope`, and must
recompute the equivalent decision itself. A field value of
`format_range_and_step` therefore never admits an edit by itself.
DATE_DMY_U8X3/TIME_HMS_U8X3 records stay candidate (**Hypothesis**) and their
STEP stays **Unknown**, so they never receive range-and-step validation from
this fixture.

[source-1]:
  ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md
[source-2]:
  ebus-vaillant-b524-explorer-discovery.md#bundled-metadata-and-rechecking
[source-3]:
  ../types/ebusd-csv.md
[source-4]:
  fixtures/b524-basv0-validation-scope-v1.json
[source-5]:
  fixtures/b524-basv0-validation-scope-schema-v1.json
