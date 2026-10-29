# Vaillant B50B — holiday field declarations

## Evidence and scope

These Vaillant family declarations are **Hypothesis**. No native capture or
physical qualification is supplied here. The [synthetic examples](fixtures/ac04_holiday.json)
validate only the declared representation: that software result is **Proven**
when checked, while physical interpretation remains **Hypothesis** and
qualification remains **Unknown**. A synthetic example is not wire evidence.

Holiday number is separate from circuit/room identity. Raw bytes and unlabeled
values remain independent of candidate interpretation. A contradictory default
does not invalidate other useful fields or establish a physical effect.

## Candidate fields

All rows have family `Vaillant`, variant, direction and service absent, and
alternative `field-declaration`. Only the setpoint row declares an operation.
`absent` means unspecified, never zero. No field offsets are declared.

| Field | Operation | Extent (bytes) | Conversion | Default | Grade |
|---|---|---|---|---|---|
| holiday_number | absent | 1 | unsigned byte | 0 | Hypothesis |
| start_day | absent | absent | Unknown | 0 | Hypothesis |
| start_month | absent | absent | Unknown | 0 | Hypothesis |
| start_year | absent | absent | Unknown | 0 | Hypothesis |
| end_day | absent | absent | Unknown | 0 | Hypothesis |
| end_month | absent | absent | Unknown | 0 | Hypothesis |
| end_year | absent | absent | Unknown | 0 | Hypothesis |
| op02_setpoint | OP02 | 1 | unsigned byte in degrees C | 0 | Hypothesis |
| room_action | absent | absent | Unknown | 0 | Hypothesis |
| holiday_status | absent | absent | Unknown | 0 | Hypothesis |
| keycode_1 | absent | 1 | independent numeric byte | absent | Hypothesis |
| keycode_2 | absent | 1 | independent numeric byte | absent | Hypothesis |
| keycode_3 | absent | 1 | independent numeric byte | absent | Hypothesis |
| keycode_4 | absent | 1 | independent numeric byte | absent | Hypothesis |
| circuit_name | absent | 10 | ASCII characters | absent | Hypothesis |

## Defaults and candidate domains

Holiday number and all six calendar components default to zero. Zero day/month
conflicts with calendar domains; it is not a valid calendar date and does not
mean delete, disable or reset. Calendar year interpretation remains Unknown.

OP02 setpoint has candidate bounds 5..30 degrees C. Default zero lies outside
those bounds. Values remain raw, without clipping. Off/frost/deletion meaning
is Unknown, including for zero.

| Setpoint raw byte | Candidate degrees C | Inside candidate bounds | Physical meaning |
|---|---|---|---|
| 0 | 0 | false | Unknown |
| 5 | 5 | true | Unknown |
| 30 | 30 | true | Unknown |
| 31 | 31 | false | Unknown |

## Candidate enumerations

Room-action and holiday-status defaults are zero. Holiday status 0/1 is a raw
value declaration with no on/off interpretation. Other raw values stay unlabeled.

| Field | Raw value | Candidate label | Grade |
|---|---|---|---|
| room_action | 0 | no-action | Hypothesis |
| room_action | 1 | switch-on | Hypothesis |
| room_action | 2 | thermostat | Hypothesis |
| room_action | 3 | unlabeled | Hypothesis |
| holiday_status | 0 | 0 | Hypothesis |
| holiday_status | 1 | 1 | Hypothesis |
| holiday_status | 2 | unlabeled | Hypothesis |

## Keycode and circuit name

The four keycode bytes are independent numeric bytes, not ASCII, packed decimal
or a u32. The synthetic bytes [1,2,3,4] retain four independent numeric values.

A circuit name occupies exactly ten ASCII characters (ten bytes). Nine and
eleven ASCII bytes do not match that declaration. Padding, trimming, NUL
termination, UTF-8 and truncation are Unknown; no text repair is implied.

## Unresolved write alternatives

These alternatives remain separate. Their direction, operation, offsets and
extents are absent; the name of an alternative does not establish a wire layout.
The remote-control alternative has no declared service here. B50D is named only
for the UI-direction alternative; neither alternative is paired with B50C reads.

| Family | Variant | Direction | Service | Operation | Alternative | Extent (bytes) | Grade |
|---|---|---|---|---|---|---|---|
| Vaillant | remote-control | absent | absent | absent | remote-control-write | absent | Hypothesis |
| Vaillant | UI-direction | absent | B50D | absent | UI-direction-write | absent | Hypothesis |

## Unknown physical properties

| Property | Grade |
|---|---|
| calendar century | Unknown |
| timezone | Unknown |
| valid-date rules | Unknown |
| start-before-end rules | Unknown |
| atomicity | Unknown |
| persistent assignment | Unknown |
| physical response | Unknown |
| readback | Unknown |
| pairing of B50B writes with B50C reads | Unknown |
| native adaptation | Unknown |
| peer effects | Unknown |
| qualification | Unknown |

No operation numbers beyond OP02 or field offsets are supplied. Unspecified
extents remain absent. These declarations grant no runtime capability, transmit
route or write admission, and provide no automatic native qualification.
