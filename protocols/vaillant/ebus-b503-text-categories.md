# B503 text, unlock and category alternatives

## Evidence and qualification

This finite Vaillant family supplement records the supplied candidate declarations
for issue #1014. No vendor specification or reproducible native capture is
provided for these fields. Each supplied native field is **Hypothesis**;
unprovided properties remain **Unknown**. **Proven** applies only to synthetic
representation checks, never to physical qualification. The
[synthetic tuples](fixtures/aj04_b503_text_categories.json) are invented examples,
without observed endpoints, firmware or capture conditions.

## Native field table

Operation values are hexadecimal. Widths count characters for unlock, bytes for
unsigned-byte fields, and the remaining data extent for text. `Unknown` does not
mean zero. Variant and direction are unprovided for these fields; no request or
response assignment is inferred. All physical coordinates are Unknown.

| operation | variant | direction | field | width | encoding | default | coordinate | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 03 | Unknown | Unknown | unlock | 8 characters | Unknown | Unknown | Unknown | Hypothesis |
| 03 | Unknown | Unknown | trailing-byte | 1 byte | unsigned byte | 0 | Unknown | Hypothesis |
| 04 | Unknown | Unknown | text | through data extent | ASCII | Unknown | Unknown | Hypothesis |
| 05 | Unknown | Unknown | text | through data extent | ASCII | Unknown | Unknown | Hypothesis |
| 05 | Unknown | Unknown | mode | 1 byte | unsigned byte | Unknown | Unknown | Hypothesis |
| 06 | Unknown | Unknown | unlock | 8 characters | Unknown | Unknown | Unknown | Hypothesis |
| 06 | Unknown | Unknown | trailing-byte | 1 byte | unsigned byte | 0 | Unknown | Hypothesis |

For OP03 and OP06, the separate unsigned byte follows the eight-character
unlock field. Character encoding, padding and absolute coordinates are Unknown;
eight characters do not establish eight encoded bytes. Seven, eight and nine
synthetic characters distinguish the declared width only.

OP04 and OP05 text extends through its declared data extent. ASCII `41 42`
represents `AB`. OP05 mode is a separate byte, never the numeric value
`FFFFFFFF`. Its position relative to variable text is Unknown. Synthetic OP05
text lengths 0, 2 and 5 leave the mode coordinate absent; no fixed tail position
or rule splitting a physical payload follows. Termination on the wire is Unknown.

## Category alternatives

The family, variant and direction must qualify each table. The direction and
operation associated with these category alternatives are Unknown. The names
`common` and `reset` distinguish supplied alternatives, not proven wire
selectors. Common categories 1..5 are named; only category 2 has a supplied
semantic label. Reset names only 1 and 3. Reset category 2 is an unlabeled probe,
not an additional named category. Other common labels remain Unknown.

| family | variant | direction | category | named | label | grade |
| --- | --- | --- | --- | --- | --- | --- |
| Vaillant | common | Unknown | 1 | yes | Unknown | Hypothesis |
| Vaillant | common | Unknown | 2 | yes | predictive maintenance | Hypothesis |
| Vaillant | common | Unknown | 3 | yes | Unknown | Hypothesis |
| Vaillant | common | Unknown | 4 | yes | Unknown | Hypothesis |
| Vaillant | common | Unknown | 5 | yes | Unknown | Hypothesis |
| Vaillant | reset | Unknown | 1 | yes | error | Hypothesis |
| Vaillant | reset | Unknown | 2 | no | Unknown | Unknown |
| Vaillant | reset | Unknown | 3 | yes | status | Hypothesis |

Never extend the reset alternative using common labels. Preserve each raw value
and unresolved alternative independently, including unlabeled category values.

## Partial evidence and limits

Positive forms with only a declared prefix do not establish an empty physical
response. Physical success, session exclusivity and physical effects are
**Unknown**. Preserve raw partial evidence beside the last-known-good complete
state; a prefix-only or ambiguous form cannot replace it or establish success.
No complete physical extent is supplied here. Synthetic width matches and ASCII
examples establish neither native admission nor physical qualification.
