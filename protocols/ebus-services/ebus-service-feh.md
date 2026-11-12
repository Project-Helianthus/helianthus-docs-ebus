# eBUS Service 0xFE — General Broadcast (Application Layer)

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1, §3.7

## Scope

Service `0xFE` carries general-purpose broadcast messages. Currently only one secondary command is defined: the error message (`0x01`).

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`.
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

**Telegram type:** Broadcast (`DST=0xFE`). The official spec includes trailing ACK and SYN bytes in the wire table, though broadcast semantics do not require a target acknowledgement.

**Bus load:** `0.0%` (one-time only, on error event).

## Vaillant variants

**Hypothesis (partial FE01 family form):** Only the eight-bit constants
`0xFE` at logical position 0, bit 0, and `0x01` at logical position 1, bit 0,
are declared. These are logical declaration coordinates, not physical offsets.
Request and positive placements remain alternatives; positive-prefix relevance
is specific to a PeBUS declaration. Explicit and unspecified encoding remain
separate alternatives; unspecified encoding does not inherit the explicit one.
Encoding details beyond the presence of a declaration remain Unknown.

| Placement alternative | Encoding declaration | Constants (logical position, bit, width) | Native body | Status |
|---|---|---|---|---|
| request | explicit (details Unknown) | `FE` (0, 0, 8); `01` (1, 0, 8) | Unknown | Hypothesis |
| request | unspecified | `FE` (0, 0, 8); `01` (1, 0, 8) | Unknown | Hypothesis |
| positive (PeBUS declaration) | explicit (details Unknown) | `FE` (0, 0, 8); `01` (1, 0, 8) | Unknown | Hypothesis |
| positive (PeBUS declaration) | unspecified | `FE` (0, 0, 8); `01` (1, 0, 8) | Unknown | Hypothesis |

**Unknown body:** No native body, unit, enum, selector, sentinel, text,
termination or physical length is declared in this partial form. Absence of a
body declaration is not a declared empty body or a zero length. The FE/01
constants alone cannot establish a two-byte physical reply.

The general-broadcast ten-character body contract above remains separate and
authoritative for that generic form. It is not the body of this partial family
form. The [synthetic alternatives](./fixtures/ac26_fe01.json) preserve only the
partial declarations; they are representation examples, not captures or
physical qualification evidence.

## Open questions

- **Unknown:** Family availability, endpoint support, lifecycle and effects.
- **Unknown:** Physical qualification, physical offsets and physical length of
  the partial form; the declaration alternatives do not resolve them.

## See Also

- [`ebus-application-layer.md`](./ebus-application-layer.md) — service index
- [`ebus-overview.md`](./ebus-overview.md) — broadcast frame type definition
- [`ebus-service-ffh.md`](./ebus-service-ffh.md) — NM failure message (`0xFF 0x02`), a related but distinct error reporting mechanism
