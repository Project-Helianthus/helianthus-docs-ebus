# SunSpec Additional Model Evidence V1

## Status

This packet is the FMV3-M7-01 evidence boundary for standard SunSpec model
expansion. It is not an implementation or support statement. The candidate
sets below remain manufacturer-neutral and do not alter the currently admitted
Fronius chain.

## Primary Source

The authoritative input is the Apache-2.0 `sunspec/models` repository pinned at
commit `7abdf8982d5364f8ae916deee18aac86c11be36d`. Helianthus consumes only the
model definitions at that immutable revision. This page independently
summarizes model identity and admission constraints; it does not reproduce the
upstream JSON model files.

## Candidate Sets

| Candidate | Model IDs | Disposition | M7 boundary |
| --- | --- | --- | --- |
| Integer AC meter | `201`, `202`, `203`, `204` | `PROFILE_CANDIDATE` | Read-only decoding may be evaluated in M7-02. |
| Float AC meter | `211`, `212`, `213`, `214` | `PROFILE_CANDIDATE` | Must prove canonical equivalence with the integer family before promotion. |
| Environmental telemetry | `302` through `308` | `PROFILE_CANDIDATE` | Irradiance, module temperature, orientation, location, and meteorological facts need separate canonical capability review. |
| Grid and control models | `125` through `145` | `EVIDENCE_ONLY` | Read-only decoding may be researched, but no write, control, or activation authority exists. |

Models `125` through `145` include pricing, scheduling, grid-support curves,
ride-through settings, and extended settings. Their presence in the public
model catalog does not authorize Helianthus writes. FC05, FC06, FC0F, FC10,
FC16, FC17, or any vendor write operation remains forbidden.

## Detection And Chain Rules

The only fixed detector PDU is the existing SunSpec signature read: configured
unit, FC03, PDU offset `40000`, quantity `2`. After a valid signature and Common
Model, each candidate is discovered by the generic `(model_id, model_length)`
header walk. Dynamic block reads remain bounded by the model length and the
runtime maximum of 125 registers per PDU.

FC04 may be used only by a separately versioned profile whose authoritative
model contract assigns a candidate to input registers. This packet does not
change the currently deployed FC03-only Fronius acquisition profile.

Unknown standard model IDs remain structurally retained as opaque blocks with
provenance. Repeated IDs retain occurrence order. A malformed length, missing
terminator, unsupported schema revision, or ambiguous model definition fails
that candidate closed without invalidating other structurally valid blocks.

## Admission Requirements

M7-02 may admit only a bounded subset that proves:

- exact upstream commit and model-file identity;
- model ID, declared length, schema revision, field type, units, scale, sentinel,
  enum, bitfield, string, accumulator, and repeated-group behavior;
- integer/scale-factor and float equivalence where both families exist;
- no vendor names or firmware assumptions in the standard decoder;
- no canonical fact promotion before a versioned capability contract exists;
- no write path, even for standard fields marked writable upstream.

The candidate set is therefore evidence-qualified but not catalog-admitted.
