# Vaillant B515 Legacy Timer Template

`PB=0xB5`, `SB=0x15`.

## Status

`B515` appears in john30 TypeSpec templates as a generic read/write timer
family. It is distinct from the newer `B555` timer/schedule protocol documented
for newer controller families.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.
- `CANDIDATE`: a layout that is not confirmed on the wire. Every
  `CANDIDATE` statement is **Hypothesis**, unconfirmed on the wire.

## Wire Shape

The TypeSpec template defines:

```text
Read template:
  @base(MF, 0x15)
  ign : up to 1 ignored byte

Write template:
  @write
  @base(MF, 0x15)

Timer value:
  value : timer composite
```

Concrete timer include files add two selector bytes via `@ext(day, group)`.

## Known Selector Groups

| Include file | Group byte | TypeSpec names | Evidence | Falsification test |
|---|---|---|---|---|
| `timerhc_inc.tsp` | `00` | `HcTimer_Monday`..`HcTimer_Sunday` | | Read `B515 <day> 00` from a legacy controller and show it cannot decode as a heating timer. |
| `timerhwc_inc.tsp` | `01` | `HwcTimer_Monday`..`HwcTimer_Sunday` | | Same test for DHW timer windows. |
| `timercc_inc.tsp` | `02` | `CcTimer_Monday`..`CcTimer_Sunday` | | Same test for circulation timer windows. |
| `timercool_inc.tsp` | `03` | `CoolingTimer_Monday`..`CoolingTimer_Sunday` | | Same test for cooling timer windows. |
| `timertariff_inc.tsp` | `04` | `TariffTimer_Monday`..`TariffTimer_Sunday` | | Capture a tariff timer read and show no B515 timer composite is used. |

## Candidate time-frame layout

> **Hypothesis**, unconfirmed on the wire. The layout below is a candidate
> layout for B515; no exchange of it is confirmed on the wire. Its
> two selector bytes correspond to the day/group pair of the TypeSpec template
> above, but the candidate read reply begins with the two echoed selector bytes
> where the template has up to one ignored byte; both forms are kept and the
> difference is unresolved.

In this candidate physical form, the first payload byte is the weekday (`0` Monday .. `6` Sunday) and the
second byte the channel:

```text
Read request:    B5 15 <weekday> <channel>
Read reply:      <weekday> <channel> s1 e1 s2 e2 s3 e3 mode   (9 payload bytes)
Write request:   B5 15 <weekday> <channel> s1 e1 s2 e2 s3 e3 mode
Write reply:     <weekday>                                    (1 payload byte)
```

`s1 e1 s2 e2 s3 e3` are the start and end of three periods. Each is one byte
`n` with `0..144` meaning `n` x 10 minutes (`00:00`..`24:00`); the meaning of `FF` is
unresolved. A period with `start == end` is not known to be a deletion.

Synthetic candidate bytes for Monday, heating circuit one (not a transmission instruction):
`B5 15 00 00 21 30 57 60 6F 7E 01` = `05:30-08:00`, `14:30-16:00`,
`18:30-21:00`, mode `1`.

| Channel | Candidate meaning |
|---:|---|
| `00` | heating circuit one |
| `01` | domestic hot water |
| `02` | circulation |
| `03` | cooling one |
| `04` | tariff |
| `05` | noise reduction |
| `06` | ventilation one |
| `07` | mixer two |
| `08` | cooling two |

Generic programming mode (the last byte, candidate; separate from the five
unnamed variants below): `0` valid for the given day, `1`
Monday..Sunday, `2` Monday..Friday, `3` Saturday..Sunday. On some targets the
candidate names cover `0..3`, all as "valid for the given day" (unresolved;
candidate, unconfirmed on the wire). Mode `0` is not "off" (candidate,
unconfirmed on the wire). Candidate values when no value is set (unconfirmed on
the wire): the three periods of the example with mode `1` in the generic form,
and all `00:00` with mode `0` in the heating-circuit form.

Candidate, unconfirmed on the wire: the read and the write service of this
family are available under both the eBUS and the PeBUS profiles; neither is
known to be available only on PeBUS.

## Finite period declarations

These are **Hypothesis** candidate declarations for the Vaillant legacy timer
family, not confirmed native behavior. The synthetic representation can be
checked as **Proven** software behavior; physical qualification remains
**Unknown**. A fixture validates the declared representation only.

### Period vocabulary

| Raw decimal | Declared time | Grade |
|---|---|---|
| 0 | 00:00 | Hypothesis |
| 54 | 09:00 | Hypothesis |
| 144 | 24:00 | Hypothesis |
| 145 | Unknown | Unknown |
| 255 (FF) | Unknown | Unknown |

Raw 0..144 inclusive declares ten-minute steps: 145 labels, not 144.
There is no declared conversion or rounding rule for 09:05.
Raw 145 and FF have no established role; preserve their raw bytes.

### Selector carriers and defaults

The carrier domain does not establish a meaning for every value. Request
defaults are declarations, not instructions to send or evidence of peer effects.
The weekday default is Monday; the narrower Monday..Sunday names in the generic
layout do not restrict the raw carrier. A default channel is not a channel map:
mixer two default zero does not resolve the generic channel 07 candidate above.

| Field | Raw decimal domain | Context | Default | Grade |
|---|---|---|---|---|
| weekday | 0..255 | read/write request and read positive | Monday | Hypothesis |
| channel | 0..255 | read/write request: circulation | 2 | Hypothesis |
| channel | 0..255 | read/write request: DHW | 1 | Hypothesis |
| channel | 0..255 | read/write request: mixer one | 0 | Hypothesis |
| channel | 0..255 | read/write request: mixer two | 0 | Hypothesis |
| channel | 0..255 | read positive | 0 | Hypothesis |
| mode | 0..255 | read/write request and read positive | Unknown | Hypothesis |

### Logical extents

Logical extents include prefix positions; they are not physical offsets or
validated payload lengths. The physical forms, including the competing
two-position gap, remain Unknown. Keep both the echoed day/channel reply and
the template's up-to-one-ignored-byte reply above as unresolved alternatives.
An absent extent is Unknown, never zero.

| Family | Variant | Direction | Service | Operation | Alternative | Logical extent | Physical extent | Grade |
|---|---|---|---|---|---|---|---|---|
| Vaillant legacy timer | periods | request | B515 | read | request | 4 | Unknown | Hypothesis |
| Vaillant legacy timer | periods | response | B515 | read | positive | 11 | Unknown | Hypothesis |
| Vaillant legacy timer | periods | response | B515 | read | negative | Unknown | Unknown | Hypothesis |
| Vaillant legacy timer | periods | request | B515 | write | request | 11 | Unknown | Hypothesis |
| Vaillant legacy timer | periods | response | B515 | write | positive | 3 | Unknown | Hypothesis |
| Vaillant legacy timer | periods | response | B515 | write | negative | Unknown | Unknown | Hypothesis |

### Unnamed mode variants

Five candidate variants map raw 0..3 non-injectively. Their exact per-variant
labels remain absent. Preserve each variant and raw value; do not derive a
reversible default or merge these variants with the generic ordering above.
The numbers below distinguish unresolved variants only, not device identities.

| Family | Variant | Direction | Service | Operation | Alternative | Raw decimal domain | Injective | Inverse default | Labels | Grade |
|---|---|---|---|---|---|---|---|---|---|---|
| Vaillant legacy timer | mode candidate 1 | Unknown | B515 | Unknown | mode candidate 1 | 0..3 | no | Unknown | Unknown | Hypothesis |
| Vaillant legacy timer | mode candidate 2 | Unknown | B515 | Unknown | mode candidate 2 | 0..3 | no | Unknown | Unknown | Hypothesis |
| Vaillant legacy timer | mode candidate 3 | Unknown | B515 | Unknown | mode candidate 3 | 0..3 | no | Unknown | Unknown | Hypothesis |
| Vaillant legacy timer | mode candidate 4 | Unknown | B515 | Unknown | mode candidate 4 | 0..3 | no | Unknown | Unknown | Hypothesis |
| Vaillant legacy timer | mode candidate 5 | Unknown | B515 | Unknown | mode candidate 5 | 0..3 | no | Unknown | Unknown | Hypothesis |

### Ordering and qualification

Hypothesis: a written start equal to end declares a disabled interval.
First-before-second-before-third ordering is declared as Hypothesis.
An out-of-order interval example remains unqualified; it does not establish
rejection, sorting, or any other peer enforcement. Disabled does not establish
deletion or reset. Preserve complete native bytes and independent useful fields
beside any candidate interpretation. Native adaptation and peer effects remain
Unknown; these declarations grant no runtime capability or write admission.

| Property | Grade |
|---|---|
| physical forms | Unknown |
| competing two-position gap | Unknown |
| enforcement | Unknown |
| deletion/reset | Unknown |
| atomicity | Unknown |
| overlap | Unknown |
| midnight-crossing | Unknown |
| timezone/DST | Unknown |
| physical schedule effects | Unknown |
| native adaptation | Unknown |
| peer effects | Unknown |
| physical qualification | Unknown |

This is a partial catalog. Completing mode tables and physical layout remains
later work. Synthetic examples are in
[the finite-period fixture](fixtures/ac12_legacy_timer.json); they are not
captures or physical qualification evidence.

## Relationship to B555

`B515` and `B555` should not be merged as one protocol. `B515` is modeled as a
generic legacy timer template with day/group selectors. `B555` uses explicit
schedule opcodes such as `A3`..`A6` and different payload semantics.

## Unknowns

- Which Vaillant controller generations still use B515 for user-visible
  schedules.
- Exact write ACK semantics.
- Whether B515 timers share setpoint coupling behavior with B524/B555 on any
  device class.

## Open questions

- No B515 exchange has been captured: the request and reply lengths, the
  acknowledgement and the write reply are unconfirmed on the wire.
- Which controllers answer channels `05`..`08`; the TypeSpec template covers
  channels `00`..`04` only.
- Whether `start == end` deletes a period, and the effect of `FF`.
- The mode names of targets whose candidate names cover `0..3` alike.
- The read reply: the candidate begins with the two echoed selector bytes,
  the template has up to one ignored byte; which form a target uses is
  unresolved.
- Whether any Vaillant requester sends B515; no sender or responder
  implementation is known either way.

## References

- Public TypeSpec template: [`src/vaillant/_templates.tsp`](https://github.com/john30/ebusd-configuration)
- Public TypeSpec: [`src/vaillant/timerhc_inc.tsp`](https://github.com/john30/ebusd-configuration)
- Public TypeSpec: [`src/vaillant/timerhwc_inc.tsp`](https://github.com/john30/ebusd-configuration)
- B555 schedule protocol: [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
