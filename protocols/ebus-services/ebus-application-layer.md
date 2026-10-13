# eBUS Application Layer (OSI 7) — Service Index

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1 (March 2007), eBUS Interest Group.

This document is the index for all standard (non-proprietary) eBUS Application Layer services. Each service is documented in its own file with wire formats, payload tables, and communication flow diagrams.

For wire-level framing (SRC/DST, CRC8, escaping, ACK/NACK, transaction flow), see [`ebus-overview.md`](./ebus-overview.md). For Vaillant proprietary messages (`PB=0xB5`), see [`ebus-vaillant.md`](../vaillant/ebus-vaillant.md).

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`.
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

For detailed type definitions and encoding formulas, see [`../../types/primitives.md`](../../types/primitives.md).

## Communication Rules

1. Standardised commands: payload **typically** limited to **10 data bytes** in both initiator and target telegram parts. **Known exceptions:** Service `0x09` read commands (`0x00`/`0x02`) permit `DN > 10` in service mode (writes remain constrained); Service `0x0F` test message (`0x02` only) allows `NN` up to `0x10`.
2. Manufacturer-specific commands: payload sum must not exceed **14 data bytes**.

## Bus Load Calculation

```
Bus load (%) = byte_count × (1 / cycle_period) × 4.16 × 10⁻³ s × 100%
```

The official spec expresses cycle rates as `1/x[unit]` (e.g., `1/10s`, `1/15min`). Commands marked `unique` are listed as `0.0%` bus load. Commands described as "one-time" may still carry nonzero bus load when the spec assigns a cycle-rate window (e.g., `0x05 0x03` block 2 at `0.66%`).

Manufacturer-specific PB families (e.g., Vaillant `0xB5`) are not part of the standard Application Layer and are documented separately in [`ebus-vaillant.md`](../vaillant/ebus-vaillant.md).

## Vaillant variants

Each service page adds a "Vaillant variants" section with the Vaillant layouts for that service. The standard text stays authoritative everywhere; every Vaillant layout is stated as a candidate interpretation, unconfirmed on the wire. The 49 standard service identifiers (`03 04`–`03 08`, `03 10`, `05 00`–`05 0D`, `07 00`–`07 05` including the `07 04` broadcast form, `07 FE`, `07 FF`, `08 00`–`08 04`, `09 00`–`09 03`, `0F 01`–`0F 03`, `FE 01`, `FF 00`–`FF 06`) fall into these groups:

| Result | Services |
|---|---|
| Follows the standard layout (candidate) | `07 02`, `07 03`, `07 05`, `09 00`, `09 01`, `09 02`; `09 03` for the request (whether its reply is always empty is unresolved) |
| Differs from the standard (candidate) | `07 04` (bytes 8–9 are a software product number for Vaillant regulators; for every other Vaillant device class their meaning is **Unknown**), `07 00`, `05 01`, `03 05` |
| Defined with unresolved request/reply placement | `03 04`, `03 06` |
| Only PB/SB defined, no body (candidate) | `07 FE`, `07 FF`, `FE 01` |
| No Vaillant definition known (implementation **Unknown**) | `03 07`, `03 08`, `03 10`, `05 00`, `05 02`–`05 0D`, `07 01`, the `07 04` broadcast form, `08 00`–`08 04`, `0F 01`–`0F 03`, `FF 00`–`FF 06` |

Service `0F`: a Vaillant layout gives the primary byte `0x0F` with no known secondary byte and no body (candidate; the secondary byte of the request on the wire is unknown, see [`ebus-service-0Fh.md`](./ebus-service-0Fh.md#vaillant-variants)). That layout does not encode any of the three standard identities `0F 01`–`0F 03`, which are therefore counted under "No Vaillant definition known".

A missing Vaillant definition is not proof that a device lacks the service.

Evidence labels in these sections, in the terms of the repository's evidence rules: a Vaillant layout marked candidate, unconfirmed on the wire, is **Hypothesis**; for a service marked "No Vaillant definition known", whether Vaillant devices implement it is **Unknown**; the `07 04` software product number reading is a **Hypothesis** as well, used by the [Vaillant regulator identity crosswalk](../vaillant/ebus-vaillant-regulators.md#spn-field-07-04-bytes-8-9-representation). No statement in these sections is **Proven**.

Protocol profiles: no standard service in this index is known to be available only on PeBUS (candidate, unconfirmed on the wire). Which of the standard services with a Vaillant layout (`03 04`–`03 06`, `05 01`, `07 00`, `07 02`–`07 05`, `07 FE`, `07 FF`, `09 00`–`09 03`, `FE 01`, and the `0F` layout without a known secondary byte) are available under each profile is **Unknown**.

## Open questions

- Every difference listed above, including the `07 04` software product number, is a candidate, unconfirmed on the wire; no device or capture observation is known.
- The services with no Vaillant definition may still be implemented by Vaillant devices; this is neither shown nor excluded.
- No capture of a Vaillant exchange of `03`, `05`, `08`, `0F`, `FE` or `FF` standard services is known.
- The availability of each standard service under the eBUS and the PeBUS profiles is not established; only the absence of a known PeBUS-only service is stated.

## See Also

- [`ebus-overview.md`](./ebus-overview.md) — wire-level framing, CRC8, ACK/NACK, transaction flow
- [`ebus-vaillant.md`](../vaillant/ebus-vaillant.md) — Vaillant proprietary (`0xB5`) message index
- [`../../types/overview.md`](../../types/overview.md) — type system model
