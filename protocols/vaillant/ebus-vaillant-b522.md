# Vaillant B522 Ventilation and Demand Candidates

`PB=0xB5`, `SB=0x22`.

## Status

`B522` appears in the john30 `08.recov` TypeSpec as a write command family for
recoVAIR ventilation modes. The configured base includes a static `0x00`
selector after `SB=0x22`.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec defines:

```text
Write base:
  @base(MF, 0x22, 0)

Configured request payload:
  00 <selector> 00 ff ff
```

The trailing `00 ff ff` bytes are part of the static TypeSpec extension for the
known ventilation commands.

## Known Selectors

| Request suffix | TypeSpec name | Configured direction | Candidate meaning | Grade |
|---|---|---|---|---|
| `02 00 ff ff` | `VentDay` | write | ventilation day mode | Hypothesis |
| `01 00 ff ff` | `VentNight` | write | ventilation night mode | Hypothesis |
| `03 00 ff ff` | `VentBoost` | write | boost ventilation | Hypothesis |

## Relationship to B509 Registers

The same `08.recov` TypeSpec also exposes many recoVAIR values through B509-like
register templates. `B522` is only the small command family for ventilation mode
writes and should not be used as the general recoVAIR register map.

## Configured ventilation layout (separate hypothesis)

The existing configured ventilation candidate uses the op `B5 22 00`, air ventilation
control; it has not been confirmed on the wire. Offsets count from the first
byte of the service prefix; a target response on the bus carries no such prefix,
and how the candidate response offsets map onto the bytes of a bus response is
unconfirmed on the wire (**Hypothesis**: response offset 3 is the first data
byte; see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)):

- Request (candidate, unconfirmed on the wire): fan stage `u8` at offset 3;
  automatic mode in bit 0 at offset 4; room setpoint `u8` ÷2 °C at offset 5;
  current mode `u8` at offset 6.
- Positive reply (candidate, unconfirmed on the wire): at offset 3, bit 0 error,
  bit 1 maintenance, bit 2 filter maintenance.

**Hypothesis**, unconfirmed on the wire: in the configured rows above the leading
`00` is the op byte, the selector byte (`01` night, `02` day, `03` boost) is the
fan stage of the candidate layout, the `00` after it is the automatic-mode
byte (off), and the trailing
`ff ff` are an unset room setpoint and an unset current mode. This would make the
ventilation mode commands one request layout with different fan stages, and the
positive reply the status bits above.

## Partial demand and raw-carrier catalog

This partial field catalog is a separate candidate declaration, not an alias of
those configured ventilation selectors. Its absent operation, direction, extent,
names and coordinates stay absent; logical extents include prefix positions and
are not physical response lengths. No physical offsets follow from an extent.
The older offset and status-role hypotheses above do not fill these absences.

**Proven** applies only to the declared representation checked with
[synthetic examples](fixtures/ac24_fan_demand.json), not to native wire behavior.
Every physical interpretation below is **Hypothesis**. Physical mapping,
installed support, execution, semantic equivalence, native adaptation, peer
effects and physical qualification remain **Unknown**. No device exchange is
claimed by these examples. This page grants no runtime capability or write
admission; acknowledgment alone does not establish a resulting physical state.

### Candidate identities

`absent` denotes an unspecified value, never zero or a wildcard. Family names
identify candidate scope rather than installed support. These alternatives stay
independent, including the negative alternative with no declared fields.

| Family | Variant | Direction | Service | Operation | Alternative | Logical extent | Grade |
|---|---|---|---|---|---|---|---|
| vaillant | B522 | absent | B522 | absent | current-mode | absent | Hypothesis |
| vaillant | B522 | request | B522 | absent | request | 7 | Hypothesis |
| vaillant | B522 | response | B522 | absent | positive | 4 | Hypothesis |
| vaillant | B522 | response | B522 | absent | negative | absent | Hypothesis |
| vaillant | B522 | absent | B522 | absent | FF FF unset | absent | Hypothesis |

### Candidate fields

All field coordinates in this partial catalog are absent. The three positive
Boolean roles have no established names here; they remain raw bits. Defaults
are candidate declarations, not observed initial or reset states.

| Alternative | Field | Representation | Raw domain | Default | Reserved bits | Grade |
|---|---|---|---|---|---|---|
| current-mode | current_mode | u8, identity | 0..255 | 0 | none declared | Hypothesis |
| request | fan | u8, identity, no established enum | 0..255 | 0 | none declared | Hypothesis |
| request | automatic | bit0: 0 disabled, 1 enabled | 0..1 | disabled | 1..7 zero | Hypothesis |
| request | room_temperature | u8 times 0.5 degrees C | 0..255 | 0 | none declared | Hypothesis |
| request | mode | u8, identity, unlabeled | 0..255 | 0 | none declared | Hypothesis |
| positive | unnamed bit0 | Boolean | 0..1 | false | 3..7 zero | Hypothesis |
| positive | unnamed bit1 | Boolean | 0..1 | false | 3..7 zero | Hypothesis |
| positive | unnamed bit2 | Boolean | 0..1 | false | 3..7 zero | Hypothesis |

### Current-mode candidate meanings

These meanings do not define a fan enum or label the separate request mode.
Raw 1 retains two unresolved alternatives: the competing label is Unknown,
so neither alternative is selected as authoritative.

| Raw | Candidate meaning | Competing alternative | Grade |
|---|---|---|---|
| 0 | no heating demand to source/circuits | none declared | Hypothesis |
| 1 | no source demand but demand from a sink | Unknown (unresolved label) | Hypothesis |
| 2 | source heating demand | none declared | Hypothesis |
| 3 | no source cooling demand but demand from a sink | none declared | Hypothesis |
| 4 | source cooling demand | none declared | Hypothesis |
| 5..255 | unlabeled | Unknown | Unknown |

Heating priority during simultaneous cooling and bypass behavior remain candidate
semantics only (**Hypothesis**), with no established physical effect.

### Synthetic carrier examples

The bytes below are independent carriers, not a reconstructed telegram. Preserve
raw bytes and reserved-bit discrepancies alongside useful independent fields.
Room temperature uses raw u8 scaling, not BCD conversion. FF is not a sentinel
for the individual room, mode or fan carriers. The separate **Hypothesis** that
FF FF means unset has no established coordinates or equivalence to those fields.

| Alternative | Field | Raw hex | Declared result | Reserved discrepancy | Grade |
|---|---|---|---|---|---|
| request | room_temperature | 00 | 0 degrees C | none | Hypothesis |
| request | room_temperature | 01 | 0.5 degrees C | none | Hypothesis |
| request | room_temperature | FF | 127.5 degrees C | none | Hypothesis |
| request | fan | FF | raw255 | none | Hypothesis |
| request | mode | FF | raw255, unlabeled | none | Hypothesis |
| request | automatic | 01 | enabled (bit0 only) | none | Hypothesis |
| request | automatic | 80 | disabled | 80 | Hypothesis |
| positive | unnamed bits0..2 | 08 | false, false, false | 08 | Hypothesis |

A reserved bit is not a fourth positive Boolean and does not enable automatic.
Unlabeled current modes and unresolved alternatives remain Unknown rather than
being inferred from adjacent values. No native qualification follows from this
representation, and no transmission route is defined here.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Open questions

- ACK/status response shape for each command (the candidate positive reply
  carries error, maintenance and filter-maintenance bits).
- Whether command effects are latched, timed, or controller-policy dependent.
- Whether non-recoVAIR ventilation products reuse B522.
- Whether the fan-stage reading of the configured rows is correct.
- The candidate layout is known only as a candidate layout; no exchange of it was
  observed beyond the configured rows on this page, and whether any device
  implements it is not established.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.

## References

- Public TypeSpec: [08.recov.tsp](https://github.com/john30/ebusd-configuration) path `src/vaillant/08.recov.tsp`
