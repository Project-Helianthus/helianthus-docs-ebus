# eBUS Service 0xFE — General Broadcast (Application Layer)

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1, §3.7

## Scope

Service `0xFE` carries general-purpose broadcast messages. Currently only one secondary command is defined: the error message (`0x01`).

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping: `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

## Command Summary

| PB | SB | Name | Direction | Telegram Type | Cycle Rate |
|---:|---:|---|---|---|---|
| `0xFE` | `0x01` | Error Message | Any initiator → all | Broadcast | One-time (on error) |

## Commands

### Service 0xFE 0x01 — Error Message

**Description:** A broadcast error message that any device may issue once upon detecting an error condition. Intended to be relayed by an eBUS modem to a service centre.

**Payload (initiator telegram):**

| Byte | Field | Type | Range | Repl. | Description |
|---:|---|---|---|---|---|
| 0–9 | error_text | CHAR×10 | — | — | 10-character error message (ASCII) |

**Telegram type:** Broadcast (`DST=0xFE`). No ACK, no response.

**Bus load:** `0.0%` (one-time only, on error event).

## See Also

- [`ebus-application-layer.md`](./ebus-application-layer.md) — service index
- [`ebus-overview.md`](./ebus-overview.md) — broadcast frame type definition
- [`ebus-service-FFh.md`](./ebus-service-FFh.md) — NM failure message (`0xFF 0x02`), a related but distinct error reporting mechanism
