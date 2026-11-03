# B516 statistics directions and index metadata

This architecture contract follows the merged AM15 registry prerequisite
([companion catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab72_b516_statistics_directions.go)).
Read the public [native framing contract](../protocols/ebus-services/ebus-overview.md)
first. The existing [passive B516 energy contract](../protocols/vaillant/ebus-vaillant-B516-energy.md)
keeps its own scope. This candidate does not replace that contract, OP14, time
fields or energy-type dictionaries. It covers only OP10/11/12/18/19/1A statistics
direction/index metadata for the Vaillant family, not model qualification.

**Hypothesis** applies to every candidate native meaning below. **Proven** applies
only to the software contract: bounded metadata enumeration and exact lookup
with independent owned return storage. Physical support, presence, freshness,
execution, effects, persistence and delivery each remain **Unknown**, independently
of either grade. An accepted feedback label is not proof of effects or persistence.
Nothing here establishes stability before Helianthus 1.0.

## Software boundary

`Ab72Entries()` takes no arguments and returns the finite catalog or an error.
`Ab72Lookup(Ab72Key)` returns an entry, found boolean and error; a miss returns an
empty entry, false and no error. A catalog parse failure returns an error rather
than a partly admitted catalog. The exact key is `(family, variant, operation,
direction, selector, field)`. Operation and selector are optional coordinates:
absence differs from explicit zero. A missing operation cannot match a catalog
operation; catalog entries require one. There is no wildcard, normalization,
variant fallback, implicit side conversion or selector range expansion. Selector
00 and FF are the only enumerated OP10 selector examples; other row selectors
retain the candidate rule but are not manufactured lookup entries.

Every enumeration and lookup owns its returned nested maps, slices and optional
coordinate storage. Mutation of one result cannot change another result or the
catalog. Family is exactly `vaillant`; variants and field names are case-sensitive.
Unknown directions or keys are misses, not a request to perform discovery.
The parser rejects empty catalogs, malformed or trailing JSON, unknown entry
fields, incomplete keys, duplicate keys, invalid grades, bits above 7 and invalid
widths. These are catalog admission rules, not evidence of wire validity.

No encoder, method registration or physical exchange is supplied. This page adds
no transmit route, active executor, scan default or admission change. Existing
eBUS MCP compatibility and GraphQL parity are preserved; no new API surface is
registered by this documentation package.

## Candidate meanings and limits

All OP10 lengths are **after the sub-ID**: read request 7, read positive 11,
write request 11, write positive 7. Request time-base bits 0..1 mean total,
daily, monthly, yearly; request access is bit 2 (0 read, 1 write).
The write-positive access flag is bit 3, not bit 2. Read-positive has no named
access bit here. Energy value exists only in write request and read positive,
as binary32 LE **Wh**. Return nibble 0 means value-contained, 1 NOK; 2..15
remain unnamed. No return-nibble byte offset is invented.

Period index FF selects by date; another period index selects a table row and
ignores date. Total ignores both period index and date. Energy index FF selects
energy type and operation mode; another energy index ignores them.
**Date packing is Unknown in this candidate; no date codec is inferred.**
Missing offsets and defaults remain Unknown even where a separate passive
contract has its own packing evidence.

OP11 has no arguments and nine ordered u8 positive fields: Version, Build,
TotalEnergies, Days, DailyEnergies, Months, MonthlyEnergies, Years,
YearlyEnergies. Counts are returned metadata, not installed counts or enforced
bounds. Position in the table below is an ordinal within this nine-field list,
not an inferred offset in another operation.

OP12 request bits total/daily/monthly/yearly 0..3 are four independent bits,
not the OP10 time-base enumeration. Its positive bits 0 not-supported,
1 energy-unavailable, 2 mode-unavailable are independent. Energy selector and
mode stay separate. Meter/clear and scalar-u8/low-six-bits are four distinct
variants. In the latter, bits 0..5 select energy; bits 6 and 7 independently
select sums. Nested and outer duplicate positive flags remain distinct raw
evidence: packing precedence is Unknown. Do not flatten them, choose a winner,
or invent full variant-specific meter/clear tables.

OP18 yield type 0 solar / 1 environment / 2 energy / 3 gas-or-oil stays attached
to its direction. Read-positive and write-value sides use LEu32 **kWh**, with
no sentinel: FF FF FF FF is raw 4294967295 kWh. OP19 reset retains yield type;
feedback 1 is labelled accepted, all other meanings remain Unknown.

OP1A carries yield, month, year-index 0 this-year / 1 last-year, mode
0 all / 1 heating / 2 DHW, and an LEu32 sum. **Unit-type overlaps the second
sum byte; month 10/11 conflict remains unresolved.** Offsets, packing precedence,
defaults and unit remain Unknown. Keep the overlapping descriptions and raw
bytes; do not concatenate fields, assign invented positions, repair the month
conflict or borrow OP18's unit.

## Finite catalog

The [synthetic package](fixtures/am16_b516_statistics_directions.json) contains
`catalog`, `examples` and `conflict_evidence`. Every catalog row has family `vaillant`, grade
`Hypothesis`, software_contract `Proven`, the native framing link above, and
all seven qualification properties `Unknown`. The following table lists every
key and its remaining metadata; an absent property is not zero or a default.
Variants use registry identifiers verbatim. All numeric OP values below are hex;
selector values are decimal. These are metadata records, not telegram templates.

<!-- catalog:start -->
| Variant | OP | Direction | Selector | Field | Metadata |
| --- | --- | --- | --- | --- | --- |
| ab72-statistics-read | 10 | request | absent | layout | `{"length":7,"rules":["Lengths are after the sub-ID."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | request | absent | flags | `{"bits":{"access":2,"time-base-high":1,"time-base-low":0},"unknown":["offsets","defaults","physical support"],"values":{"access:0":"read","access:1":"write","time-base:0":"total","time-base:1":"daily","time-base:2":"monthly","time-base:3":"yearly"}}` |
| ab72-statistics-read | 10 | request | 0 | period-index | `{"rules":["Total ignores period index and date.","Select table row; ignore date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-read | 10 | request | 0 | energy-index | `{"rules":["Ignore energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | request | 255 | period-index | `{"rules":["Total ignores period index and date.","Select by date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-read | 10 | request | 255 | energy-index | `{"rules":["Select energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | positive | absent | layout | `{"length":11,"rules":["Lengths are after the sub-ID."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | positive | absent | flags | `{"bits":{"time-base-high":1,"time-base-low":0},"unknown":["offsets","defaults","physical support"],"values":{"time-base:0":"total","time-base:1":"daily","time-base:2":"monthly","time-base:3":"yearly"}}` |
| ab72-statistics-read | 10 | positive | absent | energy-value | `{"encoding":"binary32 LE","unit":"Wh","unknown":["offsets","defaults","physical support"],"width":32}` |
| ab72-statistics-read | 10 | positive | 0 | period-index | `{"rules":["Total ignores period index and date.","Select table row; ignore date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-read | 10 | positive | 0 | energy-index | `{"rules":["Ignore energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | positive | 255 | period-index | `{"rules":["Total ignores period index and date.","Select by date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-read | 10 | positive | 255 | energy-index | `{"rules":["Select energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-read | 10 | positive | absent | return-nibble | `{"unknown":["meanings 2..15","offsets"],"values":{"0":"value-contained","1":"NOK"},"width":4}` |
| ab72-statistics-write | 10 | request | absent | layout | `{"length":11,"rules":["Lengths are after the sub-ID."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | request | absent | flags | `{"bits":{"access":2,"time-base-high":1,"time-base-low":0},"unknown":["offsets","defaults","physical support"],"values":{"access:0":"read","access:1":"write","time-base:0":"total","time-base:1":"daily","time-base:2":"monthly","time-base:3":"yearly"}}` |
| ab72-statistics-write | 10 | request | absent | energy-value | `{"encoding":"binary32 LE","unit":"Wh","unknown":["offsets","defaults","physical support"],"width":32}` |
| ab72-statistics-write | 10 | request | 0 | period-index | `{"rules":["Total ignores period index and date.","Select table row; ignore date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-write | 10 | request | 0 | energy-index | `{"rules":["Ignore energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | request | 255 | period-index | `{"rules":["Total ignores period index and date.","Select by date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-write | 10 | request | 255 | energy-index | `{"rules":["Select energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | positive | absent | layout | `{"length":7,"rules":["Lengths are after the sub-ID."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | positive | absent | flags | `{"bits":{"access":3,"time-base-high":1,"time-base-low":0},"unknown":["offsets","defaults","physical support"],"values":{"time-base:0":"total","time-base:1":"daily","time-base:2":"monthly","time-base:3":"yearly"}}` |
| ab72-statistics-write | 10 | positive | 0 | period-index | `{"rules":["Total ignores period index and date.","Select table row; ignore date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-write | 10 | positive | 0 | energy-index | `{"rules":["Ignore energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | positive | 255 | period-index | `{"rules":["Total ignores period index and date.","Select by date."],"unknown":["date packing","offsets","defaults"]}` |
| ab72-statistics-write | 10 | positive | 255 | energy-index | `{"rules":["Select energy type and operation mode."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-write | 10 | positive | absent | return-nibble | `{"unknown":["meanings 2..15","offsets"],"values":{"0":"value-contained","1":"NOK"},"width":4}` |
| ab72-statistics-index | 11 | request | absent | layout | `{"length":0,"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-index | 11 | positive | absent | ordered-fields | `{"order":["Version","Build","TotalEnergies","Days","DailyEnergies","Months","MonthlyEnergies","Years","YearlyEnergies"],"rules":["Counts are returned metadata, not installed counts or enforced bounds."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-statistics-index | 11 | positive | absent | Version | `{"encoding":"u8","position":0,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | Build | `{"encoding":"u8","position":1,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | TotalEnergies | `{"encoding":"u8","position":2,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | Days | `{"encoding":"u8","position":3,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | DailyEnergies | `{"encoding":"u8","position":4,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | Months | `{"encoding":"u8","position":5,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | MonthlyEnergies | `{"encoding":"u8","position":6,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | Years | `{"encoding":"u8","position":7,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-statistics-index | 11 | positive | absent | YearlyEnergies | `{"encoding":"u8","position":8,"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-meter-scalar-u8 | 12 | request | absent | flags | `{"bits":{"daily":1,"monthly":2,"total":0,"yearly":3},"rules":["Four independent request bits."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-meter-scalar-u8 | 12 | request | absent | energy-selector | `{"bits":{},"encoding":"u8","rules":["Scalar u8 selector."],"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-meter-scalar-u8 | 12 | request | absent | mode | `{"encoding":"u8","unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-meter-scalar-u8 | 12 | positive | absent | flags | `{"bits":{"energy-unavailable":1,"mode-unavailable":2,"not-supported":0},"conflicts":["Nested and outer duplicate flags; packing precedence Unknown."],"unknown":["packing precedence","offsets","defaults","full variant-specific meter/clear tables"]}` |
| ab72-meter-low-six-bits | 12 | request | absent | flags | `{"bits":{"daily":1,"monthly":2,"total":0,"yearly":3},"rules":["Four independent request bits."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-meter-low-six-bits | 12 | request | absent | energy-selector | `{"bits":{"sum-6":6,"sum-7":7},"encoding":"u8","rules":["Low six bits selector; independent sum bits 6 and 7."],"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-meter-low-six-bits | 12 | request | absent | mode | `{"encoding":"u8","unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-meter-low-six-bits | 12 | positive | absent | flags | `{"bits":{"energy-unavailable":1,"mode-unavailable":2,"not-supported":0},"conflicts":["Nested and outer duplicate flags; packing precedence Unknown."],"unknown":["packing precedence","offsets","defaults","full variant-specific meter/clear tables"]}` |
| ab72-clear-scalar-u8 | 12 | request | absent | flags | `{"bits":{"daily":1,"monthly":2,"total":0,"yearly":3},"rules":["Four independent request bits."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-clear-scalar-u8 | 12 | request | absent | energy-selector | `{"bits":{},"encoding":"u8","rules":["Scalar u8 selector."],"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-clear-scalar-u8 | 12 | request | absent | mode | `{"encoding":"u8","unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-clear-scalar-u8 | 12 | positive | absent | flags | `{"bits":{"energy-unavailable":1,"mode-unavailable":2,"not-supported":0},"conflicts":["Nested and outer duplicate flags; packing precedence Unknown."],"unknown":["packing precedence","offsets","defaults","full variant-specific meter/clear tables"]}` |
| ab72-clear-low-six-bits | 12 | request | absent | flags | `{"bits":{"daily":1,"monthly":2,"total":0,"yearly":3},"rules":["Four independent request bits."],"unknown":["offsets","defaults","physical support"]}` |
| ab72-clear-low-six-bits | 12 | request | absent | energy-selector | `{"bits":{"sum-6":6,"sum-7":7},"encoding":"u8","rules":["Low six bits selector; independent sum bits 6 and 7."],"unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-clear-low-six-bits | 12 | request | absent | mode | `{"encoding":"u8","unknown":["offsets","defaults","physical support"],"width":8}` |
| ab72-clear-low-six-bits | 12 | positive | absent | flags | `{"bits":{"energy-unavailable":1,"mode-unavailable":2,"not-supported":0},"conflicts":["Nested and outer duplicate flags; packing precedence Unknown."],"unknown":["packing precedence","offsets","defaults","full variant-specific meter/clear tables"]}` |
| ab72-yield-read | 18 | request | absent | yield-type | `{"unknown":["offsets","defaults","physical support"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"},"width":8}` |
| ab72-yield-read | 18 | positive | absent | yield-type | `{"unknown":["offsets","defaults","physical support"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"},"width":8}` |
| ab72-yield-read | 18 | positive | absent | yield-value | `{"encoding":"LEu32","rules":["All u32 values retain their raw numeric meaning; no sentinel inferred."],"unit":"kWh","unknown":["offsets","defaults","physical support"],"width":32}` |
| ab72-yield-write | 18 | request | absent | yield-type | `{"unknown":["offsets","defaults","physical support"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"},"width":8}` |
| ab72-yield-write | 18 | request | absent | yield-value | `{"encoding":"LEu32","rules":["All u32 values retain their raw numeric meaning; no sentinel inferred."],"unit":"kWh","unknown":["offsets","defaults","physical support"],"width":32}` |
| ab72-yield-write | 18 | positive | absent | yield-type | `{"unknown":["offsets","defaults","physical support"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"},"width":8}` |
| ab72-yield-reset | 19 | request | absent | yield-type | `{"unknown":["offsets","defaults","physical support"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"},"width":8}` |
| ab72-yield-reset | 19 | positive | absent | feedback | `{"unknown":["other feedback meanings","effects","persistence"],"values":{"1":"accepted"},"width":8}` |
| ab72-yield-month | 1A | positive | absent | yield-type | `{"conflicts":["Unit-type overlaps second sum byte.","Month 10/11 conflict."],"unknown":["offsets","defaults","packing precedence","unit"],"values":{"0":"solar","1":"environment","2":"energy","3":"gas-or-oil"}}` |
| ab72-yield-month | 1A | positive | absent | month | `{"conflicts":["Unit-type overlaps second sum byte.","Month 10/11 conflict."],"unknown":["offsets","defaults","packing precedence","unit"],"values":{}}` |
| ab72-yield-month | 1A | positive | absent | year-index | `{"conflicts":["Unit-type overlaps second sum byte.","Month 10/11 conflict."],"unknown":["offsets","defaults","packing precedence","unit"],"values":{"0":"this-year","1":"last-year"}}` |
| ab72-yield-month | 1A | positive | absent | mode | `{"conflicts":["Unit-type overlaps second sum byte.","Month 10/11 conflict."],"unknown":["offsets","defaults","packing precedence","unit"],"values":{"0":"all","1":"heating","2":"DHW"}}` |
| ab72-yield-month | 1A | positive | absent | sum | `{"conflicts":["Unit-type overlaps second sum byte.","Month 10/11 conflict."],"encoding":"LEu32","unknown":["offsets","defaults","packing precedence","unit"],"values":{},"width":32}` |
<!-- catalog:end -->

## Synthetic field slices and partial results

Inputs to these examples are an exact catalog key and an explicitly supplied
field slice, not an inferred offset in a telegram. The focused test contains a
local conformance model only; it does not execute the companion Go API or expose
an application decoder. Outputs preserve independent owned raw bytes, a candidate
value only when the known field is complete and unconflicted, its metadata unit,
and status. Unknown keys yield `unknown`; malformed byte arrays yield `malformed`.
Short and extra slices yield `partial` and `extra` without padding or truncation.
Conflicted fields yield `conflict`; unspecified codecs yield `unknown`.
A rejected/partial field never clears independently useful metadata or replaces a
last-known-good candidate. Last-known-good is retained state, not fresh evidence.
Raw slices remain available even after semantic failure. Nested and outer flags
are retained separately, with no packing precedence. This is fail-closed semantic
admission, not suppression of raw evidence.

<!-- examples:start -->
| Case | Variant / OP / direction / field / selector | Field slice (hex) | Value | Unit | Status |
| --- | --- | --- | --- | --- | --- |
| op10-wh | ab72-statistics-read / 10 / positive / energy-value / absent | 00 00 80 3F | 1.0 | Wh | candidate |
| op10-write-wh | ab72-statistics-write / 10 / request / energy-value / absent | 00 00 00 40 | 2.0 | Wh | candidate |
| op18-maximum | ab72-yield-read / 18 / positive / yield-value / absent | FF FF FF FF | 4294967295 | kWh | candidate |
| op18-write-zero | ab72-yield-write / 18 / request / yield-value / absent | 00 00 00 00 | 0 | kWh | candidate |
| op18-partial | ab72-yield-read / 18 / positive / yield-value / absent | FF FF | None | kWh | partial |
| op18-extra | ab72-yield-read / 18 / positive / yield-value / absent | 01 00 00 00 02 | None | kWh | extra |
| op1a-conflict | ab72-yield-month / 1A / positive / sum / absent | 01 02 03 04 | None | None | conflict |
| op10-unknown-date | ab72-statistics-read / 10 / request / period-index / 255 | 00 00 | None | None | unknown |
<!-- examples:end -->

These synthetic conflict views retain both descriptions without resolving
packing or assigning positions. Slices are supplied independently, never
concatenated into a payload.

<!-- conflicts:start -->
```json
[
  {
    "case": "duplicate-flags",
    "variant": "ab72-meter-low-six-bits",
    "operation": 18,
    "direction": "positive",
    "outer_flags": [
      1
    ],
    "nested_flags": [
      2
    ],
    "packing_precedence": "Unknown"
  },
  {
    "case": "month-overlap",
    "variant": "ab72-yield-month",
    "operation": 26,
    "direction": "positive",
    "sum_raw": [
      1,
      2,
      3,
      4
    ],
    "unit_type_raw": [
      2
    ],
    "month_alternatives": [
      [
        10
      ],
      [
        11
      ]
    ],
    "positions": null,
    "unit": null,
    "packing_precedence": "Unknown"
  }
]
```
<!-- conflicts:end -->

The [focused unittest](../tests/test_am16_b516_statistics_directions.py) checks
every table row against separately authored finite expectations, independently
calculates binary32/u32 values, varies all six lookup axes, and checks malformed,
partial, extra, unknown and valid controls plus owned raw-memory behavior.
It does not establish physical support, effects or live execution. Focused offline
checks do not claim automatic discovery by Gate D. Full repository CI, Gate D,
publication checks and independent committed-change review remain later shipping
requirements. Transport and device smoke validation are not performed here.
