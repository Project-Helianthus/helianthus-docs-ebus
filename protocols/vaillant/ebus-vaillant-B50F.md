# Vaillant-family B50F demand and integrity candidates

## Evidence and finite scope

PB=B5 and SB=0F identify this bounded family candidate. Every declaration
below is **Hypothesis**. Native evidence and physical qualification are
**Unknown** independently of synthetic arithmetic correctness. None is Proven.
Only the supplied demand, five temperatures with adjacent raw errors,
stack-voltage-labelled field, integrity pairs and feedback candidates are in
scope. The companion AE11 finite catalog entries are the boundary of companion
scope; no broader completed catalog or additional entries are assumed here.
Other variants and OP02 status partitions remain separate.

Direction, source, destination and firmware context are Unknown. A logical
position is not a wire offset. Pair coordinates below are abstract positions;
absolute scalar positions are Unknown. Extents are field sizes, not frame
lengths. OP00 has three temperatures and OP01 has two further temperatures,
each followed immediately by its own independent raw error byte. The OP01
stack-voltage label is retained separately from its conflicting temperature
conversion metadata; neither a voltage scale nor a converted value is selected.

## Relation to the earlier layout hypothesis

The [Vaillant overview](ebus-vaillant.md) keeps an older Hypothesis that puts
values in the request, feedback at reply offset 3, and scalars at concrete
offsets (temperatures at 3, 6 and 9 with errors at 5, 8 and 11). That
hypothesis is retained there as a separate candidate and is not withdrawn.
This page does not adopt or reject its absolute offsets: it keeps direction and
absolute scalar positions Unknown, so the two are an unresolved disagreement in
candidate layout, not a replacement. The integrity pair positions here are
abstract coordinates that coincide with the older candidate's CRC positions.

## Scoped declarations

| Grade | Identity | Direction | Logical position / extent | Raw type / domain | Scale / unit | Sentinel / default / conflict | Unresolved properties |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=03 / demand | Unknown | Unknown / 8 bits | uint8 00..FF; bits 0..4: burner, reformer-gas-valve, gas-flow, fan-power, valve; bits 5..7 reserved | none | Sentinel/default Unknown; demand is not applied actuation | Reserved semantics and physical effect Unknown; preserve all bits |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / temperature_1 | Unknown | Unknown / 16 bits | signed int16 little-endian -32768..32767 | divide by 16 / degrees Celsius | Sentinel/default Unknown | Absolute scalar position and channel meaning Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / error_1 | Unknown | immediately after temperature_1 / 8 bits | uint8 00..FF | none | Sentinel/default Unknown; independent raw error byte | Absolute scalar position and error meanings Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / temperature_2 | Unknown | Unknown / 16 bits | signed int16 little-endian -32768..32767 | divide by 16 / degrees Celsius | Sentinel/default Unknown | Absolute scalar position and channel meaning Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / error_2 | Unknown | immediately after temperature_2 / 8 bits | uint8 00..FF | none | Sentinel/default Unknown; independent raw error byte | Absolute scalar position and error meanings Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / temperature_3 | Unknown | Unknown / 16 bits | signed int16 little-endian -32768..32767 | divide by 16 / degrees Celsius | Sentinel/default Unknown | Absolute scalar position and channel meaning Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / error_3 | Unknown | immediately after temperature_3 / 8 bits | uint8 00..FF | none | Sentinel/default Unknown; independent raw error byte | Absolute scalar position and error meanings Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / temperature_1 | Unknown | Unknown / 16 bits | signed int16 little-endian -32768..32767 | divide by 16 / degrees Celsius | Sentinel/default Unknown | Absolute scalar position and channel meaning Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / error_1 | Unknown | immediately after temperature_1 / 8 bits | uint8 00..FF | none | Sentinel/default Unknown; independent raw error byte | Absolute scalar position and error meanings Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / temperature_2 | Unknown | Unknown / 16 bits | signed int16 little-endian -32768..32767 | divide by 16 / degrees Celsius | Sentinel/default Unknown | Absolute scalar position and channel meaning Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / error_2 | Unknown | immediately after temperature_2 / 8 bits | uint8 00..FF | none | Sentinel/default Unknown; independent raw error byte | Absolute scalar position and error meanings Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / stack_voltage_label | Unknown | Unknown / 16 bits | raw ordered pair 00..FF each | Unknown / Unknown | Stack-voltage label conflicts with temperature conversion metadata; no voltage scale chosen; sentinel/default Unknown | Conversion, unit, signedness and absolute scalar position Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / integrity | Unknown | 12, 13 / two independent 8-bit bytes | two uint8 00..FF; ordered bytes, not a word | none | Sentinel/default Unknown; preserve each byte independently | Word byte order, polynomial, initialization, reflection, final transform and coverage Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / integrity | Unknown | 12, 13 / two independent 8-bit bytes | two uint8 00..FF; ordered bytes, not a word | none | Sentinel/default Unknown; preserve each byte independently | Word byte order, polynomial, initialization, reflection, final transform and coverage Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=02 / integrity | Unknown | 11, 12 / two independent 8-bit bytes | two uint8 00..FF; ordered bytes, not a word | none | Sentinel/default Unknown; preserve each byte independently | Word byte order, polynomial, initialization, reflection, final transform and coverage Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=03 / integrity | Unknown | 4, 5 / two independent 8-bit bytes | two uint8 00..FF; ordered bytes, not a word | none | Sentinel/default Unknown; preserve each byte independently | Word byte order, polynomial, initialization, reflection, final transform and coverage Unknown |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=00 / feedback | Unknown | Unknown / 8 bits | uint8 00..FF; 01 accepted; 00 and 02..FF rejected | none | Sentinel/default Unknown; acceptance does not validate integrity | Physical effect Unknown; feedback does not establish physical effect |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=01 / feedback | Unknown | Unknown / 8 bits | uint8 00..FF; 01 accepted; 00 and 02..FF rejected | none | Sentinel/default Unknown; acceptance does not validate integrity | Physical effect Unknown; feedback does not establish physical effect |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=02 / feedback | Unknown | Unknown / 8 bits | uint8 00..FF; 01 accepted; 00 and 02..FF rejected | none | Sentinel/default Unknown; acceptance does not validate integrity | Physical effect Unknown; feedback does not establish physical effect |
| Hypothesis | vaillant / B50F / PB=B5 / SB=0F / OP=03 / feedback | Unknown | Unknown / 8 bits | uint8 00..FF; 01 accepted; 00 and 02..FF rejected | none | Sentinel/default Unknown; acceptance does not validate integrity | Physical effect Unknown; feedback does not establish physical effect |

## Synthetic examples and preservation

The [synthetic examples](fixtures/ae12_b50f_candidates.json) are independent
arithmetic illustrations, not captured telegrams or evidence of physical
support. Demand flags are ordered burner, reformer-gas-valve, gas-flow,
fan-power, valve. Demand values 00, 01, 1F, E0 and FF retain all reserved bits;
single-bit controls also distinguish every allocated and reserved bit.
No demand establishes applied actuation.

Signed pairs F0 FF, 00 00 and 10 00 represent -16, 0 and 16 before division
by 16, giving -1, 0 and 1 degrees Celsius. The adjacent error byte remains
independent, including 00, 01 and FF beside the same F0 FF pair. A
stack-voltage-labelled 10 00 remains raw with a conversion conflict, not 1 volt.

At every listed integrity pair, 00 00, 12 00, 00 34 and 12 34 vary each byte
independently and retain their order. They are never composed into a CRC word.
Feedback 00, 01, 02 and FF means rejected, accepted, rejected and rejected
for each independent integrity-byte combination. Acceptance does not validate
integrity and does not establish physical effect.

Missing bytes remain absent, distinct from zero. A partial current pair retains
its available byte and is not admitted as complete; a separate last-known-good
pair does not fill the missing current byte or establish current validity.
No integrity algorithm or safety-status executor is established here.

## Open questions

Native direction and scalar positions, sentinel/default semantics, reserved-bit
meanings, error-byte meanings and physical effect remain Unknown. Integrity
word byte order, polynomial, initialization, reflection, final transform and
coverage remain Unknown. The two independent bytes are the only integrity
candidate, with abstract OP00/OP01 positions 12/13, OP02 positions 11/12 and
OP03 positions 4/5. The stack-voltage conversion conflict remains unresolved;
feedback supplies no integrity verdict or proof of actuation.
