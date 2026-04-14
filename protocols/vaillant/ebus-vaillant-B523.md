# Vaillant B523 Functional Module Actor and Sensor Data

`PB=0xB5`, `SB=0x23`.

The local TypeSpec template defines `MF = 0xb5`, so `@base(MF, 0x23)` in the
VR70/VR71 TypeSpec files is a direct B523 identifier, not an inferred mapping.

## Status

`B523` is a functional-module protocol family in john30 TypeSpec files. It is
defined for `VR_71` and two `VR_70` TypeSpec profiles (`52.vr_70.tsp` and
`53.vr_70.5.tsp`), which correspond to profile names `FM5` and `FM3` in
Vaillant controller documentation. The profile names are not wire-level protocol
identifiers; the wire evidence is the target address and device identity.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Device-Specific Shapes

### VR_71 / FM5-style target (`0x26`)

The `26.vr_71.tsp` TypeSpec uses `@base(MF, 0x23)` for both reads and writes.

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `05` | `SetActorState` | write | relay states `r1..r12` plus two raw bytes | `LOCAL_TYPESPEC` | Change one relay through a safe test fixture and prove the corresponding byte does not track the actor state. |
| `02 00` | `Mc1Operation` | write | status, desired flow temp, pump, mixer | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Capture controller-to-VR71 traffic while circuit 1 pump/mixer changes and show these bytes do not correlate. |
| `02 01` | `Mc2Operation` | write | status, desired flow temp, pump, mixer | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Same test for circuit 2. |
| `02 02` | `Mc3Operation` | write | status, desired flow temp, pump, mixer | `LOCAL_TYPESPEC` | Same test for circuit 3. |
| `06` | `SensorData1` | read | sensors `s1..s7` plus two raw bytes | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Read from VR71 and show response cannot decode as seven temperatures plus two bytes. |
| `07` | `SensorData2` | read | sensors `s8..s12`, `Sx`, plus three raw bytes | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Read from VR71 and show response cannot decode as six temperatures plus three bytes. |

Operator-provided traffic included examples consistent with the VR71 mapping:

```text
REQ:  10 26 b5 23 01 06
RESP: 10 cd 00 0c 01 1e 01 00 80 e7 02 e9 02 76 05 40 00

REQ:  10 26 b5 23 01 07
RESP: 0f 5a 01 00 80 00 80 00 80 03 00 00 00 80 54 04

REQ:  10 26 b5 23 04 02 00 00 00
RESP: 02 01 9c
```

These prove local B523 traffic on target `0x26`, but they do not by themselves
prove every field label without correlation against physical terminals.

### VR_70 / FM3-style target (`0x52`)

The `52.vr_70.tsp` and `53.vr_70.5.tsp` TypeSpec files also use
`@base(MF, 0x23)` for reads and writes, but their selector set is smaller than
the VR71 set. Both local files comment `@zz(0x52)`, so treat `53.vr_70.5.tsp`
as a profile/file variant unless a capture proves a distinct target address.

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `01` | `SetActorState` | write | relay states `r1..r6`, `s7` | `LOCAL_TYPESPEC` | On isolated hardware, change one actor and show the mapped byte does not track it. |
| `02 00` | `Mc1Operation` | write | status, desired flow temp, pump, mixer | `LOCAL_TYPESPEC` | Capture a VR70 target while circuit 1 changes and show the bytes do not correlate. |
| `02 01` | `Mc2Operation` | write | status, desired flow temp, pump, mixer | `LOCAL_TYPESPEC` | Same test for circuit 2. |
| `03` | `SensorData` | read | sensors `s1..s6` plus three raw bytes | `LOCAL_TYPESPEC` | Read from VR70 and show response cannot decode as six temperatures plus three bytes. |

## Relationship to B524 Functional-Module Semantics

`B524` carries controller-side structural/configuration information used by
Helianthus to infer functional-module presence and ownership. `B523` is the
direct module traffic for actor commands and sensor snapshots on VR70/VR71-like
targets. Do not use B523 alone to infer the whole hydraulic scheme; correlate it
with device identity, B524 functional-module inventory, and physical wiring.

## Local MCP State

At the time of this documentation pass, the current live MCP bus summary did
not list `B523`, and `bus_protocol_specimens_list(family="B523")` returned no
items. That only proves the current observe-first specimen buffer did not retain
B523 frames. The operator-provided ebusd dump did contain `1026b523...` VR71
traffic.

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
- Local TypeSpec template: `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/_templates.tsp`
- Functional-module architecture: [`../../architecture/functional-modules.md`](../../architecture/functional-modules.md)
- B524 functional-module register map: [`ebus-vaillant-B524-register-map.md`](ebus-vaillant-B524-register-map.md)
