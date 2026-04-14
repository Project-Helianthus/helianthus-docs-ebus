# Vaillant B514 Service Test Menu Values

`PB=0xB5`, `SB=0x14`.

## Status

`B514` appears in john30 TypeSpec files for HMU and VWZ/VWZIO service test-menu
values. The observed TypeSpec forms use an additional static selector byte
`0x05`, so the common configured prefix is `B5 14 05`.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec defines service-authenticated read and write templates:

```text
Read request payload:
  05 <selector>

Write/enable request payload:
  05 03 ff ff <selector>
```

The `03 ff ff` write prefix is a TypeSpec constant for the VWZ/VWZIO enable
template. HMU defines a second service write template with `00 00 00` for some
EEV temperature tests. Treat those constants as target/profile-specific until
verified by capture.

## Known Selectors

| Prefix | Selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|---|
| `05` | `02` | `TestThreeWayValve` / `EnableTestThreeWayValve` | read/write | 3-way valve state | `LOCAL_TYPESPEC` | Enable the test on isolated hardware and show `B514 05 02` does not track valve state. |
| `05` | `2c` | `TestHwcTemp` / `EnableTestHwcTemp` | read/write | HWC temperature, scaled | `LOCAL_TYPESPEC` | Enable the test and show `B514 05 2c` does not track the expected temperature. |
| `05` | `45` | `TestOutdoorTemp` | read | outdoor temperature, scaled | `LOCAL_TYPESPEC` | Capture the value while outdoor temperature changes and show no correlation. |
| `05` | `15` | `EnableTestEEVPosition` | write | EEV position test enable | `LOCAL_TYPESPEC` | Enable through service menu and show no matching `B514 05 15` traffic. |
| `05` | `3b` | `EnableTestEEVTemp` | write/read | EEV temperature test | `LOCAL_TYPESPEC` | Enable through service menu and show no matching `B514 05 3b` traffic. |

## Safety

`B514` belongs to service/test-menu behavior. Do not issue B514 writes on a live
installation unless the actuator or test mode is understood and the system is in
a safe state.

## Unknowns

- Whether `B514` read selectors require a preceding enable write on every
  target class.
- Exact status/ACK semantics for service test enable writes.
- Whether HMU and VWZ/VWZIO share all selector meanings or only a subset.

## References

- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [76.vwz.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/76.vwz.tsp)
- Public TypeSpec: [76.vwzio.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/76.vwzio.tsp)
