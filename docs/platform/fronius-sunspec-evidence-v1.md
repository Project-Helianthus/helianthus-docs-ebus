# Fronius SunSpec Phase-One Evidence Packet V1

## Status and scope

This is the `FMV3-M3-01` evidence packet for issue #397. It records the
documentary boundary for a future Fronius-oriented SunSpec profile in
`helianthus-modbusreg`. It is not an implementation claim, a device
qualification result, a live capture, or permission to start gateway work.

The machine-readable companion is
[`manifests/fronius-sunspec-phase1-v1.json`](./manifests/fronius-sunspec-phase1-v1.json).
Original, synthetic logical-word examples are under
[`fixtures/fronius-sunspec-phase1/v1/`](./fixtures/fronius-sunspec-phase1/v1/).
Their focused contract test is
[`tests/test_fronius_sunspec_phase1_contract.py`](../../tests/test_fronius_sunspec_phase1_contract.py).

This packet refines the evidence and profile boundary in
[`modbus-multivendor-boundaries.md`](./modbus-multivendor-boundaries.md). The
Modbus transport operation boundary remains authoritative in
[`modbus-foundation-profile-contract-v1.md`](./modbus-foundation-profile-contract-v1.md)
and its CC0 wire companion; this packet does not redefine Modbus framing.

## Evidence register

| Source | Inspectable pin | What is used here | Publication treatment |
| --- | --- | --- | --- |
| Fronius *Modbus TCP & RTU* manual | document `42,0410,2649`, edition `033-24022026`; [HTML](https://manuals.fronius.com/html/4204102649/en-US.html), [PDF](https://www.fronius.com/~/downloads/Solar%20Energy/Operating%20Instructions/42%2C0410%2C2649.pdf) | SunSpec base and zero-based address normalization, dynamic chain discovery, FC03, TCP unit ID `0x01`, serial/TCP availability, model-mode families, and request pacing | Independently summarized; no manual pages, tables, or register rows copied |
| Fronius current register package | [QR-link 0024](https://www.fronius.com/QR-link/0024), redirect target `gen24-modbus-api-external-docs.zip`, package `1.2.7-2` | GEN24 Primo/Symo ROW int+SF applicability, Common `1` reported length `65`, inverter `101`/`103` reported length `50`, `Fronius` manufacturer string, and end marker | Source-only. Workbook contents and proprietary register tables are not redistributed |
| SunSpec Models | [github.com/sunspec/models](https://github.com/sunspec/models), commit `7abdf8982d5364f8ae916deee18aac86c11be36d` dated 2026-04-22, Apache-2.0 | Standard Common and inverter model identifiers, declared types, and end-sentinel convention | Independently summarized; model files are not copied |
| SunSpec Device Information Model Specification | [approved version 1.1, 2022-05-09](https://sunspec.org/wp-content/uploads/2025/01/SunSpec-Device-Information-Model-Specificiation-V1-1-final-1.pdf) | Standard integer representation, multi-register ordering, scale-factor semantics, and fixed-width string rules | Independently summarized; specification pages and tables are not copied |

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

## M3-02 implementation boundary

The following is a downstream contract for `FMV3-M3-02`, not evidence that the
code exists:

| M3-02 may implement | M3-02 must not silently implement |
| --- | --- |
| signature/base normalization; bounded chain parser; Common model `1`; models `101`, `102`, `103`; unknown-model structural skip; end sentinel; documented standard signedness, scaling, fixed-width string, and word order; exact raw and sample identity; coherent single-generation observations; source/profile/codec provenance; explicit profile-version gates; transport-neutral activation | float models `111`, `112`, `113`; models `120` through `124`; `160`; `20x`/`21x`; `7xx`; any write/control operation; fixed vendor table addresses; Fronius manufacturer, unit-ID, firmware, or package assumptions inside the standard profile |

An unknown model may be skipped only after its header and declared extent are
validated within the bounded read. It does not establish semantic support, and
an absent end sentinel, malformed length, or overrun is a chain failure.

## Applicability and Fronius overlay disposition

The current Fronius register package directly qualifies only the documented
GEN24 Primo/Symo ROW int+SF map at package `1.2.7-2` / bundle `1.36.x`, subject
to successful runtime chain discovery. The package contains Verto and Tauro
maps, but their phase-one qualification is `UNKNOWN` until separately
admitted and tested. Older Datamanager/SnapINverter products and all live
hardware are also `UNKNOWN`.

The Fronius overlay disposition is **`HYPOTHESIS` / `PENDING_M3_03`**. The
sources establish that manufacturer, model, firmware, and package are plausible
gates; they do not provide a production detector or prove that no overlay is
needed. Therefore no `STANDARD_ONLY` profile conclusion is made here.

`FMV3-M3-03` must replace this pending state with exactly one terminal
disposition: **`STANDARD_ONLY`** or **`OVERLAY_REQUIRED`**. No third terminal
state is valid. `STANDARD_ONLY` adds no production Fronius overlay;
`OVERLAY_REQUIRED` may add only evidence-supported, transport-neutral,
read-only Fronius profile logic. Both paths must retain green standard
conformance and the phase-one no-write boundary.

## Synthetic fixtures

The fixture set is deliberately logical and small. Every JSON file says it is
an original `SYNTHETIC` example under the repository's AGPL documentation lane,
uses placeholder identity, and denies that it is a capture. It contains no
serial number, host, private address, credential, control payload, or copied
vendor register row.

Positive fixtures cover signature/base normalization and a chain, Common model
strings, standard `101`, `102`, and `103` value decoding, unknown-model skip,
the end sentinel, and the observation context that M3-02 must preserve.
Negative fixtures constrain malformed length, extent overrun, missing end
sentinel, invalid scale factors on both sides of the permitted range, and an
unsupported profile version. The model `102` fixture carries the complete
source-observation envelope required by the foundation contract, including
version identities, endpoint/unit identity, ordered raw dependencies,
normalization records, logical/wire response identities, and bounded
multi-response coherence. The fixture values are invented examples chosen to
make decoding errors observable; they do not describe a customer system or a
Fronius device state.

## Open questions and downstream use

| Question | Current disposition | Next use |
| --- | --- | --- |
| Which exact product, firmware, package, and model-chain observations are sufficient for automatic profile admission? | `HYPOTHESIS`; no detector exists | `FMV3-M3-03` overlay/detection evidence |
| Is a Fronius overlay required after a standard chain parser and int+SF decoder exist? | `HYPOTHESIS`; not `STANDARD_ONLY` | `FMV3-M3-03` |
| Are Verto, Tauro, older Datamanager/SnapINverter, or a particular live device eligible? | `UNKNOWN` | Separate admission and sanitized test evidence |
| Can any control model be written? | Outside phase one | A separately authorized write-safety plan |

The manifest maps each durable claim to its sources, fixture IDs,
applicability, disposition, and M3-02/M3-03 use. It deliberately contains no
document hash as an authorization mechanism.
