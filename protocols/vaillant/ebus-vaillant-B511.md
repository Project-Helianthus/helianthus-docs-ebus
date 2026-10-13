# Vaillant B511 Boiler-to-Controller Status / Remote Control Data

`PB=0xB5`, `SB=0x11`.

## Status

`B511` is modeled by john30 TypeSpec as a read/status family. Historical
Vaillant notes describe it as boiler/burner operational data back to the
room/controller. Observed source/target roles are topology-dependent and
involve a boiler, a VRC720-family controller and an internet gateway (see the
Direction Caveat).

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.
- `CANDIDATE`: a layout, a request or a reply that is not confirmed on the
  wire. Every `CANDIDATE` statement is **Hypothesis**, unconfirmed on the wire.

## Known Selectors

| Selector | TypeSpec name | Response shape | Evidence | Falsification test |
|---:|---|---|---|---|
| `0x01` | `Status01` | flow temp, return temp, outside temp, DHW temp, storage temp, pump state | `PUBLIC_CAPTURE` | Capture `B511 01` and prove it does not return the modeled temperatures/pump state on a target claiming this profile. |
| `0x02` | `Status02` | DHW mode, max/current temperature pairs | `PUBLIC_CAPTURE` | Change DHW mode or target temperatures and show `B511 02` bytes do not track the changes. |
| `0x03` | `Status` | temperature, pressures, mode, hex/status byte | | Capture `B511 03` and show it cannot decode to the modeled fields. |
| `0x07` | HMU `State` in `08.hmu.tsp` | 6-field payload including `State` UCH enum (see state table below) | `PUBLIC_CONFIG` (P4, issue #335) | Query HMU target and show the selector is unsupported or maps to a different field set. |
| `0x18 0x01/0x02` | compressor runtime/cycles on HW5103+ | runtime and cycles | | Query matching firmware and show payload does not contain runtime/cycle counters. |

### Selector 0x07 State Enum (HMU Only)

> Hypothesis from public community sources; no publishable capture is included here.

Selector `0x07` returns a 6-field response payload when targeting HMU at address `0x08`. The `State` field is a UCH enum with the following values. This selector and enum are **HMU/heat-pump-specific** — a boiler at address `0x08` does NOT use selector `0x07` for this purpose.

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

## Operating-data classes (candidate)

> **Hypothesis**, unconfirmed on the wire: the table lists the B511 sub-commands
> (the first payload byte) with a candidate layout. Quoted names are Vaillant
> names, kept as correspondence names only.

| `OP` | Candidate name | Reply content (candidate) |
|---:|---|---|
| `00` | detailed operational data | nine data bytes: flow temperature s16 /16 °C (bytes 0..1), pressure u8 /10 bar (2), modulation value 1 u8 raw/2 (3), burner status ASCII (4), three status bytes (5..7), modulation value 2 u8 raw/2 percent (8) |
| `01` | compressor operating data | see the next section |
| `02` | upper/lower limits of CH and DHW setpoint, operating-mode info | six data bytes: status info (0), lower and upper CH setpoint limit (1, 2; u8 raw/2 °C), lower and upper DHW setpoint limit (3, 4; u8 raw/2 °C), current DHW setpoint (5; u8 raw/2 °C) — this differs from the community `Status02` reading (DHW mode, maximum/current temperature pairs); the discrepancy is unresolved. |
| `03` | operational data from a heat pump | flow temperature s16 /16 °C, pressures of the CH and brine circuits (u16, mbar), heat-up basic status number, status info, message number |
| `04` | zeolite data | control byte in the request; status info, flow and return temperature |
| `05` | data for `p2` (a Vaillant name; expansion unknown) | CH and DHW setpoints, status infos |
| `06` | operational data AI-BMU | minimum/maximum CH, DHW, water pressure and cooling setpoints, status infos |
| `07` | operational data AI-HMU | current power, energy per day (u16 kWh), actual states, status info |
| `08` | fresh-water station | current DHW setpoint, current tapping volume, status |
| `09` | operational data for solar station AI | collector temperature, solar yield of the current day (u16 kWh), current solar power, status |
| `0A` | operational data for solar station BMU | status byte (solar station error, solar loading active) |
| `0B` | recovery ventilation | current airflow (u16 m³/h), bargraph value (u8 %), status |
| `0C` | standby information | operating state, switch-on information |
| `0D` | shift-load storage | DHW state byte (system error, circulation function, DHW function, legionella-protection function) |
| `0E` | communication-module status | one status byte |
| `0F` | operational data of an appliance controller | binding of a zone to the remote controller, special-function status, heating mode, display wish temperature, quick-veto end time |
| `10` | operational data of the burner control and interface electronics | header-only candidate; no field layout is known |
| `11` | retrieve setpoints | header-only candidate; no field layout is known |

In the candidate layouts (unconfirmed on the wire), several requests carry
assistant, control or configuration bytes, so the family has no single
empty-request form. Request-side fields of two classes (candidate, unconfirmed
on the wire): class `0A` carries the tank temperature (s16 /16 °C) and an
actuator byte (bit 0 activate legionella pump, bit 1 deactivate solar
function) in the request; class `0D` carries the DHW storage setpoint (u8,
raw/2 °C) and a DHW configuration byte (primary pump available, circulation
release, DHW release, legionella-protection release and abort) in the request.
These fields are not part of the replies in the table.

Candidate codec notes (unconfirmed on the wire):

- Classes `08` (DHW setpoint) and `09` (collector temperature) choose a
  variant from the same bytes as the value (candidate): raw `8000` is a
  candidate replacement value (no value available) in place of the signed
  little-endian s16 /16 °C value. Class `0B` airflow uses raw `8000` before
  u16 m³/h and bargraph raw `FF` before u8 % (candidate). Whether raw `8000`
  means "invalid" or "unavailable" is not established.
- Class `0F` special function (candidate): the base values are `0` none, `1`
  ventilation boost, `4` quick veto, `7` holiday and `10` system off. No
  universal enumeration is established; candidate additional values include
  `3` Party, `5` OneDayHoliday, `6` OneDayBankHoliday and `8` BankHoliday, and
  `11` = ManualCooling on some targets. Heating mode (candidate) is `0` off,
  `1` auto, `2` day, `3` setback.
- Class `0E` status byte (candidate, unconfirmed on the wire): bit 0 LAN, 1
  WLAN, 2 eBUS, 3 PeBUS, 4 backend, 5 scan available, 6 firmware update, 7
  reserved.
- The six-field heat-pump payload with the `State` enumeration documented
  above for selector `0x07` and the candidate class `07` (current power,
  energy per day, actual states, status info) may or may not describe the
  same reply; the relationship is unresolved.

Candidate, unconfirmed on the wire: every class with a candidate layout (`00`
to `0F`) is available under both the eBUS and the PeBUS profiles; none is known
to be available only on PeBUS. The profile availability of the header-only
entries (B511 `10`, `11`) is not established.

## B5 11 01 failure-mode read (candidate)

> **Hypothesis**, unconfirmed on the wire. The request is the one sent by a
> Vaillant requester that polls heat-pump targets; no frame of it with a
> heat pump is confirmed on the wire.

```text
QQ ZZ B5 11 01 01
```

`QQ` is the requester's address, `NN` = `0x01`, payload `01` = class `01`
(compressor operating data) (candidate, unconfirmed on the wire). The requester reads
nine reply bytes and uses bit 0 of the eighth data byte (index 7) as the
target's failure indication (`0` or `1`) (candidate, unconfirmed on the wire).

Candidate layout of the nine reply data bytes of class `01` (index 0 is the
first byte after the length byte):

| Index | Candidate meaning | Encoding |
|---:|---|---|
| 0 | flow temperature | u8, raw/2 °C |
| 1 | return temperature | u8, raw/2 °C |
| 2..3 | outdoor temperature (direct sensor value, no offset included) | s16 LE, raw/256 °C |
| 4 | DHW temperature | u8, raw/2 °C |
| 5 | tank temperature | u8, raw/2 °C |
| 6 | status info 4 | bit 0 flame on in heating, 1 flame on in DHW tapping, 2 flame on in tank loading, 3 chimney-sweep/test, 4 solar pump running, 5 flame on in warm start, 6 DHW active, 7 cooling test mode |
| 7 | status info 5 | bit 0 boiler error, 1 maintenance status, 2 legionella-protection status, 3 end-user-resettable error, 4 refill heating water, 5 enable remote reset screen, 6..7 reserved |
| 8 | external flow/return sensor | u8, raw/2 °C; `FF` = sensor error |

The nine-byte length matches the second capture in "Local Captures" below.
Whether a heat pump answers with this layout, and whether bit 0 of index 7
is the bit the requester treats as a failure, is unresolved.

## Local Captures

No publishable capture is included; the following shape was reported as:

```text
REQ:  10 08 b5 11 01 00
RESP: 09 8f 01 1e 00 00 10 11 80 00

REQ:  10 08 b5 11 01 01
RESP: 09 31 30 00 80 30 ff 00 01 ff

REQ:  10 08 b5 11 01 02
RESP: 06 03 3c 96 46 82 78
```

The first response has the nine data bytes of the candidate class `00` reply,
and the third response has the six data bytes of the candidate class `02`
reply (candidate, unconfirmed on the wire). The second response is consistent
with `Status01` length. The third response does not match the simple `Status02`
length exactly; treat it as target/profile specific until correlated with
product ID and firmware.

## Direction Caveat

The top-level Vaillant overview records these observed roles:

- A boiler can initiate `B511` toward an internet gateway.
- A VRC720-family controller can initiate related control/status traffic
  toward the boiler.
- The boiler can also respond as a target.

VWZIO involvement at address `0x76` remains a hypothesis pending a publishable capture.

Therefore, do not infer semantics from `PB/SB` alone. Keep source, target,
selector, and response length in every specimen.

## Open questions

- No frame of the B5 11 01 failure-mode read (with a heat pump) has been
  captured.
- Whether bit 0 of data byte 7 of class `01` is what the requester treats as
  the failure flag on every target that answers.
- The bit meanings of the class `0E` status byte are unconfirmed on the wire;
  the bit order in the codec notes is a candidate.
- Class `02`: the candidate layout and the community `Status02` reading
  differ. The 6-byte capture in Local Captures has the length of the candidate
  class `02` reply (candidate, unconfirmed on the wire); its relation to the
  community `Status02` reading is not established.
- The relationship between the six-field heat-pump payload of selector `0x07`
  and the candidate class `07`.
- The classes beyond `00`..`03` have candidate layouts only; no exchange and
  no sender or responder implementation is known either way.
- The profile availability (eBUS or PeBUS) of the header-only classes `10` and
  `11`.
- The initiator and responder roles of the Direction Caveat were observed on
  one topology; other installations were not observed.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [08.hmu.HW5103.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.HW5103.tsp)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
