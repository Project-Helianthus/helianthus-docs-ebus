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
| 0 | operating mode | `0` auto, `1` forced off, `2` forced CH, `3` forced DHW, `4` forced frost protection (heat pumps only) |
| 1 | actual CH setpoint | u8, raw/2 °C; `FF` selects internal control by the appliance |
| 2 | actual DHW setpoint | u8, raw/2 °C; valid for every mode except forced DHW; `FF` = internal |
| 3 | DHW flow setpoint | u8, raw/2 °C; valid only in forced DHW; `FF` = internal |
| 4 | maximum degree of modulation | u8, percent; `FF` is replaced by 100 % |
| 5 | disable bits | bit 0 CH blocked, 1 DHW tapping blocked, 2 tank loading blocked, 3 second CH-disable entry (meaning unresolved), 4 clear the burner DHW blocking time, 5 disable appliance temperature control (block modulation), 6 clear the burner CH blocking time, 7 start legionella protection |
| 6 | loading-pump setpoint | u8, raw/2 (candidate unit percent); `0` = off |
| 7 | option bits | bit 0 remote control of the CH pump, 1 backup-heater release, 2 cooling release, 3 reserved, 4/5 left/right DHW stop position, 6/7 left/right CH stop position |

Candidate value 255.0 when no value is set (the DHW setpoint and the DHW flow
setpoint; unconfirmed on the wire) lies outside the candidate range 0..127.5 of
the three setpoints, so it cannot be read as a valid setpoint. The candidate
value of the CH setpoint when no value is set is 90.0 (unconfirmed on the
wire). The candidate layout of `OP=00` has eight argument bytes and one
feedback byte; the meaning of mode value `0x17` is unresolved.

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

- Full semantics of all disable/release bits across controller generations.
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
- Sub-commands `01`..`06` have candidate layouts only; no exchange and no
  sender or responder implementation is known either way.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
