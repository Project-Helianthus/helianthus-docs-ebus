# Lossless Modbus/SunSpec migration inventory

This is an AGPL-3.0 development inventory for issue #586, a partial slice of
parent #550. It authorizes no move, deletion, redirect, runtime change or live
qualification. The parent remains open until the companion and redirect work
has merged and both repositories validate.

## Recorded comparison snapshot and evidence status

All nine source pages and their docs-modbus counterparts were read from the
main branch of each repository at the time of writing; this change's history
records when. Links below are moving branch or repository-relative references,
not immutable historical content. Subsequent drift in either repository is
unverified; this recorded comparison snapshot does not establish current parity.
Exact private comparison coordinates may support orchestration but are not
publishable in this artifact.

The destination [native-owner statement](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) selects docs-modbus as
the canonical home for Modbus-family knowledge. The source
[README licensing scope](../README.md#licensing) still names Modbus;
that statement and its protocol-map link need a later, coordinated update.

`Proven` here means the stated text, overlap or absence is established in
the repository content inspected for this recorded snapshot. `Hypothesis` means a proposed merge destination
or resolution still requiring companion review. `Unknown` covers native
claims not independently established by these repository snapshots and future
merge/qualification state. Documentary evidence and observed structure do not
qualify a family, operation, endpoint, decoder or writable capability.

The inventory compares public documentation, not hardware. Existing native
claims must retain their cited source and limits; implementation behavior alone
must not promote them to Proven wire facts. The family names below are
navigation categories, not compatibility claims. Original exact observation
context remains in the linked public source, without republishing model or
firmware fingerprints here.

## Nine-page section comparison and destinations

Each row is a Proven comparison of text in the recorded snapshot. Proposed new paths and
merge actions are Hypothesis until reviewed and merged in docs-modbus. A
missing counterpart requires preservation and migration, never dropping facts.
No source page has an identical same-path destination in the inspected destination snapshot.

| Source page | Existing counterpart / canonical merge target | Section-level duplicate, unique and conflicting disposition |
| --- | --- | --- |
| [protocols/modbus/README.md](../protocols/modbus/README.md) | [README.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) | Entire index: duplicate purpose and CC0 scope; source uniquely groups the phase-one wire and four local references. Destination index has broader vendor coverage and an explicit native-owner statement. Merge navigation after the missing wire page exists; do not import application contracts. |
| [protocols/modbus/growatt-candidate-evidence-v1.md](../protocols/modbus/growatt-candidate-evidence-v1.md) | [protocols/growatt/protocol-ii-readonly-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/growatt/protocol-ii-readonly-v1.md) | Unheaded vendor-source paragraph: source uniquely contrasts incompatible product ranges; preserve that warning and inspection-only attribution. FC03 candidate paragraph: offsets/quantities duplicate destination Identity tuple, which additionally requires a coherent complete tuple. Final paragraph: proprietary-map/non-SunSpec disclaimer duplicates Scope. Destination uniquely defines encoding, serial slice, fail-closed admission, native/MCP identity, synthetic FC04 schema, and collision rules. Never broaden the narrow candidate to all source families. |
| [protocols/modbus/huawei-gateway-candidate-evidence-v1.md](../protocols/modbus/huawei-gateway-candidate-evidence-v1.md) | [protocols/huawei/gateway-readonly-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md) | Opening family distinction duplicates Scope. Address, numeric and string paragraphs duplicate Shared encoding. Candidate offsets and child request duplicate SmartLogger candidate, S-Dongle candidate, EMMA candidate and Child inventory. Preserve the source documentary-only/no-probing qualification. Destination uniquely adds exact applicability branches, complete tuples, stable inventory, pagination bounds, no fallback and default-denied private operations. A documentary offset is not a qualified operation. |
| [protocols/modbus/modbus-phase-one-wire-v1.md](../protocols/modbus/modbus-phase-one-wire-v1.md) | Missing complete counterpart; create the proposed native wire destination | License And Scope and its three official citations must migrate intact. Common PDU, FC03 And FC04, FC2B/MEI0E Request/Objects/Response, Modbus TCP ADU, and Modbus RTU ADU have no complete counterpart. Private Function Code Transport overlaps only bounded reads, exception correlation, extent checks and RTU integrity/timing; it uniquely defines transport admission/lifecycle policy and is not a replacement. Preserve the full neutral summary, including object limits, restart/progress behavior, TCP framing, CRC and serial timing. Proposed destination: `protocols/modbus/modbus-phase-one-wire-v1.md` (absent in the inspected destination snapshot). |
| [protocols/sunspec/README.md](../protocols/sunspec/README.md) | [README.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) | Entire index: duplicate reference-index purpose. Source uniquely exposes the two observation revisions and documentary catalog note. Destination index uniquely enumerates V1, V2, nested-layout, vendor and applicability contracts. Add links to preserved historical evidence before replacing this index. |
| [protocols/sunspec/additional-model-evidence-v1.md](../protocols/sunspec/additional-model-evidence-v1.md) | [protocols/sunspec/read-only-core-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md) | Unheaded catalog paragraph: meter and environmental groups and upstream pin duplicate Initial model catalog; documentary grid/control range 125–145 is unique and must remain separate from executable admission. Signature paragraph uniquely specifies FC03, offset and quantity; model-header/extent statements duplicate Chain structure. Destination uniquely gives exact decoder tuples, sentinels, value rules and rejection rules. Preserve the source no-device/no-control/no-write disclaimer. Proposed additional destination: `protocols/sunspec/additional-model-evidence-v1.md` for unique documentary facts, not an extension of the core catalog. |
| [protocols/sunspec/fronius-observed-flavor-v1.md](../protocols/sunspec/fronius-observed-flavor-v1.md) | [protocols/fronius/sunspec-float-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md) | Entire observation: source uniquely records the earlier ordered chain without Model 123 and its FC03/unit/signature context; the exact applicability tuple is shared evidence but is not republished here. Destination Exact chain geometry describes V1.1 with Model 123; Applicability and Read-only result uniquely add exact-match and downstream qualification constraints. These are distinct observations, not interchangeable duplicates. Proposed historical destination: `protocols/fronius/observed-chain-v1.md`; preserve original public evidence and provenance by citation without widening family support. |
| [protocols/sunspec/fronius-observed-flavor-v1-1.md](../protocols/sunspec/fronius-observed-flavor-v1-1.md) | [protocols/fronius/sunspec-float-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md) | Entire revision note: added 123/L24 duplicates Exact chain geometry. Source uniquely states the separate observation and prohibition on widening V1 to another device, firmware or acquisition configuration. Merge that provenance distinction and retain a link to the historical V1 record; never silently replace its chain. Destination uniquely contains full V1.1 geometry and qualification boundary. |
| [protocols/sunspec/sunspec-model-chain-v1.md](../protocols/sunspec/sunspec-model-chain-v1.md) | [protocols/sunspec/read-only-core-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md) | Opening upstream pin and Model occurrences: catalog pin, exact V1 lengths and Model 160 formula duplicate Initial model catalog; destination uniquely bounds counts and enumerates meter/environment lengths. Chain framing: order, occurrences, opaque unknown blocks, terminal marker and raw words duplicate Chain structure/Value rules; explicitly preserve nonzero pre-terminal lengths, checked arithmetic, no overrun and no trailing words. Final non-claims duplicate Safety and disposition. Destination uniquely adds typed-value rules, field equivalence and executable schema keys; preserve the distinction between neutral structure and decoder admission. |

## Conflicts and preservation decisions

- **Growatt scope versus general RTU addressing:** source family contrasts do
  not establish the destination's narrow Protocol II applicability. The native
  wire summary bounds addressed RTU units to 1–247, while the destination's
  Transport and addressing section says 1–254. This is an unresolved textual
  conflict, not permission to extend standard addressing. Companion review must
  retain both citations, resolve against native evidence and distinguish a
  vendor-specific exception if one is actually supported; admission stays
  fail-closed meanwhile.
- **Fronius revisions:** the earlier observation lacks the block added by
  V1.1. Preserve both ordered chains and separate provenance; the later flavor
  does not retroactively qualify the earlier observation or the family.
- **Catalog versus decoder:** documentary range 125–145 does not appear in
  the destination's admitted V1 catalog. That is a scope difference, not a
  missing decoder to enable. Preserve it as documentary-only. The separate
  [model-family guide](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1-model-families.md)
  adds topology explanations but does not admit this range; the
  [V2 contract](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v2.md)
  has a distinct revision and model scope and is not a replacement for V1.
- **Structure versus publication:** raw ordered occurrences, unknown blocks,
  checked extents and original public provenance must survive migration.
  A failed acquisition/admission must retain available native evidence and
  separately labelled partial last-known-good state; it must not turn stale or
  incomplete data into a newly admitted profile or partial successful publication.
  Keep the destination's stricter tuple and no-fallback rules.
- **Protocol versus implementation:** the
  [private-function transport contract](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/private-function-codes.md)
  contains separate selection, lifecycle and admission requirements. Its partial
  overlap does not replace the standard wire reference. This inventory makes no
  new transport claim.

## Every inbound-link location in the recorded source snapshot

The following exhausts tracked repository Markdown inline links resolving to
one of the nine pages, including links inside those pages. Locations use the
recorded source snapshot; anchors are part of the migration obligation. Labels mentioning a
source filename but resolving to an `architecture/` contract are not inbound
links to the nine pages and must keep that AGPL target.
External consumers and untracked material are Unknown; they need a companion
consumer audit before redirects. Citations in this inventory use moving branch or repository-relative references;
their destinations and anchors also require verification during migration.

| Inbound location | Source target and anchor | Later action |
| --- | --- | --- |
| [README.md:25](../README.md) | `protocols/modbus/README.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [architecture/protocol-routing-vendor-modbus-overview.md:5](../architecture/protocol-routing-vendor-modbus-overview.md) | `protocols/modbus/README.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [architecture/protocol-routing-vendor-modbus-overview.md:7](../architecture/protocol-routing-vendor-modbus-overview.md) | `protocols/modbus/modbus-phase-one-wire-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [architecture/protocol-routing-vendor-sunspec-overview.md:5](../architecture/protocol-routing-vendor-sunspec-overview.md) | `protocols/sunspec/README.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:33](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:95](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md#common-pdu` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:125](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md#fc2bmei0e-read-device-identification` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:139](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md#response` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:186](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md#modbus-tcp-adu` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-foundation-profile-contract-v1.md:287](../docs/platform/modbus-foundation-profile-contract-v1.md) | `protocols/modbus/modbus-phase-one-wire-v1.md#modbus-rtu-adu` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [docs/platform/modbus-multivendor-boundaries.md:212](../docs/platform/modbus-multivendor-boundaries.md) | `protocols/modbus/modbus-phase-one-wire-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/modbus/README.md:6](../protocols/modbus/README.md) | `protocols/modbus/modbus-phase-one-wire-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/modbus/README.md:8](../protocols/modbus/README.md) | `protocols/sunspec/sunspec-model-chain-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/modbus/README.md:10](../protocols/modbus/README.md) | `protocols/modbus/growatt-candidate-evidence-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/modbus/README.md:13](../protocols/modbus/README.md) | `protocols/modbus/huawei-gateway-candidate-evidence-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/sunspec/README.md:6](../protocols/sunspec/README.md) | `protocols/sunspec/sunspec-model-chain-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/sunspec/README.md:7](../protocols/sunspec/README.md) | `protocols/sunspec/additional-model-evidence-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/sunspec/README.md:8](../protocols/sunspec/README.md) | `protocols/sunspec/fronius-observed-flavor-v1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |
| [protocols/sunspec/README.md:9](../protocols/sunspec/README.md) | `protocols/sunspec/fronius-observed-flavor-v1-1.md` | Retarget to merged native destination; preserve section anchor or explicit replacement. |

## Non-link dependencies and publication lanes

The following are blockers to blind redirects, even where link text is valid.
The future companion must inventory downstream locks outside this checkout too.

| Pinned dependency | Obligation before redirect |
| --- | --- |
| [docs/platform/manifests/modbus-foundation-profile-contract-v1.json#L14](../docs/platform/manifests/modbus-foundation-profile-contract-v1.json) | Wire artifact path and digest bind actual content; a redirect changes contract bytes. Coordinate explicit contract revision and downstream lock migration, preserving old pinned revisions. |
| [scripts/validate_modbus_companion.py#L200](../scripts/validate_modbus_companion.py) | Required policy term names the wire path; canonical artifact checks also constrain path and digest. A redirect cannot satisfy the same wire contract. |
| [tests/test_modbus_companion_contract.py#L26](../tests/test_modbus_companion_contract.py) | Wire artifact tests require the contract, not navigation text. Update only in the separately owned companion scope. |
| [tests/test_sunspec_model_chain_contract.py#L32](../tests/test_sunspec_model_chain_contract.py) | Lines 32–33 require the CC0 and implementation-neutral SunSpec index wording. Preserve the boundary when redesigning the index. |

The source `protocols/` and `types/` lane is CC0-1.0; this inventory and
Helianthus `architecture/`, `docs/platform/`, APIs, development guidance,
application schemas and tooling are AGPL-3.0. The destination
[license policy](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/LICENSE) and
[applicability/licensing contract](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/applicability-and-licensing.md)
keep protocol knowledge CC0 and implementation guidance in its separate AGPL
lane. Move only independently stated protocol facts and permitted public
provenance into the native CC0 lane. Do not copy vendor manuals, tables,
firmware, screenshots or extracted prose; preserve inspection-only attributions.
The Apache-2.0 upstream catalog pin is provenance, not a license change or
permission to redistribute catalog contents under CC0.

Keep existing AGPL application contracts at their implementation home, linking
out for native facts. Preserve gateway policy, profile admission, consumer lock
schemas and runtime acquisition rules in that lane. Future migration must keep
eBUS MCP compatibility and GraphQL parity; moving facts cannot change either
API's values, provenance, availability, rejection or last-known-good behavior.
This inventory establishes no runtime or smoke-test evidence.

## Ordered companion work and completion gates

1. **Native companion preparation (docs-modbus):** review all nine rows against
   the source facts recorded above and native public sources, accounting for
   subsequent drift without losing retained facts. Create the missing wire
   reference, preserve documentary-only catalog facts and the earlier Fronius
   observation; merge overlapping vendor/core text without widening admission.
   Record each section's retained destination and resolve the addressing
   conflict explicitly. Keep old public provenance links and distinct revisions.
2. **Native companion validation and merge:** validate docs-modbus with its
   declared documentation checks and license boundary. Review exact companion
   HEAD, then merge. Verify the merged destinations and section anchors; record
   public branch or repository-relative links and the verification outcome,
   without publishing commit identifiers or pinned blob links.
   This companion has no assigned issue/PR in the supplied snapshot; its identity
   and merge status are Unknown. Nothing in this inventory claims it exists.
3. **Consumer and contract coordination:** after that merge, update native
   references and any artifact/manifest/validator/consumer-lock dependencies in
   separately authorized changes. Prove revision compatibility, retained pinned
   contracts and fail-closed admission; do not weaken digests or gates to accept
   redirect bytes. Confirm eBUS MCP compatibility and GraphQL parity in affected
   consumers. Audit external links before removing any compatibility material.
4. **docs-ebus redirect companion:** only after native merge and dependent
   contract migration, update every inbound location above, preserve anchors,
   replace eligible duplicate pages with CC0 navigation, and revise README
   protocol-map/licensing scope to the eBUS/native-owner boundary. Keep any page
   whose unique facts or pinned consumers are still unresolved. Do not redirect
   unmerged facts or turn implementation guidance into CC0 content.
5. **Joint closure:** run both repositories' full declared documentation gates,
   including docs-ebus companion validation, public-domain boundary and diff
   checks. Verify merged destination content, links and anchors, all nine disposition
   rows and no lost unique sections. Close #550 only when the migration,
   redirects, consumer dependencies and both repositories' validation are done.
   #586 delivers this inventory only and uses Refs for the parent slice.
