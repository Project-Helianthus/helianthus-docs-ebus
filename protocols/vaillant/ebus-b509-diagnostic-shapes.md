# Vaillant B509 diagnostic address and software identity shapes

## Scope and evidence

This finite family declaration concerns `PB=0xB5`, `SB=0x09`, operations
`0x13`, `0x34`, `0x35` and `0x51`. All native field claims below are
**Hypothesis**. **Proven** applies only to the synthetic representation and
local arithmetic, never native support. Qualification, freshness, persistence
and execution permission remain **Unknown** independently of those grades.
No installed device behavior or physical effect is established.

The [native B509 reference](ebus-vaillant-B509.md) describes the distinct
`0x0D`/`0x0E` register-access forms. Its two-byte symbolic address does not
establish the diagnostic address width here. Those raw alternatives remain
separate; no capture resolves a conflict or establishes equivalence.

OP13 is a candidate no-argument query with a Boolean result. The Boolean byte
mapping is Unknown: neither zero nor any other raw result is assigned a truth
value. OP34 declares a little-endian unsigned 32-bit address and an unsigned
byte requested count; its positive response declares an address and variable
raw data. “Positive” describes a response form, not a nonzero address rule.
OP35 declares address and variable raw data, without the OP34 count field;
its write-status domain is 0..6, with every individual meaning Unknown.

OP51 declares a diagnostic component in 0..7, an initiator byte, exactly five
ASCII identity characters, and four separate software decimal components.
Diagnostic component identity is separate from transport session and security
identity. OP51 direction is Unknown. No NUL terminator, variable identity
length, software packed word or single version string is declared.

## Family identity and grades

| attribute | value |
| --- | --- |
| "family" | "vaillant" |
| "service" | "B509" |
| "primary" | 181 |
| "secondary" | 9 |
| "representation" | "Proven" |
| "native_grade" | "Hypothesis" |

## Field declarations

Each row is one claim. Operation strings are hexadecimal; numeric limits are
decimal. Cells use JSON scalars, with null meaning Unknown. Row order groups
logical fields; it does not supply byte offsets or a complete telegram layout.
Field identity includes family, service, PB, SB, operation, direction and field.

The OP51 initiator byte retains its legacy field name in this table.

<!-- legacy-role-mapping:begin -->
| operation | direction | field | width_bits | signedness | byte_order | conversion | minimum | maximum | recommended_bytes | maximum_bytes | grade | mapping_grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "13" | "request" | "arguments" | 0 | "Unknown" | "Unknown" | "no_arguments" | null | null | null | null | "Hypothesis" | "Unknown" |
| "13" | "response" | "result" | null | "Unknown" | "Unknown" | "Boolean" | null | null | null | null | "Hypothesis" | "Unknown" |
| "34" | "request" | "address" | 32 | "unsigned" | "little_endian" | "identity" | 0 | 4294967295 | null | null | "Hypothesis" | "Hypothesis" |
| "34" | "request" | "requested_count" | 8 | "unsigned" | "not_applicable" | "identity" | 0 | 255 | null | null | "Hypothesis" | "Hypothesis" |
| "34" | "response" | "address" | 32 | "unsigned" | "little_endian" | "identity" | 0 | 4294967295 | null | null | "Hypothesis" | "Hypothesis" |
| "34" | "response" | "data" | null | "Unknown" | "Unknown" | "raw_bytes" | null | null | 10 | null | "Hypothesis" | "Unknown" |
| "35" | "request" | "address" | 32 | "unsigned" | "little_endian" | "identity" | 0 | 4294967295 | null | null | "Hypothesis" | "Hypothesis" |
| "35" | "request" | "data" | null | "Unknown" | "Unknown" | "raw_bytes" | null | null | null | null | "Hypothesis" | "Unknown" |
| "35" | "response" | "write_status" | null | "Unknown" | "Unknown" | "status_domain" | 0 | 6 | null | null | "Hypothesis" | "Unknown" |
| "51" | "Unknown" | "component" | null | "Unknown" | "Unknown" | "identity" | 0 | 7 | null | null | "Hypothesis" | "Hypothesis" |
| "51" | "Unknown" | "master" | 8 | "unsigned" | "not_applicable" | "identity" | 0 | 255 | null | null | "Hypothesis" | "Hypothesis" |
| "51" | "Unknown" | "identity" | 40 | "not_applicable" | "not_applicable" | "ASCII_exact" | null | null | null | null | "Hypothesis" | "Hypothesis" |
| "51" | "Unknown" | "software_component_1" | null | "Unknown" | "Unknown" | "decimal_scalar" | null | null | null | null | "Hypothesis" | "Unknown" |
| "51" | "Unknown" | "software_component_2" | null | "Unknown" | "Unknown" | "decimal_scalar" | null | null | null | null | "Hypothesis" | "Unknown" |
| "51" | "Unknown" | "software_component_3" | null | "Unknown" | "Unknown" | "decimal_scalar" | null | null | null | null | "Hypothesis" | "Unknown" |
| "51" | "Unknown" | "software_component_4" | null | "Unknown" | "Unknown" | "decimal_scalar" | null | null | null | null | "Hypothesis" | "Unknown" |

<!-- legacy-role-mapping:end -->

Ten bytes is a diagnostic recommendation for OP34 response data, not buffer
capacity. A synthetic eleven-byte data field is therefore not rejected by
that recommendation. The variable maximum remains Unknown. Count zero and
count 255 are distinct raw values; neither implies an unlimited count.

## Write-status meanings

Domain membership is Hypothesis; each status meaning remains Unknown.
Status 7 stays raw and unlabeled, outside the declared domain.

| status | meaning |
| --- | --- |
| 0 | null |
| 1 | null |
| 2 | null |
| 3 | null |
| 4 | null |
| 5 | null |
| 6 | null |

## Unknowns and preservation

These unknowns apply to every declaration. Unresolved or out-of-domain values
retain their original bytes; no replacement or guessed meaning is supplied.
Partial evidence cannot fill missing fields or replace an earlier known value
with an inferred one. These declarations establish no memory access, encoder
or write route, and confer no execution permission.

| property | value |
| --- | --- |
| "offsets" | null |
| "defaults" | null |
| "response_correlation" | null |
| "variable_maximum" | null |
| "padding" | null |
| "physical_effects" | null |
| "boolean_byte_mapping" | null |
| "software_widths" | null |
| "software_ranges" | null |
| "source" | null |
| "destination" | null |
| "device" | null |
| "firmware" | null |
| "qualification" | "Unknown" |
| "freshness" | "Unknown" |
| "persistence" | "Unknown" |
| "execution_permission" | "Unknown" |
| "raw_fallback" | "preserve original bytes" |

## Synthetic native tuples

These are isolated field tuples, not complete exchanges or response binding.
The raw column preserves bytes in decimal; null raw for software scalars means
that no byte encoding is asserted. `fits` is a local representation/domain
predicate, not a support or qualification decision. Rejected values remain
raw alternatives. Source, destination and physical provenance are Unknown.

| case | operation | direction | field | raw | value | fits |
| --- | --- | --- | --- | --- | --- | --- |
| "address" | "34" | "request" | "address" | [120, 86, 52, 18] | 305419896 | true |
| "response_address" | "34" | "response" | "address" | [120, 86, 52, 18] | 305419896 | true |
| "write_address" | "35" | "request" | "address" | [120, 86, 52, 18] | 305419896 | true |
| "count_zero" | "34" | "request" | "requested_count" | [0] | 0 | true |
| "count_255" | "34" | "request" | "requested_count" | [255] | 255 | true |
| "data_eleven" | "34" | "response" | "data" | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | true |
| "write_data" | "35" | "request" | "data" | [170, 85] | [170, 85] | true |
| "status_six" | "35" | "response" | "write_status" | [6] | 6 | true |
| "status_seven" | "35" | "response" | "write_status" | [7] | 7 | false |
| "identity_five" | "51" | "Unknown" | "identity" | [65, 66, 67, 68, 69] | "ABCDE" | true |
| "identity_short" | "51" | "Unknown" | "identity" | [65, 66] | "AB" | false |
| "identity_long" | "51" | "Unknown" | "identity" | [65, 66, 67, 68, 69, 70] | "ABCDEF" | false |
| "identity_non_ascii" | "51" | "Unknown" | "identity" | [65, 66, 67, 68, 128] | null | false |
| "identity_terminated" | "51" | "Unknown" | "identity" | [65, 66, 67, 68, 69, 0] | "ABCDE\u0000" | false |
| "component_seven" | "51" | "Unknown" | "component" | [7] | 7 | true |
| "component_eight" | "51" | "Unknown" | "component" | [8] | 8 | false |
| "software_1" | "51" | "Unknown" | "software_component_1" | null | 1 | true |
| "software_2" | "51" | "Unknown" | "software_component_2" | null | 20 | true |
| "software_3" | "51" | "Unknown" | "software_component_3" | null | 3 | true |
| "software_4" | "51" | "Unknown" | "software_component_4" | null | 40 | true |

## Evidence

The [synthetic tuple fixture](fixtures/ai10_b509_diagnostic_shapes.json)
records these finite declarations and no capture. The native B509 reference
above supplies family context only; it does not prove these diagnostic shapes.
No primary native exchange is supplied for these candidates, so all native
claims retain Hypothesis and the listed gaps retain Unknown.
