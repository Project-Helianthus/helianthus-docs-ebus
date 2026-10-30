# AJ27: bounded local identity construction and scan variants

Refs #834; partial child of #736, which remains open. This pre-1.0 architecture
candidate is **Hypothesis**. Nothing here is a stable contract or physical
qualification. The supplied issue snapshot is the source for local software
facts; the [synthetic scenarios](fixtures/aj27_standard07_local_responder.json)
are examples, not captures.

The public native contract comes first: [service 07 identification](../protocols/ebus-services/ebus-service-07h.md#service-0x07-0x04--identification)
describes the standard ten-byte layout and separately grades the regulator-family
interpretation of its last two bytes as Hypothesis. This page describes only a
local construction candidate. It does not extend that native interpretation to
other families or qualify any physical identity. Native behavior remains Unknown.

## Local builder

| Field | Local candidate rule |
|---|---|
| direction | local_response |
| prefix | B5 |
| identifier | five raw bytes, in supplied order |
| versions | two decimal inputs, each packed decimal only within 0..99 |
| number | remainder modulo 100, then quotient divided by 100 narrowed to low 8 bits |
| data_bytes | 10 |
| grade | Hypothesis |

Identifier, version components, original number, remainder, full quotient and
narrowed quotient remain distinct fields. Do not discard raw input when a
semantic output is unavailable. For in-range decimal components the candidate
packs tens into the upper nibble and units into the lower nibble. For a decimal
component above 99, output behavior is **Unknown**, including after narrowing;
no truncation to two digits or assumed standard BCD is authorized.

| Example | Identifier hex | Versions decimal | Number decimal | Remainder | Quotient | Low 8 decimal | Output hex | Full local identity |
|---|---|---|---|---|---|---|---|---|
| ordinary | 41 42 43 44 45 | 12 / 34 | 417 | 17 | 4 | 4 | B5 41 42 43 44 45 12 34 17 04 | true |
| narrowed | 41 42 43 44 45 | 12 / 34 | 65535 | 35 | 655 | 143 | Unknown | false |
| short | 41 42 43 44 | 12 / 34 | 417 | 17 | 4 | 4 | Unknown | false |

“Full local identity” means only that this synthetic builder can construct all
ten bytes; it never means admitted, present or physically qualified.

## Separate lifecycles and selection

Two bounded local stores, `store_a` and `store_b`, and `shared_scratch` have
separate lifecycles. Exact capacities, copy ordering and short read completion
rules are **Unknown**. The fixture's transitions are proposed fail-closed
bookkeeping expectations, not recovered runtime algorithms. A clear affects only
the selected store; it does not imply clearing its sibling or scratch. A copy
with unprovided completion rules preserves prior useful state pending completion.
A short locally successful read preserves the partial raw bytes beside the
last-known-good identity and cannot promote full identity. Scratch reuse does
not establish either store's validity. Clearing selected state explicitly is
different from losing it as a side effect of an incomplete read.

GPIO-selected and conditionally imported identity are separate selection paths.
The actual import/override predicates and path precedence are **Unknown**. The
synthetic predicate result true/false/unknown is only an input for testing
conditionality; it does not define a GPIO mapping or recover an override rule.
Only a true supplied condition can select an import in that abstract example;
false or unknown withholds it. A setter does not imply persistence.

## Scan variants

These are independent bounded candidates; shared I/O/coupler ordering does not
merge them. Sweep cardinality is a counter, not an invented address list.

| Variant | Sweep count | Solar hex set | Secondary hex set | Controller jobs | Attempts per job | Maximum controller attempts |
|---|---|---|---|---|---|---|
| A | 230 | 06 ED EE EF F2 | FC 0A 12 | Unknown | Unknown | 7 |
| B | 0 | 06 | FC | 3 | 2 | 6 |

The full 230-entry destination set is **Unknown**. Maximum budgets are ceilings,
not required work: A allows zero through seven controller attempts; B allows
zero through three jobs with zero through two attempts per job, total at most
six. Eight attempts in A and seven in B are invalid. B's smaller solar and
secondary sets cannot inherit A's additional entries.

| Timing field | Value | Meaning |
|---|---|---|
| queue_seconds | 180 | queue_timeout |
| physical_response_seconds | Unknown | Unknown |

Mutative follow-up stays outside discovery. The existing low-nibble parser and
the 0704/07FE distinction are outside this slice. No responder, scanner, GPIO,
request path, polling default or control execution is implemented. These offline
checks establish no physical result or admission. eBUS MCP compatibility and
GraphQL parity remain unchanged; no surface, registration or schema is added.

## Unknown properties

Every item below remains Unknown independently of the candidate grade.

| Property | Grade |
|---|---|
| store_a_capacity | Unknown |
| store_b_capacity | Unknown |
| copy_ordering | Unknown |
| short_read_completion | Unknown |
| identity_override_predicates | Unknown |
| sweep_destinations | Unknown |
| decimal_above_99_output | Unknown |
| persistence | Unknown |
| physical_response_seconds | Unknown |

## Offline validation

The standard-library unittest checks the page tables and fixture against
independent arithmetic and transition expectations. It varies identifier byte
positions, both version components, the number split and narrowing, both store
targets, both selection paths and all three abstract predicate results, variant
budgets, set members, direction, grades and unknown properties. Mutated in-memory
contracts must be rejected while valid controls still pass. These are contract
regressions, not executed production mutants or runtime tests.
