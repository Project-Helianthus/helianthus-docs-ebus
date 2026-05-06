# Static Seed Provenance

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD07, AD08, AD14

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and eBUS address-pair
> vocabulary require them.

This document defines the provenance and semantics of static seed entries. The
seed source is the `helianthus-ebus-vaillant-productids` repository.

## Seed Semantics

Per AD07, a static seed MUST create address visibility with:

```text
source=static_seed
confidence=candidate
verification_state=candidate
```

Static seeds MUST make the listed addresses visible in GraphQL `devices`, but
they MUST NOT collapse identities before a later merge gate passes. A seeded
address is visible candidate-state evidence, not confirmed identity proof.

## Feature Flag

Per AD08, `EnableStaticSeedTable` MUST default to `false`. Operators MAY opt in
through addon configuration for Phase A validation. Promoting the default to
`true` requires this documentation set to establish the entries as model-level
Vaillant facts rather than operator-topology-only observations.

## Seed Provenance

The seed table is curated in `helianthus-ebus-vaillant-productids` from:

- operator hardware observations; and
- stable Vaillant device-pair conventions reflected in the locked plan.

The seed table MUST therefore be treated as curated model provenance, not as a
replacement for passive or identity-bearing runtime evidence.

## Initial Seed Entries

Per AD07 and AD08, the initial seed set is:

- `NETX3 = {0xF1 master, 0xF6 slave, 0x04 slave}`
- `BASV2 = {0x15 slave, 0xEC slave}`

The NETX3 entry is justified by the operator-confirmed radio gateway
dual-slave ownership model. The BASV2 entry is justified by the
operator-confirmed solar-plus-regulator combo that owns both `0x15` and
`0xEC`.

## Consumer Visibility

Per AD14, GraphQL and HA-facing surfaces MUST preserve static-seed provenance
and candidate verification state. Consumers MUST NOT silently treat a seeded
candidate as identity-confirmed hardware.
<!-- legacy-role-mapping:end -->
