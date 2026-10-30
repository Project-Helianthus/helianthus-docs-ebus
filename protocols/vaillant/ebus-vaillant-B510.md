# Vaillant B510 SetMode / Controller-to-Boiler Operational Data

`PB=0xB5`, `SB=0x10`.

## Status

`B510` is modeled by john30 TypeSpec as a passive/write `SetMode` command in
the heating-circuit mode family. Historical Vaillant notes describe it as
operational data from room/controller to burner/boiler.

This document supersedes the weaker older label "Status/Diagnostic" for
`B510` in the top-level Vaillant identifier overview.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.
- `CANDIDATE`: a layout or a request that is not confirmed on the wire.
  Every `CANDIDATE` statement is **Hypothesis**, unconfirmed on the wire.

## Wire Shape

Known `SetMode` shape:

```text
Request payload:
  00
  hcmode
  flowtempdesired
  hwctempdesired
  hwcflowtempdesired
  ign
  disable bits
  ign
  release/control bits
```

The exact byte widths and scaling come from ebusd data types (`hcmode`,
`temp1`, `temp0`, `IGN`, and bit fields). Do not decode bytes without the
request context and target profile.

## Candidate sub-commands

> **Hypothesis**, unconfirmed on the wire: the table lists the B510
> sub-commands (the first payload byte, `OP`) with a candidate layout.
> Quoted names are Vaillant names, kept as correspondence names only. No
> exchange of these sub-commands is confirmed on the wire.

| `OP` | Candidate name | Request arguments (candidate) | Reply (candidate) |
|---:|---|---|---|
| `00` | heating control | eight bytes, see the next section | one feedback byte |
| `01` | switch off remote heating control | none | one feedback byte |
| `02` | remote control of current CH/DHW setpoint | remote status, upper limit of the CH setpoint, upper limit of the DHW setpoint | one feedback byte |
| `03` | air-conditioning outdoor-unit control data (write) | selected climate mode, required capacity, energy cost limit, force mode | none (header only) |
| `04` | primary energy cost update | primary energy type, cost of primary energy | none (header only) |
| `05` | domestic hot water adjustment | DHW setpoint, adjustment control | one feedback byte |
| `06` | Green iQ | status of Green iQ | none (header only) |

Feedback byte (candidate): `1` is the candidate success value ("accepted");
`0` and `2` to `255` are candidates for "not accepted" (unconfirmed on the
wire).

Candidate, unconfirmed on the wire: every sub-command of this family is
available under both the eBUS and the PeBUS profiles; none is known to be
available only on PeBUS.

### Heating control (`OP=00`), eight argument bytes (candidate)

| Argument | Meaning (candidate) | Encoding |
|---:|---|---|
| 0 | operating mode | automatic, forced-heating, forced-DHW and forced-off are named candidates; numeric mode codes Unknown |
| 1 | actual CH setpoint | u8, raw/2 °C; `FF` selects internal control by the appliance |
| 2 | actual DHW setpoint | u8, raw/2 °C; valid for every mode except forced DHW; `FF` = internal |
| 3 | DHW flow setpoint | u8, raw/2 °C; valid only in forced DHW; `FF` = internal |
| 4 | maximum degree of modulation | u8, percent; `FF` is replaced by 100 % |
| 5 | disable bits | see the bounded operational candidate table below; logical argument 5 is not an established wire offset |
| 6 | loading-pump setpoint | u8, raw/2 (candidate unit percent); `0` = off |
| 7 | option bits | bit 0 remote control of the CH pump, 1 backup-heater release, 2 cooling release, 3 reserved, 4/5 left/right DHW stop position, 6/7 left/right CH stop position |

Candidate value 255.0 when no value is set (the DHW setpoint and the DHW flow
setpoint; unconfirmed on the wire) lies outside the candidate range 0..127.5 of
the three setpoints, so it cannot be read as a valid setpoint. The candidate
value of the CH setpoint when no value is set is 90.0 (unconfirmed on the
wire). The candidate layout of `OP=00` has eight argument bytes and one
feedback byte; the meaning of mode value `0x17` is unresolved.

### Bounded operational enums and disable-bit candidates

All rows below are **Hypothesis**, unconfirmed on the wire. Identity is the
Vaillant B510 family, PB=0xB5, SB=0x10, OP and field shown in each row;
direction is a candidate controller-to-boiler request. A logical position is
not a wire offset. Absent positions remain Unknown, including the disable
carrier position in the finite companion declarations. The eight-argument
variant above supplies only a logical argument index. This table does not
extend to the ten-argument query or the broadcast variant.

| Grade | OP | Field | Direction | Logical position / extent | Raw type / domain | Scale / unit | Values / bit candidates | Sentinel / default / conflict / unresolved |
|---|---|---|---|---|---|---|---|---|
| Hypothesis | 02 | remote_status | request | Unknown; 8 bits | u8 0..255 | Unknown | raw status only | sentinel/default Unknown; semantics Unknown |
| Hypothesis | 02 | CH_setpoint_upper_limit | request | Unknown; 8 bits | u8 0..255 | raw/2 degrees Celsius | none declared | sentinel/default Unknown; physical acceptance Unknown |
| Hypothesis | 02 | DHW_setpoint_upper_limit | request | Unknown; 8 bits | u8 0..255 | raw/2 degrees Celsius | none declared | sentinel/default Unknown; physical acceptance Unknown |
| Hypothesis | 03 | climate | request | Unknown; 8 bits | u8 0..255 | none declared | 0 off; 1 heating; 2 cooling | sentinel/default Unknown; other values unmapped |
| Hypothesis | 03 | capacity | request | Unknown; 8 bits | u8 0..250 | raw/10 kW | none declared | sentinel/default Unknown; 251..255 outside candidate domain |
| Hypothesis | 03 | cost | request | Unknown; 8 bits | u8 0..250 | reciprocal-MWh; divisor Unknown | none declared | sentinel/default Unknown; monetary versus emissions Unknown |
| Hypothesis | 03 | force | request | Unknown; 8 bits | u8 0..255 | none declared | 0 normal; 1 maximum; 2 minimum; 3 off; 4 cooling-leak-test; 5 cooling-charge-test; 6 capacity-test; 7 I/O-test | sentinel/default Unknown; 8..255 unmapped |
| Hypothesis | 04 | energy | request | Unknown; 8 bits | u8 0..255 | none declared | 0 unknown; 1 gas; 2 electricity-one; 3 electricity-two; 4 fuel; 5 pellet | sentinel/default Unknown; monetary versus emissions Unknown; 6..255 unmapped |
| Hypothesis | 05 | DHW_setpoint | request | Unknown; 8 bits | u8 0..255 | raw/2 degrees Celsius | none declared | sentinel/default Unknown; physical acceptance Unknown |
| Hypothesis | 05 | adjustment | request | Unknown; 8 bits | u8 0..255 | none declared | bit 0 CH; bit 1 DHW; 0 released / 1 blocked; bits 2..7 reserved, retained | sentinel/default Unknown; reserved expected values Unknown |
| Hypothesis | 06 | status | request | Unknown; 8 bits | u8 0..255 | none declared | bit 0: 0 off / 1 on; bits 1..7 reserved zero, retained | sentinel/default Unknown; nonzero reserved bits do not acquire meaning |
| Hypothesis | 00 | disable | request | Unknown; 8 bits (logical argument 5 in eight-argument variant) | u8 0..255 | none declared | bits 0..2 active only in automatic; ignored in forced-heating, forced-DHW, forced-off; bit 6 relates to subsequent flame status; bit 7 starts legionella protection, persists until corresponding status, does not command termination | sentinel/default Unknown; bits 3/4 timer assignment unresolved (Unknown); bit 5 meaning Unknown; numeric mode codes Unknown; bit 7 mode applicability Unknown |

The competing timer assignments for bits 3/4 remain independent unresolved
alternatives; neither a CH nor a DHW timer assignment is settled. Bit 6 must
not be relabeled as a timer clear. Bit 7 is independent of low disable bits;
its persistence is not an instruction to terminate protection. No control
path or active timer follows from these declarations.

The [synthetic cases](fixtures/ae14_b510_candidates.json) preserve raw values,
reserved bits and explicitly absent metadata. Capacity raw 0/250 corresponds
to 0/25 kW; raw 251 is outside the candidate domain. Temperature raw 01 is
0.5 degrees Celsius for both OP02 limits and OP05. Adjustment 00 releases
both, 03 blocks both, and FC retains reserved bits. Disable 07 has active low
candidates only in automatic mode, with the same low bits ignored in each
named forced mode. These arithmetic examples provide no physical qualification:
physical acceptance, freshness and actual execution remain **Unknown**.

The finite companion is [AE13 catalog entries](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab65_b510_candidates.json)
([merged change](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/244)).
Its twelve declarations corroborate this bounded candidate scope, not a broader
completed catalog or proof of a native wire contract. No native observation
is supplied here; all candidate claims retain their grades.

## B5 10 00 query with ten argument bytes (candidate)

> **Hypothesis**, unconfirmed on the wire. The request below is the one
> sent by a Vaillant requester that polls a heat-pump interface unit; no
> frame of it is confirmed on the wire.

```text
QQ ZZ B5 10 0B 00 17 00 00 00 00 00 00 00 00 00
```

- `QQ` is the requester's address, `ZZ` = `0x08`. Whether `ZZ`
  is always the heat-pump interface unit's address or the address of a
  discovered device is unresolved; see the
  [B531 page](ebus-vaillant-B531-hem-power-limit.md).
- `NN` = `0x0B`: the command byte `00`, the operating-mode byte `0x17` and
  nine zero bytes, that is ten argument bytes where the eight-argument
  candidate layout above has eight.

Reply handling by the requester (candidate). Reply bytes are numbered from 0
(the first byte after the length byte), as on the B511, B516 and B531 pages:

| Reply element | Handling |
|---|---|
| reply length ≥ 1 | the reply is accepted |
| byte 0 | feedback byte; `1` is the candidate success value |
| bytes 1..2 | one little-endian u16, present when the reply carries more than two data bytes |
| bit 6 of that u16 | candidate meaning: "heat pump supported"; read only when the feedback value is `1` and the reply has more than two data bytes |

Feedback `1` is the candidate success value; `0` and `2` to `255` are
candidates for "not accepted" (unconfirmed on the wire). No relation of the
feedback byte to the eBUS acknowledgement is established, and feedback `1` is
not evidence that a heat pump is physically supported.
The same requester is a candidate sender (**Hypothesis**, unconfirmed on the
wire) of the [B5 31 requests](ebus-vaillant-B531-hem-power-limit.md)
and the B5 16 14 power read (see [B516](ebus-vaillant-B516-energy.md)): the
B5 31 `03` request goes to address `0x15`, and the other B5 31 requests and the
B5 16 14 power read go to the candidate target addresses of the B531 page; the
relation of those targets to this query is unresolved. The B5 11 01
failure-mode read and the B5 11 0E status byte are described on the
[B511 page](ebus-vaillant-B511.md) (bit meanings unconfirmed on the wire).

## Public evidence

The public references below provide corroborating capture examples; they do not establish a complete schema.

## Falsification Tests

- Change controller mode/setpoints and passively capture `B510`; falsify the
  `SetMode` mapping if the fields do not track the changed values.
- Compare captured `B510` bytes against controller B509 monitor registers whose
  names mirror `B510` payload bytes; falsify if the monitor registers do not
  match.
- Capture a topology where `B510` is not controller-to-boiler and document the
  alternate source/target role.

## Unknowns

- Physical acceptance of the bounded candidates across controller families;
  disable bits 3/4 timer assignments and bit 5 meaning remain Unknown.
- Whether the broadcast `B510 06 00` form is part of the same `SetMode` family
  or a separate broadcast selector.
- Whether non-BAI targets reuse the same payload layout.

## Open questions

- No frame of the ten-argument B5 10 00 query, of the B5 31 requests, of the
  B5 16 14 power read or of the B5 11 01 failure-mode read has been captured.
  The `QQ`/`ZZ`/`NN` framing shown above, the reply length a heat pump
  produces and the acknowledgement are all unconfirmed on the wire.
- The meaning of operating-mode byte `0x17` and of the two extra argument
  bytes of the ten-argument query (the eight-argument candidate layout ends at
  option bits).
- Whether feedback values `0` and `2` to `255` mean "not accepted" on a real
  target (candidate), and whether the feedback byte relates to the eBUS
  acknowledgement.
- Whether bit 6 of the little-endian u16 in reply bytes 1..2 means "heat pump
  supported" on a real target; only the requester's use of it is known.
- The scale of the loading-pump setpoint: raw/2 with a candidate range of
  0..127.5 and unit percent, versus steps of 2 percent.
- Sub-commands `01`..`06` have candidate layouts only. The finite companion
  declarations do not establish a sender, responder, exchange or physical
  acceptance. Positions, sentinel/default meanings and the monetary versus
  emissions interpretation remain Unknown as scoped in the table.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/main/src/vaillant/hcmode_inc.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/main/src/vaillant)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
