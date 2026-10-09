# B524 class discovery and parameter descriptions

B524 selectors are `(OP, GG, II, RR)`. OP02 and OP06 are separate namespaces;
OP00 identifiers are not group numbers. The [protocol specification](ebus-vaillant-B524.md)
defines request and response layouts, and the [register map](ebus-vaillant-B524-register-map.md)
records observed classes and register addresses.

## System information and concrete instances

OP00 `circuit_count` and `zone_count` describe supported capacity for the
characterized VRC720 profile, not the number of configured or connected
instances. OP02/GG02 has heating selectors II01..08 and a separate virtual DHW
selector II09 in that profile. A capacity does not assign instance numbers,
make sparse instances contiguous, or prove physical presence.

The characterized OP06 slot interval is II01..08. These are profile observations,
not a universal bound of the one-byte instance field. The numerical equality of
an OP00 identifier and a GG is not evidence of a relationship.

## Availability observations

**Hypothesis:** OP02/GG01/RR0001 is an availability indication for native DHW
when a correlated read has an exact two-byte UIN body and a nonzero value.
A zero value is a negative indication for that profile. Empty, malformed or
failed replies remain Unknown.

**Hypothesis:** OP06/RR0001 `device_connected` is a common Boolean connection
indication, including GG0D. An exact one-byte zero is false and one is true;
other values, widths or unmatched replies remain Unknown. Readable class or
version registers do not override a false connection value. GG0D's terminal
register maximum remains Unknown.

A class description at IIFF does not prove that any concrete device is present.
The [survey methodology](ebus-vaillant-b524-survey-methodology.md) distinguishes
positive read observations, empty replies and transport failures.

## Parameter description correlation

OP01 `DescribeParameter` describes OP02 parameters; OP07
`DescribeDeviceParameter` describes OP06 parameters. The normalized response is
`GG RRlo RRhi MIN MAX STEP`. MIN, MAX and STEP occupy three equal-width spans.
The request instance is not echoed. Correlate each reply to the outstanding
request and interpret it with the parameter's matching codec, never by guessing
a datatype from reply length alone.

A writable attribute identifies a description candidate. Description bytes do
not authorize a write or independently prove current writability. For HDA:3
and numeric-byte HTI, format and range may be decoded while STEP remains
**Unknown**; raw STEP bytes must not be converted into an invented duration.

## Generic IIFF class observations

An IIFF description is a generic class observation, distinct from a
concrete-instance read or description. It establishes neither installed device
identity nor physical presence. Observations from one controller/software/API
profile must not silently become verified limits for another profile.

Sanitized OP07 common-header bodies after `GG RRlo RRhi` include `00 01 01`
for BOOL `device_connected`, `00 FF 01` for UCH `device_class_address`, and
`00 01 01` for UCH `device_error_code`. These are class-level format/range
observations only. The corresponding
[observed-window data](fixtures/b524-op06-observed-windows-v1.json)
retains selector-correlated payloads and their qualification.

## Observed register windows

| OP06 GG | Observed RR window | Evidence boundary |
| --- | --- | --- |
| 01, 02, 03, 05, 06, 07, 08, 0B, 0C | 0000..002F | Correlated read/description observations |
| 09, 0A | 0000..0035 | Correlated read/description observations |
| 0E, 0F | 0000..0033 | Read-only RR0033 observed; its generic description body remains unqualified |
| 04, 0D | Unknown | No terminal bound established |

These windows are not terminal maxima. Read-only state can exist above the
highest qualified description response. An empty response is not proof that a
register or class is absent.
