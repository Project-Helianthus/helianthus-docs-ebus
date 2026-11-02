# Vaillant B513 Value-Range Query

`PB=0xB5`, `SB=0x13`.

## Status

`B513` appears in the john30 TypeSpec `General` namespace as a read-only
value-range query. It is not yet proven by a publishable capture.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.
- `CANDIDATE`: a layout that is not confirmed on the wire. Every
  `CANDIDATE` statement is **Hypothesis**, unconfirmed on the wire.

## Wire Shape

The TypeSpec uses `@base(MF, 0x13)` and `@ext(0x4)` for `Valuerange`.

```text
Request payload:
  04 <id: UIN?>

Response payload:
  id  : UIN
  ign : up to 2 ignored bytes
  cur : UIN
  min : UIN
  max : UIN
  def : UIN
```

The request-side `id` is marked `@out` in TypeSpec. Treat the exact request
encoding as unconfirmed until captured against real hardware.

## Known Selectors

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `04` | `Valuerange` | read | register id plus current/min/max/default unsigned 16-bit values | | Query `B513 04` for a known configurable value and show the response cannot decode as id/current/min/max/default. |

## Candidate sub-commands

> **Hypothesis**, unconfirmed on the wire. The sub-commands below are the first
> payload byte (`OP`) of the B513 services with a candidate layout. Quoted names
> are Vaillant names, kept as correspondence names only. No exchange of these
> services is confirmed on the wire.

| `OP` | Candidate name | Request (candidate) | Reply (candidate) |
|---:|---|---|---|
| `00` | configuration data 1 to boiler control / appliance interface | device-specific number (`DSN`, u16 LE) and its complement (u16 LE) | the same two fields |
| `04` | get symbolic address with range information | `04 AddrLo AddrHi` | address, value, minimum, maximum, default (see below) |
| `05` | disable appliance-interface functions/parameters | one argument byte (see below) | one feedback byte |
| `06` | light synchronisation | light, colour | one feedback byte |
| `07` | read boiler information | none | appliance information at logical positions 3..11 (see below); total physical extent Unknown |

### `OP=04` get symbolic address with range information

Candidate interpretation, unconfirmed on the wire: the request is
`B5 13 04 AddrLo AddrHi` (the symbolic address as u16 LE). The positive reply,
in payload order after the `04`, carries address (u16 LE), value (u16 LE),
minimum adjustable value (u16 LE), maximum adjustable value (u16 LE) and
default value (u16 LE); all values are raw unsigned 16-bit numbers (range
0..65535) with no candidate unit or codec. Address `FFFF` has the candidate
name "All Addresses"; no multi-response mechanism is known for it.

The community template above allows up to two ignored bytes between the
address and the current value; the candidate layout places the value
directly after the address (candidate, unconfirmed on the wire). Which one a
target uses is unresolved.

Candidate interpretation, unconfirmed on the wire: the address-to-name
correspondence depends on the target family. The candidate names for one
family are in the fixture
[`fixtures/hem-b513-symbolic-addresses.csv`](fixtures/hem-b513-symbolic-addresses.csv)
(columns `address`, `address_decimal`, `vaillant_name`, `bus_profile`,
`status`; the `status` of every row is `candidate, unconfirmed on the wire`).
The device class to which this candidate name set applies is not established.
Another family uses the same numbers for different quantities (for example
address `0` is "AccessoryRelaisOne" in the fixture and
"DisplayedRoomTemperature" in a heating-circuit family; `4`
"FlowTemperatureSensorVF1", `6` "OutsideTemperatureSensor", `43`
"HeatingCircuitOperationMode", `142` "HeatingCircuitPumpState"), so a name is
only meaningful together with the family that applies to the target. No codec
is known for these names. In the family of this fixture no candidate name is
known for the addresses `0B18` and `0D5B`, which appear in the compressor-power
reads of the [B531 page](ebus-vaillant-B531-hem-power-limit.md); that page
gives candidate names for them on other targets.

### `OP=05` disable functions/parameters

All declarations in the following tables are **Hypothesis**, unconfirmed on
the wire. Logical positions include the prefix; they are not physical byte
offsets. An unspecified position or extent is **Unknown**, not zero. All
fields are raw unsigned bytes with identity conversion and no known unit.
Preserve every raw byte, including reserved values and unlabeled values.

| Bit | Request meaning (candidate) | Default |
|---|---|---|
| 0 | disable tank-loading/warm-start time program (display) | false |
| 1 | disable CH time program | false |
| 2 | disable circulation-pump program and parameters | false |
| 3 | disable weather-compensated control and parameters | true |
| 4 | disable drop-temperature adjustment | false |
| 5 | weather-compensated controller connected; request data | false |
| 6..7 | reserved | zero |

The packed request default is raw `08`. Bit 5 is request data, not feedback.
The request byte and feedback byte have Unknown logical positions; their
physical offsets and total message extents remain Unknown.

| OP | Direction | Alternative | Logical position | Raw feedback | Candidate meaning | Grade |
|---|---|---|---|---|---|---|
| 05 | response | positive | Unknown | 1 | accepted | Hypothesis |
| 05 | response | negative | Unknown | 0, 2..255 | not-accepted-or-not-supported | Hypothesis |
| 06 | response | positive | 3 | 1 | accepted | Hypothesis |
| 06 | response | negative | 3 | 0, 2..255 | rejected | Hypothesis |

The OP05 negative alternative does not resolve rejection versus lack of
support. OP06 has its own rejected label; the feedback tables are not merged.

### `OP=06` light synchronisation

| Logical position | Request field | Candidate mapping | Default | Grade |
|---|---|---|---|---|
| 3 | light | 0 off; 100 on; 255 replacement; others unlabeled | 0 (off) | Hypothesis |
| 4 | colour | raw u8, no colour interpretation | 0 | Hypothesis |

Positive feedback is at logical position 3; the separate alternatives above
retain all raw values. No physical effect is established by these labels.

### `OP=07` appliance information

The candidate request has no arguments (argument extent zero). This does not
establish a total physical message extent. The positive response has these
logical fields; total physical extent and physical offsets remain Unknown.
All Boolean defaults are false; reserved and opaque defaults are zero.

<!-- legacy-role-mapping:begin -->
| Logical position | Positive response field | Candidate mapping | Default | Grade |
|---|---|---|---|---|
| 3 | appliance type | 0 modulating; 1 single-step; 2 two-step; others unlabeled | 0 (modulating) | Hypothesis |
| 4 | appliance flags | bits 0..7: floor-standing, condensing, fan-assisted, open-vented, high-modulation-range, water-heater, step-modulation, ECS | 0 | Hypothesis |
| 5 | fuel flags | bits 0/1/2: gas, oil, ABC; bits 3..7 reserved | 0 | Hypothesis |
| 6 | tank flags | bits 0/1/2/3: layer-tank, warm-start, external-tank, combination; bits 4..7 reserved | 0 | Hypothesis |
| 7 | feature flags | bits 0..5: solar-compact, basic-solar, AAPS, advanced-power, partial-load, parameter-master; bits 6..7 reserved | 0 | Hypothesis |
| 8 | pump-mode Boolean | 0 false; 1 true; others unlabeled | 0 (false) | Hypothesis |
| 9 | opaque | raw u8 | 0 | Hypothesis |
| 10 | opaque | raw u8 | 0 | Hypothesis |
| 11 | opaque | raw u8 | 0 | Hypothesis |
<!-- legacy-role-mapping:end -->

The feature labels are candidate correspondence names, not evidence of
physical adaptation. Type 3 and Boolean 2 remain unlabeled. Opaque bytes are
independent useful fields: the synthetic tail `[7, 8, 9]` remains three bytes.

### Evidence and limits for OP05..OP07

The [synthetic examples](fixtures/ac10_appliance_info.json) declare the B513
family with variant Unknown, service B513, separate request/response and
positive/negative alternatives. **Proven** applies only to the mechanically
checked declared representation, never to a native exchange. Candidate
interpretations remain **Hypothesis**. Physical qualification, native
adaptation and peer effects remain **Unknown**. No runtime capability or write
admission follows from these declarations.

OP00 complement semantics and OP04 address dictionaries remain **Unknown**
outside this slice. The existing OP04 family alternatives above remain
unresolved; no address codec is supplied. Synthetic examples are not captures
and establish no physical behavior.

Candidate, unconfirmed on the wire: every sub-command of this family is
available under both the eBUS and the PeBUS profiles; none is known to be
available only on PeBUS.

## Unknowns

- Which device classes implement `B513`.
- Whether the `id` field is always present in the request or only in the
  decoded response model.
- Whether the ignored bytes carry status, units, or access flags.

## Open questions

- No B513 exchange has been captured: the request encoding of `04`, the
  position of the value relative to the address, the acknowledgement and the
  targets that implement each `OP` are unconfirmed on the wire.
- Which symbolic-address name set applies to which target, and the device
  class to which the candidate name set of the fixture applies.
- Whether `FFFF` returns anything useful given that no multi-response
  mechanism is known.
- The value codec behind each address: no codec is known for the candidate
  names.
- Which `OP` the community name `Valuerange` corresponds to beyond `04`, and
  whether a Vaillant requester sends any of the `OP` services; no sender or
  responder implementation is known either way.

## References

- Public TypeSpec source: [ebusd-configuration](https://github.com/john30/ebusd-configuration), `src/vaillant/general.tsp`.
