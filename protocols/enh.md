# ENH (Enhanced) Framing

ENH wraps each data byte in a two-byte frame that carries a command nibble and the data byte.

## Byte Layout

```text
byte1: 1 1 C C C C D D
byte2: 1 0 D D D D D D
```

- `C` = 4-bit command
- `D` = 8-bit data payload (split across the two bytes)

The data bits are assembled as:

```text
data[7:6] = byte1[1:0]
data[5:0] = byte2[5:0]
```

## Command IDs

```text
Requests:
  0x0 = INIT
  0x1 = SEND
  0x2 = START
  0x3 = INFO

Responses:
  0x0 = RESETTED
  0x1 = RECEIVED
  0x2 = STARTED
  0x3 = INFO
  0xA = FAILED
  0xB = ERROR_EBUS
  0xC = ERROR_HOST
```

## INIT Handshake (Observed)

Hosts typically send `INIT` once with a feature byte (often `0x00`). Some adapters respond with `RESETTED`, but others immediately start streaming bus data or `INFO` without ever sending `RESETTED`.

Practical, ebusd-compatible behavior is to treat `INIT` as **best-effort**: send it, then proceed if a `RESETTED` arrives *or* if no `RESETTED` appears within a short timeout while valid data continues to flow.

## Stream Parsing

When parsing a byte stream:

- If the high bit is **0**, the byte is treated as a raw data byte.
- If the byte matches the ENH header (`11xxxxxx`), the parser expects a second byte (`10xxxxxx`) to complete the ENH frame.
- A valid `RECEIVED` response yields one data byte to the upper layer.

Invalid header combinations are rejected.

## Short-Form Receive Notifications

For bytes `< 0x80`, the enhanced protocol allows receive notifications to be sent without an ENH frame prefix. These unframed bytes are semantically equivalent to a `RECEIVED` response carrying the same data byte.

## Arbitration Bytes

Receive data notifications are **not** sent for bytes that are part of an arbitration request initiated by the host. Implementations should not expect echo notifications for those arbitration bytes (typically the address bytes at the start of an initiator frame).

## START/STARTED and the Source Byte

When using `START`/`STARTED` to acquire the bus (arbitration), the adapter emits the **initiator source address** on the physical bus as part of that arbitration sequence.

As a consequence, the first command telegram sent immediately after a successful `STARTED` does not need to re-send the `SRC` byte; it can begin at `DST`.

This matches ebusd-style “direct” operation over ENH and explains why `SRC` echo notifications are typically absent right after arbitration.

## Example (Hex)

```text
Command SEND (0x1), Data 0x5A:
byte1 = 0xC0 | (0x1 << 2) | (0x5A >> 6) = 0xC5
byte2 = 0x80 | (0x5A & 0x3F)           = 0x9A
```
