# B509 OP59 quantity fragments

## Scope and evidence

This supplement narrows the [B509 family reference](ebus-vaillant-B509.md).
The candidate selector is PB `0xB5`, SB `0x09`, operation `0x59` in the
Vaillant family. The quantity interpretations below are **Hypothesis**, not
native support claims. The supplied synthetic fragments illustrate arithmetic;
they are not captures, complete telegrams or evidence of physical qualification.
No absolute field position, source, destination or direction is supplied.

## Candidate fields

| Field | Representation | Divisor | Unit | Grade |
| --- | --- | --- | --- | --- |
| temperature | signedLE16 | 16 | Celsius | Hypothesis |
| flow | unsignedLE16 | 100 | litres per minute | Hypothesis |
| volume | unsignedLE16 | 10 | litres | Hypothesis |
| minimum_volume | raw | Unknown | Unknown | Hypothesis |
| maximum_volume | raw | Unknown | Unknown | Hypothesis |

The three quantity codecs are independent. Interpret the two-byte fragments
little-endian, apply signed two's-complement only to temperature, then divide
by the field's own divisor. Neither volume limit inherits the volume codec.
Keep minimum and maximum values raw; their widths, scales, units, coordinates
and enforcement are unprovided.

## Synthetic fragments

| Field | Fragment or raw value | Expected value | Unit |
| --- | --- | --- | --- |
| temperature | F0 FF | -1 | Celsius |
| temperature | 00 80 | -2048 | Celsius |
| flow | 7B 00 | 1.23 | litres per minute |
| flow | FF FF | 655.35 | litres per minute |
| volume | 7B 00 | 12.3 | litres |
| volume | FF FF | 6553.5 | litres |
| minimum_volume | raw 123 | 123 | Unknown |
| maximum_volume | raw 456 | 456 | Unknown |

The high-bit and asymmetric fragments distinguish signedness and byte order.
The `FF FF` examples are arithmetic controls only: sentinel meaning remains
Unknown, including whether any such value denotes unavailable data.

## Evidence boundaries

| Property | Grade | Supplied value |
| --- | --- | --- |
| absolute_field_positions | Unknown | unprovided |
| native_support | Unknown | unprovided |
| sentinels | Unknown | unprovided |
| response_adaptation | Unknown | unprovided |
| direction | Unknown | unprovided |
| physical_qualification | Unknown | unprovided |
| limit_widths | Unknown | unprovided |
| limit_scales | Unknown | unprovided |
| limit_units | Unknown | unprovided |
| limit_coordinates | Unknown | unprovided |
| limit_enforcement | Unknown | unprovided |

Raw fragments and partial information remain available independently of these
candidate interpretations. Unknown facts cannot be filled from another field,
family or operation. Diagnostic/software identity, OP07 widths, OP06 feedback
and symbolic access are outside this supplement.

## Evidence

The [synthetic tuples](fixtures/aj16_b509_op59_quantities.json) preserve the
separate field fragments and raw limits. Their provenance is synthetic;
no native capture or vendor specification proving these candidate codecs is
provided. Agreement with the arithmetic controls does not promote Hypothesis
to Proven.
