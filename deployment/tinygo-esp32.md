# TinyGo / ESP32

## Current Status

TinyGo compatibility is enforced at the library layer:

- `helianthus-ebusgo` builds with TinyGo (including `cmd/tinygo-check`).
- `helianthus-ebusreg` avoids JSON schema loading on TinyGo targets.

The gateway does not currently run on TinyGo.

## Constraints Implemented

- JSON schema loading is disabled on TinyGo targets.
- Transport framing and protocol logic avoid `net/http` and other full-Go dependencies.

## Example Build Check

```bash
# In helianthus-ebusgo:
tinygo build -target esp32 ./cmd/tinygo-check
```
