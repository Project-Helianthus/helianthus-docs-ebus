# Device Discovery (BASV) (Observed)

This document describes the **BASV orchestration flow** used to enumerate devices and build one coherent identity view.

Wire-level message layouts are intentionally documented in protocol-centric docs:
- standard eBUS discovery functions in `protocols/ebus-overview.md`,
- Vaillant extended discovery in `protocols/ebus-vaillant.md`.

## BASV Orchestration Flow (Observed)

1. Run a presence-refresh phase.
2. Run an identity-probe phase against candidate target addresses.
3. For Vaillant-class identities, optionally run vendor enrichment.
4. Merge results into one device identity record per discovered target.

## BASV Output Shape (Observed)

Each BASV discovery record is expected to include:
- target address,
- manufacturer,
- device id,
- software version,
- hardware version,
- optional vendor-enriched metadata (for example Vaillant `scan.id`).

## References

- `protocols/ebus-overview.md#queryexistence-0x07-0xfe`
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`
