# B512 fan control and air-quality field candidates

This focused native contract covers the fan-module and smart-module families
OP0B, OP0C, OP0D and OP0E of B512 (PB B5, SB 12). The
[public B512 family contract](ebus-vaillant-b512.md#candidate-sub-commands-op)
is the prior native declaration; its candidate layouts remain **Hypothesis**.
The field detail here is a synthetic candidate declaration, not new native
observation. No native specification or capture establishes these field details.
See also the separate [OP01 feedback family](ebus-b512-feedback-fallback.md).

## Fields

Every row is individually graded. Logical coordinates are not wire offsets.
Request and positive sides have independent identities and layouts; in
particular request relay and positive status at logical 7 are different fields.
Default values are candidate metadata, not evidence of an installed state.
Unknown defaults remain Unknown. Raw bytes are retained beside interpretation.

| OP | Side | Logical | Field | Type | Divisor | Unit | Default | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0B | request | 3 | fan-1-target | u16le | 1 | rpm | 0 | Hypothesis |
| 0B | request | 5 | fan-2-target | u16le | 1 | rpm | 0 | Hypothesis |
| 0B | request | 7 | relay | u8 | 1 | raw | 0 | Hypothesis |
| 0B | positive | 3 | fan-1-actual | u16le | 1 | rpm | 0 | Hypothesis |
| 0B | positive | 5 | fan-2-actual | u16le | 1 | rpm | 0 | Hypothesis |
| 0B | positive | 7 | status | u8 | 1 | raw | 0 | Hypothesis |
| 0B | positive | 8 | temperature-1 | s16le | 16 | degC | 0 | Hypothesis |
| 0B | positive | 10 | temperature-2 | s16le | 16 | degC | 0 | Hypothesis |
| 0B | positive | 12 | temperature-3 | s16le | 16 | degC | 0 | Hypothesis |
| 0C | request | 3 | pulse | u8 | 1 | raw | Unknown | Hypothesis |
| 0C | request | 4 | P | u8 | 1 | raw | Unknown | Hypothesis |
| 0C | request | 5 | I | u8 | 1 | raw | Unknown | Hypothesis |
| 0C | request | 6 | D | u8 | 1 | raw | Unknown | Hypothesis |
| 0C | request | 7 | minimum-PWM | s16le | 256 | percent | 1.0 | Hypothesis |
| 0C | request | 9 | maximum-PWM | s16le | 256 | percent | 1.0 | Hypothesis |
| 0C | request | 11 | fan-count | u8 | 1 | raw | Unknown | Hypothesis |
| 0C | positive | 3 | feedback | u8 | 1 | raw | 0 | Hypothesis |
| 0D | positive | 3 | digital | u8 | 1 | raw | 0 | Hypothesis |
| 0D | positive | 4 | temperature-1 | s16le | 16 | degC | Unknown | Hypothesis |
| 0D | positive | 6 | temperature-2 | s16le | 16 | degC | Unknown | Hypothesis |
| 0E | positive | 3 | temperature | s16le | 16 | degC | 0 | Hypothesis |
| 0E | positive | 5 | humidity | u16le | 16 | percent | 0 | Hypothesis |
| 0E | positive | 7 | air-quality | u16le | 1 | Unknown | 0 | Hypothesis |

## Field spans

These byte counts cover only the listed synthetic fields in logical order,
starting at logical 3. They exclude all framing, selection and acknowledgement.
OP0D and OP0E requests have no arguments. An exact field span is only a locally
complete candidate field set; missing or extra bytes fail that local predicate.
Neither an exact span nor a missing or extra span establishes a complete physical
packet. Framing, wire offsets and acknowledgement remain **Unknown**.

| OP | Side | Field bytes |
| --- | --- | --- |
| 0B | request | 5 |
| 0B | positive | 11 |
| 0C | request | 9 |
| 0C | positive | 1 |
| 0D | request | 0 |
| 0D | positive | 5 |
| 0E | request | 0 |
| 0E | positive | 6 |

## Candidate token meanings

Reserved bits remain raw and reserved, including relay bit 2; they are not
additional outputs. Unlabeled values retain their raw alternatives and are not
coerced to a Boolean. Feedback acceptance is a candidate token meaning and does
not establish native acknowledgement or permission for execution.

| OP | Side | Field | Raw condition | Meaning | Grade |
| --- | --- | --- | --- | --- | --- |
| 0B | request | relay | bit-0=0 | output-1-15V | Hypothesis |
| 0B | request | relay | bit-0=1 | output-1-tray-heater-relay | Hypothesis |
| 0B | request | relay | bit-1=0 | output-2-15V | Hypothesis |
| 0B | request | relay | bit-1=1 | output-2-tray-heater-relay | Hypothesis |
| 0B | request | relay | bits-2..7 | reserved | Hypothesis |
| 0B | positive | status | 0 | idle | Hypothesis |
| 0B | positive | status | 1 | running | Hypothesis |
| 0B | positive | status | 255 | fault | Hypothesis |
| 0B | positive | status | 2..254 | unlabeled | Hypothesis |
| 0C | positive | feedback | 1 | accepted | Hypothesis |
| 0C | positive | feedback | 0,2..255 | rejected | Hypothesis |
| 0D | positive | digital | 0 | false | Hypothesis |
| 0D | positive | digital | 1 | true | Hypothesis |
| 0D | positive | digital | 2..255 | unlabeled | Hypothesis |

## Representation ranges

LE means little endian; s16le is signed two's complement. Divide the decoded
integer by the divisor. These are representation ranges, not physical limits.
Both PWM fields use the signed /256 range with candidate default 1.0 percent.
Humidity is unsigned /16; neither PWM nor humidity is capped at 100 percent.
Air quality stays raw LE u16 with **Unknown** unit; no concentration unit is
assigned. Temperature fields use signed /16 degrees Celsius.

| Type | Raw minimum | Raw maximum | Divisor | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- |
| u8 | 0 | 255 | 1 | 0 | 255 |
| u16le | 0 | 65535 | 1 | 0 | 65535 |
| s16le | -32768 | 32767 | 16 | -2048 | 2047.9375 |
| s16le | -32768 | 32767 | 256 | -128 | 127.99609375 |
| u16le | 0 | 65535 | 16 | 0 | 4095.9375 |

## Evidence

[The synthetic tuples](fixtures/ai12_b512_air_fields.json) contain only field
bytes, ordered by the tables above. They have no physical packet context.

| OP | Side | Raw field bytes | Ordered decoded values |
| --- | --- | --- | --- |
| 0B | request | 02 01 04 03 04 | 258,772,4 |
| 0B | positive | 02 01 04 03 FF 10 00 F0 FF 00 00 | 258,772,255,1,-1,0 |
| 0C | request | 02 03 05 07 00 01 FF 7F 02 | 2,3,5,7,1,127.99609375,2 |
| 0C | request | 02 03 05 07 00 80 00 01 02 | 2,3,5,7,-128,1,2 |
| 0C | positive | 01 | 1 |
| 0C | positive | 02 | 2 |
| 0D | request | (empty) | (empty) |
| 0D | positive | 02 10 00 F0 FF | 2,1,-1 |
| 0E | request | (empty) | (empty) |
| 0E | positive | F0 FF 40 06 FF FF | -1,100,65535 |
| 0E | positive | 10 00 50 06 FF FF | 1,101,65535 |

**Proven (synthetic representation only):** These tuples distinguish fan words
0102 and 0304, signed temperature and PWM arithmetic, relay reserved bit 2,
feedback rejection, an unlabeled digital value, humidity above 100 and raw air
quality. They prove only the declared local representation and predicates.

**Hypothesis:** Every field mapping, token meaning and stated default above is
unconfirmed native behavior. The public family page and these tuples do not
resolve native acknowledgement, packet extent or physical behavior. No conflicting
native evidence is supplied; any future conflict must retain both raw alternatives
rather than silently selecting a mapping.

**Unknown:** Physical support, acknowledgement, wire offsets, actual physical
limits, unspecified defaults, freshness, persistence and delivery. Qualification
is independent of Proven/Hypothesis/Unknown claim grades. Synthetic consistency
confers no installed support or execution permission.
