# Primitive Types

This document lists the primitive data types and their wire semantics.

## DATA1b (D1B)

- **Size:** 1 byte
- **Encoding:** signed 8-bit integer
- **Range:** -127 .. 127 (value -128 is reserved)
- **Replacement value:** `0x80`

```text
byte0: signed int8 (two's complement)
```

```go
// Example decode (illustrative)
val, err := DecodeDATA1b([]byte{0x7F}) // 127
_ = val
_ = err
```

## DATA2b (D2B)

- **Size:** 2 bytes
- **Encoding:** signed 16-bit, little-endian, divided by 256
- **Range:** -32767/256 .. 32767/256
- **Replacement value:** `0x00 0x80` (0x8000 little-endian)
- **Encoding notes (when writing):**
  - Scale by 256, round to nearest integer (ties away from zero), and require an exact fit.
  - Reject NaN/Inf, out-of-range values, and any value that would encode to the replacement value.

```text
byte0: low byte
byte1: high byte
value = int16(le) / 256
```

```go
// Example decode (illustrative)
val, err := DecodeDATA2b([]byte{0x00, 0x01}) // 256 -> 1.0
_ = val
_ = err
```

## DATA2c (D2C)

- **Size:** 2 bytes
- **Encoding:** signed 16-bit, little-endian, divided by 16
- **Range:** -32767/16 .. 32767/16
- **Replacement value:** `0x00 0x80` (0x8000 little-endian)
- **Encoding notes (when writing):**
  - Scale by 16, round to nearest integer (ties away from zero), and require an exact fit.
  - Reject NaN/Inf, out-of-range values, and any value that would encode to the replacement value.

```text
byte0: low byte
byte1: high byte
value = int16(le) / 16
```

```go
// Example decode (illustrative)
val, err := DecodeDATA2c([]byte{0x10, 0x00}) // 16 -> 1.0
_ = val
_ = err
```

## EXP

- **Size:** 4 bytes
- **Encoding:** IEEE-754 float32, little-endian
- **Range:** float32 (NaN/Inf are treated as invalid)
- **Replacement value:** `0x00 0x00 0xC0 0x7F` (0x7FC00000)

```text
byte0..3: little-endian float32
```

```go
// Example decode (illustrative)
val, err := DecodeEXP([]byte{0x00, 0x00, 0x80, 0x3F}) // 1.0
_ = val
_ = err
```

## WORD

- **Size:** 2 bytes
- **Encoding:** unsigned 16-bit, little-endian
- **Range:** 0 .. 65534 (0xFFFF reserved)
- **Replacement value:** `0xFF 0xFF`

```text
byte0: low byte
byte1: high byte
```

```go
// Example decode (illustrative)
val, err := DecodeWORD([]byte{0x34, 0x12}) // 0x1234
_ = val
_ = err
```

## BCD

- **Size:** 1 byte
- **Encoding:** packed BCD (tens in high nibble, ones in low nibble)
- **Range:** 00 .. 99
- **Replacement value:** `0xFF`

```text
byte0: [tens][ones] (4 bits each)
```

```go
// Example decode (illustrative)
val, err := DecodeBCD([]byte{0x42}) // 42
_ = val
_ = err
```
