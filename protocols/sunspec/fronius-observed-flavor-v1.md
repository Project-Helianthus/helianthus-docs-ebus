# Fronius Observed SunSpec Flavor V1

## Status and evidence boundary

`sunspec.flavor.fronius.gen24.float.observed@1.0.0` is an experimental,
read-only vendor flavor for one publicly sanitized observation. It is not a
product-family support claim and does not infer support for another Fronius
model, firmware, market variant, or model chain.

The evidence is the FC03-only preflight recorded publicly on
`Project-Helianthus/helianthus-ebusgateway#807`. The endpoint and serial remain
omitted. No vendor register row, SunSpec table, or private capture is copied
here.

## Exact admission tuple

The capability must already be admitted as
`sunspec.inverter.three_phase.monitoring@1.0.0`. Flavor evaluation then requires
all of these independent exact gates:

- Common manufacturer: `Fronius`, exact string match;
- Common model: `Symo GEN24 10.0`, exact string match;
- Common version/firmware: `1.41.11-1`, exact string match;
- exact ordered chain match:
  `1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0`;
- exactly one admitted Model `113/L60` source for the required capability facts.

There is no case folding, prefix match, semantic-version range, model-ID-only
fallback, reordering, subset match, or int+SF substitution. A future broader
Fronius flavor needs separate evidence and a new versioned contract.

## Outcomes

Flavor evaluation is deterministic and fail-closed. It returns one of these
categorical reasons without partial flavor facts:

- `CAPABILITY_NOT_ADMITTED`;
- `COMMON_IDENTITY_MISMATCH`;
- `FIRMWARE_MISMATCH`;
- `CHAIN_MISMATCH`;
- `AMBIGUOUS_SOURCE`;
- `MATCHED`.

Evaluation uses the same complete snapshot as capability admission. Reason
precedence is exact: a capability `AMBIGUOUS_SOURCE` maps first to flavor
`AMBIGUOUS_SOURCE`; every other non-admitted capability maps to
`CAPABILITY_NOT_ADMITTED`; then Common manufacturer/model mismatch maps to
`COMMON_IDENTITY_MISMATCH`; version mismatch maps to `FIRMWARE_MISMATCH`;
ordered-chain mismatch maps to `CHAIN_MISMATCH`; otherwise the result is
`MATCHED`.

The identity tuple contains exactly Common `Mn`, `Md`, and `Vr`, matched as the
three strings above without trimming, case folding, prefixing, or version-range
interpretation. Common `SN`, `Opt`, and `DA`, plus endpoint, unit ID, function,
PDU offset, and other acquisition provenance are not flavor matching inputs.
They remain retained by their owning raw/typed provenance contracts and cannot
be supplied separately to this evaluator.

Raw model occurrences, canonical capability facts, and acquisition provenance
remain owned by their original contracts. A mismatch never rewrites or drops
them.

## Observed acquisition provenance and deltas

The sanitized observation used FC03 holding-register reads, unit ID `1`, and
normalized PDU offset `40000` for the SunSpec signature. These values are
non-actionable provenance only. The flavor MUST NOT use them to construct a
request, select a transport, configure acquisition, or activate runtime work;
those decisions remain gateway-owned. They are not defaults and do not prove
that another Fronius device uses the same acquisition parameters.

This version has no documented quirk, no semantic override, no custom model,
and no extension fact. Standard SunSpec decoders remain authoritative. The
flavor creates no write authority, configuration mutation, control operation,
gateway publication, private eeBUS/Matter binding, or live qualification
result.
