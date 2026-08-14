# SunSpec Model-Chain Contract V1

## Scope and source boundary

This implementation-neutral contract defines how a future SunSpec reader keeps
the wire-discovered structure separate from typed interpretation, capability
admission, and vendor evidence. It is an independent summary, not a copy of
upstream definitions: this page must not copy model files, DIM tables,
specification text, Fronius manuals, or vendor workbook/register tables.

The source pins below make the claimed catalog inspectable while preserving the
source licenses and publication boundaries.

- SunSpec Models: `sunspec/models` commit
  `7abdf8982d5364f8ae916deee18aac86c11be36d`, Apache-2.0. The identifiers,
  names, and declared lengths summarized here are independently stated facts.
- SunSpec Device Information Model Specification v1.2: reference only. Its
  presentation and tables are not reproduced or relicensed here.
- Fronius *Modbus TCP & RTU* manual `42,0410,2649`, edition `033-24022026`,
  PDF SHA-256
  `aa1e69432472ae2f25075c01a651201f747ae0f9e85c8894dfa1f36883d06890`:
  vendor evidence only, without copied pages or register rows.
- Fronius external documentation package `1.2.7-2`, ZIP SHA-256
  `dc4c5d49362ee0c9721f21886f17fa18497e54c4d92bb5cc2c50472deb266b55`:
  vendor evidence only, without vendoring the archive or its tables.

This page creates no decoder, transport, device activation, support statement,
live result, semantic projection, or write surface.

## Model

A **Model** is one schema-revision-specific interpretation candidate for a
single SunSpec model occurrence. Its decoder key is exactly
`(model_id, model_length, schema_revision)`. A model-ID-only primary map is
forbidden and cannot select a decoder. A known ID with an unsupported length is
retained as an unsupported occurrence; it cannot qualify or fabricate a
capability.

The initial catalog is deliberately small and records only independently
summarized identifiers, names, encodings, and declared lengths:

- Model `1`, Common: standard length `L66`; `L65` is an evidence-backed
  compatibility shape, not a claim that L65 is the current standard. L65 is
  admissible only through an explicitly registered `(1, 65, schema_revision)`
  compatibility decoder key distinct from the standard L66 key. Without that
  exact key, an L65 occurrence is raw-retained unsupported and cannot admit a
  capability; no model-ID fallback is permitted.
- Models `101`, `102`, and `103`, inverter integer plus scale-factor forms:
  `L50` each.
- Models `111`, `112`, and `113`, inverter FLOAT forms: `L60` each.
- Model `120`, Nameplate: `L26`.
- Model `121`, Basic Settings: `L30`.
- Model `122`, Measurements_Status: `L44`.
- Model `123`, Immediate Controls: `L24`. Its exact decoder key is
  `(123, 24, schema_revision)`. It belongs to standard SunSpec core and is not
  a vendor custom model. Helianthus may provide a read-only decoder for
  retained observation and diagnosis; upstream RW metadata creates no write
  authority.
- Model `124`, Storage / Basic Storage Controls: `L24`.
- Model `160`, Multiple MPPT: `L = 8 + 20 * N`, where the occurrence carries
  its reported `N` and must prove that geometry against the declared length.

No item in this catalog asserts that a particular vendor exposes it, that an
implementation can decode it, or that its documented read/write metadata is
enabled by Helianthus.

## Model Chain

A **Model Chain** is the ordered sequence discovered after the SunSpec
signature. In the standard common order, the Common occurrence follows the
signature before subsequent model occurrences; the L65 compatibility nuance
does not change that order. A chain is not a set and is not reducible to a
model-ID map. Every
occurrence, including duplicates and unknown IDs, retains its ordinal, model
ID, declared length, header offset, payload offset, declared source span,
exact raw words, schema revision, and full acquisition provenance. Full
acquisition provenance includes the source logical view, request and wire
response identities, endpoint/unit identity as supplied by the acquisition
layer, receipt/generation identity, and each logical/slice offset and count.

Structural retention does not itself grant semantic admission. Before typed
interpretation, capability admission, or vendor-flavor evaluation, exactly one
Common Model `1` at a supported length must be the first occurrence after the
signature. A missing Common Model, an out-of-order Common Model, or a repeated
Common Model fails semantic admission. The bounded raw chain and provenance may
remain available for diagnosis, but it produces no typed observation,
capability, or vendor flavor.

The chain parser uses checked arithmetic. It rejects a bad signature, a
nonterminal zero length, arithmetic overflow, an extent overrun, a malformed
or missing end marker, a nonzero end-marker length, and trailing words after a
terminal end marker. Those failures may retain raw diagnostic evidence but do
not produce a valid chain, typed observation, capability, or vendor flavor.

An unknown occurrence whose declared extent is in-bounds is retained in order
with the same record fields as a known occurrence. A known occurrence with a
wrong length is also retained, but is unsupported. Neither condition permits
fallback to an ID-only decoder.

For Model `160`, the reported `N` must satisfy `L = 8 + 20 * N` using checked
arithmetic. An `N mismatch`, negative/invalid geometry representation, or
length disagreement is raw-retained invalid encoding with no capability.

## Capability Profile

A **Capability Profile** is a separately versioned, encoding-neutral statement
derived only from a complete valid model-chain occurrence set and valid typed
facts. The initial profile identifier is
`sunspec.inverter.three_phase.monitoring@1.0.0`. It may be satisfied by either
Model `103` or Model `113` only when the following complete minimum fact set is
present and valid:

| Canonical field ID | Unit |
|---|---|
| `inverter.ac.current.total` | `A` |
| `inverter.ac.current.phase_a` | `A` |
| `inverter.ac.current.phase_b` | `A` |
| `inverter.ac.current.phase_c` | `A` |
| `inverter.ac.voltage.phase_a` | `V` |
| `inverter.ac.voltage.phase_b` | `V` |
| `inverter.ac.voltage.phase_c` | `V` |
| `inverter.ac.power.active` | `W` |
| `inverter.ac.frequency` | `Hz` |
| `inverter.ac.energy_lifetime` | `Wh` |
| `inverter.temperature.cabinet` | `C` |
| `inverter.operating_state` | `none` |
| `inverter.events.1` | `none` |
| `inverter.events.2` | `none` |

The capability evaluator accepts the complete `SunSpecChainSnapshot`, not a
caller-provided decoded-model list or detached identity values. Before source
selection it reparses the snapshot raw words and requires the signature,
checked nonzero model extents, exactly one consuming `FFFF/0` terminal, no
trailing words, and exact agreement with every retained occurrence ordinal,
wire key, raw words, header/payload offsets, and source-span word count. This
verification creates no transport or acquisition authority.

The capability decision has this closed reason set and precedence:

1. `INVALID_CHAIN`: snapshot verification or Common-first/exactly-once decode
   fails;
2. `AMBIGUOUS_SOURCE`: more than one exact `103/L50` or `113/L60` occurrence
   exists, including a duplicate of one encoding or one of each;
3. `SOURCE_ABSENT`: no exact `103/L50` or `113/L60` occurrence exists;
4. `SOURCE_UNSUPPORTED`: the one exact source lacks its exact admitted decoder
   key or three-phase topology;
5. `INVALID_REQUIRED_FACT`: the one admitted source lacks one exact required
   field/unit pair or its required value fails the rules below;
6. `ADMITTED`: all checks pass.

Source counting occurs against the terminal-verified occurrence list before
typed decoding. An unsupported wrong-length occurrence is retained but is not
an exact source and does not make a separate exact source ambiguous.

Admission requires exactly one qualifying source occurrence, either `103/L50`
or `113/L60`, with three-phase topology. A duplicate source occurrence or a
chain carrying both encodings is ambiguous and fails closed. The registry does
not pick the first or last occurrence and does not merge facts across source
models.

Model `103` and Model `113` are capability-equivalent only for that complete,
valid minimum fact set: both decoders must emit the same canonical field IDs,
units, and three-phase topology. They remain distinct decoder keys with distinct
raw encodings and provenance. Capability equivalence does not assert equal
precision or representation. A wrong model length, invalid encoding, sentinel,
or non-finite value in any required fact fails admission rather than producing
a partial or inferred capability.

A required enum is valid for admission only when its numeric value has a known
symbol in the pinned schema. A required bitfield is valid only when it has no
unknown required bitfield bits. An unknown required enum symbol or unknown
required bitfield bits therefore fails admission even though the decoder keeps
the raw numeric value for diagnosis.

Capability facts preserve their original cloned typed `SunSpecValue`, source
decoder key, occurrence ordinal, raw words, source spans, and snapshot source
views. Their additional encoding-neutral value uses this closed representation:

- numeric values use the ASCII grammar
  `0|-?[1-9][0-9]*(?:\.[0-9]*[1-9])?|-?0\.[0-9]*[1-9]`. An int+SF value
  first computes the exact decimal `coefficient * 10^exponent` and serializes
  that decimal under this grammar. For example, `(12,-1)` and `(120,-2)` both
  produce `1.2`, `(-5,0)` produces `-5`, and any zero coefficient produces
  `0`. A FLOAT value uses the shortest finite base-10 form under the same
  grammar that round-trips to the same FLOAT32; for example `1.25` produces
  `1.25`, and positive or negative zero produces `0`. Exponent notation,
  leading zeroes on a nonzero integer part, a leading plus sign, a trailing
  decimal point, and redundant trailing fractional zeroes are forbidden;
- enums retain both the numeric code and the nonempty pinned symbol;
- bitfields retain the numeric bits and pinned symbols in ascending bit order,
  and require an unknown-bit mask of zero;
- fields without a physical unit expose the canonical unit string `none`, not
  an empty string.

This normalization permits deterministic value comparison but does not claim
equal precision, metrological accuracy, or original representation between
Models 103 and 113. Optional facts are not copied into this capability. Under
the pinned V1 schema, `inverter.events.2` has a zero known-bit mask, so only a
zero value can satisfy that required fact; a future nonzero mapping needs a new
pinned schema revision and capability version.

No raw value becomes a capability merely because its model ID is known. Raw
sentinel values, noncanonical NaN or infinity values, invalid scale factor
encodings, unknown enum values, unknown bitfield bits, malformed fixed-width
strings, and invalid accumulator states retain their raw encoding and cannot
fabricate a capability. Validation failure is fail-closed for capability
admission while preserving the occurrence and provenance for diagnosis.

`sunspec.phase1@1.0.0` is a separate legacy compatibility profile. Its
existing int+SF behavior is preserved exactly; it is legacy and must not widen
to FLOAT, storage, MPPT, vendor-specific, or newly inferred behavior through
this contract.

## Vendor Flavor

A **Vendor Flavor** is optional vendor-specific applicability evidence attached
after a valid model chain and capability profile have been selected. It records
only an evidence-backed delta, such as bounded applicability or a documented
quirk; it cannot replace the ordered chain, select a decoder by model ID alone,
or turn a capability into support for a vendor product.

The separately documented
[`fronius-observed-flavor-v1.md`](./fronius-observed-flavor-v1.md) contract uses
the Fronius materials in the source boundary plus one sanitized public
observation to define an exact, experimental flavor after capability admission.
The versioned
[`fronius-observed-flavor-v1-1.md`](./fronius-observed-flavor-v1-1.md)
successor records a second exact chain that includes standard Model `123/L24`;
it does not reinterpret or widen V1. This model-chain contract does not itself
activate either flavor, and none of these contracts records a completed live
qualification or broad Fronius support result.

## Read/write boundary

Upstream read/write metadata associated with Models `1`, `121`, or `124`
creates no write authority. All SunSpec work described here is read-only
documentation. Any write behavior requires a separately authorized safety
contract, implementation, and validation; neither a model, a chain, a
capability, nor a vendor flavor can imply it.

## Ownership and downstream boundary

`helianthus-modbus` owns generic Modbus transport and raw wire provenance.
`helianthus-modbusreg` is the future owner of chain planning/parsing, the
schema-revision decoder registry, type validation, capability profiles, and
vendor flavors. The gateway only acquires, schedules, activates, and dispatches
already-defined registry outcomes. Private bindings consume later canonical
facts only. This documentation change does not authorize changes in any of
those repositories.
