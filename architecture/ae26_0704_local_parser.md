# Bounded 0704 local representation and arithmetic

The [native service contract](../protocols/ebus-services/ebus-service-07h.md#bounded-0704-candidate-declarations)
comes first. **Hypothesis:** the following describes partial local software
behavior only. It grants no native qualification, physical BCD qualification,
freshness, installed support or execution authority. Nothing here is a stable
pre-1.0 interface.

| Grade | Property | Local declaration | Unresolved / conflict |
|---|---|---|---|
| Hypothesis | declared count | at least 10; no own upper bound | Native variable lengths Unknown |
| Hypothesis | available bytes | every access bounded by actual available bytes; at least 10 needed | A larger declared count cannot supply missing bytes |
| Hypothesis | identifier | exactly bytes 1..5; first byte nonzero; every byte 00 or 20..7E | Internal 00 permitted; native character domain Unknown |
| Hypothesis | numeric predicate | bytes 6..9: low nibble <=9 only; no high-nibble bound | Distinct from stricter physical BCD qualification |
| Hypothesis | decimal | 10*(byte>>4)+(byte&15) | Local arithmetic only |
| Hypothesis | major / minor | decimal(byte6) / decimal(byte7) | Native representation Unknown |
| Hypothesis | product number | decimal(byte8)+100*decimal(byte9) | Separate from major/minor; family predicates Unknown |
| Hypothesis | byte 0 | not consumed | Never a family selector in this partial parser |
| Hypothesis | 07FE | missing direct response is not identification failure | Separate identity from 0704 |

The [synthetic examples](../protocols/ebus-services/fixtures/ae26_07_candidates.json)
retain raw octets, absent results as null, and independent expected tuples.
The baseline `A1 41 42 43 44 45 F9 99 17 04` represents `ABCDE`, major 159,
minor 99 and product number 417. Here `F9` is admitted by the local predicate;
`FA` is invalid. This is not evidence that `F9` is physically qualified BCD.

| Case | Result | Identifier bytes | Major, minor, product |
|---|---|---|---|
| baseline | admitted | 41 42 43 44 45 | 159, 99, 417 |
| low_nibble_a | invalid | absent | absent |
| first_zero | invalid | absent | absent |
| internal_zero | admitted | 41 42 00 44 45 | 159, 99, 417 |
| below_character_domain | invalid | absent | absent |
| above_character_domain | invalid | absent | absent |
| byte_zero_changed | admitted | 41 42 43 44 45 | 159, 99, 417 |
| declared_nine | incomplete | absent | absent |
| declared_eleven | admitted | 41 42 43 44 45 | 159, 99, 417 |
| available_nine | incomplete | absent | absent |

These are declarative acceptance examples, not an implementation of a decoder.
Invalid or incomplete data provides no new identity: preserve raw evidence and
partial last-known-good state without admitting an unvalidated replacement.

The companion scope is exactly AE25's seven standard-family entries: 0704
response fields identifier, major, minor, product_number, version_control and
revision_control, plus the 07FE request existence_inquiry. Operation is absent
in each key. Logical positions and widths are absent except the controls'
logical positions 8 and 9; these positions are not parser offsets. A control
has not-okay domain 0..98, default not-okay and no declared okay values.
The identifier entry alone carries the partial local-parser metadata.
**Hold:** [AE25 companion PR](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/256)
for [issue #248](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/248)
was open in the supplied companion snapshot; its merge is not established here.
Do not assume a broader completed catalog.

Existing standard scanner/provider invocation is unchanged. Candidate metadata
never selects a family by itself. Family-specific overrides, local responders,
sweeps and follow-up writes are excluded. No eBUS MCP or GraphQL behavior is
changed; parity and compatibility receive no new runtime qualification here.
Native variable lengths, physical extra bytes, all family override predicates,
complete schemas for all seven services and installed support remain **Unknown**.
