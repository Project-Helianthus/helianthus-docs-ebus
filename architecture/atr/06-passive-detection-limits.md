# Passive Detection Limits

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD03, AD08, AD10

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and eBUS address-pair
> vocabulary require them.

This document records the live-verified passive-observation limits that justify
the Phase A split.

## 0xF6 Passive Detection Path

`0xF6` is the NETX3 primary slave. It is detectable passively because
`companion(0xF1) = 0xF6` per AD03. The locked plan records a 24-hour
Prometheus capture with `9` observations of `0xF1` as source in `3` hours.

The architecture MUST therefore allow `slot[0xF6]` insertion after the second
corroborating observation of `0xF1`, even when `0xF6` itself never appears as
source or destination.

## 0x04 Pure-Passive Limit

`0x04` is the NETX3 secondary slave. It is structurally undetectable in
pure-passive mode on the operator's bus because `companion(0x04) = 0xFF`, and
the 24-hour Prometheus capture recorded `0` observations of `0xFF` as a master
source. Companion derivation therefore cannot fire for `0x04` in Phase A live
conditions.

`0x04` MUST require static seeding in M5 when `EnableStaticSeedTable=true`.

## 0xEC Pure-Passive Limit

`0xEC` is structurally undetectable in pure-passive mode because
`companion(0xEC) = none`: `0xEC - 0x05 = 0xE7`, and `0xE7` fails the AD03
bit-pattern rule. The locked plan also records `0` observations of `0xEC` as
source or destination. No master transmits to `0xEC` in the operator's normal
runtime path.

`0xEC` MUST require static seeding in M5 when `EnableStaticSeedTable=true`.

## Limit Summary

Per AD10, the address-table architecture covers all addresses that have at
least one observable transmission path:

- master-source observation; or
- slave-destination observation; or
- companion derivation from one of those observations.

Slave-only addresses with no observable path on the live bus MUST be supplied
by static seeding. That requirement is what covers `0x04` and `0xEC`.
<!-- legacy-role-mapping:end -->
