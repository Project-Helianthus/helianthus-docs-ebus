# Device Discovery (BASV) (Observed)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

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
| `BASS0` | `Wireless 700/720-series Regulator *BA*se *S*tation *S*aunier Duval-branded (Exacontrol E7RC / MiPro Sense f) Revision 1 (implied)` |
| `BASS2` | `Wireless 720-series Regulator *BA*se *S*tation *S*aunier Duval-branded (MiPro Sense f) Revision *2*` |
| `BASS3` | `Wireless 720-series Regulator *BA*se *S*tation *S*aunier Duval-branded (MiPro Sense f) Revision *3*` |
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

## Known Device ID Codes (Legacy Regulators)

These legacy `device_id` codes have been observed/verified for older Vaillant-group regulators:

| device_id | friendly_name (tool/UI) |
| --- | --- |
| `43000` | `VRC 430/430f calorMATIC Regulator` |
| `47000` | `VRC 470/470f calorMATIC Regulator` |
| `62000` | `VRC 620 auroMATIC Cascade Regulator` |
| `63000` | `VRC 630 calorMATIC Cascade Regulator` |

## Known Device ID Codes (700/710 Series, Gateways, Other)

| device_id | friendly_name (tool/UI) |
| --- | --- |
| `70000` | `Wired 700-series multiMATIC Regulator Controller, Vaillant Branded` |
| `700f0` | `Wireless 700-series multiMATIC Regulator Base Station, Vaillant Branded` |
| `E7C00` | `Wired 700-series Exacontrol E7C Regulator Controller, Saunier Duval Branded` |
| `EMM00` | `Wired 710-series sensoDIRECT Regulator (NETX2/NETX3 or Heater UI dependent, no VR9x support)` |
| `CTLR0` | `Wired 380-series Regulator *C*on*T*ro*L*ler Generic-branded Revision 1 (implied)` |
| `CTLR2` | `Wired 380-series Regulator *C*on*T*ro*L*ler Generic-branded Revision *2*` |
| `BASR0` | `Wireless 380-series Regulator *BA*se *S*tation Generic-branded Revision 1 (implied)` |
| `BASR2` | `Wireless 380-series Regulator *BA*se *S*tation Generic-branded Revision *2*` |
| `VAI00` | `vSMART/eRELAX WiFi Regulator Gateway (Generation 1)` |
| `NETX2` | `sensoNET VR 920/921 WiFi/LAN Gateway (Generation 2) - Optional Regulator` |
| `NETX3` | `myVAILLANT VR 940 WiFi Gateway (Generation 3) - Optional Regulator` |

## VRC720 Controller Family Classification

> Source: `FINAL-corrections-and-devices.md` Part B, `GATES-protocol-level.md` Section 1.

All 720-series device IDs listed in the table above are firmware/hardware variants of the **VRC720 controller family**. They are NOT separate device types. The family splits into two form factors:

- **Wireless base stations (BASV\*):** BASV0, BASV2, BASV3 — the RF bridge unit mounted near the boiler/heat pump. Communicates wirelessly with the wall-mounted controller.
- **Wired controllers (CTLV\*/CTLS\*):** CTLV0, CTLV2, CTLV3, CTLS2 — wall-mounted wired controllers connected directly via eBUS.

All VRC720-family devices share:
- eBUS target address `0x15`
- B524 extended register protocol (opcodes `0x02`/`0x06`)
- B555 timer/schedule protocol
- Config-compatible register map (john30 `15.700.csv` symlinked for CTLV2/CTLV3)

### Known HW/SW Versions

| device_id | HW version | SW version | Source |
|-----------|-----------|-----------|--------|
| BASV2 | 1704 | 0507 | Helianthus live hardware |
| CTLV2 | 1104 | 0514 | john30/ebusd issue #487 (live hardware) |
| CTLV3 | 3704 | 0709 | john30/ebusd issue #487 (live hardware) |

### VRC700 Is a Separate Family

The **VRC700** (device ID `70000`, including Saunier Duval alias `B7S00`) is a different, older controller family. It shares eBUS address `0x15` but differs in protocol support:
- Uses B524 opcodes `0x03`/`0x04` for timer operations (NOT B555)
- Does NOT respond to B555 frames
- Separate register namespace in some B524 groups

B7S00 is a Saunier Duval branding alias of the VRC700 — do NOT include it in VRC720-family classifications.

## References

- `protocols/ebus-overview.md#queryexistence-0x07-0xfe`
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`
