# Vaillant B521 OMU Service Register Family

`PB=0xB5`, `SB=0x21`.

## Status

`B521` appears in john30 OMU TypeSpec files as a service/register family with a
static `0x00` selector after `SB=0x21`. It is used for source input sensor
offsets, deicing parameters, fan/speed parameters, and related OMU values.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec defines a passive write-capable base:

```text
Configured base:
  @write
  @passive
  @base(MF, 0x21, 0)

Request payload:
  00 <selector> 00 <value?>  (inferred from TypeSpec register template)
```

The exact read/write byte order is inherited from shared register templates and
must be verified with captures before implementing a a writer.

## Known Selector Examples

| Selector | TypeSpec name | Shape | Evidence | Falsification test |
|---|---|---|---|---|
| `4a 00` | `SourceInputSensorOffset` | install register, temperature | | Change the offset on isolated hardware and show no `B521 00 4a 00` correlation. |
| `4b 00` | `SourceInputSensorOffsetBrine` | install register, temperature | | Same test for brine sensor offset. |
| `45 00` | `DeiceTimeMax` | install register, minutes | | Change max deicing time and show no matching B521 selector. |
| `46 00` | `DeicePeriodMin` | install register, minutes | | Change minimum deicing period and show no matching B521 selector. |
| `29 00` | `DeicefinishTemp` | install register, temperature | | Change finish temperature and show no matching B521 selector. |
| `3f 00` | `FanSpeedMax` | install register, percent | | Change max fan speed and show no matching B521 selector. |

## Safety

Many B521 entries are installer/service parameters. Treat writes as dangerous
until proven on a test fixture, because deicing and fan-speed values can affect
heat-pump safety and performance.

## Candidate layout

One candidate layout is known for B521, the op `B5 21 00`, an operational-data
exchange with the outdoor unit of a heat pump and with ventilation; it is
unconfirmed on the wire and has not been observed on a bus. Both the request and
the response carry values (offsets count from the first byte of the service
prefix; a target response on the bus carries no such prefix, and how the
candidate response offsets map onto the bytes of a bus response is unconfirmed on
the wire; **Hypothesis**: response offset 3 is the first data byte; see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)):

- Request (candidate, unconfirmed on the wire): control bits at offset 3 (bits
  0..5: compressor demand, de-icing release, brine OK or heater allow, noise
  period, manual de-icing, fan mode); offset 4 unknown; a `u8` percentage
  parameter at offset 5 (**Hypothesis**: a noise reduction factor); a frost
  protection `u8` °C at offset 6.
- Response (candidate, unconfirmed on the wire): offsets 3 and 4 unknown;
  brine temperature `i16` LE ÷16 °C at offset 5, air inlet temperature at offset 7, brine pump `u8` % at offset
  9, fan speed `u8` × 10 rpm at offset 10 and fan PWM `u8` % at offset 11.

The community TypeSpec rows treat `B5 21 00` as `00 <selector> 00 <value>`
register reads and writes (selector examples `4a 00`, `45 00`), whereas the
candidate layout is a fixed process-data layout with control bytes; whether the
service is a register family, a process-data exchange or both is unresolved.

No op on this page is documented as safe to send; a state-changing op needs a separately established safety procedure and target qualification, and an ACK does not show the resulting device state.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Open questions

- Which OMU product IDs and software versions implement B521.
- Whether all selectors are valid for both `e0.omu` and `e1.omu.1`.
- Exact ACK/status bytes for writes.
- The candidate process-data layout is known only as a candidate layout; no
  exchange of it was observed beyond the examples on this page, and whether any
  device implements it is not established.
- Whether the candidate layout and the community register-family reading
  describe the same service is unresolved.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.

## References

- Public TypeSpec: [e0.omu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/e0.omu.tsp)
- Public TypeSpec: [e1.omu.1.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/e1.omu.1.tsp)
