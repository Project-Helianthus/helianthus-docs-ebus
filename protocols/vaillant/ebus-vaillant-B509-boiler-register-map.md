# Vaillant B509 Boiler Register Map (BAI00)

This document is the authoritative public reference for the direct BAI00 boiler registers used by the GW-2 PASS-profile boiler model in Helianthus.

Scope:
- direct `0xB5 0x09` B509 reads from the physical boiler (`BAI00`)
- boiler fields exposed through `boilerStatus` in GraphQL and MCP
- writable boiler config fields exposed through `setBoilerConfig`

This document does not replace the B524 controller register map. The current boiler semantic plane is a hybrid:
- primary boiler state/config/diagnostics come from direct BAI00 B509 reads
- a small set of controller-mirrored fields still come from BASV2 B524 and are listed separately below

## Semantic Mapping

Source: `refreshBoilerStatusTier()` in `cmd/gateway/semantic_vaillant.go`

### Fast tier

| Semantic Path | B509 register | Codec / scale | Notes |
|---------------|---------------|---------------|-------|
| `state.flowTemperatureC` | `0x1800` | `DATA2c` | Live boiler flow temperature |
| `state.centralHeatingPumpActive` | `0x4400` | `on/off` | CH pump state |
| `state.waterPressureBar` | `0x0200` | `DATA2b` | Boiler water pressure |
| `state.flameActive` | `0x0500` | `on/off` | Burner flame status |
| `state.gasValveActive` | `0xBB00` | `on/off` | Gas valve state |
| `state.fanSpeedRpm` | `0x8300` | `UIN` | Fan speed in RPM |
| `state.modulationPct` | `0x2E00` | `SIN / 10` | Boiler modulation percent |
| `state.stateNumber` | `0xAB00` | `UCH` | Raw boiler state number |
| `state.diverterValvePositionPct` | `0x5400` | `UCH` | Diverter valve position percent |
| `state.dhwDemandActive` | `0x5800` | `on/off` | DHW demand state |
| `state.dhwWaterFlowLpm` | `0x5500` | `UIN / 100` | DHW water flow in L/min |

### Medium tier

| Semantic Path | B509 register | Codec / scale | Notes |
|---------------|---------------|---------------|-------|
| `config.flowsetHcMaxC` | `0x0E04` | `DATA2c` | Primary register for max HC flow setpoint |
| `config.flowsetHcMaxC` | `0xA500` | `DATA2c` | Fallback register when `0x0E04` is present but undecodable on the target boiler model |
| `config.flowsetHwcMaxC` | `0x0F04` | `DATA2c` | Max HWC flow setpoint |
| `config.partloadHcKW` | `0x0704` | `UCH` | Whole-number kW |
| `config.partloadHwcKW` | `0x0804` | `UCH` | Whole-number kW |
| `state.storageLoadPumpPct` | `0x9E00` | `percent0` | Storage load pump percent |
| `state.flowTempDesiredC` | `0x3900` | `DATA2c` | Desired boiler flow temperature |
| `state.dhwTempDesiredC` | `0xEA03` | `DATA2c` | Desired DHW temperature |
| `state.circulationPumpActive` | `0x7B00` | `on/off` | Circulation pump state |
| `state.externalPumpActive` | `0x3F00` | `on/off` | External pump state |
| `state.heatingSwitchActive` | `0xF203` | `on/off` | Heating switch state |
| `state.targetFanSpeedRpm` | `0x2400` | `UIN` | Target fan speed in RPM |
| `state.ionisationVoltageUa` | `0xA400` | `SIN / 10` | Ionisation voltage in uA |
| `state.primaryCircuitFlowLpm` | `0xFB00` | `UIN / 100` | Primary circuit flow in L/min |

### Slow tier

| Semantic Path | B509 register | Codec / scale | Notes |
|---------------|---------------|---------------|-------|
| `diagnostics.centralHeatingHours` | `0x2800` | `Hoursum2` | CH operating hours |
| `diagnostics.dhwHours` | `0x2200` | `Hoursum2` | DHW operating hours |
| `diagnostics.centralHeatingStarts` | `0x2900` | `UIN` | CH starts count |
| `diagnostics.dhwStarts` | `0x2300` | `UIN` | DHW starts count |
| `diagnostics.pumpHours` | `0x1400` | `Hoursum2` | Pump operating hours |
| `diagnostics.fanHours` | `0x1B00` | `Hoursum2` | Fan operating hours |
| `diagnostics.deactivationsIFC` | `0x1F00` | `UCH` | IFC deactivations |
| `diagnostics.deactivationsTemplimiter` | `0x2000` | `UCH` | Temperature limiter deactivations |

### Slow-config tier (installer/maintenance)

| Semantic Path | B509 register | Codec / scale | Access | Notes |
|---------------|---------------|---------------|--------|-------|
| `config.installerMenuCode` | `0x4904` | `UCH` (1 byte) | r;ws | Boiler installer menu access code. Range 0..255. Write via `setBoilerConfig(field: "installerMenuCode")` |
| `config.phoneNumber` | `0x8104` | `HEX:8` (8 bytes) | r;wi | Installer phone number as raw hex string (16 hex chars). Write via `setBoilerConfig(field: "phoneNumber")` |
| `config.hoursTillService` | `0x2004` | `Hoursum2` (2 bytes) | r | Service countdown in hours. **Read-only by design** — service counter must not be written |

## B524 Provenance Still Used By `boilerStatus`

The PASS-profile boiler contract still merges a small set of controller-side
mirrored values from B524.

`state.flowTemperatureC` remains authoritative on direct B509 register `0x1800`.
The B524 entries below are documented only as controller-side provenance,
mirror, or fallback candidates. They do **not** move the authoritative source
away from B509.

| Semantic Path | B524 register | Type | Notes |
|---------------|---------------|------|-------|
| `state.dhwTemperatureC` | `GG=0x01, RR=0x0005` | `f32` | Mirrored from DHW group on BASV2 |
| `state.dhwTargetTemperatureC` | `GG=0x01, RR=0x0004` | `f32` | Mirrored from DHW group on BASV2 |
| `config.dhwOperatingMode` | `GG=0x01, RR=0x0003` | `u16 -> enum string` | Published as decoded GraphQL string |
| `state.flowTemperatureC` | `OP=0x06, GG=0x00, RR=0x0015` | `f32` | Controller-side primary heat-source mirror / fallback candidate, corroborated by analiza ISC Smartconnect KNX. B509 `0x1800` remains authoritative |
| `diagnostics.activeErrors` | `OP=0x06, GG=0x00, RR=0x0012` | `u8 raw` | Controller-side primary heat-source provenance. `0=no active error`; non-zero semantics remain pending validation. Corroborated by analiza ISC Smartconnect KNX |
| `diagnostics.heatingStatusRaw` | `GG=0x02, II=0x00, RR=0x001B` | `u16` | Controller mirror of circuit/heating status |

Fields currently present in the GraphQL/MCP schema but not populated from a validated direct B509 mapping:
- `state.returnTemperatureC`
- `diagnostics.dhwStatusRaw`

## Write Path: `setBoilerConfig`

Supported writable fields:

| GraphQL field | Register selection | Codec | Accepted range | Notes |
|---------------|--------------------|-------|----------------|-------|
| `flowsetHcMaxC` | `0x0E04`, fallback `0xA500` | `DATA2c` | `20..80` C | Runtime chooses the first decodable register and confirms by read-back |
| `flowsetHwcMaxC` | `0x0F04` | `DATA2c` | `30..65` C | Read-back must match encoded payload |
| `partloadHcKW` | `0x0704` | `UCH` | `0..40` kW | Whole-number kW only |
| `partloadHwcKW` | `0x0804` | `UCH` | `0..40` kW | Whole-number kW only |
| `installerMenuCode` | `0x4904` | `UCH` | `0..255` | Boiler installer access code |
| `phoneNumber` | `0x8104` | `HEX:8` | 16 hex chars | Raw 8-byte hex string |

Write semantics:
- GraphQL accepts the `value` argument as a string and validates it server-side.
- Non-finite values (`NaN`, `Inf`) are rejected before range validation.
- `DATA2c` writes are normalized from the encoded wire payload. Example: `55.1` is encoded and published back as `55.0625`, not the original input string.
- Success requires both a valid B509 write acknowledgement and a matching read-back payload.
- After a confirmed write, the in-memory boiler snapshot is updated with copy-on-write semantics before the live semantic publish.

## Model-Specific Note

Runtime validation on BAI00 model `0010024604` showed:
- `0x0E04` may return an undecodable one-byte payload (`0xF0`) for `flowsetHcMaxC`
- fallback register `0xA500` returns the decodable `DATA2c` value and is therefore used for both read and write confirmation on that model
