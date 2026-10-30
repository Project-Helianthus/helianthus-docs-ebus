# Vaillant B505 SetOperationalData

`PB=0xB5`, `SB=0x05`.

## Status

`B505` is the write-side companion to `B504`. It is op-coded and
device/state-dependent. Treat every write as side-effectful until a safe test
fixture proves otherwise.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The request shape builds:

```text
Request payload:
  op      : byte
  payload : bytes, optional and op-dependent
```

The response is usually interpreted as ACK/status plus any target-specific
bytes. A successful eBUS response alone does not prove that the target accepted
or persisted the requested state.

## Known Selectors and Shapes

| Selector bytes | Name/context | Request data | Evidence | Falsification test |
|---|---|---|---|---|
| `09 01..09 07` | Timer periods Monday..Sunday | `timer` composite | | Write on isolated hardware, then read back with the matching `B504 02..08` selector and show no matching change. |
| `2E 01..2E 07` | Daily temperature setpoints | three `temp1` values | | Write setpoints, read back with matching `B504 19 <day>` selector, and show no match. |
| `2D` | Room temperature offset | `temp` | | Write a harmless test offset on non-production hardware and show no matching room-offset change. |
| `05`, `06`, `07` | archived quick commands | command-specific | archived john30 config | Prove that the selector is read-only or that the target never ACKs it on devices that claim support. |

## Local Validation Rule

For writes, protocol-level ACK is not sufficient. A safe write must
be followed by a read-back through the authoritative read path for that field.
This is the same rule used by the existing B509 boiler config write path.

## Candidate op catalogue

The candidate layouts of B505 cover the ops `B5 05 01` to `B5 05 62`
(no candidate layout is known for `1F`, `50` and `52`), unconfirmed on the wire.
Outside the bounded sentinel and override slice below, each op is a candidate
write: the request carries the value, and the positive reply carries no response
data (candidate) except for the ops described under "Feedback-style writes".
The older field-level layout declarations (byte offset, bit, width, codec,
default, range, unit, conversion, enumeration) are in
[`fixtures/b504-b505-candidate-fields.csv`](fixtures/b504-b505-candidate-fields.csv);
`vaillant_name` in that file is a correspondence column (Vaillant name,
correspondence only), not a canonical name. For the exact fields in the bounded
slice below, the bounded table states the current candidate limits; the older CSV does
not resolve their conflicting conversions, bounds, positions or response claims.

Offsets count from the first byte of the service prefix (PB, SB and the op
byte): offset 0 = `B5`, 1 = `05`, 2 = op byte. A target response on the bus
carries no such prefix (eBUS framing: `NN`, data, CRC); how the candidate
response offsets map onto the bytes of a bus response is unconfirmed on the
wire. The request length NN counts the op byte plus its data bytes. The
descriptions are plain-language and are not canonical names.

| Op | Candidate description | Request NN | Reply bytes |
|---|---|---:|---:|
| `B5 05 01` | desired day temperature | 2 | 0 |
| `B5 05 02` | operating mode | 2 | 0 |
| `B5 05 03` | floor pavement drying day | 2 | 0 |
| `B5 05 04` | holiday function | 2 | 0 |
| `B5 05 05` | party function | 2 | 0 |
| `B5 05 06` | single tank charge | 2 | 0 |
| `B5 05 07` | savings function | 2 | 0 |
| `B5 05 08` | circuit type | 2 | 0 |
| `B5 05 09` | set time frames | 9 | 0 |
| `B5 05 0A` | drop temperature | 2 | 0 |
| `B5 05 0B` | heating curve | 3 | 0 |
| `B5 05 0C` | outside temperature cut-off limit | 2 | 0 |
| `B5 05 0D` | pump idle period | 2 | 0 |
| `B5 05 0E` | minimum flow temperature | 2 | 0 |
| `B5 05 0F` | maximum flow temperature | 2 | 0 |
| `B5 05 10` | maximum preheating time | 2 | 0 |
| `B5 05 11` | recharge delay | 2 | 0 |
| `B5 05 12` | charge pump overrun | 2 | 0 |
| `B5 05 13` | legionella protection | 2 | 0 |
| `B5 05 14` | parallel tank charge | 2 | 0 |
| `B5 05 15` | pre-boiler cut-off time | 2 | 0 |
| `B5 05 16` | frost protection delay | 2 | 0 |
| `B5 05 17` | temperature excess | 2 | 0 |
| `B5 05 18` | DHW loading active | 2 | 0 |
| `B5 05 19` | DHW start loading | 2 | 0 |
| `B5 05 1A` | maximum solar tank temperature (first tank) | 2 | 0 |
| `B5 05 1B` | switching-on and cut-off difference (first tank) | 3 | 0 |
| `B5 05 1C` | outside temperature offset | 2 | 0 |
| `B5 05 1D` | maximum solar tank temperature (second tank) | 2 | 0 |
| `B5 05 1E` | switching-on and cut-off difference (second tank) | 3 | 0 |
| `B5 05 20` | reset solar yield | 2 | 0 |
| `B5 05 21` | flow rate value | 3 | 0 |
| `B5 05 22` | reset solar pump operating hours | 2 | 0 |
| `B5 05 23` | duty cycle control of the collector pumps | 2 | 0 |
| `B5 05 24` | teleswitch operating mode | 2 | 0 |
| `B5 05 25` | 230 V output type | 2 | 0 |
| `B5 05 26` | hydraulic scheme | 2 | 0 |
| `B5 05 27` | DHW state of the energy manager | 4 | 0 |
| `B5 05 28` | tank separation | 2 | 0 |
| `B5 05 29` | force heat consumption | 2 | 0 |
| `B5 05 2A` | vacation setpoint | 2 | 0 |
| `B5 05 2B` | cyclically sent data for heat consumers | 8 | 0 |
| `B5 05 2C` | detection time for heating-circuit setpoint not reached | 2 | 0 |
| `B5 05 2D` | room remote control | 4 | 0 |
| `B5 05 2E` | comfort temperature levels | 5 | 0 |
| `B5 05 2F` | set storage sensor SP1 | 3 | 0 |
| `B5 05 30` | enable CH operation | 2 | 1 |
| `B5 05 31` | enable normal DHW operation | 2 | 1 |
| `B5 05 32` | heat circuit offsets | 5 | 0 |
| `B5 05 33` | DHW circuit legionella protection | 4 | 0 |
| `B5 05 34` | DHW circuit tank loading offset | 2 | 0 |
| `B5 05 35` | continuous heating limit | 2 | 0 |
| `B5 05 36` | heating circuit summer mode offset | 2 | 0 |
| `B5 05 37` | maximum temperature of solar tank 3 | 2 | 0 |
| `B5 05 38` | difference of solar tank 3 | 3 | 0 |
| `B5 05 39` | solar storage priority | 2 | 0 |
| `B5 05 3A` | third difference control | 3 | 0 |
| `B5 05 3B` | compressed circuit information | 3 | 0 |
| `B5 05 3C` | measured room temperature | 5 | 0 |
| `B5 05 3D` | compressed information for an EHP circuit setpoint | 3 | 0 |
| `B5 05 3E` | compressed information for an EHP circuit system mode | 2 | 0 |
| `B5 05 3F` | preheating time | 2 | 0 |
| `B5 05 40` | minimum temperature for a solid-fuel boiler | 2 | 0 |
| `B5 05 41` | solar frost protection | 2 | 0 |
| `B5 05 42` | indoor-unit room desired day temperature | 2 | 0 |
| `B5 05 43` | room temperature for the indoor unit | 3 | 0 |
| `B5 05 44` | room climate mode for the indoor unit | 2 | 0 |
| `B5 05 45` | dehumidifying status for the indoor unit | 2 | 0 |
| `B5 05 46` | sleep function status for the indoor unit | 2 | 0 |
| `B5 05 47` | night setpoint temperatures | 3 | 0 |
| `B5 05 48` | vacation setpoint temperatures | 3 | 0 |
| `B5 05 49` | control interface data for the indoor unit | 3 | 0 |
| `B5 05 4A` | system state of the energy manager | 3 | 0 |
| `B5 05 4B` | operating mode per channel | 3 | 0 |
| `B5 05 4C` | desired cooling start temperature offset | 2 | 0 |
| `B5 05 4D` | remote-control solar data | 8 | 0 |
| `B5 05 4E` | solar yield data | 5 | 0 |
| `B5 05 4F` | minimum temperature for solar circuit 1 | 2 | 0 |
| `B5 05 51` | extended solar logging | 2 | 0 |
| `B5 05 53` | switch-on room temperature | 2 | 0 |
| `B5 05 54` | cascade of the water modules | 3 | 0 |
| `B5 05 55` | flexible legionella cycle | 2 | 0 |
| `B5 05 56` | one-day holiday function | 2 | 0 |
| `B5 05 57` | one-day bank holiday function | 2 | 0 |
| `B5 05 58` | bank holiday function | 2 | 0 |
| `B5 05 59` | system-off function | 2 | 0 |
| `B5 05 5A` | new room temperature setpoint (remote control) | 2 | 0 |
| `B5 05 5B` | impact ventilation function | 2 | 0 |
| `B5 05 5C` | heating/cooling information | 2 | 0 |
| `B5 05 5D` | cooling function | 2 | 1 |
| `B5 05 5E` | enable signal of the energy manager | 4 | 1 |
| `B5 05 5F` | force cooling consumption | 2 | 1 |
| `B5 05 60` | heat generator error status | 2 | 1 |
| `B5 05 61` | operational data for the cascade | 4 | 1 |
| `B5 05 62` | distribution of humidity and dew point | 3 | 0 |

The candidate op `09` has a weekday at offset 3 (Monday 1 to Sunday 7), which is
consistent with the `09 01..09 07` timer selectors above; the candidate op `2E`
(weekday 1..7 followed by three `u8` ÷2 °C comfort levels) is consistent with the
`2E 01..2E 07` daily setpoints above; the candidate op `2D` (an `i16` LE ÷16 °C
room temperature offset followed by a room control state: 0 normal, 1 circuit
disabled for a thermostat function, 2 frost protection) is consistent with the
`2D` room offset above. The archived quick commands `05`, `06` and `07` coincide
with the candidate party function, single tank charge and savings function
(**Hypothesis**, unconfirmed on the wire).

## Candidate encodings and enumerations

Every item in this section is a candidate layout, unconfirmed on the wire.

- **Time frames** (`B5 05 09`): candidate, unconfirmed on the wire: weekday at
  offset 3 (Monday 1 to Sunday 7), three start/stop pairs at offsets 4..9 and a
  mode at offset 10, with the same time code as B504 (`0` = 00:00 to `144` =
  24:00 in 10-minute steps). The mode is `0` the given day, `1` Monday to
  Friday, `2` Saturday and Sunday, `3` Monday to Sunday (a different order from
  B515). The candidate defaults are first pair 06:00 to 22:00, the other pairs
  00:00 to 00:00 and mode 3. An equal start and stop time is not known to mean
  delete or disable.
- **Feedback-style writes**: candidate, unconfirmed on the wire: `B5 05 30`,
  `31`, `5D`, `5E`, `5F` and `60` reply with a `u8` feedback at offset 3 where
  `1` means accepted and any other value means not accepted; the separate
  cascade-response candidate for `B5 05 61` describes
  an error flag in bit 0. It does not establish acknowledgement or acceptance
  for the bounded DHW override below. Outside that bounded slice, remaining ops
  carry no
  response data (candidate), so a successful eBUS response alone does not show
  acceptance (see the read-back rule above).
- **Numeric codecs** (candidate, unconfirmed on the wire): heating curve (`0B`)
  `u16` LE ÷100; room temperatures and offsets outside the bounded slice below
  `i16` LE ÷16 °C; in most other ops,
  setpoints and comfort levels `u8` ÷2 °C, preheating times `u8` × 5 minutes and
  temperature differences `u8` K. Exceptions in the fixture include the desired
  day temperature (`01`) and the vacation setpoint (`2A`), which are plain `u8`
  °C, the maximum preheating time of `10`, which is `u8` hours (0..5), and the
  switching-on and cut-off differences of `1B` and `1E`, which are given in °C.
- **Flow rate** (`B5 05 21`): candidate, unconfirmed on the wire: 16 bits at
  offsets 3..4, LSB-first, litres per hour, range 0..9999; candidate
  interpretation: packed BCD, nibble order unresolved. **Solar yield**
  (`B5 05 4E`): candidate, unconfirmed on the wire: 24 bits at offsets 3..5,
  LSB-first, kWh, range 0..99999; the separate priority candidate is bounded
  below and has no established absolute position here. Candidate interpretation:
  packed BCD, nibble order unresolved.
  Neither is a plain little-endian integer. The handling of invalid nibbles is
  unresolved (**Hypothesis**).
- **Operating mode per channel** (`B5 05 4B`): candidate, unconfirmed on the
  wire: the channel byte at offset 3 is `0` heating circuit one, `1` domestic hot
  water circuit, `2` circulation circuit, `3` cooling circuit one, `4` tariff, `5`
  noise reduction, `6` ventilation circuit one, `7` mixer circuit two, `8`
  cooling circuit two; the mode byte at offset 4 is `1` Day, `2` OFF, `3` Auto,
  `4` Eco, `5` Night.
- **Cascade** (`B5 05 54`): candidate, unconfirmed on the wire: mode `0` no
  cascade (stand alone), `1` cascade on, `2` cascade off, `3` cascade heat-up;
  temperature `u8` °C, range 40..60.
- **Forced consumption** (`B5 05 29`, `5F`): candidate, unconfirmed on the wire:
  `0` function disabled, `1` no heat (cooling) consumption, `2` maximum heat
  (cooling) consumption.

## Bounded sentinel and override candidates

These eight declarations concern the Vaillant family and B505 (`PB=0xB5`,
`SB=0x05`) only. They are **Hypothesis**, not Proven native behavior or physical
qualification. Other operations and variants remain separate. Logical positions
identify independent alternatives, not wire offsets; absolute positions and
source/destination roles are Unknown in this slice. Unknown metadata is absent,
not zero. No capture or device observation is asserted.

| Identity (operation / field) | Grade | Direction | Logical position / extent | Raw type/domain | Scale | Sentinel/default/conflict | Unresolved |
|---|---|---|---|---|---|---|---|
| OP32 / temperature_1 | Hypothesis | Unknown | first temperature / 16 bits; absolute position Unknown | raw word; signedness Unknown | Unknown | 8000: preserve-existing; 0000: circuit-default; otherwise: numeric-candidate; select raw branch before conversion | normal conversion and conflicting numeric bounds Unknown; default temperature Unknown |
| OP32 / temperature_2 | Hypothesis | Unknown | second temperature / 16 bits; absolute position Unknown | raw word; signedness Unknown | Unknown | 8000: preserve-existing; 0000: circuit-default; otherwise: numeric-candidate; select raw branch before conversion independently | normal conversion and conflicting numeric bounds Unknown; default temperature Unknown |
| OP61 / dhw_setpoint | Hypothesis | Unknown | Unknown / extent Unknown | Unknown | Unknown | validity 15 minutes = 900 seconds; default Unknown; no OP32 sentinel interpretation | acknowledgement, acceptance, persistence and duration enforcement Unknown |
| OP4D / collector_temperature | Hypothesis | Unknown | Unknown / extent Unknown | Unknown | Unknown | validity 15 minutes = 900 seconds; default Unknown | acknowledgement, acceptance, persistence and duration enforcement Unknown |
| OP4D / collector_error | Hypothesis | Unknown | Unknown / 8 bits | raw byte; signedness Unknown | Unknown | 55: short-circuit; AA: open; other codes Unknown; validity 15 minutes = 900 seconds; default Unknown | acknowledgement, acceptance, persistence and duration enforcement Unknown |
| Unknown operation / pump_power_display | Hypothesis | Unknown | Unknown / extent Unknown | raw encoding Unknown; display domain 0, 25, 50, 75, 100 percent | raw conversion Unknown; display step 25 percent | default Unknown | operation, raw bounds and duration Unknown |
| Unknown operation / remote_control | Hypothesis | Unknown | Unknown / 8 bits | raw byte; signedness Unknown | Unknown | 01: enable-associated-output; other bytes Unknown; default Unknown | operation and duration Unknown |
| OP4E / priority | Hypothesis | Unknown | Unknown / 8 bits | unsigned byte; 0..255 | no quantity scale | 0: lowest; 255: highest; default Unknown | absolute position and duration Unknown; independent of quantity units, freshness and execution |

For every row, physical support, acknowledgement, acceptance, persistence,
freshness, execution and enforcement of any proposed duration remain **Unknown**.
A fifteen-minute declaration does not establish an enforced expiry. No write
builder or timer service follows from these declarations. Neither OP32 sentinel
is a temperature: retain the raw word without numeric conversion. In particular,
`0001` remains a numeric candidate with no assigned scale, and `8000` in another
operation gains no OP32 interpretation. Priority ordering is independent of any
temperature value. Missing or conflicting evidence cannot establish acceptance;
retain raw evidence and any partial last-known-good state without promoting a
candidate to supported behavior.

[Synthetic candidate cases](fixtures/ae04_b505_candidates.json) preserve raw
alternatives and absent metadata; synthetic correctness does not qualify native
wire behavior. The finite companion scope is the eight independently merged
AE03 declarations, not a completed family catalogue.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Open questions

- Complete write selector namespace.
- Which selectors require user, installer, or service authentication state.
- Whether some controllers silently clamp values while still ACKing the frame.
- The candidate ops are known only as candidate layouts; no exchange was
  observed beyond the examples on this page, and whether any device implements
  them is not established.
- The packed-BCD nibble order, invalid-nibble handling and overflow for the flow
  rate (`21`) and the solar yield (`4E`) are unresolved.
- Whether the archived quick commands `05`, `06` and `07` are the candidate
  party function, single tank charge and savings function is unconfirmed.
- Several candidate default values lie outside their candidate intervals (see
  the fixture; for example the charge pump overrun default 0 against 3..9
  minutes); the intended defaults are unresolved.
- For the bounded OP32 fields, normal conversion and conflicting numeric bounds
  remain Unknown; neither sentinel supplies a numeric temperature. For the
  bounded overrides, absolute positions, acknowledgement, acceptance, persistence
  and duration enforcement remain Unknown. OP4E priority does not resolve the
  separate solar-yield encoding questions.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.

## References

- Finite companion declarations (AE03, implementation corroboration, not native
  wire proof): [candidate catalogue](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab55_b505_candidates.json),
  merged in [companion review](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/235).

- Public TypeSpec: [timer_inc.tsp](https://github.com/john30/ebusd-configuration/blob/main/src/vaillant/timer_inc.tsp)
- Public TypeSpec: [tempsetpoints_inc.tsp](https://github.com/john30/ebusd-configuration/blob/main/src/vaillant/tempsetpoints_inc.tsp)
- Public TypeSpec: [roomtempoffset_inc.tsp](https://github.com/john30/ebusd-configuration/blob/main/src/vaillant/roomtempoffset_inc.tsp)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
