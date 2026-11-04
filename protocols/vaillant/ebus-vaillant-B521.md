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
must be verified with captures before implementing a writer.

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

### Evidence boundary

**Hypothesis:** the outdoor-module family has a candidate process-data
interpretation of B521 alongside the public TypeSpec register-family
interpretation above. Whether these describe the same service, separate variants,
or both remains **Unknown**. Variant and operation are **Unknown**; neither the
service prefix nor a register selector establishes a process-data operation.
Ventilation role is **Unknown**.

**Proven** applies only to the declared representation checked by the
[synthetic examples](fixtures/ac22_outdoor_module.json), not to native behavior.
Every field interpretation below is **Hypothesis**. Physical qualification,
native adaptation and peer effects are **Unknown**. This partial declaration
establishes no runtime capability or safe transmission.

Logical positions include the service prefix in an abstract coordinate system;
they are not physical payload offsets. Abstract request extent is 7; abstract
positive extent is 12. Physical lengths are **Unknown**, not zero. The negative
alternative has no established logical extent or fields. Preserve raw bytes and
unresolved alternatives, including useful independently declared fields; an
unknown property does not justify discarding those fields or filling gaps.

### Request bits (Hypothesis)

Each listed bit is independent: 0 means disabled, 1 means enabled, and the
default is disabled. Exact names of request logical 3 bits 0..5 are **Unknown**;
raw labels deliberately preserve that gap. No composite appliance-code enum is
established. Reserved bits default to zero and retain their raw values.

| Logical | Bits | Field | Mask |
|---|---|---|---|
| 3 | 0 | raw-bit-0 | 0x01 |
| 3 | 1 | raw-bit-1 | 0x02 |
| 3 | 2 | raw-bit-2 | 0x04 |
| 3 | 3 | raw-bit-3 | 0x08 |
| 3 | 4 | raw-bit-4 | 0x10 |
| 3 | 5 | raw-bit-5 | 0x20 |
| 3 | 6..7 | reserved | 0xC0 |
| 4 | 0 | appliance-code-bit-0 | 0x01 |
| 4 | 1 | appliance-code-bit-1 | 0x02 |
| 4 | 2 | appliance-code-bit-2 | 0x04 |
| 4 | 3 | appliance-code-bit-3 | 0x08 |
| 4 | 4 | appliance-code-bit-4 | 0x10 |
| 4 | 5..7 | reserved | 0xE0 |

### Positive bits (Hypothesis)

Each named bit uses the same independent disabled/enabled representation and
zero default. Reserved bits default to zero and retain their raw values.

| Logical | Bits | Field | Mask |
|---|---|---|---|
| 3 | 0 | ready | 0x01 |
| 3 | 1 | deicing-request | 0x02 |
| 3 | 2 | deicing-active | 0x04 |
| 3 | 3 | deicing-timeout-error | 0x08 |
| 3 | 4 | deicing-with-heater | 0x10 |
| 3 | 5..6 | reserved | 0x60 |
| 3 | 7 | cleaning-request | 0x80 |
| 4 | 0 | heater | 0x01 |
| 4 | 1 | relay-output | 0x02 |
| 4 | 2 | fan-running | 0x04 |
| 4 | 3 | brine-flow-reverse | 0x08 |
| 4 | 4 | fan-error | 0x10 |
| 4 | 5 | safety-limiter-error | 0x20 |
| 4 | 6 | hot-summer | 0x40 |
| 4 | 7 | bad-weather | 0x80 |

### Scalars (Hypothesis)

All scalars default to zero and retain the full raw carrier domain. Positions
not declared here stay absent; the two temperatures have no established physical
roles. Unit metadata does not scale the converted value again. No BCD or sentinel
conversion is established. Percent values are not clipped to 100.

| Alternative | Logical | Field | Carrier | Raw domain | Conversion | Unit |
|---|---|---|---|---|---|---|
| request | 5 | noise-reduction | u8 | 0..255 | raw | percent |
| request | 6 | frost-protection-temperature | u8 | 0..255 | raw | degrees C |
| positive | Unknown | brine-pump-speed | u8 | 0..255 | raw | percent |
| positive | Unknown | fan-PWM | u8 | 0..255 | raw | percent |
| positive | Unknown | fan-speed | u8 | 0..255 | raw × 10 | rpm |
| positive | Unknown | temperature-1 | signed LE16 | -32768..32767 | raw ÷ 16 | degrees C |
| positive | Unknown | temperature-2 | signed LE16 | -32768..32767 | raw ÷ 16 | degrees C |

Synthetic examples of the declaration: walking logical 3 positive bits select
ready at bit 0, reserved at bits 5 and 6, and cleaning-request at bit 7.
Percent `FF` remains 255 percent; fan-speed `FF` becomes 2550 rpm;
temperature bytes `FE FF` become -0.125 degrees C. These examples establish no
physical result.

### Unresolved properties (Unknown)

Complete request-bit names; positive scalar positions; variant; operation;
ventilation role; negative forms; acknowledgement; retries/deadlines; atomicity;
endpoint effects; relationship to other registers; physical lengths; native
adaptation; peer effects; physical qualification. The slice remains partial until
missing names and positions can be represented without guessing. An
acknowledgement alone does not establish resulting device state.

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
- How abstract logical positions relate to physical request and response bytes
  remains Unknown; positive scalar positions are not declared in this slice.

## References

- Public TypeSpec: [e0.omu.tsp](https://github.com/john30/ebusd-configuration) path `src/vaillant/e0.omu.tsp`
- Public TypeSpec: [e1.omu.1.tsp](https://github.com/john30/ebusd-configuration) path `src/vaillant/e1.omu.1.tsp`
