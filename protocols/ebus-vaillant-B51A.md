# Vaillant B51A Heat-Pump Statistics and Live-Monitor Values

`PB=0xB5`, `SB=0x1A`.

## Status

`B51A` is a selector-heavy heat-pump family in john30 HMU TypeSpec files. It
contains energy/yield/COP statistics, live-monitor values, compressor runtime
statistics, and installer-level test-menu statistics. Response prefix bytes are
not fully explained.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

Common configured read shape:

```text
Request payload:
  05 prefix_1 prefix_2 selector
```

Known configured `@base(MF, 0x1a, ...)` forms include:

| Static suffix after `1a` | Context | Evidence | Falsification test |
|---|---|---|---|
| `05 ff 32` | heat-pump daily/month/year yield/COP/consumption statistics | `LOCAL_TYPESPEC` | Query HMU devices and show selectors under `ff 32` do not return energy/COP-style payloads. |
| `05 ff 34` | compressor runtime/statistics group | `LOCAL_TYPESPEC` | Query HMU devices and show selectors under `ff 34` are unsupported or map to unrelated fields. |
| `05 e5 34` | passive alternate for compressor runtime/statistics group | `LOCAL_TYPESPEC` | Capture matching firmware and show `e5 34` traffic is unrelated to the `ff 34` group. |
| `05 00 32` | live-monitor desired/current supply, current power, compressor utilization, air intake temp | `LOCAL_TYPESPEC` | Enable live monitor and show selectors under `00 32` do not track live values. |
| `05` | installer statistics with selector-defined subgroups | `LOCAL_TYPESPEC` | Query installer-level stats on isolated hardware and show selector identity is not prefix-tuple dependent. |

## Known Selectors

Examples from HMU TypeSpec:

| Request suffix | Name | Value type | Evidence |
|---|---|---|---|
| `ff 32 00` | `YieldHcDay` | energy, kWh scaled | `LOCAL_TYPESPEC` |
| `ff 32 01` | `YieldCoolDay` | energy, kWh scaled | `LOCAL_TYPESPEC` |
| `ff 32 02` | `YieldHwcDay` | energy, kWh scaled | `LOCAL_TYPESPEC` |
| `ff 32 0e` | `YieldHcMonth` | energy, kWh scaled | `LOCAL_TYPESPEC` |
| `ff 32 0f` | `CopHcMonth` | COP-style value | `LOCAL_TYPESPEC` |
| `00 32 1f` | `LiveMonitorDesiredSupplyTemp` | temperature | `LOCAL_TYPESPEC` |
| `00 32 20` | `LiveMonitorCurrentSupplyTemp` | temperature | `LOCAL_TYPESPEC` |
| `00 32 23` | `LiveMonitorCurrentYieldPower` | `UIN / 10` kW | `LOCAL_TYPESPEC` |
| `00 32 24` | `LiveMonitorCurrentConsumedPower` | `UIN / 10` kW | `LOCAL_TYPESPEC` |
| `00 32 25` | `LiveMonitorCurrentCompressorUtil` | percent | `LOCAL_TYPESPEC` |
| `00 32 26` | `LiveMonitorAirIntakeTemp` | temperature | `LOCAL_TYPESPEC` |

## Local Captures

Operator-provided traffic included several `B51A` frames such as:

```text
REQ:  f1 08 b5 1a 04 05 00 0c 00
RESP: 0a 00 02 46 ff 00 25 00 ff 00 0a

REQ:  f1 08 b5 1a 04 05 00 0c 4d
RESP: 0a 00 02 47 46 01 25 00 46 01 0a
```

These use prefix `00 0c`, not the HMU `00 32` live-monitor prefix documented
above. Treat the `00 0c` group as observed but not decoded here.

## Unknowns

- Meaning of response prefix bytes and whether they echo request selectors,
  encode status, or identify data groups.
- Whether prefix tuples are firmware-specific, hardware-specific, or both.
- Mapping for the locally observed `05 00 0c xx` request group.

## References

- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [08.hmu.HW5103.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.HW5103.tsp)
