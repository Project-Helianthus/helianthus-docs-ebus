# Vaillant B508 NoiseReduction Broadcast Protocol

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

`PB=0xB5`, `SB=0x08`.

## Status

**Hypothesis** -- not live-validated on a tested bus.
The candidate B508 broadcast (`ZZ=0xFE`) is associated with NoiseReduction
timer activation or deactivation. No independent capture is included here.

Evidence labels:

- `P1_COMMUNITY`: ebusd community fork CSV for VRC720-family and VRC700-family
  system timer configurations.

**Qualification:** candidate CSV layout; the purpose and causal chain below
remain hypotheses without independently inspectable capture confirmation.

## Wire Format

```
QQ FE B5 08 04 02 XX SS SS CRC
               |  |  |  |  +-- CRC byte
               |  |  |  +---- State2 (onoff: 0x00=off, 0x01=on)
               |  |  +------- State1 (onoff: 0x00=off, 0x01=on)
               |  +---------- IGN byte (content unknown)
               +------------- Message ID = 0x02
            NN = 0x04 (data length)
         PBSB = B5 08
      ZZ = FE (broadcast -- no target response)
QQ = source initiator (address unconfirmed from live capture)
```

### ebusd CSV Definition

```
*BRC,BRC,B5,08,02,IGN:1,State,,onoff,,State,,onoff
```

## Purpose

**Hypothesis:** broadcasts the noise reduction active/inactive state when
the NoiseReduction timer activates or deactivates.

## Cross-Protocol Stack

```
Timer channel activates/deactivates
  (B555 HC=0x04 on VRC720-family controllers)
  OR (B524 opcode 0x03 SEL1=0x00, SEL2=0x00, SEL3=0x02 on VRC700-family controllers)
      |
      v
B508 broadcast (ZZ=FE, State1/State2 = on/off)
      |
      +---> heat pump (0x08) -- updates B509 registers:
      |       A901 NoiseReduction (yesno)
      |       2401 NoiseReductionFactor (percent)
      |
      +---> outdoor unit (0xE0) -- fan / compressor speed adjustment (inferred)
```

**Inferred -- not live-verified.** The causal chain (B508 broadcast -> EHP
B509 register update -> OMU behavior change) is architecturally plausible
but has no live capture confirmation. The EHP register names (A901, 2401)
come from community CSV definitions; the OMU fan speed adjustment is
inferred from device function, not observed.

## Device Matrix

| Device | Address | Role | Evidence |
|--------|---------|------|----------|
| VRC720-family / VRC700-family controller | `0x15` | Emitter | P1_COMMUNITY: timer configs for HC=0x04 / SEL 0x02 |
| Heat pump | `0x08` | Receiver | P1_COMMUNITY: B509 registers A901, 2401 documented -- register existence documented, B508->register update causal link not live-verified |
| Outdoor unit | `0xE0` | Receiver | **Inferred** from fan/compressor control function -- no live capture |

## Message Table

| ID (hex) | Name | Data fields | Direction | Confidence |
|----------|------|-------------|-----------|------------|
| `02` | noise_reduction_broadcast (`NoiseReductionBroadcast`) | IGN:1, State1:onoff, State2:onoff | initiator (`0x15`?) -> broadcast (`0xFE`) | Candidate; not capture-verified |

## Candidate layouts

The candidate layouts of B508 cover the ops `B5 08 01` to `B5 08 0B`,
unconfirmed on the wire. They carry control values from a controller to a heat
generator or boiler (configuration, set flow temperatures, DHW, pump release,
heat demand, noise reduction demand, storage temperatures, solar cascading).
None of it has been confirmed on the wire. The field-level layout of every op
is in
[`fixtures/b506-b508-candidate-fields.csv`](fixtures/b506-b508-candidate-fields.csv);
`vaillant_name` in that file is a correspondence column (Vaillant name,
correspondence only), not a canonical name.

Offsets count from the first byte of the service prefix (PB, SB and the op
byte): offset 0 = `B5`, 1 = `08`, 2 = op byte. A target response on the bus
carries no such prefix (eBUS framing: `NN`, data, CRC); how the candidate
response offsets map onto the bytes of a bus response is unconfirmed on the
wire. The request length NN counts the op byte plus its data bytes.
**Hypothesis**: response offset 3 is the first data byte of a bus response (see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)).

| Op | Candidate description | Request NN | Reply bytes |
|---|---|---:|---:|
| `B5 08 01` | boiler configuration (write) | 2 | 0 |
| `B5 08 02` | boiler 1 set flow temperature (`u8` °C, 0..90) | 2 | 0 |
| `B5 08 03` | boiler 2 set flow temperature (`u8` °C, 0..90) | 2 | 0 |
| `B5 08 04` | boiler DHW | 2 | 0 |
| `B5 08 05` | boiler pump (KP) release | 2 | 0 |
| `B5 08 06` | heat demand for the solar circuit | 2 | 0 |
| `B5 08 07` | heat demand for the ASC | 7 | 0 |
| `B5 08 08` | KP / AV | 2 | 0 |
| `B5 08 09` | noise reduction demand | 2 | 0 |
| `B5 08 0A` | set storage temperatures | 5 | 1 |
| `B5 08 0B` | solar cascading | 4 | 1 |

- `01`: candidate, unconfirmed on the wire: a `u8` where `0` is false and `1` is
  true; `04` and `08` carry `u8` where `1` is on and any other value is off.
- `05`: candidate, unconfirmed on the wire: bit 0 of the data byte is `0` blocked
  or `1` released (the other 7 bits are reserved).
- `06`: candidate, unconfirmed on the wire: heat demand `1` no heat demand, `2`
  heat demand; raw `0` has no known meaning.
- `07`: candidate, unconfirmed on the wire: DHW request `u8` @3 and CH request
  `u8` @4 (`0` no request, `1` request), DHW flow setpoint `i16` LE ÷16 °C @5 and
  CH flow setpoint `i16` LE ÷16 °C @7.
- `09`: candidate, unconfirmed on the wire: bit 0 of the data byte is `0`
  disabled or `1` enabled; the other 7 bits are reserved.
- `0A`: candidate, unconfirmed on the wire: storage sensor SP2 `i16` LE ÷16 °C @3
  and sensor T6 `i16` LE ÷16 °C @5; the reply is a `u8` feedback @3 (`1`
  accepted, any other value not accepted).
- `0B`: candidate, unconfirmed on the wire: three flags in separate bytes (cycle
  pause @3, solar temperature reached @4 and @5); the reply is a `u8` feedback @3
  (`1` accepted, otherwise not accepted).

Candidate, unconfirmed on the wire: the noise reduction demand is at op `09` (one
bit), while the community configuration above places a broadcast at op `02` with
an ignored byte and two states; the relation is unresolved.

Candidate, unconfirmed on the wire: op `02` itself has two layouts. The
candidate layout gives `02` as the boiler 1 set flow temperature (one `u8` °C
data byte, NN=2), whereas the community configuration above gives `02` as the
broadcast with NN=04, an ignored byte, State1 and State2; which layout op `02`
carries is unresolved.

No op on this page is documented as safe to send; a state-changing op needs a separately established safety procedure and target qualification, and an ACK does not show the resulting device state.

## Pump roles and independent solar flags

**Hypothesis:** these B508 family declarations are candidate interpretations,
not physical behavior. The boiler-pump correspondence is role-qualified;
universal boiler support and exclusivity to one appliance remain **Unknown**.

Logical positions include PB, SB and the operation at positions 0, 1 and 2;
they are not established physical offsets. The following scoped alternatives
preserve absent extents as **Unknown**, not zero. They do not replace the
separately qualified candidate layouts above.

| Family | Variant | Direction | Service | Operation | Alternative | Logical extent | Grade | Physical qualification |
|---|---|---|---|---|---|---|---|---|
| B508 | pump role | Unknown | B508 | OP05 | candidate default | Unknown | Hypothesis | Unknown |
| B508 | solar cascading | Unknown | B508 | OP0B | independent tank flags | Unknown | Hypothesis | Unknown |
| B508 | noise-reduction | broadcast | B508 | OP02 | distinct noise-reduction candidate | Unknown | Hypothesis | Unknown |

| Operation | Field | Logical position | Candidate declaration | Operational default | Grade |
|---|---|---|---|---|---|
| OP05 | pump state | Unknown | raw 0 = blocked; raw 1 = released | blocked (candidate) | Hypothesis |
| OP0B | cycle-pause | 3 | interpretation unresolved in this scoped alternative | Unknown | Hypothesis |
| OP0B | tank-one flag byte | 4 | bit 0 = flag; bits 1..7 reserved | Unknown | Hypothesis |
| OP0B | tank-two flag byte | 5 | bit 0 = flag; bits 1..7 reserved | Unknown | Hypothesis |

Cycle-pause is a **Hypothesis** candidate label at logical position 3.
Here, "interpretation unresolved" leaves its physical meaning and operational
default **Unknown**; the earlier candidate flag declaration remains a separate
qualified layout.

Each tank byte is unsigned and one byte wide. Its candidate flag conversion is
`(raw & 1) >> 0`; 0 means flag clear and 1 means flag set. No bit in one tank
byte supplies the other tank's state. Preserve the complete raw bytes, including
reserved bits and unmapped values; reserved bits have no assigned meaning.

| Synthetic tank-one / tank-two bytes | Flag one | Flag two | Reserved one / two |
|---|---|---|---|
| 01 / 00 | 1 | 0 | 00 / 00 |
| 00 / 01 | 0 | 1 | 00 / 00 |
| 80 / 00 | 0 | 0 | 80 / 00 |

The synthetic examples in [`fixtures/ac08_pump_roles.json`](fixtures/ac08_pump_roles.json)
validate only the declared representation. **Proven** applies only to software
verification of that representation; physical interpretations remain
**Hypothesis**. Native adaptation, peer effects and physical qualification
remain **Unknown**. No runtime capability or permission to send follows.

The OP05 candidate operational default is blocked (**Hypothesis**); released
is the meaning of raw value 1, not a second default. Physical qualification
remains **Unknown**.
The existing OP02 NoiseReduction broadcast remains a distinct candidate and is
not replaced by the pump form. A candidate broadcast, timer and later register
change establish no causal chain, physical support or exclusive use. An actuator
effect remains **Unknown**.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Open Questions

- **State1 vs State2:** Both bytes present in the frame; whether they are
  always identical (redundant) or represent "requested vs active" states
  is unknown. No live capture available.
- **QQ source address:** Which initiator emits the broadcast is unconfirmed.
- **IGN byte content:** Purpose of the ignored byte between the ID and
  State1 is unknown.
- **Candidate versus community layout:** the candidate noise reduction demand
  (op `09`, one bit) and the community broadcast (op `02`, three data bytes)
  are not reconciled.
- **Op `02` collision:** the candidate op `02` (boiler 1 set flow temperature,
  NN=2) and the community broadcast at op `02` (NN=04, IGN, State1, State2) are
  not reconciled; which layout op `02` carries is unresolved.
- **Candidate ops:** known only as candidate layouts; no exchange of them was
  observed beyond the examples on this page, and whether any device implements
  them is not established.
- **Feedback semantics:** whether a reply value other than `1` for `0A` and
  `0B` distinguishes refusal reasons is unknown.
- **Response offsets:** how the candidate response offsets map onto the data
  bytes of a bus response is unconfirmed on the wire.

## Cross-References

- **B555 HC=0x04:** NoiseReduction timer channel on VRC720-family systems.
  The B555 channel HC=0x04 is named "NoiseReduction" in one community CSV and
  "Silent" in another. See
  [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md).
- **B524 opcode 0x03:** Timer channel SEL1=0x00, SEL2=0x00, SEL3=0x02 on
  VRC700-family systems. See [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md).

## Falsifiable Claims

1. On a VRC720-family system with an active NoiseReduction timer schedule
   (HC=0x04), a bus sniffer captures a frame with PBSB=`B508`, ZZ=`FE`,
   NN=`0x04`, ID=`0x02`, State=`0x01` at the start of the quiet window
   and State=`0x00` at the end.
2. Heat-pump B509 register A901 (NoiseReduction) changes value in sync with
   the B508 broadcast.

## Evidence

- ebusd community fork CSV: `*BRC,BRC,B5,08,02,...` definition
