# Raw Correlation And Leaf Promotion

Canonical source: this page.

Plan provenance:
`helianthus-execution-plans/multi-runtime-semantic-platform.draft`, MSP-02C.

## Purpose

This contract defines how Helianthus may compare raw eeBUS evidence with
existing eBUS and myVaillant observations without turning that comparison into
consumer-facing semantics. It also defines the Leaf Promotion Dossier that is
required before any correlated leaf can move from raw/candidate evidence into
GraphQL, Portal, Home Assistant, command routing, or the semantic registry.

## Scope

This page covers:

- raw correlation policy for eeBUS/eBUS/myVaillant evidence;
- anti-leak rules between raw eeBUS and existing eBUS/semantic surfaces;
- required evidence fields for candidate facts;
- the Leaf Promotion Dossier template;
- mutable-proof constraints for any future write-capable validation.

This page does not define:

- SHIP/SPINE protocol facts or VR940f device facts;
- eBUS B509/B524/B555 register semantics;
- runtime capture format beyond the raw evidence refs already defined by
  `helianthus-eebusreg`;
- GraphQL, Portal, Home Assistant, or command-routing schemas.

eeBUS-native protocol and device evidence lives in `helianthus-docs-eebus`.
Durable cross-protocol promotion rules and consumer rollout gates live here.

## Raw Correlation Policy

Raw correlation is evidence comparison only. It may create candidate facts in
M7, but candidate facts do not promote leaves. M8 proves coexistence. M8.5
locks individual leaves through a completed dossier.

Correlation input may include only publishable evidence:

- redacted eeBUS evidence refs from `eebus.v1.*` or replay bundles;
- existing read-only eBUS evidence, including B509/B524/B555 source-family
  identity;
- user-visible myVaillant observations recorded as publishable evidence IDs;
- redacted hashes and replay outputs generated from the same capture window.

Correlation input may not include `vendor_restricted` material in public
repositories, public issues, public PRs, public review comments, or public ADR
rationale. Private notes can guide local investigation, but public claims cite
only publishable evidence IDs.

### Anti-Leak Rule

No raw `eebus.v1.*` field, label, entity, service, feature, path, evidence ref,
or candidate fact may be merged into:

- `ebus.v1.*` MCP outputs;
- GraphQL outputs;
- Portal outputs;
- Home Assistant outputs;
- command-routing decisions;
- `helianthus-ebusreg` registry, projection, or semantic outputs.

The only permitted bridge before M8.5 is a candidate correlation record that
stores source evidence, comparator parameters, pass/fail results, terminal
negative states, replay references, coexistence evidence, and redacted hashes.

### Candidate Status

Candidate status controls which evidence fields are mandatory:

| Status | Meaning | Coexistence evidence |
| --- | --- | --- |
| `draft` | Correlation is being investigated. | Optional; use `pending` or omit. |
| `rejected` | Comparator or terminal negative state disproved the candidate. | Optional; include when rejection depends on coexistence evidence. |
| `coexistence_proven` | M8 has shown no eeBUS/eBUS runtime drift for this leaf. | Required. |
| `locked` | M8.5 dossier is accepted for promotion. | Required. |
| `superseded` | Replaced by a newer candidate or dossier. | Preserve previous value if one existed. |

### Correlation Keys

Every candidate correlation record must carry the fields below. Fields marked
`pending` are allowed only for `draft` or `rejected` candidates and must be
resolved before `coexistence_proven` or `locked`:

| Field | Meaning |
| --- | --- |
| `candidate_id` | Stable local identifier for the candidate dossier. |
| `leaf_path` | Proposed protocol-agnostic semantic leaf path; candidate-only before M8.5. |
| `eebus_ref` | Raw eeBUS evidence ref with runtime, contract, tool/scope, mask tier, and auth scope. |
| `ebus_source_family` | B509, B524, B555, or other source family; family-specific identity is defined below. |
| `myvaillant_evidence_id` | Optional publishable evidence ID for app-visible or API-visible observations. |
| `comparator_id` | Versioned comparator definition, including units, tolerance, cadence, and stale policy. |
| `coexistence_bundle_id` | Evidence that eeBUS observation did not perturb eBUS runtime behavior; `pending` only for `draft` or `rejected`. |
| `replay_bundle_id` | Replay artifact able to regenerate the candidate result. |
| `redacted_hashes` | Hashes of raw inputs and normalized candidate output. |
| `status` | `draft`, `rejected`, `coexistence_proven`, `locked`, or `superseded`. |

Field names in code may differ by package convention, but the same information
must be reviewable in the dossier before promotion.

### eBUS Source-Family Identity

The source-family identity must be precise enough to avoid collisions between
register families, target devices, and schedule namespaces.

| Family | Required identity fields |
| --- | --- |
| B509 | target address, target device/product identity when known, register family, register id, unit/scale source, and whether the value is authoritative or mirror/fallback evidence. |
| B524 | full opcode-scoped tuple `(opcode, GG, II, RR)`, target/source address context, group meaning, instance gate, register category, and unit/scale source. |
| B555 | device family, schedule/program identity, slot/day/time identity when applicable, operation mode context, and unit/scale source. |
| Other | protocol family, address/device context, exact read identity, unit/scale source, and evidence status. |

If a family-specific field is unavailable, the candidate remains `draft` or is
`rejected`; it cannot be locked with a generic "register identity" placeholder.

### Hash And Replay Comparability

Evidence hashes are comparable only when the binding fields match. Every
evidence row used for a candidate must therefore record:

- contract or schema version;
- tool id or replay tool id;
- snapshot scope;
- mask tier;
- auth scope;
- data timestamp or capture window;
- data hash;
- replay tool version;
- replay input bundle id;
- normalized output hash.

Missing binding fields keep the candidate in `draft` or `rejected`.

### Comparator Requirements

A comparator is not just a value equality check. It must define:

- source leaf identity on both sides;
- unit and scaling rules;
- sampling window and clock source;
- stale TTL and missing-data behavior;
- tolerance or exact-match rule;
- hysteresis or debounce, when applicable;
- pass count and fail count thresholds;
- conflict handling when sources disagree;
- terminal negative states that conclusively reject the candidate.

If any comparator parameter is unknown, the candidate remains `draft` or
`rejected`; it cannot be promoted by reviewer intuition.

### Terminal Negative States

Terminal negative states prevent accidental promotion from partial matches.
Examples include:

- eeBUS leaf absent while the eBUS source family is live and stable;
- eBUS leaf absent while eeBUS reports a stable but incompatible path;
- unit mismatch that cannot be normalized without undocumented assumptions;
- value moves in opposite direction across a controlled state transition;
- coexistence proof shows eBUS behavior drift after eeBUS runtime activation;
- replay cannot regenerate the candidate output from the recorded evidence.

Rejected candidates remain useful evidence. They must stay out of consumer
outputs and may be retained only as raw/candidate records.

## Leaf Promotion Dossier Template

Each promoted leaf needs one dossier. A dossier may start in M7, but promotion
is locked only in M8.5 after coexistence evidence exists.

```markdown
# Leaf Promotion Dossier: <candidate_id>

Status: draft | rejected | coexistence_proven | locked | superseded
Owner:
Reviewers:
Target milestone:
Retest trigger:

## Candidate Leaf

- Proposed semantic leaf path:
- User-visible meaning:
- Read-only or mutable:
- Consumer targets after lock:

## Source Identity

| Source | Identity | Evidence ID | Notes |
| --- | --- | --- | --- |
| eeBUS | entity/service/feature/path |  |  |
| eBUS B509 | target address; device/product identity; register family; register id; unit/scale source; authoritative or mirror/fallback |  |  |
| eBUS B524 | `(opcode, GG, II, RR)`; target/source address context; group meaning; instance gate; register category; unit/scale source |  |  |
| eBUS B555 | device family; schedule/program identity; slot/day/time identity; operation mode context; unit/scale source |  |  |
| eBUS other | protocol family; address/device context; exact read identity; unit/scale source; evidence status |  |  |
| myVaillant | app/API observation ID, if used |  |  |

## Evidence Inventory

| Evidence ID | Source | Contract/schema | Tool/scope | Mask tier | Auth scope | Capture window | Data hash | Replay tool/version | Replay input | Output hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |

## Comparator

- Comparator ID and version:
- Units and scaling:
- Sampling cadence:
- Clock source:
- Stale TTL:
- Missing-data behavior:
- Tolerance:
- Hysteresis/debounce:
- Pass threshold:
- Fail threshold:
- Conflict rule:

## Pass/Fail Results

| Run ID | Input evidence | Result | Reason |
| --- | --- | --- | --- |
|  |  | pass/fail |  |

## Terminal Negative States

- Negative state:
- Evidence ID:
- Disposition:

## Coexistence Evidence

- Required for `coexistence_proven` and `locked`:
- eBUS baseline bundle:
- eeBUS-enabled bundle:
- Drift checks:
- Anti-leak checks:
- Existing consumer smoke result:

## Replay Regeneration

- Replay command or tool:
- Replay tool version:
- Replay input bundle:
- Expected output hash:
- Actual output hash:
- Determinism result:

## Security And Privacy

- Public evidence only:
- `vendor_restricted` quarantine checked:
- Redaction/mask tier checked:
- Raw eeBUS field anti-leak checked:
- Mutable-proof appendix required: yes/no

## Mutable-Proof Appendix

Required only when the candidate leaf is mutable.

- Lab lease:
- Exclusive writer proof:
- Gateway/router write path proof:
- Direct adapter writes excluded:
- Abort conditions:
- Rollback verification per cycle:
- Perturbation cycle 1 evidence:
- Perturbation cycle 2 evidence:
- Perturbation cycle 3 evidence:
- Consumer mutable-control gate:

## Promotion Decision

- Decision:
- Locked semantic leaf:
- Linked docs PRs:
- Linked code PRs:
- Rollback plan:
```

## Mutable-Proof Appendix

Any mutable proof is a separate gate. The dossier may not authorize writes
unless all of these conditions are satisfied:

- lab lease is recorded;
- exactly one writer is active;
- writes go through the gateway/router path only;
- no direct adapter writes are used;
- abort conditions are explicit before the run starts;
- rollback verification runs after every cycle;
- three independent perturbation cycles pass;
- no consumer-facing mutable control ships before the promotion lock and
  command-routing gate.

## Cross-Seeding Rules

`helianthus-docs-eebus` may keep eeBUS-native RE notes, VR940f observations,
and SHIP/SPINE device details. When those observations become durable
cross-protocol promotion knowledge, the dossier or summary must be cross-linked
from this platform page or from a future platform docs repository.

eBUS register facts remain under `helianthus-docs-ebus/protocols/`. eeBUS
device facts remain under `helianthus-docs-eebus`. The dossier is the bridge;
it is not a new protocol registry.
