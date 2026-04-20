# M6a Transport Matrix — Cross-Reference

Status: Normative (pointer chapter)
Milestone: M6b_docs_publication_and_closeout
Plan reference: `ebus-standard-l7-services-w16-26.implementing/00-canonical.md`
Canonical SHA-256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`
Gateway anchor commit: `686dfaf0` (helianthus-ebusgateway#514, merged 2026-04-19)

## Purpose

The M6a transport matrix artifact is maintained in
`helianthus-ebusgateway` as the authoritative live-bus conformance record
for the `ebus_standard` L7 namespace. This chapter exists so operators
discovering `ebus_standard` via docs-ebus can locate the matrix without
having to infer its repository of origin.

This chapter is a **pointer**: it does not restate the matrix content and
MUST NOT diverge from it. Any conflict between the prose here and the
linked artifact is resolved in favour of the artifact.

## §1 — Location

The canonical transport matrix artifact lives at:

```
helianthus-ebusgateway/matrix/M6a-transport-matrix.md
```

Anchor commit at time of this chapter's lock: `686dfaf0`
(helianthus-ebusgateway#514).

The matrix is co-located with the gateway because it records live-bus
conformance behaviour emitted by the gateway's transport stack; drift
between the matrix and the running producer is detectable only against
that source tree.

## §2 — Section pointers

Within the matrix artifact, the following sections are the load-bearing
references for `ebus_standard` consumers and reviewers:

| Matrix section | Subject |
|---|---|
| §3 | Vaillant regression surface — confirms the `0xB5` provider namespace is unaffected by `ebus_standard` parallel operation. |
| §4 | NM wire behaviour — records observed initiator/responder dynamics against the adopt-and-extend NM plan. |
| §5 | Cadence floor — per-transport minimum inter-frame spacing observed on the live bus. |
| §6 | Rollback criteria — the conditions under which `ebus_standard` emission MUST be disabled at runtime via the M3 provider-contract disable switch. |
| §7 | BENCH-REPLACE obligation — operator follow-up on the BASV2 bench for synthetic-to-live fixture replacement. |

Consumers that need to reason about transport-conditional responder
capability SHOULD cross-read §5 (cadence) and §6 (rollback) together
with [`13-responder-capability-signal.md`](./13-responder-capability-signal.md)
§4 (fail-closed consumer rule) and §5.2 (`transport_mux_bypass` reason
semantics).

## §3 — BENCH-REPLACE status

At the time of this chapter's lock, matrix §7 carries the status marker
`PLACEHOLDER`. The bench-replacement obligation is deferred to an
operator BASV2 bench follow-up outside the cruise-run's merge scope. Once
the bench pass lands, the matrix §7 status flips from `PLACEHOLDER` to a
fixture-anchored entry; this chapter does NOT need to be amended for
that flip — the matrix is the source of truth and the link above already
resolves to the updated content.

## §4 — Amendment policy

This chapter amends only when:

- The matrix artifact's repository path changes.
- A new matrix section is introduced that `ebus_standard` consumers must
  cross-read (additive pointer row).

The matrix's own content evolves independently under the gateway repo's
review process and does NOT trigger amendments here.
