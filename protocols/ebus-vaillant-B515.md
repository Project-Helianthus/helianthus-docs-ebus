# Vaillant B515 Legacy Timer Template

`PB=0xB5`, `SB=0x15`.

## Status

`B515` appears in john30 TypeSpec templates as a generic read/write timer
family. It is distinct from the newer `B555` timer/schedule protocol documented
for VRC700/VRC720-style controllers.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec template defines:

```text
Read template:
  @base(MF, 0x15)
  ign : up to 1 ignored byte

Write template:
  @write
  @base(MF, 0x15)

Timer value:
  value : timer composite
```

Concrete timer include files add two selector bytes via `@ext(day, group)`.

## Known Selector Groups

| Include file | Group byte | TypeSpec names | Evidence | Falsification test |
|---|---|---|---|---|
| `timerhc_inc.tsp` | `00` | `HcTimer_Monday`..`HcTimer_Sunday` | `LOCAL_TYPESPEC` | Read `B515 <day> 00` from a legacy controller and show it cannot decode as a heating timer. |
| `timerhwc_inc.tsp` | `01` | `HwcTimer_Monday`..`HwcTimer_Sunday` | `LOCAL_TYPESPEC` | Same test for DHW timer windows. |
| `timercc_inc.tsp` | `02` | `CcTimer_Monday`..`CcTimer_Sunday` | `LOCAL_TYPESPEC` | Same test for circulation timer windows. |
| `timercool_inc.tsp` | `03` | `CoolingTimer_Monday`..`CoolingTimer_Sunday` | `LOCAL_TYPESPEC` | Same test for cooling timer windows. |
| `timertariff_inc.tsp` | `04` | `TariffTimer_Monday`..`TariffTimer_Sunday` | `LOCAL_TYPESPEC` | Capture a tariff timer read and show no B515 timer composite is used. |

## Relationship to B555

`B515` and `B555` should not be merged as one protocol. `B515` is modeled as a
generic legacy timer template with day/group selectors. `B555` uses explicit
schedule opcodes such as `A3`..`A6` and different payload semantics.

## Unknowns

- Which Vaillant controller generations still use B515 for user-visible
  schedules.
- Exact write ACK semantics.
- Whether B515 timers share setpoint coupling behavior with B524/B555 on any
  device class.

## References

- Public TypeSpec template: [_templates.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/_templates.tsp)
- Public TypeSpec: [timerhc_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/timerhc_inc.tsp)
- Public TypeSpec: [timerhwc_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/timerhwc_inc.tsp)
- B555 schedule protocol: [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
