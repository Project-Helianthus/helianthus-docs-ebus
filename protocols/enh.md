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

## Stream Parsing

When parsing a byte stream:

- If the high bit is **0**, the byte is treated as a raw data byte.
- If the byte matches the ENH header (`11xxxxxx`), the parser expects a second byte (`10xxxxxx`) to complete the ENH frame.
- A valid `RECEIVED` response yields one data byte to the upper layer.

Invalid header combinations are rejected.

## Example (Hex)

```text
Command SEND (0x1), Data 0x5A:
byte1 = 0xC0 | (0x1 << 2) | (0x5A >> 6) = 0xC5
byte2 = 0x80 | (0x5A & 0x3F)           = 0x9A
```
