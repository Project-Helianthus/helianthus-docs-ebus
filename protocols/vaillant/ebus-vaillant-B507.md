# Vaillant B507 Heat Pump Load/Poll Protocol

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

`PB=0xB5`, `SB=0x07`.

## Status

**Enrichment research** -- not yet live-validated on a tested bus.
B507 is heat-pump specific (VRC720-family controller + heat pump topology; candidate, unconfirmed on the wire, see Open question 10). It is absent from
john30/ebusd-configuration <!-- legacy-role-mapping:begin -->master<!-- legacy-role-mapping:end --> and has no independent capture in this reference
prior to this document.

The tested bus runs a boiler and a VRC720-family controller (gas boiler topology). No B507
frames were observed on that installation; whether they appear on other boiler
installations is not established. The message table and the evidence
sections below come from community ebusd configurations; the
[candidate layouts](#candidate-layouts) are candidates, unconfirmed on the wire.

Evidence labels:

- `FORK_JONESPD`: jonesPD/ebusd-configuration `ebusd-2.1.x/en/vaillant/08.hmu.csv`
- `FORK_XERION`: xerion3800/ebusd-configuration `ebusd-2.1.x/en/vaillant/08.hmu.csv`
- `FORK_MORPHZ`: morphZ/ebusd-configuration `ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv`, `custom/myconfig.csv`
- `FORK_KOLIBRIE`: kolibrie-eric/ebusd-configuration `ebusd-2.1.x/de/vaillant/08.hmu.csv`, `ebusd-2.1.x/en/vaillant/08.hmu.csv`

**Hypothesis:** protocol existence, the 0900 poll and the HeatpumpLoadSensor
interpretation are based on community configurations. **Unknown:** native write
semantics.

## Wire Format

```
Initiator -> Target request:
  [0xB5] [0x07] [0x09] [sub] [...]

Target response (ID 0900):  :HEX:* (variable length, undecoded)
Target response (ID 0931):  1 byte (signed 0.5-step % hypothesis; community D1C codec differs, see below)

QQ (initiator):    0x15 (VRC720-family controller address)
ZZ (target):       0x08 (heat-pump unit; class not established, see Open question 12)
```

## Device Scope

**Target:** a heat-pump unit at target address `0x08`; whether the heat pump or the heat-pump interface unit answers B507 is not established (Open question 12).

In heat pump systems, `0x08` is the compressor/heat exchanger management
unit. In gas boiler systems, `0x08` is the boiler -- a different device class
at the same address.

B507 is heat-pump specific (candidate, unconfirmed on the wire; see Open
question 10). No B507 frames were observed on the one tested gas
boiler installation with a VRC720-family controller; other installations are
not established.

## Message Table

| ID (hex) | Name | ebusd type | Data fields | Direction | Poll interval | Evidence status |
|----------|------|-----------|-------------|-----------|--------------|------------|
| `09 00` | unknown_m_poll_60s_b507h (`unknownMPoll60sB507h`) | `r` | `:HEX:*` (variable, undecoded) | controller (`0x15`) -> heat pump (`0x08`) | 60 s | Hypothesis |
| `09 31` | heatpump_load_sensor (`HeatpumpLoadSensor`) | `r` / `r5` | `percent1:D1C` (1 byte, %) | controller -> heat pump | 5 s (morphZ custom) | Hypothesis |
| `09` (write) | -- (unnamed) | `*w` | -- (undecoded capture) | unknown initiator -> heat pump | observed | Unknown |

### D1C Encoding

**Hypothesis (signed B507 interpretation):** interpret the response byte as a
signed two's-complement integer, then divide by two. The following are
arithmetic examples, not observed B507 responses.

| Raw byte (hex) | Signed carrier (decimal) | Decoded percentage |
|---|---:|---:|
| `63` | 99 | 49.5% |
| `7F` | 127 | 63.5% |
| `80` | -128 | -64% |

**Proven (arithmetic only):** a signed one-byte carrier divided by two spans
-64.0% to +63.5%. Thus `63` is 49.5%, not 99.5%.

**Proven (ebusd codec only):** the [ebusd built-in datatype reference](https://github.com/john30/ebusd/wiki/4.3.-Builtin-data-types)
defines D1C as unsigned, divided by two, with a documented range of 0-100.
That codec definition conflicts with the signed interpretation above; the
community configuration's `percent1:D1C` label does not establish native B507
signedness. The claimed operational range of 0-100% also conflicts with the
signed carrier's maximum of +63.5%; this range conflict remains unresolved.

**Unknown (native physical meaning):** which interpretation applies to B507,
whether the response represents compressor load, its native operational range,
and device support. No native unavailable, sentinel or error meaning is
established for these bytes; negative values or values outside a claimed range
alone do not establish such meanings.

### ID 0900 Response

Not decoded in any fork. The `:HEX:*` wildcard in ebusd config means
response length and field structure are unknown.

### Write Direction (ID 09, *w entries)

Passive bus capture of write traffic (kolibrie-eric 2019 only). Content
unknown. May be a configuration push from the controller to the heat pump.

## Candidate layouts

The candidate layouts of B507 cover the ops `B5 07 01` to `B5 07 0B`,
unconfirmed on the wire. They exchange heat-generator information between a heat
generator and a controller (boiler configuration and state, solar circuit state,
heat-pump static and operational data, efficiency, water flow). None of it has
been confirmed on the wire. The field-level layout of every op is in
[`fixtures/b506-b508-candidate-fields.csv`](fixtures/b506-b508-candidate-fields.csv);
`vaillant_name` in that file is a correspondence column (Vaillant name,
correspondence only), not a canonical name.

Offsets count from the first byte of the service prefix (PB, SB and the op
byte): offset 0 = `B5`, 1 = `07`, 2 = op byte. A target response on the bus
carries no such prefix (eBUS framing: `NN`, data, CRC); how the candidate
response offsets map onto the bytes of a bus response is unconfirmed on the
wire. The request length NN counts the op byte plus its data bytes.
**Hypothesis**: response offset 3 is the first data byte of a bus response (see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)).

| Op | Candidate description | Request NN | Reply bytes |
|---|---|---:|---:|
| `B5 07 01` | boiler configuration (carried in the request) | 3 | 0 |
| `B5 07 02` | solar circuit state | 1 | 8 |
| `B5 07 03` | boiler state | 1 | 8 |
| `B5 07 04` | status of DHW loading | 1 | 1 |
| `B5 07 05` | static data of the heat source (outdoor unit) | 1 | 3 |
| `B5 07 06` | operational data of the heat source (outdoor unit) | 1 | 9 |
| `B5 07 07` | status of the ASC | 1 | 1 |
| `B5 07 08` | energy efficiency of the heat source | 1 | 2 |
| `B5 07 09` | heat generator COP based on the required flow temperature | 2 | 2 |
| `B5 07 0A` | advanced heat/cooling generator information | 1 | 3 |
| `B5 07 0B` | water flow request | 3 | 1 |

- **Boiler configuration** (`01`): candidate, unconfirmed on the wire: the
  request carries, at offset 3, a boiler type in bits 0..5 (`0` disabled, `1`
  switching, `2` modulating, `3` solar), a bidirectional-interface flag in bit 6
  and a configuration flag in bit 7; offset 4 is the constant `00`. The positive
  carries no response data (candidate).
- **Static data** (`05`): candidate, unconfirmed on the wire: offset 3 bit 0
  heating mode supported, bit 1 cooling mode supported; offset 4 bit 0 operation
  (`0` on-off, `1` modulating) and bit 1 efficiency (`0` fixed, `1` variable);
  offset 5 primary energy type `0` unknown, `1` gas, `2` electricity supply 1,
  `3` electricity supply 2, `4` fuel, `5` pellet.
- **Operational data** (`06`): candidate, unconfirmed on the wire: offset 3
  climate mode (`0` OFF, `1` heating, `2` cooling, `3` auto, `4` ventilation, `5`
  deicing, `6` dehumidifying, `7` temporary error, `8` locking error), offset 4
  cost of primary energy (`u8`, 0..250, 1/MWh), offset 5 current flow temperature
  (`i16` LE ÷16 °C), offset 7 current efficiency (`u8` ÷10 kW), offset 8 capacity
  output (`u8` ÷10 kW; another candidate reading gives a factor of 10, ×10 kW,
  instead of the divisor, and a second candidate reading allows a negative value
  in climate mode 5, de-icing; the scaling and the signedness are unresolved,
  see Open question 9), offset 9 energy cost limit (`u8`, 1/MWh), offset 10
  available capacity at the cost limit and offset 11 maximum capacity at the
  current conditions without cost consideration (`u8` ÷10 kW).
- **Efficiency** (`08`): candidate, unconfirmed on the wire: `u16` LE percent at
  offset 3. **COP** (`09`): candidate, unconfirmed on the wire: the request
  carries the required flow temperature (`u8` ÷2 °C) at offset 3 and the reply an
  efficiency (`u16` LE, %).
- **Advanced generator information** (`0A`): candidate, unconfirmed on the wire:
  maximum central-heating and maximum domestic-hot-water flow temperature
  setpoints (`u8` ÷2 °C) at offsets 3 and 4; offset 5 bit 0 cooling available,
  bit 1 heating available, bit 2 noise-reduction function supported.
- **Water flow request** (`0B`): candidate, unconfirmed on the wire: the request
  carries a `u16` LE flow in l/min at offset 3 (default `FFFF`); the reply bit 0
  is "system flow present".
- **Solar and boiler state** (`02`, `03`): candidate, unconfirmed on the wire:
  collector temperatures (`i16` LE ÷16 °C), pump duty cycles (`u8` %), the
  yield-sensor temperature, desired boiler flow temperatures (`u8` °C) and
  storage temperatures (`u8` ÷2 °C); see the fixture.

Candidate, unconfirmed on the wire: the `09` request byte (a flow temperature
setpoint, `u8` ÷2 °C) is the byte that the community rows treat as the sub-ID
`00` or `31`, and the `09` reply is a `u16` efficiency, not the one-byte unsigned
percentage of `HeatpumpLoadSensor`; the relation is unresolved (see Open
Questions).

No op on this page is documented as safe to send; a state-changing op (for example `01`, `09` and `0B`, which carry values in the request) needs a separately established safety procedure and target qualification, and an ACK does not show the resulting device state.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Evidence

### Fork Sources (4 named, 2-3 effectively independent)

| Fork | File | Line | URL |
|------|------|------|-----|
| jonesPD | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L4 | https://github.com/jonesPD/ebusd-configuration/blob/HEAD/ebusd-2.1.x/en/vaillant/08.hmu.csv#L4 |
| xerion3800 | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L4 | https://github.com/xerion3800/ebusd-configuration/blob/HEAD/ebusd-2.1.x/en/vaillant/08.hmu.csv#L4 |
| morphZ | `ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv` | L5 | https://github.com/morphZ/ebusd-configuration/blob/HEAD/ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv#L5 |
| morphZ | `custom/myconfig.csv` | L209 | https://github.com/morphZ/ebusd-configuration/blob/HEAD/custom/myconfig.csv#L209 |
| kolibrie-eric | `ebusd-2.1.x/de/vaillant/08.hmu.csv` | L2, L4 | https://github.com/kolibrie-eric/ebusd-configuration/blob/HEAD/ebusd-2.1.x/de/vaillant/08.hmu.csv#L2 |
| kolibrie-eric | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L5, L21 | https://github.com/kolibrie-eric/ebusd-configuration/blob/HEAD/ebusd-2.1.x/en/vaillant/08.hmu.csv#L5 |

### Independence Assessment

jonesPD and xerion3800 have near-identical 2025-era content and their
`08.hmu.csv` files appear to share a common ancestor -- they confirm each
other's content but may not constitute fully independent observations.
kolibrie-eric (2019) confirms coarse B507 traffic from a physical capture
but does not decode registers. morphZ is the primary source for the
`HeatpumpLoadSensor` decode. Effective independent sources: 2-3, not 4.

### Fork Chronology

kolibrie-eric (2019) is the oldest observation -- B507 traffic was captured
on physical hardware before 2020. morphZ (2024) first decoded the
`HeatpumpLoadSensor` name. jonesPD and xerion3800 (2025) independently
replicate the 60-second poll entry.

## Falsifiable Claims

1. On a heat pump system with a VRC720-family controller, ebusd passively captures frames
   with PBSB=`B507` and QQ=`0x15` / ZZ=`0x08` at approximately 60-second
   intervals.
2. The `HeatpumpLoadSensor` (ID `0931`) returns a D1C byte that tracks
   compressor load percentage in real time when the heat pump is active.
3. B507 frames do not appear on the tested gas boiler installation (VRC720-family
   controller + boiler); whether they appear on other boiler installations is not
   established.

## Open Questions

1. Full response layout for ID `0900` -- `:HEX:*` means no fork has decoded it.
2. Write semantics for B507 ID `09` (`*w` entries in kolibrie-eric) --
   content and trigger condition unknown.
3. Sub-selector space -- only `0x00` and `0x31` known after the `0x09` prefix.
4. Hardware scope -- whether B507 is specific to one heat-pump hardware variant
   or applies to all heat pumps.
5. Relationship to B51A (heat pump statistics) -- B507 appears to be a
   simpler, parallel poll rather than a replacement.
6. The candidate layout of `09` (see "Candidate layouts") takes a flow
   temperature setpoint in the byte after the op and returns a `u16`
   efficiency; the community-configuration reading of `09 31` as a one-byte
   unsigned 0.5-step percentage differs in response width. The relation is
   unresolved.
7. The candidate ops are known only as candidate layouts; no exchange of them
   was observed beyond the community configuration and the captures described on
   this page, and whether any device implements them is not established.
8. The default `FFFF` of the candidate water flow request (`0B`, l/min) lies
   within the candidate raw range 0..65535; no other candidate interval is
   recorded for this field, and the intended default is unresolved.
9. The candidate capacity output field (`06`, offset 8) is unsigned with a
   divisor of 10 kW (a second candidate reading gives a factor of 10) but a
   negative value is allowed in climate mode 5 (de-icing); the scaling direction
   and the signedness of this field are unresolved.
10. The page states that B507 is heat-pump specific, whereas the candidate ops
    `01` (boiler configuration), `02` (solar circuit state), `03` (boiler state)
    and `04` (DHW loading status) are generic heat-generator services; the
    heat-pump-only statement and these generic candidate ops are not reconciled.
11. How the candidate response offsets map onto the data bytes of a bus response
    is unconfirmed on the wire.
12. Which class at target address `0x08` answers B507, the heat pump or the
    heat-pump interface unit, is not established; the community entries come
    from configurations for the heat-pump interface unit.
