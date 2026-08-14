# Fronius SunSpec Phase-One Evidence Packet V1

## Status and scope

This is the `FMV3-M3-01` evidence packet for issue #397. It records a legacy qualification harness and documentary boundary, not a Fronius-oriented support
profile in `helianthus-modbusreg`. Its companion manifest retains the
`helianthus.fronius-sunspec.phase1-evidence` schema and this packet's original
provenance. A separate `m3_03_completion` object records the later issue #401
terminal disposition. This packet is not a device qualification result, a live
capture, or permission to start gateway work.

The machine-readable companion is
[`manifests/fronius-sunspec-phase1-v1.json`](./manifests/fronius-sunspec-phase1-v1.json).
Original, synthetic logical-word examples are under
[`fixtures/fronius-sunspec-phase1/v1/`](./fixtures/fronius-sunspec-phase1/v1/).
Their focused contract test is
[`tests/test_fronius_sunspec_phase1_contract.py`](../../tests/test_fronius_sunspec_phase1_contract.py).

This packet refines the evidence and legacy-harness boundary in
[`modbus-multivendor-boundaries.md`](./modbus-multivendor-boundaries.md). The
Modbus transport operation boundary remains authoritative in
[`modbus-foundation-profile-contract-v1.md`](./modbus-foundation-profile-contract-v1.md)
and its CC0 wire companion; this packet does not redefine Modbus framing.

## Evidence register

| Source | Inspectable pin | What is used here | Publication treatment |
| --- | --- | --- | --- |
| Fronius *Modbus TCP & RTU* manual | document `42,0410,2649`, edition `033-24022026`; [HTML](https://manuals.fronius.com/html/4204102649/en-US.html), [PDF](https://www.fronius.com/~/downloads/Solar%20Energy/Operating%20Instructions/42%2C0410%2C2649.pdf); PDF SHA-256 `aa1e69432472ae2f25075c01a651201f747ae0f9e85c8894dfa1f36883d06890` | SunSpec base and zero-based address normalization, dynamic chain discovery, FC03, TCP unit ID `0x01`, serial/TCP availability, model-mode families, and request pacing | Independently summarized; no manual pages, tables, or register rows copied |
| Fronius current register package | [QR-link 0024](https://www.fronius.com/QR-link/0024), redirect target `gen24-modbus-api-external-docs.zip`, package `1.2.7-2`, ZIP SHA-256 `dc4c5d49362ee0c9721f21886f17fa18497e54c4d92bb5cc2c50472deb266b55` | GEN24 Primo/Symo ROW int+SF applicability, Common `1` reported length `65`, inverter `101`/`103` reported length `50`, `Fronius` manufacturer string, and end marker | Source-only. Workbook contents and proprietary register tables are not redistributed |
| SunSpec Models | [github.com/sunspec/models](https://github.com/sunspec/models), commit `7abdf8982d5364f8ae916deee18aac86c11be36d` dated 2026-04-22, Apache-2.0 | Standard Common and inverter model identifiers, declared types, and end-sentinel convention | Independently summarized; model files are not copied |
| SunSpec Device Information Model Specification | version `1.2` reference | Standard integer representation, multi-register ordering, scale-factor semantics, and fixed-width string rules | Independently summarized; specification pages and tables are not copied |

The package changelog ties `1.2.7-0` and `1.2.7-1` to GEN24 `1.36.x`; `1.2.7-2`
fixes the Model `124` `OutWRte` unit reference. That is source qualification,
not a claim that Model `124` is supported in phase one.

## Confirmed documentary behavior

The following claims are `PROVEN` only within their stated applicability in the
manifest:

- The SunSpec PDU base register is `40001`; the zero-based Modbus request
  address for that register is `40000` (`0x9c40`). `40001` is a register
  number, not a Modbus function code.
- Actual model positions are dynamic. A reader discovers the model chain and
  derives each model position from the preceding header and declared length;
  it must not treat a published table start as a universal fixed address.
- Fronius inverter TCP uses unit ID `0x01`. The manual also describes serial
  and TCP interfaces. This phase-one packet does not admit an RTU deployment.
  The unit ID is an acquisition/applicability fact and must not be embedded in
  the transport-neutral standard profile implemented by M3-02 or in Fronius
  profile logic decided by M3-03. It is retained only for future gateway
  acquisition work beyond the current hard stop; M3-02 fixtures use a
  runtime-supplied abstract unit identity.
- The Fronius manual identifies FC03 for the listed SunSpec holding-register
  reads. Phase one remains read-only even where the vendor materials describe
  writable controls.
- The manual advises at least a one-second timeout and sequential requests,
  with at most two concurrent requests. These are vendor operational guidance;
  they do not relax the shared runtime scheduler or recovery contract.
- The model chain begins with the SunSpec signature and Common model, continues
  with inverter and optional standard models, and ends at model ID `0xffff`
  with length `0`.
- The selectable float inverter family is `111`/`112`/`113`; the selectable
  integer-plus-scale-factor family is `101`/`102`/`103`.

The standard-model source identifies the admitted fields and types. The SunSpec
Device Information Model Specification defines the required decoder semantics:
two's-complement `int16`, big-endian multi-register `acc32`, `sunssf` scaling,
fixed-width strings, and wire-order 16-bit words. An invalid scale-factor
sentinel is not a numeric scale, and a `sunssf` exponent outside `-10` through
`10` is invalid. Either case must fail the affected typed value rather than be
interpreted as zero or applied as an unbounded exponent.

The two-word `SunS` signature occupies PDU-base word offsets `0` and `1`; the
first model header therefore begins at offset `2`. A fixed-width string ends at
the first NUL byte. Bytes after that terminator are not emitted, including
non-NUL residue; a full-width field with no NUL consumes its declared width.

## M3-02 implementation boundary

The M3-02 merge
[`867c8275c090d3c703a9638548b48ea6846e8c56`](https://github.com/Project-Helianthus/helianthus-modbusreg/commit/867c8275c090d3c703a9638548b48ea6846e8c56)
implements every proven phase-one standard behavior below. This is a
provenance reference, not an authorization mechanism. No evidence in this
packet proves a Fronius-specific delta or detector for that behavior.

| M3-02 may implement | M3-02 must not silently implement |
| --- | --- |
| signature/base normalization; bounded chain parser; Common model `1`; models `101`, `102`, `103`; unknown-model structural skip; end sentinel; documented standard signedness, scaling, fixed-width string, and word order; exact raw and sample identity; coherent single-generation observations; source/profile/codec provenance; explicit profile- and codec-version gates; transport-neutral activation | float models `111`, `112`, `113`; models `120` through `124`; `160`; `20x`/`21x`; `7xx`; any write/control operation; fixed vendor table addresses; Fronius manufacturer, unit-ID, firmware, or package assumptions inside the standard profile |

An unknown model may be skipped only after its header and declared extent are
validated within the bounded read. It does not establish semantic support, and
an absent end sentinel, malformed length, or overrun is a chain failure.

## M3-03 completion and applicability

The current Fronius register package directly qualifies only the documented
GEN24 Primo/Symo ROW int+SF map at package `1.2.7-2` / bundle `1.36.x`, subject
to successful runtime chain discovery. The package contains Verto and Tauro
maps, but their phase-one qualification is `UNKNOWN` until separately
admitted and tested. Older Datamanager/SnapINverter products and all live
installations are also `UNKNOWN`.

The only current M3-03 conclusion is **`STANDARD_ONLY`**.
The M3-02 implementation above contains all proven standard behavior, and this
packet contains no evidence for a Fronius-specific delta or a product detector.
No production Fronius overlay, detector, automatic product qualification, write capability, TCP production dependency, authorization effect, or runtime effect is admitted.
The companion completion record is
[`Project-Helianthus/helianthus-modbusreg#12`](https://github.com/Project-Helianthus/helianthus-modbusreg/pull/12),
whose completion schema is `helianthus.fmv3-m3-03-completion.v2`, version `2`.
The merge SHA and PR link are provenance references only.
The hard stop is before `FMV3-M4-01`.

`FSS-C-007` remains a retained **`HYPOTHESIS`**: manufacturer, model, firmware,
and package are candidate detector gates for future research. It is explicitly
forbidden from production use, does not qualify any product automatically, and
is not an unresolved M3-03 gate. The terminal `STANDARD_ONLY` disposition is
therefore compatible with preserving this historical/evidentiary research
claim.

Issue #436 supersedes neither the synthetic fixtures nor this retained legacy
qualification harness. It defines a generic model-chain contract separately.
This packet is not a Fronius support claim, has no live result, and can only
feed a future registry-selected outcome after separately implemented registry
selection and admissible evidence.

## Synthetic fixtures

The fixture set is deliberately logical and small. Every JSON file says it is
an original `SYNTHETIC` example under the repository's AGPL documentation lane,
uses placeholder identity, and denies that it is a capture. It contains no
serial number, host, private address, credential, control payload, or copied
vendor register row.

Positive fixtures cover signature/base normalization and a chain, Common model
strings, standard `101`, `102`, and `103` value decoding, unknown-model skip,
the end sentinel, and the observation context that M3-02 must preserve.
Negative fixtures constrain signature and end-header validity, malformed
length, extent overrun, missing end sentinel, invalid scale factors on both sides of the permitted range, and
unsupported profile and codec versions. Chain fixtures carry bounded raw
logical words, including the `SunS` signature, so downstream parsers must derive
headers, offsets, and failures rather than trusting decoded metadata. The model `102` fixture carries the complete
source-observation envelope required by the foundation contract, including
version identities, endpoint/unit identity, ordered raw dependencies,
normalization records, logical/wire response identities, and bounded
multi-response coherence. The fixture values are invented examples chosen to
make decoding errors observable; they do not describe a customer system or a
Fronius device state.

## Open questions and downstream use

| Question | Current disposition | Next use |
| --- | --- | --- |
| Which exact product, firmware, package, and model-chain observations are sufficient for automatic profile admission? | `HYPOTHESIS` for future research only; no automatic qualification or detector is admitted | Separate evidence and sanitized tests, outside this completion |
| Is a Fronius-specific delta required after the standard chain parser and int+SF decoder exist? | No delta is evidenced; `STANDARD_ONLY` | Separate evidence if a future delta is observed |
| Are Verto, Tauro, older Datamanager/SnapINverter, or a particular live device eligible? | `UNKNOWN` | Separate admission and sanitized test evidence |
| Can any control model be written? | Outside phase one | A separately authorized write-safety plan |

The manifest maps each durable claim to its sources, fixture IDs,
applicability, disposition, and M3-02/M3-03 use. It deliberately contains no
document hash as an authorization mechanism.
