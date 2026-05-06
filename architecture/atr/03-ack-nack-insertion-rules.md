# ACK/NACK Insertion Rules

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD04, AD05, AD12

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and eBUS address-pair
> vocabulary require them.

This document defines when an observed frame MAY create an `AddressSlot`. Frame
reconstruction semantics remain governed by
[`../bus-observability-v2.md`](../bus-observability-v2.md). The inserter MUST
consume reconstructed frame-position fields, not raw byte-stream occurrences.

## 0xFF Dual Meaning

Per AD04, `0xFF` is both a valid lowest-priority master address at frame start
and the NACK byte in ACK position. The reconstructor MUST distinguish those
positions before insertion logic runs. The address-table inserter MUST consume
only frame-start `src` and `dst` fields, never the ACK/NACK byte as address
data.

The inserter MUST therefore insert `slot[0xFF]` only when `0xFF` appears at
frame start as `src` or `dst`. It MUST NOT insert `slot[0xFF]` when `0xFF`
appears in ACK position.

## Insertion Soundness Gate

Per AD05, a first-observation insertion candidate exists only after:

```text
complete request frame + positive ACK byte 0x00
```

The inserter MUST insert `slot[ZZ]` on positive ACK following a complete
request when `ZZ` is an eligible frame-start peer address. It MUST NOT insert
on NACK.

The inserter MUST reject all of the following as slot-creation evidence:

- `0xFF` in ACK position.
- incomplete request frames.
- self-source equal to the gateway's admitted source.
- broadcast destination `0xFE`.

## Address Eligibility

The implementation MUST treat request-header fields as follows:

- request `src` MAY create a slot if it is not the gateway's own admitted
  source;
- request `dst` MAY create a slot if it is not broadcast `0xFE`;
- ACK/NACK bytes MUST NOT create slots.

The gateway's admitted source MUST be excluded because AD05 defines the table
as remote-device discovery, not self-registration. Broadcast `0xFE` MUST be
excluded because it is not a device identity.

## Companion-Pair Corroboration

Per AD05, companion-pair insertion requires a second corroborating observation.
The implementation MUST NOT insert `slot[companion(ZZ)]` after only one
positive ACK.

The corroboration gate MUST require one of:

- two positive ACK observations at least `N` seconds apart; or
- one positive ACK observation plus one coherent identity reply.

Until that gate passes, `slot[companion(ZZ)]` MUST remain absent. After the
gate passes, the companion slot MAY be inserted with passive provenance.

## Summary Rules

The address-table inserter MUST satisfy all of the following:

- `0x00` in ACK position is positive link evidence.
- `0xFF` in ACK position is negative link evidence only.
- `0xFF` at frame start is address evidence only after position
  disambiguation.
- self-source is excluded.
- broadcast `0xFE` is excluded.
- companion insertion requires second corroboration.
<!-- legacy-role-mapping:end -->
