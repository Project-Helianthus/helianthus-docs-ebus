# B512 DHW flags and stepper release: candidate supplement

## Evidence and scope

**Hypothesis** applies to every field and declaration below. None is promoted to
**Proven** by these synthetic examples. Physical qualification is independently
**Unknown**: physical adaptation, solar/two-zone role, support and actual movement
are unresolved. Exact missing condition labels are **Unknown**. Family names are
correspondence names, not evidence of support for individual devices.

The public native [B512 reference](ebus-vaillant-B512.md#candidate-sub-commands-op)
provides the candidate service context. This focused supplement records the
bounded candidate detail; no native capture establishing these offsets or flags
is supplied. The [synthetic tuples](fixtures/aj06_b512_dhw_stepper.json) are
arithmetic examples, not captured telegrams or independent wire evidence.

Coordinates are logical and include the three-position B5/12/operation prefix.
`request` and `positive` denote abstract sides, not proven wire replies. Numeric
prefixes, operations and byte samples are hexadecimal; table positions and bit
numbers are decimal. `absent` means no declared operation, distinct from both
explicit zero and `0A` or `14`. A dash means unspecified, never zero by inference.

## Candidate field table

Each bit has its own row. Grade concerns the candidate mapping; qualification
concerns physical support. Unknown labels remain unknown even where bit positions
are candidate mappings. All defaults are declaration defaults, not observations.

| Variant | PB | SB | Operation | Direction | Field | Position | Encoding | Unit | Default | Meaning | Grade | Qualification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B512 | B5 | 12 | 03 | request | selector | 3 | u8 | — | — | 0=valve-temperature-input (candidate) | Hypothesis | Unknown |
| B512 | B5 | 12 | 03 | positive | status | 3 | u8 | — | — | 0=okay; 1=disconnected; 2=short-circuit | Hypothesis | Unknown |
| B512 | B5 | 12 | 03 | positive | temperature_raw | 4 | LEu16 | unresolved | — | raw only; conversion Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | task-active | 3 | bit 0 | — | false | task-active | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | heat-demand | 3 | bit 1 | — | false | heat-demand | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | loading-active | 3 | bit 2 | — | false | loading-active | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | loading-pump-fault | 3 | bit 3 | — | false | loading-pump-fault | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | condition_4 | 3 | bit 4 | — | false | label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | condition_5 | 3 | bit 5 | — | false | label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | condition_6 | 3 | bit 6 | — | false | label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | condition_7 | 3 | bit 7 | — | false | label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | modulation | 4 | u8/2 | Unknown (formal Celsius conflict) | 0 | unit conflict unresolved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | flow | 5 | u8/10 | l/min | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | temperature_6 | 6 | u8/2 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | temperature_7 | 7 | u8/2 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | temperature_8 | 8 | u8/2 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_condition_0 | 9 | bit 0 | — | false | separate inlet-condition flag; label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_condition_1 | 9 | bit 1 | — | false | separate inlet-condition flag; label Unknown | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_2 | 9 | bit 2 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_3 | 9 | bit 3 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_4 | 9 | bit 4 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_5 | 9 | bit 5 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_6 | 9 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | request | inlet_reserved_7 | 9 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | loading-disabled | 3 | bit 0 | — | false | loading-disabled | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | internal-test-active | 3 | bit 1 | — | false | internal-test-active | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | ready | 3 | bit 2 | — | false | ready | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | frost-protection-active | 3 | bit 3 | — | false | frost-protection-active | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | legionella-demand | 3 | bit 4 | — | false | legionella-demand | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | reset | 3 | bit 5 | — | false | reset | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | reserved_6 | 3 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | reserved_7 | 3 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | dhw_setpoint | 4 | u8/2 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | return | 5 | u8/2 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 06 | positive | adjustment | 6 | s8 | — | -1 | candidates -1/0/1/2 | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | inlet | 3 | signedLE16/16 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | status | 5 | u8 | — | valid (0) | 00=valid; 55=short; AA=interruption-or-disconnected; other=unmapped | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | stepper-release | 6 | bit 0 | — | false | release does not prove movement | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_1 | 6 | bit 1 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_2 | 6 | bit 2 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_3 | 6 | bit 3 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_4 | 6 | bit 4 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_5 | 6 | bit 5 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_6 | 6 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | request | reserved_7 | 6 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | dhw_setpoint | 3 | signedLE16/16 | Celsius | 0 | — | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | stepper-release | 5 | bit 0 | — | false | release does not prove movement | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_1 | 5 | bit 1 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_2 | 5 | bit 2 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_3 | 5 | bit 3 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_4 | 5 | bit 4 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_5 | 5 | bit 5 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_6 | 5 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 08 | positive | reserved_7 | 5 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | stepper-release | 3 | bit 0 | — | false | release does not prove movement | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_1 | 3 | bit 1 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_2 | 3 | bit 2 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_3 | 3 | bit 3 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_4 | 3 | bit 4 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_5 | 3 | bit 5 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_6 | 3 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | request | reserved_7 | 3 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 0A | request | declaration | — | untyped | — | — | no typed body | Hypothesis | Unknown |
| B51214 | B5 | F5 | absent | request | declaration | — | untyped | — | — | name supplies no encoded 14 operation | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | stepper-release | 3 | bit 0 | — | false | release does not prove movement | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_1 | 3 | bit 1 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_2 | 3 | bit 2 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_3 | 3 | bit 3 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_4 | 3 | bit 4 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_5 | 3 | bit 5 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_6 | 3 | bit 6 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 09 | positive | reserved_7 | 3 | bit 7 | — | 0 | reserved | Hypothesis | Unknown |
| B512 | B5 | 12 | 0A | positive | declaration | — | untyped | — | — | no typed body | Hypothesis | Unknown |
| B51214 | B5 | F5 | absent | positive | declaration | — | untyped | — | — | name supplies no encoded 14 operation | Hypothesis | Unknown |

## Raw preservation and partial knowledge

OP03 `34 12` is the unsigned little-endian raw value 4660. Temperature conversion
is **Unknown**; assigning Celsius or a temperature divisor fabricates a fact.
OP06 modulation has candidate division by two, with a conflicting formal Celsius
unit; the physical unit remains **Unknown**. Flow `01` gives 0.1 l/min while
candidate temperature `01` gives 0.5 Celsius. Signed adjustment `FF` gives -1,
not zero; `02` gives 2. The candidates are -1/0/1/2, with default -1.
OP08 `F0 FF` gives -1 Celsius; status `54` is unmapped, unlike `55` and `AA`.
OP09 `01` sets release; `80` sets only a reserved bit. Release does not prove movement.

Preserve raw bytes, reserved bits, unmapped status and unresolved units beside
candidate interpretation. A malformed or incomplete field does not invalidate
independent last-known-good fields and does not justify filling missing values
from defaults. Unmapped status is not valid status. No candidate mapping or
release bit establishes support, writable behavior, control success or movement.

OP0A declares B5/12/0A on both abstract sides without a typed body. The separately
named B51214 declares only B5/F5 on both sides. Its name supplies no encoded `14`
operation. This distinction qualifies the older parent table's partial `14`
label: it is not evidence of B5/12/14 or any typed body.

Pump, valve, OP07 power and fan/air declarations are outside this supplement.
These pre-1.0 candidate declarations carry no stability promise.
