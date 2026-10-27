# AD10 migration equivalence comparison records

Status: proposed offline comparison design for AD10, “Migration preserves
semantics”. No comparison has been executed by this document. All synthetic
cases below have actual results **Not run**, evidence grade **Unknown**, and
qualification **unassessed**. Nothing is stable before Helianthus 1.0.

This is a partial contract slice for docs-ebus #676, advancing
[docs-ebus #250](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/250)
and [gateway #476](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/476).
AD10 hardware acceptance remains at
[gateway #1099](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1099).
This page specifies comparison records, not a migration or capture procedure,
runtime interface, profile admission, or parent closure.

## Pairing in the transport matrix

The standalone proxy is deprecated. The baseline side of a pair is the
configuration that the multiplexer replaces on the same southbound transport:
the direct adapter transport or ebusd-tcp. In the single hardware session that
retires the proxy topologies, the proxy route itself is attached once more as
an additional baseline. Each baseline observation carries its actual topology
label (`direct`, `ebusd-tcp` or `proxy`) and its own route identity; none is
aliased to `proxy`. The `adapter_direct` side is the multiplexer. The gateway
transport matrix runs one AD10 pair per supported southbound transport; this
page defines how each pair is compared.

## Current sources and limits

The following are current documentary contracts, not newly executed evidence:

| Source | What it supports here | Limit or conflict |
|---|---|---|
| [AD evidence index](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/development/ad01-ad12-evidence-index.md) | AD10 has no identified migration equivalence test; MCP/GraphQL parity and same-family conditions remain obligations. | AD numbers in the multiplexer architecture are a different namespace. No indexed row is certified. |
| [Migration guide](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/deployment/adapter-direct-migration.md) | Semantic zones, DHW and boiler checks; mutually exclusive routes; restart is acceptable. | “Valid data” alone does not establish field equality, provenance or freshness. Rollback is separate AD11 work. |
| [Multiplexer architecture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/adapter-direct-multiplexer.md) | Active/passive/external paths and reset clearing of pending work. | INFO retention conflicts with the native contract as noted by the index; the logical-byte wording is resolved by the wire-symbol contract. Historical live claims do not fill this comparison. |
| [Native ENH](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/enh.md) | Physical SEND/RECEIVED bytes, escape handling, INIT timeout and INFO invalidation on RESETTED. | Implementation descriptions cannot override these wire rules. |
| [Native ENS](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/ens.md) | Prefix/framing scope and separation from the data-only serial codec. | A data-only codec cannot supply missing ENH control events. |
| [MCP](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/api/mcp.md) | Existing semantic tool inventory, deterministic envelopes, discovery provenance distinct from verification. | Does not define the comparison record proposed below. |
| [GraphQL](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/api/graphql.md) | Current nullable semantic fields, startup state, incremental merge, retained DHW expiry, discovery provenance and route-specific initiator status. | Merged values alone do not expose complete per-field native receipt lineage or freshness. |

All record members and comparison decisions below are **proposed future work**
for an offline evaluator. They are not added MCP or GraphQL fields. Source
inspection supports their design rationale; it does not prove implementation.
No unmerged companion specification or implementation is a prerequisite.
There is no new namespace, authentication, principal or permission check.

## Pair identity and source correspondence

Define a public synthetic family fixture with a fixed semantic state vector,
explicit schema/mapping baseline, units, deterministic event sequence, virtual
clock and freshness/retention thresholds. Publish families, not individual
models. Use ordinal events and relative virtual durations, not capture times.
Any fixture content digest must be computed from the fixture bytes; a digest
alone neither proves lineage nor supplies a missing receipt.

A proposed pair record contains:

| Record part | Required content |
|---|---|
| Pair key | `comparison_id`, `case_id`, family fixture identity and revision, state-vector identity, candidate generation, comparison-policy revision and schema/mapping baseline. |
| Two sides | Exactly one baseline observation (topology label `direct`, `ebusd-tcp` or `proxy`, with its route identity) and one `adapter_direct` observation, each with its own immutable observation ID, source generation, session/reset epoch, ordered event IDs and virtual read point. They replay the same fixture state under the declared route. |
| Correspondence | Explicit one-to-one rows mapping each side's source identity to one fixture source role and semantic entity/field. Include eBUS source and destination, direction, PB/SB or service, native operation key and expected data type/unit. For B524 the key includes opcode, group, instance and register; OP=0x02 and OP=0x06 are distinct. |
| Generation binding | A frozen pair manifest binds each route-local source generation and reset epoch to this candidate generation. IDs need not be equal across routes; their correspondence must be declared before actual results are inspected. |
| Baseline | Detached expected field results derived from the declared fixture state and cited contracts, not copied from either observed route. Unknown native mappings remain Unknown and cannot become an equivalence oracle. |

Reject an artifact from another candidate generation or a source generation not
bound to that side in the manifest, even if its values, bytes or digest match.
Do not relabel an old receipt as the new generation, or join one side's current
values with the other side's earlier metadata. A reset starts a new epoch;
post-reset evidence requires a separately bound pair at that epoch. History
may reference an earlier epoch explicitly, but cannot complete current work.

Family identity alone is insufficient correspondence. Source-role ambiguity,
one-to-many aliases without explicit ownership, absent mapping evidence, or a
changed native operation key makes the affected comparison unresolved. This is
fail-closed acceptance of evidence, not a change to ENH's bounded fail-open
INIT timeout behavior or an authorization gate.

## Native receipt lineage and retained state

Keep immutable raw/native artifacts separate from interpreted values and API
responses. For each route retain the synthetic request/response bytes or
explicit absence, direction, source/destination, service, framing layer,
ordered events, completion/error/timeout, epoch and receipt IDs. Identify the
family and firmware context when publicly known; use Unknown when absent.
Synthetic bytes are fixture evidence, not observed device behavior.

Each semantic field points through its decoder/mapping baseline to its own
native receipt and source correspondence row. An aggregate with several
receipts lists each dependency rather than borrowing a neighboring field's
lineage. API responses reference their producing observation/read point.
Where the current surface lacks lineage or freshness fields, retain this
information in an offline sidecar; mark unavailable proof Unverified. Do not
invent API provenance members or infer provenance from numerical equality.

The proposed evaluator records these transitions without implementing them:

| Event | Required comparison treatment | Current basis / remaining gap |
|---|---|---|
| Successful field update | Bind new value to the completing receipt and current epoch. Preserve other retained fields separately. | GraphQL incremental merge; precise MCP field/envelope mapping still needs an executable baseline. |
| Semantic request timeout or partial response | Record failed attempt independently; retained fields retain their old receipt and age. No new receipt or fresh value is manufactured. | GraphQL merge/retention; exact error representation must be supplied for each current surface. This is not an INIT timeout. |
| Retention expiry | Compare explicit absent DHW after its declared TTL with the independently specified baseline. Do not apply DHW TTL to every plane. | GraphQL startup/retention contract; other field policies need separate evidence. |
| RESETTED | Clear pending work; mark discontinuity; forbid late completion crossing the epoch. Keep historical semantic last-known-good evidence visibly old. Invalidate INFO per native ENH. | Architecture reset propagation and ENH INFO rules. Architecture INFO retention conflicts remain unresolved; no aggregate reset PASS until resolved. |
| Recovery | New receipts can update fields only in their bound new epoch; missing siblings retain their own history. | Proposed comparison rule motivated by reset and incremental merge; cross-route recovery proof remains absent. |

Last-known-good evidence is never deleted because a newer pair is incomplete or
fails. Keep its original scope, generation, grade and result. It cannot qualify
the newer candidate, turn stale data fresh, or authorize any live write.

## Allowed normalization and non-normalizable fields

Keep both raw responses and a separate comparison view with an explicit log of
every transformation. Allowed transformations are JSON object-member ordering,
schema-documented MCP/GraphQL path correspondence, exact numeric lexical
equivalence such as `21` and `21.0`, and reordering only collections whose
contract is unordered, keyed by the full declared entity identity. Preserve
duplicates as errors rather than discarding them. Any unit conversion needs an
explicit exact rule and independent expected result; the cases here use the
same units and no rounding tolerance. Never infer generic recursive case
conversion for semantic payloads without the current schema mapping.

These are **non-normalizable**: candidate/source generations, reset epochs,
source-role correspondence, native operation keys and direction, raw bytes and
framing/control events, receipt lineage, units/precision, quality/freshness,
retention age, missing/null/unknown/zero/false distinctions, errors, and evidence
grade. Raw transport wrapping may differ by route but cannot be erased from
the evidence or used to excuse changed decoded wire meaning. ENH physical
escape bytes and logical data remain separate layers.

Route labels, session/receipt IDs, request correlation, virtual read positions,
MCP envelope timestamps/hashes and route-specific transport status need not
be byte-equal across sides. Compare them against each side's independent
expected values and lineage, not by deleting them. Compute any expected hash
using that surface's documented serialization; do not compare whole-response
hashes as a substitute for field results. Preserve deterministic envelopes and
raw GraphQL `data`/`errors`; do not wrap GraphQL in an MCP-shaped envelope.

## Per-field MCP and GraphQL expectations

For every selected field, record separate expected and actual MCP and GraphQL
paths, presence, type, value, unit, outcome/error, read point, receipt lineage
and evidence grade for each route. The following is a **proposed fixture
baseline**, not a claim that current MCP payload member spelling has been
verified. MCP tools are current inventory names; their precise member paths
must be bound from the current surface before executable acceptance. An
unbound path blocks that field; it is never treated as absent data. The
GraphQL prefixes `zones`, `dhw` and `boilerStatus` below are proposed selection
bindings to the documented `Zone`, `Dhw` and `BoilerStatus` types. The current
API page does not enumerate these query roots in its partial Query excerpt;
confirm the executable selection and schema before using them as actual paths.

| Fixture field | MCP expectation for both routes | GraphQL expectation for both routes |
|---|---|---|
| One zone's identity / instance | `ebus.v1.semantic.zones.get`: fixture zone identity and instance `1`, exact member paths required. | `zones`: selected `id` matches that fixture zone, `instance = 1`; match entities before values. |
| Zone temperature | Same tool: temperature `21.5`, degrees Celsius, correct zone receipt. | `zones.state.currentTempC = 21.5` on the matched zone. |
| DHW temperature | `ebus.v1.semantic.dhw.get`: temperature `48`, degrees Celsius, DHW receipt. | `dhw.currentTempC = 48`. |
| Boiler flow temperature | `ebus.v1.semantic.boiler_status.get`: flow temperature `52`, degrees Celsius, boiler receipt. | `boilerStatus.state.flowTemperatureC = 52`. |
| Known zero / false | Respective semantic tool: present numeric `0` or boolean `false` with successful native lineage. | Selected nullable numeric/boolean field contains `0` / `false`, not `null`. |
| No known value / missing field | Preserve the surface's independently specified absent/null/error representation; no zero or false substitution. Exact MCP representation remains a baseline gap. | Requested nullable field is `null`; unselected field is outside comparison, not a missing-value observation. Record any GraphQL error separately. |
| Discovery origin / verification | Registry tools retain each face's `discovery_source` and independent `verification_state`; omitted for no slot. | Queried face's `discoverySource` / `verificationState` agree; no-slot nullable fields are `null`. Origin cannot be rewritten by verification. |
| Freshness / retained lineage | Compare sidecar age/receipt and any documented exposed metadata independently of the value. | Merged value plus startup state where available; do not assert a per-field freshness member exists. Require sidecar proof. |
| Deliberate route metadata | Route identity and correlation follow the declared baseline/direct side, not equality across routes. | `daemonStatus.initiatorAddress` may be `auto` for an auto-leased proxy and the configured synthetic source for direct; declare this condition in advance. |

These numbers are semantic fixture inputs, not register mappings or device
observations. No native encoding or writable behavior is inferred from them.
Before execution, attach public native mapping evidence for any proposed raw
payload-to-field relationship; otherwise that relationship remains Unknown.
Use the current MCP contract before GraphQL parity; do not add a second
provider, fallback or API solely to make comparison succeed.

## Synthetic comparison cases

Each row expands into the per-field records above on both routes and both
surfaces, including unchanged siblings. Expected decisions are independent of
actuals. For **every row here**, proxy MCP actual, proxy GraphQL actual, direct
MCP actual and direct GraphQL actual are **Not run**; each actual's evidence
grade is **Unknown**. Proposed expectations have grade **Hypothesis** until a
reviewed fixture/baseline is attached. No row is a reported PASS.

| Case | Independent expected values and lineage | Expected comparison decision if executed as specified |
|---|---|---|
| Success | Both routes deliver the zone/DHW/boiler baseline above from corresponding current-epoch receipts; each surface preserves its envelope. | Equivalent only after value, presence, type, unit, lineage and surface checks all succeed. |
| Timeout | Both semantic attempts time out with no prior value: no new semantic value or success receipt. Expected error/absence per surface must be bound before execution. | Matching error strings alone insufficient; missing error baseline is Unverified. A completed bounded timeout can satisfy a negative assertion; evaluator timeout is Unverified. |
| Stale retained value | Seed DHW `48`, then fail a field update before virtual TTL. Both retain `48` with original receipt and increased age; a successful zone update does not refresh DHW. After DHW TTL both clear DHW under its current contract. | Retained values can match while stale; cannot count as fresh success. Unknown age/receipt makes equivalence Unverified. |
| Reset boundary | Pending pre-reset request cannot complete post-reset. Old semantic evidence remains historical. New-epoch receipts required for recovered fields; old INFO invalidated. | Cross-epoch completion or retained INFO treated as current violates the native/reset assertion. Current INFO conflict stays unresolved. |
| Unknown versus zero | One subcase supplies no native value; another supplies known `0` (and known `false` for a boolean). Apply both to each route with corresponding surface selection. | Equivalent within each subcase only; coercing unknown to zero/false is a mismatch even if displayed values coincide. |
| Missing field | Omit one DHW field while zone and boiler succeed. With no prior value expect nullable GraphQL field `null` and bound MCP absence behavior; with a retained prior value apply its age/receipt policy. | Siblings may pass individually; missing required field proof prevents aggregate equivalence. An incomplete GraphQL selection is Unverified. |
| Route metadata | Proxy uses declared auto lease; direct uses declared configured synthetic source. Values match while raw route metadata differs as predicted. | Permitted route-specific difference only if both side-specific metadata expectations pass; blanket metadata stripping is invalid. |
| Equal values, wrong provenance | Direct reports `48` from another fixture role, native operation, candidate generation, source generation or epoch; proxy reports the legitimate DHW receipt. Vary each identity component independently. | Not equivalent; wrong role/key is a mismatch, foreign generation/epoch is rejected evidence. Value equality cannot repair either. |

The last row is a future negative-case design, not an executed mutation suite.
Changing opcode, group, instance or register separately must each break the
native-key check; changing candidate generation, side-bound source generation,
epoch or source-role association separately must each break its own lineage
check. None of those checks is implemented or claimed tested here.

## Result and acceptance discipline

A completed field record stores independent expected and actual values for all
four route/surface combinations, original artifact references, transformation
log, assertion outcome, evidence grade (`Proven`, `Hypothesis`, `Unknown`), and
qualification separately. Also record value comparison, provenance comparison,
and MCP/GraphQL parity as separate decisions. Equal scalar values with wrong
provenance are never real equivalence.

Use `Missing`, `Not run`, `PASS`, `FAIL`, or `Unverified` as the index does.
Only an executed assertion with checked artifacts may receive PASS; an executed
contradiction receives FAIL with its exact assertion. Absent artifacts,
unbound schema/native mappings, incomplete selection, evaluator timeout or
environment failure remain unresolved/Unverified. A deliberate invalid input
may pass a rejection assertion while remaining ineligible as equivalence
evidence. A synthetic PASS proves only its bounded implementation assertion,
not native device behavior, hardware qualification or runtime admission.

Before any aggregate equivalence result, require every mandatory field and
side-specific metadata assertion to pass, every lineage link to be checked,
and every difference to have a prior explicit rule. Preserve partial results
and historical last-known-good records when an aggregate is unresolved.

Remaining work includes executable fixtures and detached MCP member/error
baselines, native mapping/receipt evidence, both-route and cross-surface
results, reset conflict resolution, independent review, and separately
authorized AD10 hardware acceptance. The generic index, transport matrix and
consolidated handoff are unchanged. No full CI, transport execution, passive
capture, hardware smoke, profile qualification or parent acceptance is supplied
by document readability or manual source review.
