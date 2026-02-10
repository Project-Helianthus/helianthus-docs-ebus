# Data Types Overview

This section describes the data-type model used for eBUS payload decoding and encoding.

## Interface Shape

Each data type exposes a common interface:

```go
type Value struct {
    Value any
    Valid bool
}

type DataType interface {
    Decode([]byte) (Value, error)
    Encode(any) ([]byte, error)
    Size() int
    ReplacementValue() []byte
}
```

## Value / Valid Model

- `Value.Valid == true` means the payload represented a concrete value.
- `Value.Valid == false` means the payload is **not a usable value** for the type, either because it matched the replacement value *or* because the type-specific decoder rejected it (e.g., NaN/Inf or out-of-range for `EXP`).

Replacement values are defined per type and are used by devices to indicate “unknown” or “not available.”

## Replacement Value Semantics

Each type defines a byte sequence returned by `ReplacementValue()`. When decoding:

- If the payload equals the replacement value, `Valid` is false and `Value` is unset.
- Otherwise, the decoder may still set `Valid` to false if the decoded value is invalid for that type (for example, `EXP` treats NaN/Inf as invalid).
- If the value is acceptable, `Valid` is true and `Value` contains the decoded value.

When encoding:

- Values that would encode to the replacement value are rejected.
- Inputs outside the valid range are rejected.

This keeps “unknown” distinct from legitimate numeric values without using sentinel numbers in application code.

## See Also

- `types/ebusd-csv.md` – common ebusd CSV type spec strings and selector conventions (observed).
