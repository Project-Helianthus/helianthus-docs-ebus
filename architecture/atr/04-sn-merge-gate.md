# Qualified Identity Merge Gate

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD06, AD10

This document is a forward reference for Phase B `M6_ENRICHMENT_MERGE`. The
specification is frozen now so Phase A and Phase B cannot diverge.

## Activation Status

Per AD06 and AD10, the merge gate is `SPEC FROZEN` and implementation is
deferred to Phase B `M6_ENRICHMENT_MERGE`. Phase A MUST NOT activate pointer
merging from this gate.

## Merge Predicate

Cross-address identity merge is permitted only when the exact normalized
`(Manufacturer, DeviceID, SerialNumber)` triple matches. All three members
MUST be present and non-empty. Empty or partial triples create no
cross-address stable identity key.

`SerialNumber` MUST NOT be a sentinel value: `0`, `0x00000000`,
`0xFFFFFFFF`, or `0x7FFFFFFF`. Only while recognizing those hexadecimal
sentinels, case is ignored, one optional `0x` prefix is accepted, and leading
zeros are ignored. This exception MUST NOT parse, rewrite, or otherwise
reinterpret ordinary product serial formats.

An implementation MUST NOT merge independent addresses on manufacturer alone,
device ID alone, serial alone, MAC alone, model signature alone, companion
relation alone, or address co-occurrence alone.

Explicit topology aliasing based on source/target or canonical-companion
evidence is separate from identity merge and MAY group faces before a qualified
triple exists. It MUST NOT create a cross-address stable identity key.

## Gate-Fail Behavior

When the gate fails, the implementation MUST:

- log a warning; and
- DO NOT merge.

The warning SHOULD include both addresses and the rejection reason so the
operator can distinguish sentinel SN values from genuine identity mismatches.

## Enrichment and Provenance

Partial enrichment of a known address MAY retain last-known-good fields for
that address, but it MUST NOT establish cross-address identity. A static
candidate becomes `identity_confirmed` only after a complete qualified
observation. Identity confirmation MUST preserve per-face discovery provenance:
it MUST NOT rewrite `static_seed` or `passive_observed` source labels.

## Sentinel Treatment

A denied sentinel is non-identity-bearing data, not merge proof. The denylist
is a registry safety rule; it does not assert a wire-level meaning for a value
outside the qualified-identity decision.

## Registry Implementation Evidence

For the public separation of topology grouping, identity qualification, and
per-face provenance, see [Registry Alias-Group and Identity
Qualification](../regulator-identity-enrichment.md#registry-alias-group-and-identity-qualification).
The registry contract is not proof that an installed device satisfies a
wire-evidence prerequisite.
