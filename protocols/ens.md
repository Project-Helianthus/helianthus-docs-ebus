# ENS (Escaped) Stream Encoding

ENS is a byte-stuffing scheme that reserves control symbols and escapes them in a byte stream.

## Reserved Bytes

```text
ESC = 0xA9
SYN = 0xAA
```

## Encoding Rules

```text
0xA9 -> 0xA9 0x00
0xAA -> 0xA9 0x01
```

All other bytes are transmitted unchanged.

## Decoding Rules

```text
0xA9 0x00 -> 0xA9
0xA9 0x01 -> 0xAA
```

Unescaped `0xAA` is invalid. An escape at end-of-stream is invalid.

## Example

```text
Input:  0x10 0xA9 0xAA 0x20
Output: 0x10 0xA9 0x00 0xA9 0x01 0x20
```
