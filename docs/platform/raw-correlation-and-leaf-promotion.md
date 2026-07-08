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

### Correlation Keys

Every candidate correlation record must carry:

| Field | Meaning |
| --- | --- |
| `candidate_id` | Stable local identifier for the candidate dossier. |
| `leaf_path` | Proposed protocol-agnostic semantic leaf path; candidate-only before M8.5. |
| `eebus_ref` | Raw eeBUS evidence ref with runtime, contract, tool/scope, mask tier, and auth scope. |
| `ebus_source_family` | B509, B524, B555, or other source family; exact opcode/register identity when applicable. |
| `myvaillant_evidence_id` | Optional publishable evidence ID for app-visible or API-visible observations. |
| `comparator_id` | Versioned comparator definition, including units, tolerance, cadence, and stale policy. |
| `coexistence_bundle_id` | Evidence that eeBUS observation did not perturb eBUS runtime behavior. |
| `replay_bundle_id` | Replay artifact able to regenerate the candidate result. |
| `redacted_hashes` | Hashes of raw inputs and normalized candidate output. |
| `status` | `draft`, `rejected`, `coexistence_proven`, `locked`, or `superseded`. |

Field names in code may differ by package convention, but the same information
must be reviewable in the dossier before promotion.

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
| eBUS | B509/B524/B555 opcode/register identity |  |  |
| myVaillant | app/API observation ID, if used |  |  |

## Evidence Inventory

| Evidence ID | Source | Capture window | Mask tier | Data hash | Replay ID |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

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

- eBUS baseline bundle:
- eeBUS-enabled bundle:
- Drift checks:
- Anti-leak checks:
- Existing consumer smoke result:

## Replay Regeneration

- Replay command or tool:
- Expected output hash:
- Actual output hash:
- Determinism result:

## Security And Privacy

- Public evidence only:
- `vendor_restricted` quarantine checked:
- Redaction/mask tier checked:
- Raw eeBUS field anti-leak checked:
- Mutable-proof appendix required: yes/no

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
