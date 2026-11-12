# B512 heat-pump I/O candidate fields

## Evidence and status

The [native framing contract](../ebus-services/ebus-overview.md) defines wire framing.
The [B512 family reference](ebus-vaillant-b512.md) provides family context.
The finite declarations for [this supplement](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/946)
are **Hypothesis**, not a native qualification. The existing family reference uses
unavailable wording for replacements; this supplement retains replacement without
an unavailable assertion. That meaning remains **Unknown**. No additional defaults
are inferred. Family context does not establish these detailed positions on the wire.

**Proven** is limited to the checked synthetic representation and arithmetic.
Native support, physical effects, persistence, delivery, physical reply form,
physical lengths, negative replies and qualification remain **Unknown**.
The [synthetic cases](fixtures/ak10_b512_heatpump_io.json) are abstract field samples,
not telegram captures. Source, destination, firmware and physical framing are
Unknown; no observed device behavior is claimed.

## Coordinates and carriers

PB/SB is B5/12. Operations and positions below belong to an abstract logical
layout. Positions are not physical wire offsets or a response-length rule.
Widths describe field carriers only. LE means little endian; word notation
8000 and FFF0 corresponds to byte sequences `00 80` and `F0 FF` respectively.
All rows and candidate relationships are **Hypothesis**.

| OP | Direction | Field | Position | Width (bits) | Encoding |
| --- | --- | --- | --- | --- | --- |
| 0F | request | outputs | 3 | 8 | bits |
| 0F | request | valve | 4 | 8 | u8 |
| 0F | positive | temperature_one | 3 | 16 | signed-le16 |
| 0F | positive | temperature_two | 6 | 16 | signed-le16 |
| 0F | positive | input | 5 | 8 | u8 |
| 0F | positive | pressure | 8 | 8 | u8 |
| 0F | positive | backup | 9 | 8 | u8 |
| 10 | request | actuators_one | 3 | 8 | bits |
| 10 | request | actuators_two | 4 | 8 | bits |
| 10 | request | inverse_actuator | 5 | 16 | opaque-16 |
| 10 | positive | status | 3 | 8 | bits |
| 10 | positive | single_phase | 4 | 8 | u8 |
| 10 | positive | three_phase | 5 | 8 | u8 |
| 10 | positive | adc_1 | 6 | 16 | raw-le16 |
| 10 | positive | adc_2 | 8 | 16 | raw-le16 |
| 10 | positive | adc_3 | 10 | 16 | raw-le16 |
| 10 | positive | adc_4 | 12 | 16 | raw-le16 |
| 10 | positive | adc_5 | 14 | 16 | raw-le16 |
| 10 | positive | adc_6 | 16 | 16 | raw-le16 |
| 10 | positive | board | 18 | 8 | u8 |
| 11 | request | temperature_1 | 3 | 16 | signed-le16 |
| 11 | request | temperature_2 | 5 | 16 | signed-le16 |
| 11 | request | temperature_3 | 7 | 16 | signed-le16 |
| 11 | request | pressure | 9 | 8 | u8 |
| 11 | request | flow | 10 | 8 | signed8 |
| 11 | request | pump_status | 11 | 8 | raw-u8 |
| 11 | request | compressor | 12 | 8 | bits |
| 11 | positive | status | 3 | 8 | bits |
| 11 | positive | setpoint | 4 | 8 | u8 |
| 12 | request | emergency | 3 | 8 | bits |
| 12 | request | switch | 4 | 8 | raw-u8 |
| 12 | request | co2_1 | 5 | 16 | raw-le16 |
| 12 | request | co2_2 | 7 | 16 | raw-le16 |
| 12 | positive | led | 3 | 8 | bits |

## Bit roles

Every bit is retained. Reserved does not imply zero. Unmodeled does not imply
reserved. Bit numbers increase from least significant bit 0.

| OP | Direction | Field | Bits 0 through 7 |
| --- | --- | --- | --- |
| 0F | request | outputs | output one; output two; reserved; reserved; reserved; reserved; reserved; reserved |
| 10 | request | actuators_one | cooling valve; passive mixer one; passive mixer two; cooling active; well pump; backup safety; backup one; backup two |
| 10 | request | actuators_two | backup three; external valve; external backup; reserved; reserved; reserved; reserved; reserved |
| 10 | positive | status | anode channel one; anode channel two; smart-grid; well; safety limiter; safety; reserved; reserved |
| 11 | request | compressor | compressor-off; reserved; reserved; reserved; reserved; reserved; reserved; unmodeled |
| 11 | positive | status | compressor-off; pump-relay; reserved; reserved; reserved; reserved; reserved; reserved |
| 12 | request | emergency | emergency; reserved; reserved; reserved; reserved; reserved; reserved; unmodeled |
| 12 | positive | led | LED; reserved; reserved; reserved; reserved; reserved; reserved; unmodeled |

## Candidate relationships

| OP | Direction | Field(s) | Relationship |
| --- | --- | --- | --- |
| 0F | request | valve | 0 off; 1 CH; 2 DHW |
| 0F | positive | temperature_one, temperature_two | Select raw word 8000 replacement before signed LE16 /16 degrees Celsius; FFF0 = -1 degree Celsius |
| 0F | positive | input | 0 multipurpose; 1 utility contact |
| 0F | positive | pressure | u8/10 bar; byte FF = raw 255 = 25.5 bar; domain 0..25.5; declared default 255.0 conflicts with domain and is retained without clipping |
| 0F | positive | backup | 0 off; 1..3 steps; FF replacement |
| 10 | request | inverse_actuator | Opaque 16-bit data; algorithm Unknown; no complement algorithm follows even from coincidental complement values |
| 10 | positive | single_phase | Percent; approximately 50 powered; 0 absent; tolerance Unknown |
| 10 | positive | three_phase | Percent; 100 powered; 0 all phases absent; 33 one phase absent; 66 two phases absent |
| 10 | positive | adc_1, adc_2, adc_3, adc_4, adc_5, adc_6 | Six independent raw LE u16 channels; units and calibration Unknown |
| 10 | positive | board | Opaque codes 0/1/2/3/11/12; 13 and other unmapped values stay raw |
| 11 | request | temperature_1, temperature_2, temperature_3 | Signed LE16 /16 degrees Celsius; no replacement declared |
| 11 | request | pressure | u8/10 bar; no default declared |
| 11 | request | flow | Signed8 times10 l/h; FF = -10 l/h |
| 11 | request | pump_status | Raw u8; meanings Unknown |
| 11 | positive | setpoint | u8; 0..100 percent |
| 12 | request | switch | Raw u8; meanings Unknown |
| 12 | request | co2_1, co2_2 | LE u16 ppm; full 0..65535; FFFF = 65535 ppm, not a sentinel |

Replacement is not an unavailable assertion. The pressure default is a declared
conflict, not a value encodable as 255.0 bar in the one-byte carrier. All defaults
except that pressure default are Unknown. Approximate 50 has no invented tolerance.

## Literal positive conflicts

| Requested OP | Declared positive PB/SB/OP | Association |
| --- | --- | --- |
| 11 | B5/12/0C | Unknown |
| 12 | B5/12/0C | Unknown |

The declared positive is literally 0C for each requested selector. It is not
rewritten to 11 or 12. The conflict establishes neither reply association nor
acceptance. Short or extra synthetic abstract structures stay raw and cannot
choose a physical reply form. Retain raw bytes beside every candidate value,
including reserved and unmodeled bit 7; independent interpretation never discards
other fields. Synthetic correctness establishes only the declared representation.
