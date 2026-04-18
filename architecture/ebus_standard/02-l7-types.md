# ebus_standard L7 Type Rules

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Scope

The locked plan states:

> `BYTE`, `CHAR`, `DATA1c`, variable-length raw, composite BCD, and
> length-dependent selector each have exact byte handling, signedness,
> replacement-value sentinels, nibble ordering, invalid-nibble policy,
> selector length validation, truncated/overlong payload error paths, and
> validity propagation to decode output.
> Golden vectors are required for each primitive and cover positive AND
> negative cases.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

These rules are the required behavior for `ebus_standard` decode and
encode implementations.

## Decode Output Validity

Every decoded field MUST carry:

- `raw`: exact source bytes, in wire order.
- `valid`: boolean.
- `replacement`: boolean.
- `value`: omitted or unset when `valid=false`.
- `error`: structured decoder error when invalidity is caused by syntax,
  length, range, or selector failure rather than by a replacement value.

Replacement values and invalid syntax both produce `valid=false`, but
they are not the same state. Replacement values set `replacement=true`;
syntax/range/length failures set `replacement=false` and include an
error code.

## BYTE

`BYTE` is exactly one octet.

Rules:

1. Decode requires exactly one byte. Zero bytes are `truncated_payload`.
   More than one byte in a fixed-width BYTE field is `overlong_payload`.
2. The decoded value is unsigned integer `0..255`.
3. `BYTE` has no generic replacement sentinel. A field MAY declare a
   field-specific replacement value, but that sentinel belongs to the
   catalog field, not to the primitive type.
4. Encoding rejects integers outside `0..255`.

## CHAR

`CHAR` is exactly one octet. In the eBUS standard service tables it is
used for numeric bytes, address bytes, and fixed-width text bytes.

Rules:

1. Decode requires exactly one byte per `CHAR` element.
2. Numeric `CHAR` fields decode as unsigned integer `0..255` unless a
   catalog field declares a narrower range.
3. Signedness is catalog-field metadata, not implicit in the byte type.
   A field declared as signed `CHAR` decodes the byte as two's-complement
   int8 after replacement-byte handling. A field not declared signed
   MUST be decoded as unsigned.
4. A range violation sets `valid=false` with `error=out_of_range`.
5. `CHAR` has no generic replacement sentinel. A catalog field MAY
   declare a replacement byte such as `0x3F` or `0xFF`.
6. Fixed-width `CHAR[n]` text fields MUST preserve the exact raw byte
   array. Display text MAY strip trailing `0x00` and `0x20` for display
   only; raw bytes remain authoritative. `0xFF` is not padding unless the
   catalog field explicitly declares it as padding or replacement.
7. Text decoding accepts printable ASCII bytes `0x20..0x7E` as display
   characters. Other bytes remain in `raw`; display text MUST escape or
   substitute them without losing the original bytes.
8. Encoding fixed-width text pads on the right with `0x20` unless the
   catalog field declares a different pad byte. Encoding fails if the
   encoded byte length exceeds the fixed width.

## DATA1c

`DATA1c` is one unsigned byte with resolution `0.5` and replacement
sentinel `0xFF`.

Rules:

1. Decode requires exactly one byte.
2. `0xFF` is the replacement value. It decodes to `valid=false`,
   `replacement=true`, with no numeric value.
3. All non-`0xFF` bytes decode as unsigned raw integer `r`.
4. The physical value is `r / 2`.
5. DATA1c is not two's-complement signed. Values `0x80..0xFE` are
   positive half-unit values unless rejected by the catalog field range.
6. Catalog field ranges are applied after scaling. For a field range
   `0..100`, raw values above `0xC8` are `out_of_range`.
7. Encoding rejects values outside the field range, rejects values that
   do not round-trip exactly to a half-unit byte, and rejects values that
   would encode to `0xFF`.

## Variable-Length Raw Payload

A variable-length raw payload is a byte slice whose length is determined
by the telegram length prefix, a preceding field, or a selected catalog
branch.

Rules:

1. Raw payload decoding MUST preserve byte order and content exactly.
2. Zero length is valid only when the selected catalog branch permits
   zero length.
3. If the frame ends before the selected length is satisfied, decode
   fails with `truncated_payload`.
4. If bytes remain after all selected fields are decoded and the branch
   does not declare a raw tail, decode fails with `overlong_payload`.
5. Raw payloads have no replacement sentinel unless the catalog field
   declares one.
6. Encoders MUST write the length mode required by the selected branch
   and MUST reject payloads exceeding that branch's maximum.

## Composite BCD

`BCD` is one packed decimal byte. Composite BCD fields are ordered
sequences of packed BCD bytes.

Single-byte rules:

1. The high nibble is the tens digit.
2. The low nibble is the ones digit.
3. `0x42` decodes to decimal `42`.
4. Any nibble greater than `9` is invalid unless the full byte exactly
   matches a declared replacement sentinel.
5. The primitive replacement sentinel is `0xFF`.

Composite rules:

1. Each byte is validated independently before any aggregate value is
   emitted.
2. Date/time fields treat each BCD byte as an independent component.
   Example: seconds, minutes, hours, day, month, weekday, year.
3. Counter fields that use base-100 chunks MUST declare their multiplier
   in the catalog. Example: `0x03 0x10` meter reading uses multipliers
   `1`, `100`, `10000`, and `1000000`.
4. If any component is invalid, the composite field is `valid=false`.
   Valid components MAY still appear in diagnostic decode output, but no
   aggregate value is emitted.
5. If any component is a replacement value, the composite field is
   `valid=false` and `replacement=true` unless the catalog declares
   per-component replacement handling.

## Length-Dependent Selector

A length-dependent selector chooses a catalog branch using the telegram
length, request/response role, and any selector fields already decoded.

Required selector inputs:

- `PB`
- `SB`
- `direction`
- `request_or_response_role`
- telegram length prefix (`NN`)
- selected payload bytes used by the selector
- `selector_decoder` identifier from the catalog identity key

Rules:

1. Selector evaluation MUST happen before field decoding for branches
   whose layout depends on length.
2. The selected branch MUST be unique. If two branches match the same
   input, decode fails with `ambiguous_selector_branch`.
3. If no branch matches, decode fails with `unknown_selector_branch`.
4. If the selector requires a byte that is missing, decode fails with
   `truncated_payload`.
5. If the selected branch consumes fewer bytes than present and no raw
   tail is declared, decode fails with `overlong_payload`.
6. Selectors MUST validate both lower and upper length bounds. Accepting
   a prefix length because it is "at least enough" is forbidden.
7. Golden vectors MUST include positive selection, no-match,
   ambiguous-match, truncated-selector, truncated-payload, and
   overlong-payload cases.

## Validity Propagation

Decode output validity propagates upward:

1. A field with `valid=false` makes its enclosing composite invalid.
2. A composite with `valid=false` makes the command decode
   `valid=false`.
3. A command decode with invalid fields still returns raw bytes and
   field diagnostics when the catalog identity itself is known.
4. Unknown catalog identity is not a partial decode; it returns
   `unknown_method` with the frame metadata and raw payload.
