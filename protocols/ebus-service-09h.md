# eBUS Service 0x09 — Memory Server (Application Layer)

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1, §3.5

## Scope

Service `0x09` provides direct RAM and EEPROM read/write access to eBUS modules. This service is restricted to **service mode only** — devices should not support it during normal operation. All commands are one-time with no recurring bus load.

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping: `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

## Command Summary

| PB | SB | Name | Direction | Telegram Type | Access |
|---:|---:|---|---|---|---|
| `0x09` | `0x00` | Read RAM | Initiator → Target | Initiator/Target | Service only |
| `0x09` | `0x01` | Write RAM | Initiator → Target | Initiator/Target | Service only |
| `0x09` | `0x02` | Read EEPROM | Initiator → Target | Initiator/Target | Service only |
| `0x09` | `0x03` | Write EEPROM | Initiator → Target | Initiator/Target | Service only |

## Commands

### Service 0x09 0x00 — Read RAM Data

**Description:** Reads `DN` bytes from RAM starting at a 16-bit address. The target responds with the requested data bytes.

**Request payload:**

| Byte | Field | Type | Range | Description |
|---:|---|---|---|---|
| 0 | addr_lo | BYTE | — | Low byte of start address |
| 1 | addr_hi | BYTE | — | High byte of start address |
| 2 | count | BYTE | 0–255 | Number of bytes to read. The general 10-byte payload limit does not apply in service mode |

**Response payload:**

| Byte | Field | Type | Range | Description |
|---:|---|---|---|---|
| 0..DN-1 | data | BYTE×DN | — | Requested data bytes |

---

### Service 0x09 0x01 — Write RAM Data

**Description:** Writes data bytes to RAM starting at a 16-bit address.

**Request payload:**

| Byte | Field | Type | Range | Description |
|---:|---|---|---|---|
| 0 | addr_lo | BYTE | — | Low byte of memory address |
| 1 | addr_hi | BYTE | — | High byte of memory address |
| 2..NN-1 | data | BYTE×(NN-2) | — | Data bytes to write (1–8 bytes) |

**Response payload:** Empty (`NN=0x00`). ACK confirms write.

---

### Service 0x09 0x02 — Read EEPROM Data

**Description:** Reads `DN` bytes from EEPROM starting at a 16-bit address. Same request/response layout as [0x09 0x00](#service-0x09-0x00--read-ram-data).

**Request payload:** Identical to Read RAM.

**Response payload:** Identical to Read RAM.

---

### Service 0x09 0x03 — Write EEPROM Data

**Description:** Writes data bytes to EEPROM starting at a 16-bit address. Same request layout as [0x09 0x01](#service-0x09-0x01--write-ram-data).

**Request payload:** Identical to Write RAM.

**Response payload:** Empty (`NN=0x00`). ACK confirms write.

> **Note:** The last data block in a multi-block EEPROM write sequence may have `NN < 10`.

## Address Space

Both RAM and EEPROM use a flat 16-bit address space (little-endian: low byte transmitted first). The meaning of addresses is entirely device-specific and is not defined by the eBUS specification.

## Security Considerations

Memory server access bypasses all application-level validation. The specification explicitly restricts this service to service/maintenance mode. Devices that expose `0x09` during normal operation create a risk of uncontrolled state modification.

## See Also

- [`ebus-application-layer.md`](./ebus-application-layer.md) — service index
- [`ebus-overview.md`](./ebus-overview.md) — wire-level framing
- [`ebus-service-0Fh.md`](./ebus-service-0Fh.md) — test commands (also service-mode restricted)
