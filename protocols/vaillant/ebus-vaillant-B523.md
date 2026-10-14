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

## Candidate layouts

The candidate layouts of B523 cover the ops `B5 23 00` to `B5 23 07`; none of it
has been confirmed on the wire. Offsets count from the first byte of the service
prefix (PB, SB and the op byte): offset 0 = `B5`, 1 = `23`, 2 = op byte. A target
response on the bus carries no such prefix (eBUS framing: `NN`, data, CRC); how
the candidate response offsets map onto the bytes of a bus response is
unconfirmed on the wire. **Hypothesis**: response offset 3 is the first data byte
of a bus response (see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)).

| Op | Candidate meaning |
|---|---|
| `00` | configuration of the relay groups and inputs |
| `01` | output control |
| `02` | mixer circuit control |
| `03` | read sensor values |
| `04` | configuration |
| `05` | output control |
| `06` | read sensor values, part 1 |
| `07` | read sensor values, part 2 |

- **Output control** (`01`, `05`): candidate, unconfirmed on the wire: relay
  value `u8` where `0` is off, `1..253` is on for that many seconds, `254` is on
  and `255` is not influenced; PWM `0..200` is 0 to 100 %, `201..255` is not
  influenced. The reply is a feedback byte where `1` means accepted.
- **Mixer circuit control** (`02`): candidate, unconfirmed on the wire: circuit
  number `u8` at offset 3, control mode from `0` stop to `5` pump on and open, and
  a setpoint at offset 5, `i8` × 0.5 °C in one candidate reading (its range and
  signedness are unresolved; see Open questions). The reply carries a feedback
  byte and the speed and direction of the mixer movement. This is consistent with
  the `02 00`..`02 02` circuit operation writes above; the reply bytes `02 01 9c` in
  the open questions are not explained by it.
- **Sensor reads** (`03`, `06`, `07`): candidate, unconfirmed on the wire: six or
  more multiplexed values in which raw `32768` (`8000`) is a reserved value whose
  meaning is unresolved; otherwise the value is `i16` LE ÷16 °C. Each input also
  has a 2-bit status.
- **Configuration** (`00`, `04`): candidate, unconfirmed on the wire: relay-group
  and input configuration bytes; the reply is a feedback byte where `1` means
  accepted.

**Hypothesis**, unconfirmed on the wire: candidate op `02` (mixer circuit
control) corresponds to the `02 xx` selectors of both target shapes above; the
candidate ops `01` and `03` correspond to the selectors `01` and `03` of the
second shape, and the candidate ops `05`, `06` and `07` to the selectors `05`,
`06` and `07` of the first shape.

No op on this page is documented as safe to send; a state-changing op needs a separately established safety procedure and target qualification, and an ACK does not show the resulting device state.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Observation status

## Open questions

- The candidate ops are known only as candidate layouts; no exchange of them was
  observed beyond the reply bytes on this page, and whether any device
  implements them is not established.
- The candidate mixer setpoint of `02` (offset 5) is a signed byte × 0.5 °C
  (range -64 to 63.5 °C); a second candidate range of 190 to 95 for the same
  setpoint conflicts with it, and the intended range and the signedness of this
  field are unresolved.
- The coding of the feedback value of `00`, `04` and the speed and direction
  field of the `02` reply beyond "1 = accepted" is unknown.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.
- The meaning of the reserved raw value `32768` (`8000`) of the sensor reads
  (`03`, `06`, `07`) is unresolved.
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
