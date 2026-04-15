# Composite Types

## BITFIELD

BITFIELD represents a fixed-width bitmask across N bytes.

- **Size:** `N` bytes (configured by the user)
- **Replacement value:** all bytes `0xFF`
- **Decode output:** a boolean slice of length `N * 8`
- **Encode input (common forms):**
  - `[]bool` of length `N * 8` (bit0 of byte0 is index 0)
  - `[]byte` of length `N` (raw bytes)
  - integer value (packed little-endian across `N` bytes)
- **Encode rules:** values that would encode to the replacement value (all `0xFF`) are rejected.
- **Size limit:** Maximum `SizeBytes` is 8 (64 bits). Values exceeding this limit are rejected.

```text
byte0 bit0 -> index 0
byte0 bit1 -> index 1
...
byte1 bit0 -> index 8
```

```go
// Example decode (illustrative)
bits, err := DecodeBITFIELD([]byte{0x05}, 1) // 00000101 -> [true,false,true,false,...]
_ = bits
_ = err
```

## Schema

A Schema is an ordered list of fields where each field has a name and a data type. Fields are decoded sequentially, each consuming its type’s `Size()` bytes.

```text
Schema:
  - field "room_temp"  : DATA2b
  - field "target_temp": DATA2b
  - field "mode"       : DATA1b
```

During encoding, each field must be present, and encoded sizes must match the declared type size.

## SchemaSelector (Conditional Schemas)

Some messages reuse the same identifier but change layout depending on context. A SchemaSelector chooses the first matching schema based on:

- **Target address**
- **Hardware version bounds** (min/max)

If no condition matches, the **default schema** is used.

### Example (JSON)

```json
{
  "default": {
    "fields": [
      { "name": "flow_temp", "type": "DATA2b" },
      { "name": "return_temp", "type": "DATA2b" },
      { "name": "pump_status", "type": "DATA1b" }
    ]
  },
  "conditions": [
    {
      "target": 16,
      "schema": {
        "fields": [
          { "name": "room_temp", "type": "DATA2b" },
          { "name": "target_temp", "type": "DATA2b" },
          { "name": "mode", "type": "DATA1b" }
        ]
      }
    }
  ]
}
```
