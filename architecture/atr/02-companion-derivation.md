# Companion Derivation

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD03, AD04

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and eBUS address-pair
> vocabulary require them.

This document freezes the companion-address derivation algorithm. Protocol
address rows remain defined by
[`../ebus_standard/12-source-address-table.md`](../ebus_standard/12-source-address-table.md).

## Initiator-Capable Bit-Pattern Rule

Per AD03, an address is initiator-capable only when each nibble is in:

```text
{0x0, 0x1, 0x3, 0x7, 0xF}
```

Implementations MUST use
`helianthus-ebusgo/protocol.IsInitiatorCapableAddress` or an equivalent
function with identical semantics. They MUST NOT maintain a divergent manual
allowlist for this rule.

## Companion Algorithm

Per AD03, the companion function MUST be pure and MUST implement the standard
master/slave arithmetic:

```go
func Companion(addr byte) (byte, bool) {
    if IsInitiatorCapableAddress(addr) {
        return addr + 0x05, true
    }

    candidate := byte((int(addr) - 0x05) & 0xFF)
    if IsInitiatorCapableAddress(candidate) {
        return candidate, true
    }

    return 0, false
}
```

The function MUST treat an initiator-capable address as a master and derive its
slave with `addr + 0x05 (mod 0x100)`. It MUST treat a non-initiator-capable
address as a slave candidate and derive its master with `addr - 0x05 (mod
0x100)` only if the result passes the bit-pattern rule.

## Pinned Test Cases

Per AD03, the following operator-confirmed pairs MUST remain fixed test cases:

| Case | Expected |
| --- | --- |
| `0x04` | `0x04 ↔ 0xFF` |
| `0xF1` | `0xF1 ↔ 0xF6` |
| `0x08` | `0x08 ↔ 0x03` |
| `0x10` | `0x10 ↔ 0x15` |

The implementation SHOULD test both directions of each pair. `0x04 ↔ 0xFF`
requires special care: `0xFF` is a valid lowest-priority master in address
context, while AD04 separately forbids treating `0xFF` in ACK position as
address evidence.

## Exception List

Per AD03, the following slave addresses have no valid master pair:

- `0x26` has no master pair because `0x26 - 0x05 = 0x21`, and `0x21` fails the
  initiator-capable bit-pattern.
- `0xEC` has no master pair because `0xEC - 0x05 = 0xE7`, and `0xE7` fails the
  initiator-capable bit-pattern.

The implementation MUST return `(0, false)` for those cases. It MUST reach
that outcome by applying the bit-pattern rule, not by hard-coding `0x26` or
`0xEC` as exceptions.

## 0xFF Context Note

Per AD04, `0xFF` has dual meaning:

- at frame start, `0xFF` MAY be a valid master address;
- in ACK position, `0xFF` is the NACK byte.

Companion derivation MUST operate only on already-disambiguated address fields.
Frame-position disambiguation is governed by
[`03-ack-nack-insertion-rules.md`](./03-ack-nack-insertion-rules.md).
<!-- legacy-role-mapping:end -->
