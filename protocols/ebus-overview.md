# eBUS Overview (Wire-Level)

This document describes the wire-level framing and rules that are implemented. It focuses on the minimum required to interpret bytes on the bus.

## Frame Layout

An eBUS frame on the wire is represented as:

```text
| SRC | DST | PB | SB | LEN | DATA... | CRC |
|  1  |  1  |  1 |  1 |  1  |  LEN    |  1  |
```

- **SRC**: source address
- **DST**: destination address
- **PB/SB**: primary/secondary command bytes
- **LEN**: number of data bytes
- **DATA**: payload bytes
- **CRC**: CRC8 over the unescaped data (see CRC section)

## Frame Types

Frame type is derived from the destination address:

- **Broadcast**: `DST = 0xFE`
- **Master/Master**: `DST` has a valid master address pattern
- **Master/Slave**: any other valid destination address

This inference determines whether an ACK-only exchange is expected (master/master) or a full response frame (master/slave).

## ACK/NACK Symbols

The bus uses one-byte symbols:

```text
ACK  = 0x00
NACK = 0xFF
```

Broadcast frames do not receive ACK/NACK or responses.

Idle periods may include `SYN` (`0xAA`) bytes on the bus; receivers typically ignore these while waiting for an `ACK`/`NACK`.

## CRC8 and Escaping

CRC8 is computed over the frame data with special handling for control symbols:

- `0xA9` (escape) is treated as `0xA9 0x00`
- `0xAA` (SYN) is treated as `0xA9 0x01`

This substitution is applied before CRC8 updates so that control symbols do not break framing.

## Example

```text
SRC=0x10 DST=0x08 PB=0xB5 SB=0x04 LEN=0x01 DATA=0x7F CRC=0x??
```

The CRC byte depends on the exact CRC8 implementation and the escape-aware substitution described above.
