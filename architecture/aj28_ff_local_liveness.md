# AJ28: independent local liveness and reset transitions

Refs helianthus-docs-ebus#835 and helianthus-docs-ebus#736 (partial child;
the parent remains open).

## Evidence boundary

**Hypothesis:** this is a bounded local software candidate, not an implemented
runtime feature. The public native contract is [eBUS service FF](../protocols/ebus-services/ebus-service-FFh.md),
particularly its NM state machine, Start flag, FF01 and FF02 sections. That page
is native context, not proof of this local projection. Its NMInit/NMReset/NMNormal
diagram is not the two-state abstraction below. Existing native FF01/03..06
corrections and truncated-body work are outside this slice.

The issue supplies the candidate rules and [synthetic scenarios](fixtures/aj28_ff_local_liveness.json).
No native captures or qualified peer results are supplied. **Unknown:** native
behavior, physical delivery, qualified peer behavior, longest-cycle duration,
FF query bodies, physical emission policy, and any unprovided property. Synthetic
assertions prove only consistency of these artifacts; they do not promote the
candidate to Proven or qualify hardware.

## Local state and liveness

Ages are synthetic elapsed units, not a configured timeout. Refresh means setting
only the associated participant's age to zero; every other age retains its last
known value. Sender, destination and response-associated participant are distinct
axes. Destination addressing alone never supplies a sender observation. A
successful response uses its associated participant, not automatically the sender
or destination. Missing association remains partial and refreshes nobody.
CRC validity qualifies a transaction; response success is a separate predicate.
The observation direction is retained metadata, not a new wire-direction rule.

| Event | Predicate | Associated identity | Age effect | Grade |
|---|---|---|---|---|
| transaction | crc_valid=true | sender | refresh associated only | Hypothesis |
| transaction | crc_valid=false | sender | retain all | Hypothesis |
| transaction | crc_valid=unknown | sender | retain all | Hypothesis |
| response | success=true | participant | refresh associated only | Hypothesis |
| response | success=false | participant | retain all | Hypothesis |
| response | success=unknown | participant | retain all | Hypothesis |
| destination_only | any | destination | retain all | Hypothesis |
| eligible observation | association absent | none | retain all | Hypothesis |

Startup/trust and runtime active are independent booleans. Reset does not make an
active participant inactive or an inactive participant active. Clear-count below
is a synthetic witness of a true-to-false transition, not a runtime counter.
A reset re-arms the flag; longest-cycle has one clearing effect per reset epoch.
There is no inferred timer duration or physical scheduling decision.

| Event | Predicate | Startup after | Active after | Reset-state after | Dynamic configuration after | Clear-count delta | Grade |
|---|---|---|---|---|---|---|---|
| reset | any | true | retain | reset-state | retain | 0 | Hypothesis |
| longest_cycle | startup=true | false | retain | retain | retain | 1 | Hypothesis |
| longest_cycle | startup=false | false | retain | retain | retain | 0 | Hypothesis |
| initialize | any | retain | retain | normal | retain | 0 | Hypothesis |
| ff01 | any | retain | retain | retain | empty | 0 | Hypothesis |
| ff02 | responder=true | retain | retain | retain | retain | 0 | Hypothesis |
| ff02 | responder=false | retain | retain | retain | retain | 0 | Hypothesis |

FF01's row isolates configuration erasure; it does not replace or deny the native
command's other effects. The reset row models receipt of reset; initialization
moves reset-state to normal. The sequence initialization/reset/initialization
from reset-state therefore yields normal/reset-state/normal. These local labels
do not redefine native states or specify a sender implementation.

| Candidate variant | Responder available | NN | Data | Grade |
|---|---|---|---|---|
| FF02 | true | 0 | empty | Hypothesis |
| FF02 | false | 0 | empty | Hypothesis |

## Preservation and admission

Preserve each raw synthetic observation unchanged beside its partial result.
Unknown ages and unrelated last-known-good ages survive ineligible events;
configuration clearing does not erase those observations. Liveness, startup,
active, reset-state and configuration are distinct outcomes, not interchangeable
presence, trust, capability or qualification claims. No scenario grants execution
admission. Admission remains fail-closed. This slice changes no NM sender,
runtime state machine, MCP contract or GraphQL contract; it defines no new API.

This is pre-1.0 candidate documentation with no stability promise, new namespace,
polling default, active bus request or control execution. The standard-library
test checks the page tables and fixture independently, including rejected altered
contracts. No live or transport qualification follows from those checks.
