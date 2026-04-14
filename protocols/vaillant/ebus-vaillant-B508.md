# Vaillant B508 NoiseReduction Broadcast Protocol

`PB=0xB5`, `SB=0x08`.

## Status

**Enrichment research** -- not yet live-validated on a Helianthus bus.
B508 is a broadcast protocol (`ZZ=0xFE`) emitted when the NoiseReduction
timer activates or deactivates. It was absent from helianthus-docs-ebus
prior to this document.

Evidence labels:

- `P1_COMMUNITY`: ebusd community fork CSV for BASV2/VRC700 system timer
  configurations.
- `D5_DEEP`: D5-B555-B500-B508-deep.md cross-protocol analysis.

**Confidence:** MEDIUM-HIGH (wire format clear from ebusd CSV; purpose clear
from cross-protocol analysis; no live capture confirmation).

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
      ZZ = FE (broadcast -- no slave response)
QQ = source master (address unconfirmed from live capture)
```

### ebusd CSV Definition

```
*BRC,BRC,B5,08,02,IGN:1,State,,onoff,,State,,onoff
```

## Purpose

Broadcasts the noise reduction active/inactive state to all bus devices
when the NoiseReduction timer activates or deactivates.

## Cross-Protocol Stack

```
Timer channel activates/deactivates
  (B555 HC=0x04 on BASV2/VRC720)
  OR (B524 opcode 0x03 SEL1=0x00, SEL2=0x00, SEL3=0x02 on VRC700)
      |
      v
B508 broadcast (ZZ=FE, State1/State2 = on/off)
      |
      +---> EHP00 (0x08) -- updates B509 registers:
      |       A901 NoiseReduction (yesno)
      |       2401 NoiseReductionFactor (percent)
      |
      +---> OMU00 (0xE0) -- fan / compressor speed adjustment (inferred)
```

**Inferred -- not live-verified.** The causal chain (B508 broadcast -> EHP
B509 register update -> OMU behavior change) is architecturally plausible
but has no live capture confirmation. The EHP register names (A901, 2401)
come from community CSV definitions; the OMU fan speed adjustment is
inferred from device function, not observed.

## Device Matrix

| Device | Address | Role | Evidence |
|--------|---------|------|----------|
| BASV2 / VRC700 | `0x15` | Emitter | P1_COMMUNITY: timer configs for HC=0x04 / SEL 0x02 |
| EHP00 | `0x08` | Receiver | P1_COMMUNITY: B509 registers A901, 2401 documented -- register existence documented, B508->register update causal link not live-verified |
| OMU00 | `0xE0` | Receiver | **Inferred** from fan/compressor control function -- no live capture |

## Message Table

| ID (hex) | Name | Data fields | Direction | Confidence |
|----------|------|-------------|-----------|------------|
| `02` | noise_reduction_broadcast (`NoiseReductionBroadcast`) | IGN:1, State1:onoff, State2:onoff | master (`0x15`?) -> broadcast (`0xFE`) | MEDIUM-HIGH |

## Open Questions

- **State1 vs State2:** Both bytes present in the frame; whether they are
  always identical (redundant) or represent "requested vs active" states
  is unknown. No live capture available.
- **QQ source address:** Which master emits the broadcast is unconfirmed.
- **IGN byte content:** Purpose of the ignored byte between the ID and
  State1 is unknown.

## Cross-References

- **B555 HC=0x04:** NoiseReduction timer channel on BASV2/VRC720 systems.
  The B555 channel HC=0x04 is named "NoiseReduction" (BASV2 CSV) or
  "Silent" (VRC720 CSV). See
  [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md).
- **B524 opcode 0x03:** Timer channel SEL1=0x00, SEL2=0x00, SEL3=0x02 on
  VRC700 systems. See [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md).

## Falsifiable Claims

1. On a BASV2 system with an active NoiseReduction timer schedule
   (HC=0x04), a bus sniffer captures a frame with PBSB=`B508`, ZZ=`FE`,
   NN=`0x04`, ID=`0x02`, State=`0x01` at the start of the quiet window
   and State=`0x00` at the end.
2. EHP00 B509 register A901 (NoiseReduction) changes value in sync with
   the B508 broadcast.

## Evidence

- D5-B555-B500-B508-deep.md (cross-protocol analysis, B508 section)
- ebusd community fork CSV: `*BRC,BRC,B5,08,02,...` definition
