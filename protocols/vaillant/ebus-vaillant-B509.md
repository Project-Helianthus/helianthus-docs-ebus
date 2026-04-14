# Vaillant B509 Register Access

`PB=0xB5`, `SB=0x09`.

## Status

`B509` is a flat-register access primitive with an operation byte and a 16-bit
address in the common BAI/BASV-style form. Register semantics and codecs are
target-specific.

The BAI00 boiler register map used by Helianthus is documented separately in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).

Evidence labels:

- `LOCAL_CODE`: Helianthus gateway and registry code.
- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.

## Wire Shape

```text
Read request:
  0d addr_hi addr_lo

Write request:
  0e addr_hi addr_lo data...
```

Helianthus accepts either of these response forms for reads:

```text
0d addr_hi addr_lo data...
addr_hi addr_lo data...
```

The first form echoes the read opcode; the second echoes only the address.

## Local MCP Evidence

Current MCP bus summary showed active `B509` initiator-target traffic from the
gateway initiator to multiple Vaillant targets, including BAI00. This proves
the local gateway is using `B509` actively, but it does not by itself prove
individual register semantics.

## Device-Type Gate (Register Address Collision)

B509 register addresses are **not globally unique**. The same register ID at the
same eBUS bus address (`0x08`) returns completely different data depending on
whether a BAI00 (boiler) or EHP00/HMU (heat pump) is installed.

Known collisions at address `0x08`:

| Register ID | BAI00 (boiler) | EHP00/HMU (heat pump) |
|------------:|----------------|------------------------|
| `0x3F00` | `externalPumpActive` (on/off) | `ICLOut` — inrush current limiter (on/off) |
| `0xBB00` | `gasValveActive` (UCH 0x0F/0xF0) | `ActualEnvPowerPercentage` (percent0, %) |
| `0x1400` | `pumpHours` (Hoursum2, hours) | `CompPressHigh` — high-side compressor pressure (sensor, bar) |
| `0xE400` | `externGasvalve` (on/off) | `compressorState` (UCH enum) |

**Any B509 implementation that does not gate on product ID will silently return
semantically wrong data.** The product ID can be established from:

- B509 register `0x9A00` (DSN — device serial number / product identifier)
- B514 device identity frame

The BAI00 boiler register map is in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).
The EHP00/HMU heat pump register map is in
[`ebus-vaillant-B509-heatpump-register-map.md`](ebus-vaillant-B509-heatpump-register-map.md).

## Known Boiler Registers

Helianthus currently treats direct BAI00 `B509` as authoritative for most
`boilerStatus` state/config/diagnostics. Examples from the implemented BAI00
map:

| Register | Semantic use | Codec |
|---:|---|---|
| `0x1800` | boiler flow temperature | `DATA2c` |
| `0x4400` | central heating pump active | on/off |
| `0x0200` | water pressure | `DATA2b` |
| `0x0500` | flame active | on/off |
| `0xBB00` | gas valve active | on/off |
| `0x8300` | fan speed | `UIN` |
| `0x2E00` | modulation percent | `SIN / 10` |

The full list is in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).

## Falsification Tests

- Disprove flat addressing by capturing a valid `B509` exchange where bytes
  after `0x0D` or `0x0E` are not a 16-bit address.
- Disprove write semantics by producing a write ACK that is accepted as
  success without a matching read-back. Helianthus requires ACK plus read-back
  for semantic writes.
- Disprove a register mapping by changing the physical state and showing the
  documented register value does not change while an alternate register does.

## Unknowns

- Complete register map per product ID and firmware generation.
- Meaning of invalid/unavailable response markers across device classes.
- Whether every target accepts both echoed-op and address-only response forms.
- Whether B509/`0x9A00` (DSN) is available on EHP00/HMU devices for product-type
  gating, or if B514 must be used exclusively for heat pump identification.
- HMU HW5103 `540200xx` sub-addressing: single-fork source (burmistrzak TSP);
  live validation priority items: CompressorSpeed, Fan1Speed,
  ElectricPowerConsumption, AirInletTemp.
- EHP `01`-suffix register semantics: page/bank selector vs instance selector.
  Live scan comparing `XX00` vs `XX01` needed.

## References

- Public TypeSpec: [_templates.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/_templates.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant)
- Boiler register map: [`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md)
- Heat pump register map: [`ebus-vaillant-B509-heatpump-register-map.md`](ebus-vaillant-B509-heatpump-register-map.md)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
- Historical Vaillant reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
