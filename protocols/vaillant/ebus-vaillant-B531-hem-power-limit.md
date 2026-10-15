# Vaillant B531 power limit (`0xB5 0x31`)

`PB=0xB5`, `SB=0x31`.

## Status

Candidate: `B531` carries the nominal-power and power-limitation exchange
between a Vaillant heat-pump energy-manager requester and heat-pump targets;
none of it is confirmed on the wire.

> **Hypothesis**, unconfirmed on the wire: every layout on this page is a
> request a Vaillant requester sends and the reply it accepts. No frame
> of B531 has been captured. Reply-length and byte-position statements describe
> what the requester accepts, not what a heat pump is known to send.

Evidence labels:

- `CANDIDATE`: a request or reply layout that is not confirmed on the wire,
  or a unit that is not established.

Framing used below: `QQ` is the requester's address; `ZZ` is the
destination; `NN` is the payload length; the first payload byte is the
sub-command. Reply bytes are numbered from 0 (the first byte after the length
byte) and "reply length" is the declared payload length.

## Sub-commands

| Sub-command | Meaning (candidate) | Request | Reply |
|---:|---|---|---|
| `00` | known only by its number | no layout known | no layout known |
| `01` | power-limitation token | `QQ ZZ B5 31 03 01 <tokLo> <tokHi>` | feedback byte |
| `02` | minimum and maximum nominal electrical power | `QQ ZZ B5 31 01 02` | minimum u16 LE, maximum u16 LE |
| `03` | system-control limitation status | `QQ 15 B5 31 02 03 <state>` | one byte, not interpreted |

Profile availability of B531 is not established; no sub-command is known to be
available only on PeBUS.

### `00` - known only by its number

Sub-command `00` is known only by its number: no request layout, reply layout
or device capability is known for it, and it is not inferred by analogy with
`01`..`03`. No further layout, unit or profile of B531 is known.

### `01` - power-limitation token (candidate, unconfirmed on the wire)

```text
QQ ZZ B5 31 03 01 <tokLo> <tokHi>
```

- `NN` = `0x03`: the sub-command byte and the token as one u16 little-endian
  value.
- The token is one u16 little-endian value in the same counts as the
  sub-command `02` values (**Hypothesis**: a power value in units of 10 W);
  its meaning is not established on the wire. A start-up request sends the
  literal token `FFFF`;
  `FFFF` is not shown to reset or delete anything in the target.
- Reply handling: accepted when the reply length is at least 1; reply byte 0 is
  the feedback byte; only feedback `1` counts as success (feedback `3`, whose
  bit 0 is set, is rejected). Feedback `1` is the requester's own success
  test; no feedback enumeration is established and whether the target applies
  the token is not established.

### `02` - minimum and maximum nominal electrical power (candidate, unconfirmed on the wire)

```text
QQ ZZ B5 31 01 02
```

- `NN` = `0x01`, payload `02`. One request per eligible target.
- The reply is decoded only when its length is at least 4:

| Reply bytes | Candidate meaning | Encoding |
|---|---|---|
| 0..1 | minimum nominal electrical power | u16 little-endian |
| 2..3 | maximum nominal electrical power | u16 little-endian |

- The requester reads each value as 10 W per count (candidate unit, see
  "Unit"); it attaches no other unit or scale information.

### `03` - system-control limitation status (candidate, unconfirmed on the wire)

```text
QQ 15 B5 31 02 03 <state>
```

- `NN` = `0x02`, `ZZ` = `0x15` (the address of VRC720-family controllers).
- `<state>`: `0` = limitation not supported, `1` = limitation possible but
  not effective, `2` = limitation effective (candidate meanings; the condition
  under which each state is sent is the requester's own and is not
  established on the wire).
- The reply is accepted when its length is at least 1; reply byte 0 is not
  tested by the requester. The meaning of the reply byte is not established,
  and no feedback enumeration is established.

## Token and state

The token of sub-command `01` is in the same counts as the values of
sub-command `02`. The relation of the token to the maxima of sub-command `02`
is not established on the wire; a token below the maximum, a zero token and a
token that changes between requests are all candidates. The condition under
which each state of sub-command `03` is sent is not established; candidate
reading: state `2` while a limitation is active, state `1` without limitation,
state `0` when limitation is not possible.

## Unit

Candidate scale: one raw count of sub-command `02` is 10 W (raw 65535 would
be 655,350 W). The unit the heat pump itself uses for sub-command `02` is not
established. **Hypothesis**: 10 W per count; unresolved. No eBUS datum carries a unit.
The token of sub-command `01` is in the same counts as the sub-command `02`
values, so the same candidate unit applies to it; the token unit at the target
is not established.

## Targets

> **Hypothesis**, unconfirmed on the wire.

The candidate target addresses of the B5 16 14, B5 31 `01` and B5 31 `02`
requests are `0x08`, `0x76`, `0x18`, `0x38`, `0x78`, `0xF8`, `0x24`, `0x44` and
`0x84`; B5 31 `03` goes to address `0x15`. The B5 16 14, B5 31 `01` and B5 31
`02` requests are sent to targets identified as heat-pump or backup-heater
devices (candidate); the relation of the targets to the B5 10 00 query is
unresolved (see the [B510 page](ebus-vaillant-B510.md)). Address `0x76` is not
sent the compressor-power reads below nor the
[B5 11 01 failure-mode read](ebus-vaillant-B511.md) (candidate, unconfirmed on
the wire). Whether the destination
of the B5 10 00 query is always the heat-pump interface unit's address
(`0x08`) or the address of the discovered target is unresolved.

## Compressor power reads (B5 09 29 and B5 09 54)

> **Hypothesis**, unconfirmed on the wire. These reads belong to the same
> requester; for the sub-commands `29` and `54` of service B509 see the
> [B509 page](ebus-vaillant-B509.md).

Two candidate read forms exist (unconfirmed on the wire): `B5 09 29` with the
symbolic address `0B18`, and `B5 09 54` with the PeBUS address byte `02` and the
data-point address `0D5B`; `B5 09 54` is also a candidate form for `0B18`. A
requester selects one of them from the target's reported software product
number (SPN, read through the identification services; candidate, unconfirmed
on the wire); for a target whose SPN selects none of them, no read form is
established (candidate). The request is sent repeatedly (candidate); the
period is unresolved. `QQ` is the requester's address.

| Read form | Request (candidate) | Symbolic address (u16 LE) |
|---|---|---|
| `29` | `QQ ZZ B5 09 03 29 18 0B` | `0B18` |
| `54` | `QQ ZZ B5 09 05 54 02 00 18 0B` | `0B18` |
| `54` | `QQ ZZ B5 09 05 54 02 00 5B 0D` | `0D5B` |

In the `54` request, payload byte 1 (`02`) is the PeBUS address byte and
payload byte 2 (`00`) is the configuration byte (bit 0 = 0 for a read)
(candidate). The destination `ZZ` is the address of the discovered target or
the constant `0x08`; which one applies is unresolved.

Reply handling by the requester (candidate):

- `29`: accepted when the reply length is at least 4. Reply bytes 0..1 echo the
  address (not checked); bytes 2..3 are the value, u16 little-endian. No sign
  handling, no scale.
- `54`: accepted only when bit 0 of reply byte 1 (feedback) is `1`. Byte 0
  (PeBUS address) and bytes 2..3 (address echo) are not checked. For `0B18`
  the reply length must be at least 6 and the value is u16 little-endian from
  bytes 4..5. For `0D5B` the reply length must be at least 8 and the value is
  binary32 little-endian from bytes 4..7, of which the requester uses the
  integer part truncated to 16 bits (candidate).
- A reply shorter than the minimum is not used.

Candidate names, types and units of the two addresses (unconfirmed on the
wire):

| Address | Vaillant name | Candidate meaning | Candidate type and unit |
|---|---|---|---|
| `0B18` | `ApplCapacity` | capacity of the appliance | uint16 LE in W (factor 1), or int16 LE without a unit (the requester reads it unsigned); which form applies depends on the target's reported SPN |
| `0D5B` | `ASW1_PowerConsumption` | electrical power consumption | binary32 LE, no unit established |

On some targets the address `0B18` is a different quantity (candidate: a
one-byte exhaust-air humidity value), so a symbolic address is meaningful only
together with the target family. The symbolic-address names of the
[B513 page](ebus-vaillant-B513.md) are for another target family; no candidate
name in that family is known for `0B18` or `0D5B`. The unit of the value is not
established (candidate: W for the uint16 form of `0B18`). Candidate,
unconfirmed on the wire: both read forms `29` and `54` are available under the eBUS and the PeBUS
profiles; neither is known to be available only on PeBUS. In the candidate
layout of `54`, the PeBUS address byte is at payload offset 1 (candidate), the
configuration byte at 2 (bit 0: 0 = read) and the address at 3..4; its reply
carries the PeBUS address, a feedback byte (bit 0 = success), the address and
the data.

## Not known on eBUS

The following energy-management data is not known to be carried in any eBUS
frame:

- An energy-management status (DHW and CH capability and status) is not known
  to be carried in any B5 10, B5 16 14 or B5 31 frame; no service, sub-ID,
  offset or encoding for it is known.
- Grid-connection-point, photovoltaic and battery measurement values are not
  known to be carried in any B5xx or B524 frame. The B524 register
  `heating_cylinder_offset_at_pv_surplus` (B524 OP `0x02`, GG `0x00`, RR `0x00A2`,
  see the [B524 register map](ebus-vaillant-B524-register-map.md)) is not known
  to carry these values.

## Open questions

- No frame of any B5 31 request, of the ten-argument B5 10 00 query, of the
  B5 16 14 power read, of the B5 11 01 failure-mode read or of the B5 09 29 and
  B5 09 54 compressor-power reads has been captured. The `QQ`/`ZZ`/`NN` framing,
  the reply length a heat pump actually produces and the acknowledgement are
  all unconfirmed on the wire.
- The request and reply layout of sub-command `00` is not known, and no
  further layout, unit or profile of B531 is known.
- The feedback enumerations of sub-commands `01` and `03`, whether `FFFF` is a
  reset or a delete, whether the target applies the token, and the unit of the
  token at the target.
- The meaning of reply byte 0 of sub-command `03`.
- The physical unit of sub-command `02` as a heat pump uses it (candidate: 10 W
  per raw count).
- The live bytes and the unit of the compressor-power values; for some
  targets no candidate name, type or unit is known for the read address.
- No assignment of software product numbers to read forms or units is
  established.
- The software product number that selects the read form is read from replies
  of the device at `0x08` to identification requests (candidate); such replies
  are unconfirmed on the wire.
- Whether the destination of the requests is the heat-pump interface unit's
  address (`0x08`) or the discovered target's address.
- How the requester selects its targets, and the relation to the "heat pump
  supported" indication of the B5 10 00 query, and the repetition period of the
  compressor-power read.
- Whether other installations of the heat-pump systems involved behave alike
  is unresolved.

## See also

- [B510](ebus-vaillant-B510.md): the B5 10 00 query that precedes the B5 31
  requests.
- [B511](ebus-vaillant-B511.md): the B5 11 01 failure-mode read.
- [B516](ebus-vaillant-B516-energy.md): the B5 16 14 current electrical power
  read (section 9).
