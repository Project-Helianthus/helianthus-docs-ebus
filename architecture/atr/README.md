# ATR Architecture Index

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD13

This directory is the normative architecture set for `M0_DOC_SPEC`. The locked
plan is [`address-table-registry-w19-26.locked/00-canonical.md`](../../../helianthus-execution-plans/address-table-registry-w19-26.locked/00-canonical.md).

The documents in this directory canonicalize the address-table decisions from
AD01 through AD15 without duplicating the existing NM or eBUS standards docs.
NM discovery semantics remain in [`../nm-discovery.md`](../nm-discovery.md) and
[`../nm-model.md`](../nm-model.md). Protocol address facts remain in
[`../ebus_standard/12-source-address-table.md`](../ebus_standard/12-source-address-table.md).

## Documents

- [`01-address-table-model.md`](./01-address-table-model.md): defines the
  `AddressSlot`, `DeviceEntry`, and `BusFace` separation, lifecycle, and
  slot-aliasing rules for multi-address devices.
- [`02-companion-derivation.md`](./02-companion-derivation.md): freezes the
  pure companion-address algorithm, initiator-capability bit-pattern rule, and
  operator-pinned test cases.
- [`03-ack-nack-insertion-rules.md`](./03-ack-nack-insertion-rules.md): defines
  the frame-position-aware insertion gate, including `0xFF` disambiguation,
  positive-ACK-only insertion, and corroboration requirements.
- [`04-sn-merge-gate.md`](./04-sn-merge-gate.md): forward-references the
  Phase B serial-number merge gate and its sentinel denylist.
- [`05-static-seed-provenance.md`](./05-static-seed-provenance.md): documents
  static seed semantics, feature-flag policy, provenance, and the initial
  Vaillant seed set.
- [`06-passive-detection-limits.md`](./06-passive-detection-limits.md): records
  the live-verified passive-observation limits and the addresses that require
  static seeding.
- [`07-live-validation-acceptance.md`](./07-live-validation-acceptance.md):
  freezes the M8 falsifiability gate, HA compatibility check, and rollback
  criteria.
