# Device Discovery (BASV) (Observed)

This document describes the **BASV discovery flow** used to enumerate devices on the eBUS and collect identity metadata.

It intentionally does not duplicate the wire-level layouts for generic eBUS discovery or vendor extensions; those are documented in the protocol overview pages linked below.

## Discovery Flow (Observed)

1. Trigger presence refresh via `QueryExistence` broadcast (`0x07 0xFE`).
2. Probe candidate target addresses with `Identification Scan` (`0x07 0x04`) to obtain:
   - manufacturer byte
   - device id string
   - software / hardware version bytes
3. If the device manufacturer is Vaillant (`0xB5`), optionally enrich identity by reading the Vaillant `scan.id` chunks via B509 (`0xB5 0x09`, `QQ=0x24..0x27`) and assembling the 32-byte ASCII string.

## References

- `protocols/ebus-overview.md#queryexistence-0x07-0xfe`
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`
