# AGENTS

This file is the complete contributor and agent policy for this repository. It
does not depend on instructions, skills, paths, or configuration outside this
checkout.

## Repository Scope

`helianthus-docs-ebus` is the public documentation repository for eBUS wire
behavior, eBUS device and vendor knowledge, and the Helianthus components that
implement or expose eBUS behavior. Keep implementation-neutral wire and data
type material under `protocols/` and `types/`; keep Helianthus architecture,
API, deployment, and development material in their corresponding directories.

Do not use this repository as the default home for unrelated protocols. Put
protocol-native knowledge in that protocol's corresponding public docs
repository. Cross-protocol material belongs here only when it documents an
explicit Helianthus platform boundary and keeps each protocol's native evidence
and ownership visible.

## eBUS-Native Evidence Rules

1. Separate eBUS wire evidence from implementation behavior. A Helianthus,
   `ebusd`, or VRC Explorer implementation is corroborating implementation
   evidence, not by itself proof of the native wire contract.
2. Prefer primary evidence: official specifications or vendor documentation,
   reproducible captures, raw telegrams, register dumps, and repeatable device
   observations. Cite the exact source or artifact.
3. Preserve the native identity of a claim. For B524, record
   `(opcode, group, instance, register)` and never merge OP=0x02 and OP=0x06
   namespaces merely because group or register numbers match.
4. For observed behavior, include enough context to falsify the claim: source
   and destination, PB/SB or service, payload/register bytes, direction, data
   type and unit when known, device/product and firmware context when known,
   capture conditions, and provenance.
5. Label conclusions as `Proven`, `Hypothesis`, or `Unknown`. Keep candidate
   mappings distinct from supported mappings, and state conflicting evidence
   rather than averaging it away.
6. Do not infer writable behavior from readable values, one device from another,
   or protocol semantics from a UI label without native evidence. Never perform
   a live write merely to improve documentation without explicit operator
   confirmation at action time.
7. Preserve raw evidence beside semantic interpretation. Redact credentials,
   private network details, and personally identifying device data before
   publication.

## Workflow

1. Keep work scoped to one issue and one `issue/<id>-<slug>` branch based on
   current `origin/main`.
2. Keep at most one active implementation PR for this repository. Use
   squash-and-merge only when a merge is explicitly requested and all gates are
   green.
3. Documentation-only work does not require RED-first TDD. Add or update
   validators when a mechanically enforceable contract changes.
4. Run `./scripts/ci_local.sh` and `git diff --check` before pushing. Report the
   exact commands, outputs, commit SHA, and PR state.
5. Review material claims against the evidence rules above. Resolve P0-P2
   findings and rerun review against the exact current HEAD; triage lower
   severities without misreporting them as blockers.
6. Do not merge, deploy, mutate live equipment, publish secrets, or expand into
   another repository unless the operator explicitly requested that boundary.

## VRC Explorer And Portal Boundary

VRC Explorer is not deprecated. It is a standalone, community-facing eBUS and
`ebusd` exploration tool. The gateway Portal may replace selected internal
Helianthus workflows that need gateway-native projections, provenance,
snapshots, or issue bundles; it does not replace VRC Explorer as a standalone
product or community tool.
