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

Every row is **Hypothesis**. All declared defaults are zero. A `u8` carrier is
preserved even where its value has no candidate label. Relay bit roles are
**Unknown**; PWM1 and PWM2 are declaration labels, and independent physical
channel behavior is **Unknown**.

| Field | Logical position | Carrier | Declared raw domain | Candidate interpretation | Default |
| --- | --- | --- | --- | --- | --- |
| relay | 3 | u8 | 0..255 | raw; bit roles Unknown | 0 |
| PWM1 | 4 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0 |
| PWM2 | 5 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0 |
| stepper | 6 | u8 | 0..255 | 0..240 steps; 241..254 unmapped; 255 calibrate/go-to-zero | 0 |
| LED | 7 | u8 | 0..255 | 0 disabled; 1 enabled; 2..255 unmapped | 0 |
| ED | 8 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0 |
| temperature-table | 9 | u8 | 0..255 | labels below; 4..255 unmapped | 0 |

| Temperature-table raw | Candidate label | Candidate range (degrees C) | Grade |
| --- | --- | --- | --- |
| 0 | standard3K3 | -13.5..116 | Hypothesis |
| 1 | extended1K | -20..155 | Hypothesis |
| 2 | low-temperature15K | -39..80 | Hypothesis |
| 3 | standard1K | -13.9..130 | Hypothesis |

Raw `FF` for either PWM label or ED gives candidate 127.5 percent. Do not clip
at 100 or interpret `FF` as unavailable. Stepper raw 240 denotes candidate steps,
241 and 254 remain unmapped, and 255 denotes candidate calibration/go-to-zero;
the declaration does not establish physical motion.

## OP00 positive fields

Every row is **Hypothesis**. All declared defaults are zero. LE means
little-endian. Signed temperature carriers do not admit negative values into the
declared domain. The reserved byte is retained independently of the useful fields.

| Field | Logical position | Carrier | Declared raw domain | Candidate interpretation | Default |
| --- | --- | --- | --- | --- | --- |
| ADC | 3 | u16 LE | 0..1023 | raw quantity; unit Unknown | 0 |
| temperature1 | 5 | i16 LE | 0..3200 | raw/16 degrees C; 0..200 | 0 |
| temperature2 | 7 | i16 LE | 0..3200 | raw/16 degrees C; 0..200 | 0 |
| temperature3 | 9 | i16 LE | 0..3200 | raw/16 degrees C; 0..200 | 0 |
| temperature4 | 11 | i16 LE | 0..3200 | raw/16 degrees C; 0..200 | 0 |
| reserved | 13 | u8 | 0..255 | raw; meaning Unknown | 0 |
| impeller | 14 | u16 LE | 0..1000 | Hz | 0 |
| vortex | 16 | u16 LE | 0..350 | Hz; candidate operational 5..350; hysteresis on 5/off 4 Hz | 0 |

Zero is not an established sentinel. Vortex formal and candidate operational
domains are distinct; neither establishes physical enforcement or peer effects.
ADC raw 1023 lies inside its declared domain and 1024 lies outside.
Temperature bytes `00 0C` carry 3072, giving candidate 192 degrees C inside both
declared ranges. Bytes `FF FF` carry signed -1, giving -0.0625 degrees C outside
the declared domain; this is neither automatically admitted nor an established
sentinel. Vortex values 0 and 4 lie inside the formal domain but outside the
candidate operational domain; 5 and 350 lie inside both, and 351 outside both.

## Evidence and unresolved properties

The synthetic fixture validates the declared representation, not native behavior.
Raw bytes, unmapped values and the unresolved negative alternative remain useful
without a semantic interpretation. Native adaptation, physical lengths, peer
effects, device support and physical qualification remain **Unknown**. No mapping
here establishes writable behavior, a transmit route or automatic qualification.
