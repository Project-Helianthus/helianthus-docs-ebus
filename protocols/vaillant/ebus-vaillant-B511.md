# Vaillant B511 Boiler-to-Controller Status / Remote Control Data

`PB=0xB5`, `SB=0x11`.

## Status

`B511` is modeled by john30 TypeSpec as a read/status family. Historical
Vaillant notes describe it as boiler/burner operational data back to the
room/controller. Helianthus has also observed topology-dependent triangular
source/target roles involving BAI00, BASV2, and NETX3.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.

## Known Selectors

| Selector | TypeSpec name | Response shape | Evidence | Falsification test |
|---:|---|---|---|---|
| `0x01` | `Status01` | flow temp, return temp, outside temp, DHW temp, storage temp, pump state | `LOCAL_TYPESPEC`, `PUBLIC_CAPTURE` | Capture `B511 01` and prove it does not return the modeled temperatures/pump state on a target claiming this profile. |
| `0x02` | `Status02` | DHW mode, max/current temperature pairs | `LOCAL_TYPESPEC`, `PUBLIC_CAPTURE` | Change DHW mode or target temperatures and show `B511 02` bytes do not track the changes. |
| `0x03` | `Status` | temperature, pressures, mode, hex/status byte | `LOCAL_TYPESPEC` | Capture `B511 03` and show it cannot decode to the modeled fields. |
| `0x07` | HMU `State` in `08.hmu.tsp` | 6-field payload including `State` UCH enum (see state table below) | `LOCAL_TYPESPEC`, `PUBLIC_CONFIG` (P4, issue #335) | Query HMU target and show the selector is unsupported or maps to a different field set. |
| `0x18 0x01/0x02` | compressor runtime/cycles on HW5103+ | runtime and cycles | `LOCAL_TYPESPEC` | Query matching firmware and show payload does not contain runtime/cycle counters. |

### Selector 0x07 State Enum (HMU Only)

> Source: `CROSSCHECK-B555-misc.md` B511 section; P4 (john30/ebusd issue #335, joergensen70 live HMU).

Selector `0x07` returns a 6-field response payload when targeting HMU at address `0x08`. The `State` field is a UCH enum with the following values. This selector and enum are **HMU/heat-pump-specific** — BAI00 at address `0x08` does NOT use selector `0x07` for this purpose.

| Value | snake_case | ebusd label | Description |
|-------|------------|-------------|-------------|
| `0x01` | `ready` | `ready` | Heat pump powered and ready, no active cycle |
| `0x09` | `heating` | `heating` | Active heating cycle |
| `0x0b` | `error` | `error` | Fault condition active |
| `0x11` | `cooling` | `cooling` | Active cooling cycle (reversible HP only) |
| `0x81` | `heating_water` | `heatingWater` | DHW (domestic hot water) heating cycle |

**Transitions:** ready -> heating (heating demand), ready -> heating_water (DHW demand), ready -> cooling (cooling demand, reversible HP). All active states -> ready (setpoint reached). Any state -> error (fault condition). error -> ready (fault cleared). These transitions mirror the `heat_pump_status` FSM (B509 `0xD000`) via a different protocol path.

**Related registers:** B509 `0xD000` HeatPumpStatus (parallel representation), B524 GG=0x00 RR=0x0048 `energy_manager_state`.

**Confidence:** HIGH for enum values (live HMU hardware, P4 source). The 6-field response shape applies to HMU target only; the field count and layout may differ on other device types at address `0x08`.

## Local Captures

Operator-provided traffic included:

```text
REQ:  10 08 b5 11 01 00
RESP: 09 8f 01 1e 00 00 10 11 80 00

REQ:  10 08 b5 11 01 01
RESP: 09 31 30 00 80 30 ff 00 01 ff

REQ:  10 08 b5 11 01 02
RESP: 06 03 3c 96 46 82 78
```

The second response is consistent with `Status01` length. The third response
does not match the simple `Status02` length exactly; treat it as target/profile
specific until correlated with product ID and firmware.

## Direction Caveat

The top-level Vaillant overview records these observed roles:

- BAI00 can initiate `B511` toward NETX3.
- BASV2 can initiate related control/status traffic toward BAI00.
- BAI00 can also respond as a target.

Additionally, on heat pump systems with VWZIO (indoor hydraulic station at address `0x76`), B511 traffic has been observed involving that device. (Source: `CROSSCHECK-B555-misc.md` B511 section; 4 independent community forks. Confidence: MEDIUM-HIGH — no Helianthus live VWZIO hardware.)

Therefore, do not infer semantics from `PB/SB` alone. Keep source, target,
selector, and response length in every specimen.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [08.hmu.HW5103.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.HW5103.tsp)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
