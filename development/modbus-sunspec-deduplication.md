# Lossless Modbus/SunSpec migration inventory

This is an AGPL-3.0 development inventory for issue #550. The original
inventory was delivered as partial slice #586; this refresh records current
destinations without completing the parent migration. It authorizes no move,
deletion, redirect, runtime change or live qualification. The parent remains open until the companion and redirect work
has merged and both repositories validate.

## Historical comparison snapshot and evidence status

All nine source pages and their docs-modbus counterparts were read from the
main branch of each repository at the time of writing; this change's history
records when. Links below are moving branch or repository-relative references,
not immutable historical content. Subsequent drift in either repository is
unverified; this recorded comparison snapshot does not establish current parity.
The historical column below retains that comparison, including its then-missing
destinations. The current disposition column was re-read against both supplied
main-branch documentation views. Presence and the stated textual comparisons
are Proven for those views only; future branch drift and migration completion
remain Unknown. Private comparison coordinates are not published here.

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

The historical comparison is retained in the third column; its missing-page
statements describe that earlier snapshot only. The fourth column supersedes
those absence claims for the current views. Verified destination presence is
not a blanket parity verdict, qualification, or redirect approval. Unresolved
retention work remains Hypothesis; no unique section may be dropped.

| Source page | Historical counterpart / merge target | Historical section comparison | Current disposition and verified destination anchors |
| --- | --- | --- | --- |
| [protocols/modbus/README.md](../protocols/modbus/README.md) | [README.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) | Entire index: duplicate purpose and CC0 scope; source uniquely groups the phase-one wire and four local references. Destination index has broader vendor coverage and an explicit native-owner statement. Merge navigation after the missing wire page exists; do not import application contracts. | Proven: the [native README](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) retains the owner statement and broader protocol index. The wire page now exists (row below), but that index still omits it, the documentary catalog note and the historical Fronius note. The source’s wire, chain and two vendor links need explicit replacement navigation; index parity remains unresolved. |
| [protocols/modbus/growatt-candidate-evidence-v1.md](../protocols/modbus/growatt-candidate-evidence-v1.md) | [protocols/growatt/protocol-ii-readonly-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/growatt/protocol-ii-readonly-v1.md) | Unheaded vendor-source paragraph: source uniquely contrasts incompatible product ranges; preserve that warning and inspection-only attribution. FC03 candidate paragraph: offsets/quantities duplicate destination Identity tuple, which additionally requires a coherent complete tuple. Final paragraph: proprietary-map/non-SunSpec disclaimer duplicates Scope. Destination uniquely defines encoding, serial slice, fail-closed admission, native/MCP identity, synthetic FC04 schema, and collision rules. Never broaden the narrow candidate to all source families. | Proven: [scope](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/growatt/protocol-ii-readonly-v1.md#scope), [identity tuple](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/growatt/protocol-ii-readonly-v1.md#identity-tuple) cover proprietary/non-SunSpec scope and all four candidate slices. [retained primary source](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/growatt/protocol-ii-source-profile-matrix-v1.md#retained-primary-source) preserves inspection-only attribution. The explicit incompatible-range warning is not reproduced as such; retain it before redirect. Current typed result is NO_ADMISSIBLE_PROFILE; the addressing conflict below persists. No broader family admission follows. |
| [protocols/modbus/huawei-gateway-candidate-evidence-v1.md](../protocols/modbus/huawei-gateway-candidate-evidence-v1.md) | [protocols/huawei/gateway-readonly-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md) | Opening family distinction duplicates Scope. Address, numeric and string paragraphs duplicate Shared encoding. Candidate offsets and child request duplicate SmartLogger candidate, S-Dongle candidate, EMMA candidate and Child inventory. Preserve the source documentary-only/no-probing qualification. Destination uniquely adds exact applicability branches, complete tuples, stable inventory, pagination bounds, no fallback and default-denied private operations. A documentary offset is not a qualified operation. | Proven: [scope](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#scope), [shared encoding](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#shared-encoding), [smartlogger candidate](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#smartlogger-candidate), [s dongle candidate](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#s-dongle-candidate), [emma candidate](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#emma-candidate), [child inventory](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#child-inventory) retain family separation, address/string/numeric rules, candidate slices and request form. [reference conflicts and quarantined facts](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/huawei/gateway-readonly-v1.md#reference-conflicts-and-quarantined-facts) now qualifies counter routing, inventory count/width, basic identification and private-service claims. Preserve the source documentary-only/no-probing limit and those conflicts; historical overlap does not qualify each candidate. |
| [protocols/modbus/modbus-phase-one-wire-v1.md](../protocols/modbus/modbus-phase-one-wire-v1.md) | Missing complete counterpart; create the proposed native wire destination | License And Scope and its three official citations must migrate intact. Common PDU, FC03 And FC04, FC2B/MEI0E Request/Objects/Response, Modbus TCP ADU, and Modbus RTU ADU have no complete counterpart. Private Function Code Transport overlaps only bounded reads, exception correlation, extent checks and RTU integrity/timing; it uniquely defines transport admission/lifecycle policy and is not a replacement. Preserve the full neutral summary, including object limits, restart/progress behavior, TCP framing, CRC and serial timing. Proposed destination: `protocols/modbus/modbus-phase-one-wire-v1.md` (absent in the inspected destination snapshot). | Proven: the delivered native wire reference retains every section: [license and scope](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#license-and-scope), [common pdu](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#common-pdu), [fc03 and fc04](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#fc03-and-fc04), [fc2bmei0e read device identification](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#fc2bmei0e-read-device-identification), [request](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#request), [objects](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#objects), [response](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#response), [modbus tcp adu](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#modbus-tcp-adu), [modbus rtu adu](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/modbus-phase-one-wire-v1.md#modbus-rtu-adu). All text matches the source except the license-link sentence; the three official citations, object limits, restart/progress rules, TCP framing, CRC and serial timing are retained. Textual retention is verified; pinned artifact dependencies still prohibit redirect. |
| [protocols/sunspec/README.md](../protocols/sunspec/README.md) | [README.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) | Entire index: duplicate reference-index purpose. Source uniquely exposes the two observation revisions and documentary catalog note. Destination index uniquely enumerates V1, V2, nested-layout, vendor and applicability contracts. Add links to preserved historical evidence before replacing this index. | Proven: the [native README](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/README.md) lists core revisions, nested layouts and vendor contracts, but omits the delivered documentary and historical pages. The source’s four links need explicit native navigation, including both observation revisions; index replacement remains unresolved. |
| [protocols/sunspec/additional-model-evidence-v1.md](../protocols/sunspec/additional-model-evidence-v1.md) | [protocols/sunspec/read-only-core-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md) | Unheaded catalog paragraph: meter and environmental groups and upstream pin duplicate Initial model catalog; documentary grid/control range 125–145 is unique and must remain separate from executable admission. Signature paragraph uniquely specifies FC03, offset and quantity; model-header/extent statements duplicate Chain structure. Destination uniquely gives exact decoder tuples, sentinels, value rules and rejection rules. Preserve the source no-device/no-control/no-write disclaimer. Proposed additional destination: `protocols/sunspec/additional-model-evidence-v1.md` for unique documentary facts, not an extension of the core catalog. | Proven: delivered [retained documentary facts](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/additional-model-evidence-v1.md#retained-documentary-facts) preserves documentary range 125–145 and FC03/signature offset/quantity. Meter/environment families and header/extents are assigned to core [initial model catalog](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#initial-model-catalog), [chain structure](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#chain-structure). [native contract and evidence status](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/additional-model-evidence-v1.md#native-contract-and-evidence-status), [provenance and publication boundary](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/additional-model-evidence-v1.md#provenance-and-publication-boundary), [version and safety limits](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/additional-model-evidence-v1.md#version-and-safety-limits) retains attribution by source citation (not an immutable reproduction of the upstream pin) and no-device/no-control/no-write limits. Combined retention is verified; source-citation continuity requires coordination before redirect. |
| [protocols/sunspec/fronius-observed-flavor-v1.md](../protocols/sunspec/fronius-observed-flavor-v1.md) | [protocols/fronius/sunspec-float-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md) | Entire observation: source uniquely records the earlier ordered chain without Model 123 and its FC03/unit/signature context; the exact applicability tuple is shared evidence but is not republished here. Destination Exact chain geometry describes V1.1 with Model 123; Applicability and Read-only result uniquely add exact-match and downstream qualification constraints. These are distinct observations, not interchangeable duplicates. Proposed historical destination: `protocols/fronius/observed-chain-v1.md`; preserve original public evidence and provenance by citation without widening family support. | Proven: delivered [earlier ordered chain and acquisition context](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#earlier-ordered-chain-and-acquisition-context) preserves the entire chain without Model 123, FC03/unit/signature context, public provenance and exact identity constraint by source citation. [scope and evidence status](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#scope-and-evidence-status), [qualification and preservation boundary](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#qualification-and-preservation-boundary) prevents family widening. Fingerprints remain in cited source evidence; replacing that evidence with circular navigation is unresolved. |
| [protocols/sunspec/fronius-observed-flavor-v1-1.md](../protocols/sunspec/fronius-observed-flavor-v1-1.md) | [protocols/fronius/sunspec-float-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md) | Entire revision note: added 123/L24 duplicates Exact chain geometry. Source uniquely states the separate observation and prohibition on widening V1 to another device, firmware or acquisition configuration. Merge that provenance distinction and retain a link to the historical V1 record; never silently replace its chain. Destination uniquely contains full V1.1 geometry and qualification boundary. | Proven: [separate later observation](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#separate-later-observation) preserves added 123/L24, separate provenance and the no-widening constraint by citation. [exact chain geometry](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md#exact-chain-geometry), [applicability](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md#applicability), [read only result](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md#read-only-result) retains complete later geometry and qualification boundaries. Earlier acquisition context is explicitly not attributed to the later revision. Preserve the cited revision note before redirect. |
| [protocols/sunspec/sunspec-model-chain-v1.md](../protocols/sunspec/sunspec-model-chain-v1.md) | [protocols/sunspec/read-only-core-v1.md](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md) | Opening upstream pin and Model occurrences: catalog pin, exact V1 lengths and Model 160 formula duplicate Initial model catalog; destination uniquely bounds counts and enumerates meter/environment lengths. Chain framing: order, occurrences, opaque unknown blocks, terminal marker and raw words duplicate Chain structure/Value rules; explicitly preserve nonzero pre-terminal lengths, checked arithmetic, no overrun and no trailing words. Final non-claims duplicate Safety and disposition. Destination uniquely adds typed-value rules, field equivalence and executable schema keys; preserve the distinction between neutral structure and decoder admission. | Proven: [initial model catalog](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#initial-model-catalog) retains upstream attribution, exact lengths and Model 160 formula; [chain structure](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#chain-structure), [value rules](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#value-rules), [safety and disposition](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/read-only-core-v1.md#safety-and-disposition) retains signature/Common, ordered occurrences, raw extents, opaque unknown blocks, byte order and no-write/admission limits. Explicit source wording for nonzero pre-terminal lengths, checked arithmetic and no trailing words is not fully reproduced; overrun rejection alone does not prove parity. Retain these unique framing constraints before redirect. |

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

## Historical inbound-link locations and current delta

The following historical list records repository Markdown inline links resolving
to one of the nine pages, including links inside those pages. Locations use the
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

### Current inbound-link recheck

All nineteen historical locations above remain in the current source view.
An additional link in
[docs/platform/modbus-multivendor-boundaries.md](../docs/platform/modbus-multivendor-boundaries.md)
(line 222) targets the wire page’s `#modbus-rtu-adu`. The inventory’s own
source citations are additional links, not consumers to silently delete.
Filename labels resolving to `architecture/` still retain those AGPL contracts.

The current native-owner view adds three source-evidence dependencies:
[Retained documentary facts](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/sunspec/additional-model-evidence-v1.md#retained-documentary-facts)
cites the original catalog note;
[Earlier ordered chain and acquisition context](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#earlier-ordered-chain-and-acquisition-context)
cites the earlier source observation; and
[Separate later observation](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/observed-chain-v1.md#separate-later-observation)
cites the later revision note. Preserve their evidentiary meaning before
redirecting source pages; a citation loop would not retain the original facts.
The native [tolerant TCP contract](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/modbus/tolerant-tcp-modes-v1.md)
already links its local delivered wire reference. Neither repository’s links
establish external consumer completeness or immutable historical parity.

## Non-link dependencies and publication lanes

The following are blockers to blind redirects, even where link text is valid.
These four dependencies were re-read in the current source view and still apply.
The future companion must inventory downstream locks outside this checkout too.
The manifest binds policy, consumer-lock schema and trusted-revision validator/
workflow artifacts alongside the wire artifact; content-revision and consumer-lock
transitions need explicit coordination, not merely a Markdown retarget. No
validator or pin changes are authorized by this inventory.

| Pinned dependency | Obligation before redirect |
| --- | --- |
| [docs/platform/manifests/modbus-foundation-profile-contract-v1.json#L14](../docs/platform/manifests/modbus-foundation-profile-contract-v1.json) | The manifest’s `artifacts.wire` path and `artifact_sha256.wire` bind actual content; a redirect changes contract bytes. Coordinate explicit contract revision and downstream lock migration, preserving old pinned revisions. |
| [scripts/validate_modbus_companion.py#L200](../scripts/validate_modbus_companion.py) | Required policy term names the wire path; `EXPECTED_STATIC_ARTIFACT_SHA256`, regular in-repository file checks, manifest byte checks, official-source checks and the literal source license declaration constrain the artifact. The native license-link sentence alone changes its bytes. A redirect cannot satisfy the same wire contract. |
| [tests/test_modbus_companion_contract.py#L26](../tests/test_modbus_companion_contract.py) | Wire artifact tests require the contract, not navigation text. Update only in the separately owned companion scope. |
| [tests/test_sunspec_model_chain_contract.py#L32](../tests/test_sunspec_model_chain_contract.py) | Lines 32–33 require the CC0 and implementation-neutral SunSpec index wording; the later legacy-material test also requires the model-chain filename in the Modbus index and multivendor boundaries. Preserve the boundary when redesigning the index. |

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

1. **Delivered native material, remaining parity:** the wire reference,
   documentary catalog note and earlier Fronius chain are present in the current
   native view, with retained destinations and anchors recorded above. Do not
   recreate that delivered work. Resolve remaining incompatible-range wording,
   explicit chain-framing constraints, index navigation, the addressing conflict
   and source-citation continuity without widening admission or losing provenance.
2. **Native validation evidence:** current destination presence and the bounded
   text comparisons above are Proven. Full companion validation, independent
   committed-change review and merge identity are unverified in this refresh;
   do not infer them from page presence or repeat completed native-page work.
   Recheck moving branch links and content at the coordinated migration boundary.
3. **Consumer and contract coordination:** after remaining native parity and
   validation work is accepted, update native
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
   The original #586 inventory and this #550 refresh are partial slices; neither
   establishes completed migration or closes the parent.
