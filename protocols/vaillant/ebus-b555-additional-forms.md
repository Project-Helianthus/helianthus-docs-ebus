# B555 additional candidate forms

**Hypothesis:** this finite VRC720-family supplement records candidate field
coordinates and relationships. **Unknown:** native support and physical
qualification. A candidate grade and qualification are independent.

## Evidence and coordinate basis

The public native contract is the
[candidate inventory](ebus-vaillant-b555-timer-protocol.md#31-sub-command-inventory-candidate),
[availability and visibility description](ebus-vaillant-b555-timer-protocol.md#55-availability-and-visibility-reads-candidate),
and [candidate field table](fixtures/b555-candidate-field-layouts.csv).
The [finite synthetic cases](fixtures/ak16_b555_additional_forms.json) establish
representation arithmetic only, not new native evidence.

All coordinates below start immediately after the command, not at a physical
payload base. Physical adaptation, physical offsets and prefix presence are
**Unknown**. No physical offset subtraction or prefix rule follows from these
coordinates. Declared requests with no parameters are not physical empty packets.

## Availability, visibility and reserved forms

| Command | Request parameters | Reply bytes | Candidate meaning |
| --- | --- | --- | --- |
| A0 | none | 8 | availability |
| A7 | none | 8 | visibility |
| A1 | none | 6 | reserved |
| A2 | none | 6 | reserved |
| A8 | none | 6 | reserved |
| A9 | none | 6 | reserved |

A0 availability and A7 visibility are distinct relationships. The same raw mask
retains its command-specific meaning; visibility does not establish availability,
and availability does not establish visibility. A1/A2/A8/A9 retain six reserved
bytes without assigning settings or actions to their bits.

| Global field | Byte | Bit | Width in bits |
| --- | --- | --- | --- |
| dhw | 0 | 0 | 1 |
| circulation | 0 | 1 | 1 |
| noise_reduction | 0 | 2 | 1 |
| ventilation | 0 | 3 | 1 |
| high_tariff | 0 | 4 | 1 |
| reserved | 0 | 5 | 3 |
| reserved | 1 | 0 | 8 |

The reserved region has eleven bits; these bits remain raw. Each of twelve
channels has four bits: relative bit 0 zone heating, 1 zone cooling, 2 external
DHW, 3 external fixed-flow. Channel n uses byte `2+floor((n-1)/2)` and starting
bit `4*((n-1) mod 2)`; both nibbles are retained.

| Channel | Byte | Starting bit | Width in bits |
| --- | --- | --- | --- |
| 1 | 2 | 0 | 4 |
| 2 | 2 | 4 | 4 |
| 3 | 3 | 0 | 4 |
| 4 | 3 | 4 | 4 |
| 5 | 4 | 0 | 4 |
| 6 | 4 | 4 | 4 |
| 7 | 5 | 0 | 4 |
| 8 | 5 | 4 | 4 |
| 9 | 6 | 0 | 4 |
| 10 | 6 | 4 | 4 |
| 11 | 7 | 0 | 4 |
| 12 | 7 | 4 | 4 |

## Positive A4 and A5 field coordinates

The full candidate A4 field span is nine bytes, including the distinct 24-hour
count. It is not merely the seven weekday counts and status.

| A4 field | Byte | Width in bytes | Encoding |
| --- | --- | --- | --- |
| status | 0 | 1 | u8 |
| monday | 1 | 1 | u8 |
| tuesday | 2 | 1 | u8 |
| wednesday | 3 | 1 | u8 |
| thursday | 4 | 1 | u8 |
| friday | 5 | 1 | u8 |
| saturday | 6 | 1 | u8 |
| sunday | 7 | 1 | u8 |
| count_24_hour | 8 | 1 | u8 |

The full candidate A5 field span is seven bytes. Hours have domain 0..24;
minutes have domain 0..59. The raw setpoint is a little-endian unsigned word.

| A5 field | Byte | Width in bytes | Encoding |
| --- | --- | --- | --- |
| status | 0 | 1 | u8 |
| start_hour | 1 | 1 | u8 |
| start_minute | 2 | 1 | u8 |
| end_hour | 3 | 1 | u8 |
| end_minute | 4 | 1 | u8 |
| setpoint_raw | 5 | 2 | u16_le |

FFFF remains numeric 65535; contextual unit and sentinel meanings are
**Unknown**. Extra bytes remain raw. No A3 numeric-unit relationship is imported.
Other timer variants, physical effects, persistence and delivery remain
**Unknown**. The synthetic cases qualify only this declared representation.
