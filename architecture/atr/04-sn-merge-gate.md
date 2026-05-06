# SN Merge Gate

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

Pointer-merging two slots onto one `DeviceEntry` is permitted only when all of
the following are true:

- `(Manufacturer, DeviceID, SerialNumber)` matches exactly.
- `SerialNumber` is not in the denylist
  `{0x00000000, 0xFFFFFFFF, 0x7FFFFFFF}`.

An implementation MUST NOT merge on manufacturer alone, device ID alone,
companion relation alone, or address co-occurrence alone.

## Gate-Fail Behavior

When the gate fails, the implementation MUST:

- log a warning; and
- DO NOT merge.

The warning SHOULD include both addresses and the rejection reason so the
operator can distinguish sentinel SN values from genuine identity mismatches.

## Sentinel Rationale

The denylist is normative because Vaillant firmware is known to emit serial
number sentinels for inactive-register and uninitialized cases. A denied
sentinel MUST be treated as non-identity-bearing data, not as merge proof.
