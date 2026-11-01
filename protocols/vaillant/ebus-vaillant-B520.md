# B520: simulator actuator ranges and ADC quantities

This partial catalog describes the Vaillant simulator family, with no selected
variant. The [existing native overview](ebus-vaillant.md#b520-simulator-and-simbox-services)
supplies the candidate service context. All field interpretations below are
**Hypothesis**, unconfirmed on the wire. The
[synthetic declarations](fixtures/ac20_simulator_adc.json) preserve raw carriers;
**Proven** applies only to their checked software representation and arithmetic.
Physical qualification is **Unknown**. No publishable device observation is
included, and these declarations grant no runtime capability or write admission.

## Logical identity and extents

Positions count from the logical service prefix `B5 20 00`; they are not physical
response offsets. Logical extents follow from the declared fields alone.

| Family | Variant | Direction | Service | Operation | Alternative | Logical extent | Physical extent | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Vaillant simulator | Unknown | request | B520 | 0x00 | request | 10 | Unknown | Hypothesis |
| Vaillant simulator | Unknown | response | B520 | 0x00 | positive | 18 | Unknown | Hypothesis |
| Vaillant simulator | Unknown | response | B520 | 0x00 | negative | Unknown | Unknown | Hypothesis |

The unresolved negative alternative has no declared fields or extent. Absence
does not mean zero length. Remaining selectors, address-space semantics and
support remain **Unknown** and are outside this partial catalog. Other candidate
selectors in the overview retain their separate scope.

## OP00 request fields

Every row is **Hypothesis** for the sourced layout and scaling; defaults and
unsupported interpretations are **Unknown**. A `u8` carrier is
preserved even where its value has no candidate label. The request raw domain
below states carrier capacity only; accepted actuator values are **Unknown**.
Relay bit roles are **Unknown**; PWM1 and PWM2 are declaration labels, and independent physical
channel behavior is **Unknown**.

| Field | Logical position | Carrier | Declared raw domain | Candidate interpretation | Default |
| --- | --- | --- | --- | --- | --- |
| relay | 3 | u8 | 0..255 | raw; bit roles Unknown | Unknown |
| PWM1 | 4 | u8 | 0..255 | raw/2 percent; 0..127.5 | Unknown |
| PWM2 | 5 | u8 | 0..255 | raw/2 percent; 0..127.5 | Unknown |
| stepper | 6 | u8 | 0..255 | raw; steps and calibration semantics Unknown | Unknown |
| LED | 7 | u8 | 0..255 | raw; value meanings Unknown | Unknown |
| ED | 8 | u8 | 0..255 | percent label; scaling Unknown; preserve raw | Unknown |
| temperature-table | 9 | u8 | 0..255 | labels below; 4..255 unmapped | Unknown |

| Temperature-table raw | Candidate label | Candidate range (degrees C) | Grade |
| --- | --- | --- | --- |
| 0 | standard3K3 | Unknown | Hypothesis |
| 1 | extended1K | Unknown | Hypothesis |
| 2 | low-temperature15K | Unknown | Hypothesis |
| 3 | standard1K | Unknown | Hypothesis |

Raw `FF` for either PWM label gives candidate 127.5 percent by arithmetic alone.
Do not clip the candidate arithmetic at 100. Acceptance and sentinel meaning of
`FF` are **Unknown**; the overview does not establish whether it means unavailable.
ED has a candidate percent label, but its scaling is **Unknown**; the overview specifies division by two only for PWM.
Preserve ED bytes without converting them to a percentage. Stepper and LED bytes
retain their raw values without assigning motion, calibration or enabled/disabled
semantics.

## OP00 positive fields

Every row is **Hypothesis** for the sourced layout and scaling; defaults and
unsupported interpretations are **Unknown**. LE means
little-endian. Accepted raw and physical domains are **Unknown**; carrier
signedness alone does not establish acceptance or rejection of negative values.
The byte at logical position 13 has **Unknown** meaning and is retained without
classifying it as reserved; its raw domain states carrier capacity only.

| Field | Logical position | Carrier | Declared raw domain | Candidate interpretation | Default |
| --- | --- | --- | --- | --- | --- |
| ADC | 3 | u16 LE | Unknown | raw quantity; unit Unknown | Unknown |
| temperature1 | 5 | i16 LE | Unknown | raw/16 degrees C | Unknown |
| temperature2 | 7 | i16 LE | Unknown | raw/16 degrees C | Unknown |
| temperature3 | 9 | i16 LE | Unknown | raw/16 degrees C | Unknown |
| temperature4 | 11 | i16 LE | Unknown | raw/16 degrees C | Unknown |
| unknown13 | 13 | u8 | 0..255 | raw; meaning Unknown | Unknown |
| impeller | 14 | u16 LE | Unknown | Hz | Unknown |
| vortex | 16 | u16 LE | Unknown | Hz; operational domain and hysteresis Unknown | Unknown |

Zero is not an established sentinel or default. The unsigned 16-bit carriers
represent 0..65535; their accepted raw and operational domains remain **Unknown**.
Vortex hysteresis is also **Unknown** because the linked overview supplies no
threshold evidence. Carrier capacity does not establish physical enforcement or
peer effects. Temperature bytes `00 0C` carry 3072, giving candidate 192 degrees C;
bytes `FF FF` carry signed -1, giving candidate -0.0625 degrees C. These are
synthetic arithmetic examples, with acceptance and sentinel meanings **Unknown**.
ADC, temperature, impeller and vortex values are preserved without classifying
them as inside or outside an operational domain.

## Evidence and unresolved properties

The synthetic fixture validates the declared representation, not native behavior.
Raw bytes, unmapped values and the unresolved negative alternative remain useful
without a semantic interpretation. Native adaptation, physical lengths, peer
effects, device support and physical qualification remain **Unknown**. No mapping
here establishes writable behavior, a transmit route or automatic qualification.

The linked overview supplies no evidence for stepper bounds or calibration,
LED values, thermistor Celsius ranges, defaults, or ADC/temperature/impeller
acceptance bounds. Those properties remain **Unknown** in both this page and the
synthetic fixture; testing the fixture does not supply the missing evidence.
