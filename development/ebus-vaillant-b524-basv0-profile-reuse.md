# BASV0 B524 description-profile reuse

The BASV0 metadata fixture (the CC0 record is
[ebus-vaillant-b524-basv0-profile-v1.md](../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md))
is a candidate input to application profile reuse. It may be selected only after
the local EID, software raw value, hardware raw value, API version, and revision
match the fixture identity. A selector match without that profile match must not
reuse a bound or codec. The bundled-baseline states (`not_verified`, `matches`,
`differs`, `unavailable`, `profile_mismatch`), the slot-identity rule and the
recheck behavior are defined once in
[VRC Explorer discovery and descriptions](ebus-vaillant-b524-explorer-discovery.md#bundled-metadata-and-rechecking)
and apply unchanged to this fixture; this page does not restate them.

`DescribeParameter` and `DescribeDeviceParameter` echo group and register and
have equal-width limit spans. That proves response structure, not the value
codec. The consumer may use a decoded range only when the fixture labels it
`selector_qualified` and `qualified`; otherwise it must preserve the raw bytes
and expose no range-based validation authority. The `public_local_constraint_codec`
basis is itself a **Hypothesis** (a VRC720-family register-map correspondence), so a
consumer that uses a decoded range on a `selector_qualified`, `qualified` record relies
on that hypothesis.

**Proven (within the retained bytes):** the observed BASV0 DHW bivalence maximum
is 20. **Hypothesis (corroborating implementation evidence):** an application
bundle observation reports a maximum of 50 for a BASV2 controller; no BASV2
bytes or identity are published, and it resembles the register map's historical
short-probe range hint (`-20..50`), which the register map's legend says
"requires a matching complete OP01/OP07 description before validating edits"
and which the B524 protocol page says "must not provide input-validation
authority". Selection must not substitute either value across profiles, software
versions, or installation configurations.

**Proven (within the retained bytes):** for the BASV0 ventilation
`OP02/GG09/II00..II0A/RR0001` observations, the profile-qualified UIN decoder
uses a two-byte response while presence remains unknown. Treating that response
as one-byte UCH, or treating an unknown slot as installed ventilation, is unsupported.
Remote descriptions whose identity is unqualified are `raw_evidence_only`. They do not admit a device function or write path.

The profile itself has no current values and no write evidence. A consumer must
keep access flags distinct from write acceptance and use an independently
qualified, current interaction before attempting a write.

## `validation_scope` and presence

**Proven** (against the retained fixture, and enforced by the validator in both
directions): `validation_scope` is a field of the source installation's
interpretation, kept only so the classification stays identical to the copy
bundled with VRC Explorer 0.6.2. It lives in the application overlay
[b524-basv0-validation-scope-v1.json](fixtures/b524-basv0-validation-scope-v1.json)
(schema [b524-basv0-validation-scope-schema-v1.json](fixtures/b524-basv0-validation-scope-schema-v1.json)),
keyed by selector, and no longer in the CC0 description fixture. The validator
loads the overlay when present, requires one entry per description record and no
entry without a record, and enforces the derivation below. It is specific to that installation's presence
interpretation and is not reusable authority. Its derivation is:

| `validation_scope` | Holds exactly when |
| --- | --- |
| `format_range_and_step` | the record's `presence_state` is `observed_present` and its codec is `qualified`, `selector_qualified`, with basis `public_local_constraint_codec` |
| `display_only` | the codec is qualified and selector-qualified, but the instance is `observed_inactive` or `unknown`, or the basis is `public_exact_selector_schema` (every HDA:3/HTI record) |
| `raw_evidence_only` | otherwise: no description, no decoded codec, or an unqualified codec |

A consumer must derive presence from its own current evidence, never from the
fixture's `presence_state` or the overlay's `validation_scope`, and must recompute the
equivalent decision itself. A field value of `format_range_and_step` therefore
never admits an edit by itself. HDA:3/HTI records stay candidate (**Hypothesis**)
and their STEP stays **Unknown**, so they never receive range-and-step
validation from this fixture.
