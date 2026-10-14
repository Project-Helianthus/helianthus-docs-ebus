# Vaillant B504 GetOperationalData

`PB=0xB5`, `SB=0x04`.

## Status

`B504` is a selector-based read family. It must not be decoded from the
response bytes alone; the request selector and target class are part of the
schema.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The request shape builds a one-byte request payload:

```text
Request payload:
  op : byte
```

Some ebusd TypeSpec rows inherit `B504` with additional static selector bytes
through `@base(MF, 0x4, ...)`. Therefore, `op` is the simplest common model,
not a guarantee that every configured row has only one selector byte.

## Known Selectors and Shapes

| Selector | Name/context | Response shape | Evidence | Falsification test |
|---:|---|---|---|---|
| `0x00` | Date/time | variant-dependent date/time payload plus outside temperature | existing docs | Query `B504 00` on multiple target classes and show no valid date/time layout is returned. |
| `0x02..0x08` | Timer periods Monday..Sunday | `timer` composite | | Read each weekday from a timer-capable controller and show the selector does not map weekdays in order. |
| `0x09` | Parameters in older/consolidated docs | target-dependent | existing docs, historical docs | Capture `B504 09` against a boiler, a VRC720-family controller and a functional module and prove all targets share one fixed layout. |
| `0x0D` | Status in older/consolidated docs | often short status payload | existing docs | Capture state changes and show `0x0D` has no status correlation. |
| `0x16` | Outside temperature in `hcmode_inc` | `temp` | | Query target implementing `hcmode_inc` and show response cannot decode as temperature. |
| `0x19 0xNN` | Daily setpoint temperatures in `tempsetpoints_inc` | three `temp1` values | | Query each day selector and show response does not contain three setpoint temperatures. |

## DateTime Caveat

This reference documents two B504 DateTime variants in
[`ebus-vaillant.md`](ebus-vaillant.md):

- a 10-byte BTI/BDA plus `temp2` layout with weekday byte;
- an 8-byte legacy layout without weekday.

Do not hard-code a single DateTime length without validating the target.

## Candidate op catalogue

The candidate layouts of B504 cover the program-period form `B5 04 <block>`
and the ops `B5 04 00`, `B5 04 01` and `B5 04 09` to `B5 04 37` except `1A` to
`1F`, unconfirmed on the wire; `02` to `08` are the block numbers of the
program-period form, not ops, and no candidate op layout is known for `1A` to
`1F`. All of them are
candidate reads. The request of the program-period form carries the weekday
block number at offset 2 in place of an op byte and no further data; a request
carries data bytes after the op byte only for `0D` (two bytes) and `19` (one
byte, the weekday) (candidate). The field-level layout of every op (byte
offset, bit, width, codec, default, range, unit, conversion, enumeration) is in
[`fixtures/b504-b505-candidate-fields.csv`](fixtures/b504-b505-candidate-fields.csv);
`vaillant_name` in that file is a correspondence column (Vaillant name,
correspondence only), not a canonical name.

Offsets count from the first byte of the service prefix (PB, SB and the op
byte): offset 0 = `B5`, 1 = `04`, 2 = op byte. A target response on the bus
carries no such prefix (eBUS framing: `NN`, data, CRC); how the candidate
response offsets map onto the bytes of a bus response is unconfirmed on the
wire. The columns give the request length NN (the op byte plus its data bytes)
and the number of reply data bytes; "≥" marks an op with a variable-length
field (only `16`, whose reply ends with a field to the end of the telegram).
The candidate `00` reply has a fixed length of 10 bytes; the observed DateTime
layouts have 10 or 8 bytes (see [DateTime Caveat](#datetime-caveat)).
**Hypothesis**: response offset 3 is the first data byte of a bus
response, which agrees with the observed 10-byte `00` layout, where the DCF
state is the first response byte. The descriptions are plain-language and are
not canonical names.

| Op | Candidate description | Request NN | Reply bytes |
|---|---|---:|---:|
| `B5 04` | programmed periods (weekday block) | 1 | 7 |
| `B5 04 00` | date, time, outside temperature | 1 | 10 |
| `B5 04 01` | data for base display | 1 | 9 |
| `B5 04 09` | main configuration parameters | 1 | 11 |
| `B5 04 0A` | sub configuration parameters | 1 | 6 |
| `B5 04 0B` | DHW parameters | 1 | 4 |
| `B5 04 0C` | system parameters | 1 | 3 |
| `B5 04 0D` | heat demand | 3 | 5 |
| `B5 04 0E` | actual state of the circuit | 1 | 10 |
| `B5 04 0F` | detail data of the solar circuit | 1 | 10 |
| `B5 04 10` | solar storage temperatures | 1 | 10 |
| `B5 04 11` | configuration parameters of the solar controller | 1 | 10 |
| `B5 04 12` | solar controller info 1 | 1 | 10 |
| `B5 04 13` | solar controller info 2 | 1 | 9 |
| `B5 04 14` | solar yield data | 1 | 8 |
| `B5 04 15` | detection time for heating-circuit setpoint not reached | 1 | 1 |
| `B5 04 16` | corrected outside temperature for diagnostic purposes | 1 | ≥2 |
| `B5 04 17` | DHW status | 1 | 1 |
| `B5 04 18` | heat demand, extended | 1 | 6 |
| `B5 04 19` | comfort temperature levels | 2 | 4 |
| `B5 04 20` | heat circuit temperatures | 1 | 8 |
| `B5 04 21` | solar graphic data | 1 | 5 |
| `B5 04 22` | DHW circuit legionella protection | 1 | 3 |
| `B5 04 23` | DHW circuit tank loading offset | 1 | 1 |
| `B5 04 24` | heating circuit summer mode offset | 1 | 1 |
| `B5 04 25` | third difference control | 1 | 2 |
| `B5 04 26` | compressed circuit information | 1 | 7 |
| `B5 04 27` | compressed information for a heat-pump remote control | 1 | 4 |
| `B5 04 28` | solar yield for large solar yield | 1 | 3 |
| `B5 04 29` | supported modes | 1 | 1 |
| `B5 04 2A` | preheating time | 1 | 1 |
| `B5 04 2B` | minimum temperature for a solid-fuel boiler | 1 | 2 |
| `B5 04 2C` | solar frost protection | 1 | 1 |
| `B5 04 2D` | air-conditioning indoor-unit heat demand | 1 | 5 |
| `B5 04 2E` | operational data from the indoor unit | 1 | 8 |
| `B5 04 2F` | drop-back temperatures | 1 | 4 |
| `B5 04 30` | data from the indoor unit for the outdoor unit | 1 | 7 |
| `B5 04 31` | cooling demand | 1 | 2 |
| `B5 04 32` | cooling circuit status | 1 | 10 |
| `B5 04 33` | averaged outside temperature | 1 | 2 |
| `B5 04 34` | information for the ASC | 1 | 3 |
| `B5 04 35` | extended solar logging | 1 | 1 |
| `B5 04 36` | preheating time 2 | 1 | 1 |
| `B5 04 37` | heat demand read by the energy manager | 1 | 2 |

The candidate op `19` (weekday at offset 3, then three `u8` ÷2 °C comfort
levels) is consistent with the daily-setpoint shape of `0x19 0xNN`, and the
candidate op `16` (a signed 16-bit temperature at offset 3) is consistent with
the `temp` shape of `0x16`. The candidate lengths of `09` (11 reply bytes) and
`0D` (5 reply bytes, with a 2-byte request) differ from the 5-byte and 1-byte
examples in [`ebus-vaillant.md`](ebus-vaillant.md); the relation is unresolved
(see Open questions).

## Candidate encodings and enumerations

Every item in this section is a candidate layout, unconfirmed on the wire.

- **Program period** (`B5 04 <block>`): candidate, unconfirmed on the wire: the
  weekday block number at offset 2 is Monday 2 to Sunday 8 (the `0x02..0x08`
  selectors above); the reply carries three start/stop pairs at offsets 3..8 and
  a mode at offset 9. Times use the raw time code `0` = 00:00 to `144` = 24:00
  in 10-minute steps; raw `FF` has no known meaning. The mode is `0` the
  indicated day, `1` Monday to Friday, `2` Saturday and Sunday, `3` Monday to
  Sunday (a different order from B515). The 30-minute time code `0..48` is a
  candidate for the energy-saving function.
- **Date, time, outside temperature** (`B5 04 00`): candidate, unconfirmed on the
  wire: the reply is the DCF state at offset 3 (`0` no DCF signal and no
  real-time-clock value, `1` DCF signal detected, `2` signal being interpreted,
  `3` DCF data valid, `4` real-time-clock data valid), then second, minute, hour,
  day, month, weekday and year at offsets 4..10, then the outside temperature at
  offsets 11..12. The date and time components are BCD, as in DateTime layout A in
  [the overview](ebus-vaillant.md#op--0x00-datetime), with raw `FF` as a
  candidate not-set value; the outside temperature is a signed 16-bit
  little-endian value ÷256 °C, and raw `8000` is a reserved value whose meaning
  is unresolved. This is the same shape as the observed 10-byte DateTime layout A
  in [the overview](ebus-vaillant.md#op--0x00-datetime).
- **Numeric codecs** (candidate, unconfirmed on the wire): `B5 04 0A` actual
  temperature `i16` LE ÷16 °C and setpoint `u8` °C; `B5 04 09` heating curve
  `u16` LE ÷100; `B5 04 20` temperatures `u8` ÷2 °C and offsets `i16` LE ÷16 °C;
  `B5 04 33` `i16` LE ÷256 °C; `B5 04 0B` reload delay in minutes and pump
  overrun (the default 0 lies outside its interval 3..9); `B5 04 37` demand bits
  0 DHW, 1 heating, 2 cooling.
- **Heat demand** (`B5 04 0D`): candidate, unconfirmed on the wire: the request
  is `B5 04 0D` plus two bytes, but the positive begins with the bytes
  `B5 04 00` in the candidate offsets counted from the service prefix (the
  asymmetry is unresolved). Candidate interpretation,
  unconfirmed on the wire: it is read cyclically by an energy manager.
- **Corrected outside temperature** (`B5 04 16`): candidate, unconfirmed on the
  wire: a signed 16-bit little-endian value at offset 3 plus a field of unknown
  meaning to the end of the telegram. Two candidate divisors are 16 and 256; the
  divisor is unresolved (see Open questions).
- **Flow temperature** (`B5 04 0E`): candidate, unconfirmed on the wire: the
  field at offset 12 depends on the circuit type, a duty cycle in % for mixer
  circuits (case 1), a flow temperature in °C for DHW circuits (case 2) and a raw
  value for other types. The case numbers and the circuit-type enumeration below
  disagree for DHW: case 2 is given for DHW circuits, whereas the enumeration
  gives `2` as the set-value circuit and `3` as the DHW circuit; which circuit
  type selects which case is unresolved.
- **Solar yield** (`B5 04 28`): candidate, unconfirmed on the wire: 24 bits at
  offsets 3..5, LSB-first, unit kWh, range 0..99999, default 0; candidate
  interpretation: packed BCD, nibble order unresolved (it is not a plain
  little-endian 24-bit integer). **Flow rate** (`B5 04 13`): candidate,
  unconfirmed on the wire: 16 bits at offsets 6..7, LSB-first, litres per hour,
  range 0..9999; candidate interpretation: packed BCD, nibble order unresolved.
  The handling of invalid nibbles is unresolved (**Hypothesis**).
- **Enumerations** shared by several ops (candidate, unconfirmed on the wire):
  operating mode `1` Day, `2` OFF, `3` Auto, `4` Eco (switching between on and
  off), `5` Night in most ops, with exceptions: the operating mode of
  `B5 04 26` is `0` OFF, `1` Manual, `2` Auto, and that of `B5 05 3B` is `0`
  OFF, `1` Manual, `2` Auto, `3` Day, `4` Night, `5` Summer; circuit type `0` disabled, `1` mixer circuit, `2` set-value
  circuit, `3` DHW circuit, `4` back-flow circuit, `5` heating circuit without
  mixer, `6` circulation pump for domestic hot water, `7` solar circuit, `8`
  heating circuit without mixer used as a set-value circuit, `9` fresh-water
  station, `10` large advanced solar station, `11` small advanced solar station;
  circuit state `0` low temperature or off through `8` cooling mode active (full
  lists in the fixture).

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Observation status

No publishable capture is included in this reference.

## Open questions

- Complete selector namespace per target class.
- Whether some `B504` selectors require service or installer state.
- Which selectors are safe to probe actively on production systems.
- The candidate ops are known only as candidate layouts; no exchange was
  observed beyond the examples on this page, and whether any device implements
  them is not established.
- Candidate lengths of `09` (11 reply bytes) and `0D` (5 reply bytes) versus the
  5-byte and 1-byte examples in [`ebus-vaillant.md`](ebus-vaillant.md): the
  relation is unresolved.
- The packed-BCD nibble order, invalid-nibble handling and overflow for the
  solar yield (`28`) and the flow rate (`13`) are unresolved.
- The default 0 of the `B5 04 0B` pump overrun lies outside its interval 3..9;
  the intended default is unresolved. Several candidate default values lie
  outside their candidate intervals (see the fixture).
- Which circuit type selects the duty-cycle case (case 1) and which selects the
  flow-temperature case (case 2) of the `B5 04 0E` field at offset 12 is
  unresolved, because the case numbers and the circuit-type enumeration disagree
  for DHW.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.
- Whether the program-period reply echoes the block number is unconfirmed. A
  candidate layout also places the block number at offset 2 of the reply,
  counted from the service prefix; that is the op-byte position, which is not
  part of a bus response under the offset hypothesis, so the fixture lists the
  block number only on the request side and the reply as seven bytes.
- The divisor of the `B5 04 16` corrected outside temperature (two candidate
  divisors are 16 and 256) is unresolved.
- The meaning of the reserved raw value `8000` of the `B5 04 00` outside
  temperature is unresolved.
- The asymmetry of `B5 04 0D` (a request with two data bytes, a positive that
  begins with the bytes `B5 04 00` in the candidate offsets counted from the
  service prefix) is unresolved.

## References

- Public TypeSpec: [timer_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/timer_inc.tsp)
- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [tempsetpoints_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/tempsetpoints_inc.tsp)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
