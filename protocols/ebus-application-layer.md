# eBUS Application Layer (OSI 7) — Service Index

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1 (March 2007), eBUS Interest Group.

This document is the index for all standard (non-proprietary) eBUS Application Layer services. Each service is documented in its own file with wire formats, payload tables, and communication flow diagrams.

For wire-level framing (SRC/DST, CRC8, escaping, ACK/NACK, transaction flow), see [`ebus-overview.md`](./ebus-overview.md). For Vaillant proprietary messages (`PB=0xB5`), see [`ebus-vaillant.md`](./ebus-vaillant.md).

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping: `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

## Primary Command (PB) Allocation

| PB | Service Name | Commands | Doc |
|---:|---|---|---|
| `0x03` | Service Data (Burner Automats) | `0x04`–`0x08`, `0x10` | [`ebus-service-03h.md`](./ebus-service-03h.md) |
| `0x05` | Burner Control | `0x00`–`0x0D` | [`ebus-service-05h.md`](./ebus-service-05h.md) |
| `0x07` | System Data | `0x00`–`0x05`, `0xFE`, `0xFF` | [`ebus-service-07h.md`](./ebus-service-07h.md) |
| `0x08` | Controller-to-Controller | `0x00`–`0x04` | [`ebus-service-08h.md`](./ebus-service-08h.md) |
| `0x09` | Memory Server | `0x00`–`0x03` | [`ebus-service-09h.md`](./ebus-service-09h.md) |
| `0x0F` | Test Commands | `0x01`–`0x03` | [`ebus-service-0Fh.md`](./ebus-service-0Fh.md) |
| `0xB5` | Vaillant Proprietary | (manufacturer-specific) | [`ebus-vaillant.md`](./ebus-vaillant.md) |
| `0xFE` | General Broadcast | `0x01` | [`ebus-service-FEh.md`](./ebus-service-FEh.md) |
| `0xFF` | Network Management | `0x00`–`0x06` | [`ebus-service-FFh.md`](./ebus-service-FFh.md) |

## Data Type Quick Reference

These secondary data types are used across all Application Layer services.

| Name | Base Type | Range | Resolution | Replacement Value |
|---|---|---|---|---|
| BCD | CHAR | 0–99 | 1 | `0xFF` |
| DATA1b | SIGNED CHAR | -127 to +127 | 1 | `0x80` |
| DATA1c | CHAR | 0–100 | 0.5 | `0xFF` |
| DATA2b | SIGNED INTEGER | -127.99 to +127.99 | 1/256 | `0x8000` |
| DATA2c | SIGNED INTEGER | -2047.9 to +2047.9 | 1/16 | `0x8000` |

All 16-bit types are transmitted **low-byte first**.

For detailed type definitions including encoding formulas and Go codec implementations, see [`../types/primitives.md`](../types/primitives.md).

## Communication Rules

1. Standardised commands: payload **typically** limited to **10 data bytes** in both initiator and target telegram parts. **Known exceptions:** Service `0x09` read commands (`0x00`/`0x02`) permit `DN > 10` in service mode (writes remain constrained); Service `0x0F` test message (`0x02` only) allows `NN` up to `0x10`.
2. Manufacturer-specific commands: payload sum must not exceed **14 data bytes**.

## Bus Load Calculation

```
Bus load (%) = byte_count × (1 / cycle_period) × 4.16 × 10⁻³ s × 100%
```

The official spec expresses cycle rates as `1/x[unit]` (e.g., `1/10s`, `1/15min`). Commands marked `unique` or `one-time` are sent once (event-triggered) and are listed as `0.0%` bus load. Some event-driven commands with nonzero cycle rates carry nonzero bus load when actively cycling.

## See Also

- [`ebus-overview.md`](./ebus-overview.md) — wire-level framing, CRC8, ACK/NACK, transaction flow
- [`ebus-vaillant.md`](./ebus-vaillant.md) — Vaillant proprietary (`0xB5`) message index
- [`../types/overview.md`](../types/overview.md) — type system model
- [`../architecture/nm-model.md`](../architecture/nm-model.md) — Helianthus NM implementation model
