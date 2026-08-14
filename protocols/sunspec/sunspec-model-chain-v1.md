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
  compatibility nuance, not a claim that L65 is the current standard.
- Models `101`, `102`, and `103`, inverter integer plus scale-factor forms:
  `L50` each.
- Models `111`, `112`, and `113`, inverter FLOAT forms: `L60` each.
- Model `120`, Nameplate: `L26`.
- Model `121`, Basic Settings: `L30`.
- Model `122`, Measurements_Status: `L44`.
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
Model `103` or Model `113` only when the complete minimum fact set declared by
the eventual registry is present and valid; this page does not invent that fact
set or claim an implementation exists.

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

Fronius materials in the source boundary are provenance inputs, not an active
Fronius flavor. A future registry-selected outcome may select a capability and
then evaluate a vendor flavor under separately documented evidence. This
contract records no Fronius activation, live qualification, or support result.

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
