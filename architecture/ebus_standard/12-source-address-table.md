# eBUS Source Address Selection Table

Status: Normative
Milestone: SAS-01 M1
Table owner: `helianthus-docs-ebus`

## Purpose

This chapter freezes the standard eBUS source-address table used by
Helianthus source-address selection code. The table is protocol data, not a
gateway policy: consumers may filter or order it, but they must not rewrite the
standard rows or infer device intent from priority alone.

## Official Spec Evidence

This table is derived only from local official specifications in the workspace
corpus:

- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:28-60`
  for the 25 source-capable address rows and free-use note.
- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:69-77`
  for companion-address reservation examples.
- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_12_V1_3_1_E.en.md:178-184`
  for the companion-address arithmetic.
- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_12_V1_3_1_E.en.md:254-256`
  for the source-address and arbitration role.
- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_12_V1_3_1_E.en.md:320-349`
  and `/Users/razvan/Desktop/Helianthus Project/docs/SRC/Spec_Prot_12_V1_3_1_E.md:320-349`
  for the priority-class and sub-address split.
- `/Users/razvan/Desktop/Helianthus Project/docs/Spec_Prot_12_V1_3_1_E.en.md:471-478`
  for the ACK/NACK byte context.

The checker in
[`scripts/check_source_address_table_against_official_specs.py`](../../scripts/check_source_address_table_against_official_specs.py)
validates these rows against the local official specs when
`HELIANTHUS_OFFICIAL_SPEC_DIR` is set. Repo-only CI uses a committed
official-derived fixture with source file hashes and line provenance instead
of comparing the table to itself.

## Semantics

- `Source` is the byte emitted as the source address of an active eBUS frame.
- `Priority index` is the p0..p4 source-address priority class.
- `Arbitration nibble` is the low nibble used for byte-oriented arbitration.
  Lower bus priority class wins on the wire: p0 / `0x0`, then p1 / `0x1`,
  p2 / `0x3`, p3 / `0x7`, and p4 / `0xF`. This does not define Helianthus
  preference order.
- `Official description summary` is a compact summary of the local official
  spec row. It is not an enum.
- `Canonical description` is the stable Helianthus enum-facing description.
- `Free-use` and `Recommended for` are separate fields. A recommendation never
  authorizes gateway startup selection by itself.
- `Companion` is the responder-side address derived by adding `0x05` to the
  source address modulo one byte; `0xFF` therefore maps to `0x04`.
- `0xFF` is valid in the `Source` column. In an ACK/NACK field, `0xFF` is a
  negative acknowledgement. Consumers must keep those contexts separate.

## Gateway Selection Policy

The standard table does not prescribe the Helianthus gateway startup order.
When no source description, priority index, or exact address is configured, the
gateway uses `HelianthusGatewayDefaultPolicy`:

1. p4 candidates: `0xFF`, `0x7F`, `0x3F`, `0x1F`
2. p3 candidates: `0xF7`, `0x77`, `0x37`, `0x17`, `0x07`
3. p1 candidates: `0x11`, `0x31`
4. p0 candidates: `0x00`

This is a Helianthus policy, not an eBUS priority claim. The p4 rows lose to
p0..p3 during bus arbitration; they are tried first because Helianthus wants
free-use or tool-like addresses before preallocated controller identities.

If gateway startup configuration supplies only a priority index, selection
filters `HelianthusGatewayDefaultPolicy`; it does not search every standard
row at that priority. If it supplies a standard source description, selection
uses only rows with that exact canonical description and optionally intersects
them with the configured priority index. Free-use recommendations remain
informational.

An exact source address uses `explicit_validate_only`: candidate search is
bypassed, but the selected source and companion must still pass availability
and active-probe validation before any normal gateway-owned bus-reaching path
can use them.

## Startup Admission Boundary

`helianthus-ebusgo` owns the reusable `SourceAddressSelector` mechanics and
the static table constants. `helianthus-ebusgateway` owns startup admission:
active probe, retry/quarantine, persistence metadata, operator recovery
surfaces, and admission status. `helianthus-ebusreg` remains admission-agnostic
and consumes only the source byte it is given.

Normal gateway-owned operations use only the admitted
`SourceAddressSelection.Source` after `active_probe_passed`. This includes MCP,
GraphQL, Portal explorer, semantic pollers/writers, schedulers, NM runtime, and
gateway-internal protocol dispatch. A redundant caller-provided source matching
the admitted source may be accepted as diagnostic input; a nonmatching source
is rejected on normal gateway-owned paths.

Only transport-specific diagnostic MCP requests may use a non-admitted source,
and only for one audited, non-persistent request that does not mutate the
admitted source.

`DEGRADED_SOURCE_SELECTION` is fail-closed. While it is active, Helianthus
originates no eBUS traffic: no scan, semantic polling, MCP/GraphQL bus invoke,
NM `FF 00`/`FF 02`, `0x07/0xFF`, or companion responder activity.

The only first-implementation pre-discovery validation probe is addressed
`0x07/0x04`, classified as `read_only_bus_load`, against a configured or
current bounded positive target. Startup admission must not use broadcast
`0x07/0xFE`, `0x0F` test commands, NM services, mutating services, memory
writes, full-range probes, SYN/ESC/broadcast destinations, the selected source,
or the selected companion as a validation target.

## Hash Contract

Table anchor: `#ebus-source-address-table-v1`

Table version: `ebus-source-address-table/v1`

Hash algorithm: SHA-256 over the exact Markdown table block from the header
row through the last data row, UTF-8 encoded, LF line endings, trailing spaces
stripped per line, and exactly one terminal LF. The heading and surrounding
prose are excluded.

Normalized table hash:
`e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103`

## eBUS Source Address Table v1

| Source | Priority index | Arbitration nibble | Official description summary | Canonical description | Free-use | Recommended for | Companion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0x00` | p0 | `0x0` | PC/Modem | PC/Modem | no | none | `0x05` |
| `0x10` | p0 | `0x0` | Heating controller | Heating regulator | no | none | `0x15` |
| `0x30` | p0 | `0x0` | Heating circuit controller 1 | Heating circuit regulator 1 | no | none | `0x35` |
| `0x70` | p0 | `0x0` | Heating circuit controller 2 | Heating circuit regulator 2 | no | none | `0x75` |
| `0xF0` | p0 | `0x0` | Heating circuit controller 3 | Heating circuit regulator 3 | no | none | `0xF5` |
| `0x01` | p1 | `0x1` | Hand programmer / Remote control | Handheld programmer / remote | no | none | `0x06` |
| `0x11` | p1 | `0x1` | Bus interface / Climate controller | Bus interface / climate regulator | no | none | `0x16` |
| `0x31` | p1 | `0x1` | Bus interface | Bus interface | no | none | `0x36` |
| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x76` |
| `0xF1` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0xF6` |
| `0x03` | p2 | `0x3` | Burner controller 1 | Combustion controller 1 | no | none | `0x08` |
| `0x13` | p2 | `0x3` | Burner controller 2 | Combustion controller 2 | no | none | `0x18` |
| `0x33` | p2 | `0x3` | Burner controller 3 | Combustion controller 3 | no | none | `0x38` |
| `0x73` | p2 | `0x3` | Burner controller 4 | Combustion controller 4 | no | none | `0x78` |
| `0xF3` | p2 | `0x3` | Burner controller 5 | Combustion controller 5 | no | none | `0xF8` |
| `0x07` | p3 | `0x7` | empty | Not preallocated | yes | none | `0x0C` |
| `0x17` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x1C` |
| `0x37` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x3C` |
| `0x77` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x7C` |
| `0xF7` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0xFC` |
| `0x0F` | p4 | `0xF` | Clock module / Radio clock module | Clock/radio-clock module | no | none | `0x14` |
| `0x1F` | p4 | `0xF` | Burner controller 6 recommendation | Not preallocated | yes | Combustion controller 6 | `0x24` |
| `0x3F` | p4 | `0xF` | Burner controller 7 recommendation | Not preallocated | yes | Combustion controller 7 | `0x44` |
| `0x7F` | p4 | `0xF` | Burner controller 8 recommendation | Not preallocated | yes | Combustion controller 8 | `0x84` |
| `0xFF` | p4 | `0xF` | PC | PC | no | none | `0x04` |
