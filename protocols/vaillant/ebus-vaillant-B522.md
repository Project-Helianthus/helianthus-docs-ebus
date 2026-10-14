# Vaillant B522 recoVAIR Ventilation Commands

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

| Request suffix | TypeSpec name | Direction | Meaning | Evidence | Falsification test |
|---|---|---|---|---|---|
| `02 00 ff ff` | `VentDay` | write | set ventilation day mode | | Issue the command on isolated recoVAIR hardware and show day mode is not selected. |
| `01 00 ff ff` | `VentNight` | write | set ventilation night mode | | Issue the command on isolated recoVAIR hardware and show night mode is not selected. |
| `03 00 ff ff` | `VentBoost` | write | activate boost ventilation | | Issue the command on isolated recoVAIR hardware and show boost is not activated. |

## Relationship to B509 Registers

The same `08.recov` TypeSpec also exposes many recoVAIR values through B509-like
register templates. `B522` is only the small command family for ventilation mode
writes and should not be used as the general recoVAIR register map.

## Candidate layout

One candidate layout is known for B522, the op `B5 22 00`, air ventilation
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

No op on this page is documented as safe to send; a state-changing op needs a separately established safety procedure and target qualification, and an ACK does not show the resulting device state.

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

- Public TypeSpec: [08.recov.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.recov.tsp)
