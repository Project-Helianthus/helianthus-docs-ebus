# B514 diagnostic-menu feedback and pressure candidates

## Evidence and qualification

This finite Vaillant family supplement refines the
[existing B514 candidate sub-commands](ebus-vaillant-B514.md#candidate-sub-commands).
Its source is the supplied finite declaration set in issue #840, corroborated
by the AI13 B514 menu-feedback catalog (companion registry PR #274). Neither is
a reproducible native capture or vendor specification. Every native declaration
below is **Hypothesis**. Unprovided properties are **Unknown**. **Proven** applies
only to the local synthetic representation and arithmetic, never native behavior.

The [synthetic tuples](fixtures/ai14_b514_menu_feedback.json) carry no observed
source, destination, firmware, or capture conditions. Physical qualification,
native adaptation, cessation enforcement and peer effects are **Unknown**.
Synthetic checks establish no installed support, freshness, persistence or
execution permission. No operational use is established by these declarations.

## Native declaration table

Positions are zero-based logical positions including prefixes, not physical
telegram offsets. Extents count logical positions. Hexadecimal primary,
secondary and operation columns describe candidate prefixes; label keys, ranges,
defaults and constants are decimal. `-` means absent or no supplied mapping;
`Unknown` means no supplied property. Unlisted byte values stay unmapped.
The `generic`, `specific-a` and `specific-b` names distinguish unresolved OP06
table alternatives only; no additional on-wire variant discriminator is known.
The `named-09` name is correspondence text, not an encoded operation.

| operation | variant | direction | field | primary | secondary | position | width | extent | encoding | scale | unit | default | constant | conflict | labels | ranges | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | menu | request | mode | B5 | 14 | Unknown | Unknown | 4 | Unknown | Unknown | Unknown | Unknown | Unknown | - | 0=off;1=on | 2..255=off | Hypothesis |
| 01 | menu | positive | answer | F5 | 14 | Unknown | Unknown | 5 | Unknown | Unknown | Unknown | Unknown | Unknown | - | 0=normal;1=actors-deactivated | - | Hypothesis |
| 01 | menu | positive | feedback | F5 | 14 | Unknown | Unknown | 5 | Unknown | Unknown | Unknown | Unknown | Unknown | - | 1=accepted | - | Hypothesis |
| 06 | generic | request | command | B5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 0=query;1=start | - | Hypothesis |
| 06 | generic | positive | feedback | F5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 1=in-progress;255=unsupported | - | Hypothesis |
| 06 | specific-a | request | command | B5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 0=query;1=start | - | Hypothesis |
| 06 | specific-a | positive | feedback | F5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 1=not-successful | 3..255=invalid | Hypothesis |
| 06 | specific-b | request | command | B5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 0=query;1=start | - | Hypothesis |
| 06 | specific-b | positive | feedback | F5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | - | 1=not-successful | 3..255=invalid | Hypothesis |
| 07 | menu | request | command | B5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | 0 | Unknown | - | 0=query;1=start-liquefied-gas;2=start-natural-gas;3=abort | - | Hypothesis |
| 07 | menu | positive | feedback | F5 | 14 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | 0 | Unknown | - | 0=idle;1=progress;2=passed;3=warning;4=combustion-error;5=gas-type-error;6=aborted;255=unsupported | - | Hypothesis |
| 08 | menu | request | command | B5 | 14 | 3 | 1 | 6 | u8 | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | request | pressure | B5 | 14 | 4 | 2 | 6 | u16 LE | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | positive | feedback | F5 | 14 | 3 | 1 | 13 | u8 | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | positive | pressure | F5 | 14 | 4 | 2 | 13 | u16 LE | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | positive | minimum | F5 | 14 | 6 | 2 | 13 | u16 LE | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | positive | maximum | F5 | 14 | 8 | 2 | 13 | u16 LE | Unknown | Unknown | Unknown | Unknown | - | - | - | Hypothesis |
| 08 | menu | positive | step | F5 | 14 | 10 | 1 | 13 | u8 | Unknown | mbar | 0 | 1 | constant 1 mbar versus default zero; unresolved | - | - | Hypothesis |
| 08 | menu | positive | flow | F5 | 14 | 11 | 2 | 13 | u16 LE | /100 | l/min | Unknown | Unknown | - | - | - | Hypothesis |
| - | named-09 | request | prefix | B5 | - | 0 | 1 | Unknown | u8 | Unknown | Unknown | Unknown | 181 | - | - | - | Hypothesis |
| - | named-09 | positive | prefix | F5 | - | 0 | 1 | Unknown | u8 | Unknown | Unknown | Unknown | 245 | - | - | - | Hypothesis |

## Interpretation limits and raw alternatives

**Hypothesis — OP01:** only mode 1 means on; mode 0 and 2..255 mean off.
Answer 1 means actors-deactivated, separately from feedback 1 accepted. Other
feedback values remain unqualified. Candidate cessation after fifteen minutes
or mode zero is not established enforcement (**Unknown**).

**Hypothesis — OP06:** request 0 is query and 1 start in each alternative.
Reply 1 is in-progress in the generic table and not-successful in each specific
table. Generic FF is unsupported; specific 3..255, including FF, is invalid.
Values not supplied in a table receive no additional label. Raw bytes and all
three alternatives must remain visible; no variant selection is established.

**Hypothesis — OP07:** request default 0 is query; positive default 0 is idle.
Positive 6 is aborted, 7 is unmapped. The table gives the complete supplied
mapping; other values remain unmapped, without inferred error labels.

**Hypothesis — OP08:** pressure, minimum and maximum remain independent raw
unsigned little-endian words. No pressure factor is a qualified unit conversion;
pressure units are Unknown. Flow alone is a little-endian word divided by 100
in l/min. The step constant 1 mbar versus default zero is an unresolved conflict;
a raw zero must not be silently replaced by 1.

The synthetic request `B5 14 08 00 34 12` has extent 6 and raw pressure 4660.
The synthetic positive abstract object
`F5 14 08 00 01 00 00 01 34 12 00 64 00` has extent 13: raw pressure 1,
minimum 256, maximum 4660, step zero and flow 1.0 l/min (`64 00` / 100).
These values exercise representation only; no meaning is assigned to the
command or feedback zero. A 12-position object is incomplete, even for a field
whose own bytes are present; retain the partial raw object without admitting
it as a complete positive. It does not replace a last-known-good complete value.

**Hypothesis — named 09:** only B5 request and F5 positive at logical zero are
supplied. Secondary, operation, body and complete extent are Unknown/absent.
No encoded 09 or executable form follows from the label. This limited evidence
does not establish the broader header-only candidate in the existing page.

**Unknown:** no physical qualification, adaptation, enforced cessation or peer
side effects follow from any row. Preserve unknowns and raw alternatives;
incomplete or ambiguous declarations cannot establish permission to execute.
