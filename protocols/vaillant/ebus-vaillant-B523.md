# Vaillant B523 Functional Module Actor and Sensor Data

`PB=0xB5`, `SB=0x23`.

The public TypeSpec template defines `MF = 0xb5`, so `@base(MF, 0x23)` in the
VR70/VR71 TypeSpec files is a direct B523 identifier, not an inferred mapping.

## Status

`B523` is a functional-module protocol family in john30 TypeSpec files. It is
defined for `VR_71` and two `VR_70` TypeSpec profiles (`52.vr_70.tsp` and
`53.vr_70.5.tsp`), which correspond to profile names `FM5` and `FM3` in
Vaillant controller documentation. The profile names are not wire-level protocol
identifiers; the wire evidence is the target address and device identity.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Device-Specific Shapes

### VR_71 / FM5-style target (`0x26`)

The `26.vr_71.tsp` TypeSpec uses `@base(MF, 0x23)` for both reads and writes.

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `05` | `SetActorState` | write | relay states `r1..r12` plus two raw bytes | | Change one relay through a safe test fixture and prove the corresponding byte does not track the actor state. |
| `02 00` | `Mc1Operation` | write | status, desired flow temp, pump, mixer | | Capture controller-to-VR71 traffic while circuit 1 pump/mixer changes and show these bytes do not correlate. |
| `02 01` | `Mc2Operation` | write | status, desired flow temp, pump, mixer | | Same test for circuit 2. |
| `02 02` | `Mc3Operation` | write | status, desired flow temp, pump, mixer | | Same test for circuit 3. |
| `06` | `SensorData1` | read | sensors `s1..s7` plus two raw bytes | | Read from VR71 and show response cannot decode as seven temperatures plus two bytes. |
| `07` | `SensorData2` | read | sensors `s8..s12`, `Sx`, plus three raw bytes | | Read from VR71 and show response cannot decode as six temperatures plus three bytes. |

No publishable capture is included in this reference.

## VR_70 / FM3-style target (`0x52`)

The `52.vr_70.tsp` and `53.vr_70.5.tsp` TypeSpec files also use
`@base(MF, 0x23)` for reads and writes, but their selector set is smaller than
the VR71 set. Both local files comment `@zz(0x52)`, so treat `53.vr_70.5.tsp`
as a profile/file variant unless a capture proves a distinct target address.

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `01` | `SetActorState` | write | relay states `r1..r6`, `s7` | | On isolated hardware, change one actor and show the mapped byte does not track it. |
| `02 00` | `Mc1Operation` | write | status, desired flow temp, pump, mixer | | Capture a VR70 target while circuit 1 changes and show the bytes do not correlate. |
| `02 01` | `Mc2Operation` | write | status, desired flow temp, pump, mixer | | Same test for circuit 2. |
| `03` | `SensorData` | read | sensors `s1..s6` plus three raw bytes | | Read from VR70 and show response cannot decode as six temperatures plus three bytes. |

## Relationship to B524 Functional-Module Semantics

`B524` carries controller-side structural/configuration information that can
support a functional-module inventory. `B523` is the
direct module traffic for actor commands and sensor snapshots on VR70/VR71-like
targets. Do not use B523 alone to infer the whole hydraulic scheme; correlate it
with device identity, B524 functional-module inventory, and physical wiring.

## Observation status

## Unknowns

- Exact physical terminal mapping for every relay/sensor byte across all VR70
  and VR71 configurations.
- Whether `VR_70` at target `0x52` is the only FM3 address form; Vaillant
  product documentation describes FM3 as addressable/multi-instance, but that
  is profile evidence, not a B523 wire rule by itself.
- Whether response bytes such as `02 01 9c` on operation writes are stable ACK
  semantics or target-state dependent status.

## References

- Public TypeSpec: [26.vr_71.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/26.vr_71.tsp)
- Public TypeSpec: [52.vr_70.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/52.vr_70.tsp)
- Public TypeSpec: [53.vr_70.5.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/53.vr_70.5.tsp)
- B524 functional-module register map: [`ebus-vaillant-B524-register-map.md`](ebus-vaillant-B524-register-map.md)
