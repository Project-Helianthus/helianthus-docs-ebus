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

## Known Device ID Codes (720-Series Regulators)

The `device_id` field returned by `Identification Scan (0x07 0x04)` is an ASCII identifier.
For Vaillant-group 720-series regulators we use the following observed codes and a stable naming scheme.

Naming scheme:
- `BAS*` = wireless / RF base station (the "bridge" side)
- `CTL*` = wired controller (the "wall unit" side)
- `S` = Saunier Duval branding
- `V` = Vaillant branding
- suffix `2` / `3` = generation / revision of the 720 series (observed)
- suffix `0` = "revision 1 implied" placeholder (convention)

| device_id | friendly_name (tool/UI) |
| --- | --- |
| `72000` | `Wired 720-series Regulator Controller Revision 0` |
| `BASS0` | `Wireless 720-series Regulator *BA*se *S*tation *S*aunier Duval-branded Revision 1 (implied)` |
| `BASS2` | `Wireless 720-series Regulator *BA*se *S*tation *S*aunier Duval-branded Revision *2*` |
| `BASS3` | `Wireless 720-series Regulator *BA*se *S*tation *S*aunier Duval-branded Revision *3*` |
| `BASV0` | `Wireless 720-series Regulator *BA*se *S*tation *V*aillant-branded Revision 1 (implied)` |
| `BASV2` | `Wireless 720-series Regulator *BA*se *S*tation *V*aillant-branded Revision *2*` |
| `BASV3` | `Wireless 720-series Regulator *BA*se *S*tation *V*aillant-branded Revision *3*` |
| `CTLS0` | `Wired 720-series Regulator *C*on*T*ro*L*ler *S*aunier Duval-branded Revision 1 (implied)` |
| `CTLS2` | `Wired 720-series Regulator *C*on*T*ro*L*ler *S*aunier Duval-branded Revision *2*` |
| `CTLS3` | `Wired 720-series Regulator *C*on*T*ro*L*ler *S*aunier Duval-branded Revision *3*` |
| `CTLV0` | `Wired 720-series Regulator *C*on*T*ro*L*ler *V*aillant-branded Revision 1 (implied)` |
| `CTLV2` | `Wired 720-series Regulator *C*on*T*ro*L*ler *V*aillant-branded Revision *2*` |
| `CTLV3` | `Wired 720-series Regulator *C*on*T*ro*L*ler *V*aillant-branded Revision *3*` |

Notes:
- Some UIs may render `*...*` segments as bold for readability; the underlying `device_id` remains unchanged.

## References

- `protocols/ebus-overview.md#queryexistence-0x07-0xfe`
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`
