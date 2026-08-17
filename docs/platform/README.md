# Helianthus Platform Contracts

This directory is the temporary canonical home for cross-protocol Helianthus
platform contracts.

It owns contracts that apply across protocol families:

- MCP-first lifecycle and namespace governance;
- raw evidence and snapshot rules;
- semantic promotion gates;
- multi-runtime coexistence and conflict handling;
- consumer rollout order for GraphQL, Portal, and Home Assistant.

Current platform contracts:

- [`cross-runtime-envelope.md`](./cross-runtime-envelope.md)
- [`hash-auth-binding.md`](./hash-auth-binding.md)
- [`shared-registry-boundary.md`](./shared-registry-boundary.md)
- [`promotion-and-consumer-contract.md`](./promotion-and-consumer-contract.md)
- [`ownership-validation.md`](./ownership-validation.md)
- [`ownership-and-doc-gates.md`](./ownership-and-doc-gates.md)
- [`modbus-multivendor-boundaries.md`](./modbus-multivendor-boundaries.md) -
  pre-implementation ownership, evidence, licensing, and public/private
  direction contract for the shared Modbus runtime and multi-vendor registry
- [`modbus-foundation-profile-contract-v1.md`](./modbus-foundation-profile-contract-v1.md) -
  normative M1 transport and M2 profile-registry contract for phase-one
  read-only Modbus
- [`../../api/modbus-v1-mcp.md`](../../api/modbus-v1-mcp.md) - bounded M4-02
  raw/profile MCP contract, redaction, source-observation envelope, and limits
- [`../../api/modbus-v1-addon-runtime.md`](../../api/modbus-v1-addon-runtime.md) -
  FMV3-M4-03 disabled-by-default add-on configuration, protected endpoint-file,
  one direct gateway launch, and protocol-local Modbus failure contract
- [`fronius-sunspec-evidence-v1.md`](./fronius-sunspec-evidence-v1.md) -
  FMV3-M3-01 evidence packet and FMV3-M3-03 `STANDARD_ONLY` completion for
  bounded synthetic fixtures and the Fronius SunSpec admission boundary
- [`canonical-pv-semantics-v1.md`](./canonical-pv-semantics-v1.md) -
  FMV3-M5-02 pre-implementation canonical photovoltaic fact, lifecycle,
  provenance, continuity, capability, and compatibility contract
- [`manifests/canonical-pv-v1.json`](./manifests/canonical-pv-v1.json) -
  closed machine-readable V1 catalog and three-phase capability inventory
- [`schemas/canonical-pv-observation-v1.schema.json`](./schemas/canonical-pv-observation-v1.schema.json) -
  recursively closed canonical observation envelope used by positive and
  negative conformance fixtures
- [`manifests/modbus-foundation-profile-contract-v1.json`](./manifests/modbus-foundation-profile-contract-v1.json) -
  machine-readable M1/M2 companion inventory and downstream pin contract
- [`opaque-runtime-acquisition-v1.md`](./opaque-runtime-acquisition-v1.md) -
  normative source-owned one-shot runtime acquisition capability and M2
  attempt/publication boundary
- [`manifests/opaque-runtime-acquisition-v1.json`](./manifests/opaque-runtime-acquisition-v1.json) -
  closed machine-readable inventory for the opaque runtime acquisition contract
- [`eebus-raw-first-contract.md`](./eebus-raw-first-contract.md)
- [`eebus-raw-runtime-freeze.md`](./eebus-raw-runtime-freeze.md) - M3.5
  identity, snapshot-envelope, and evidence-object freeze boundary
- [`raw-correlation-and-leaf-promotion.md`](./raw-correlation-and-leaf-promotion.md)
- [`synchronized-evidence-bundle-v1.md`](./synchronized-evidence-bundle-v1.md) -
  MSP-065 closed synchronized capture and deterministic offline replay contract
- [`synchronized-evidence-one-shot-control-v1.md`](./synchronized-evidence-one-shot-control-v1.md) -
  MSP-065-LIVE-R1 owner-only one-shot activation and crash-idempotency contract
- [`draft-candidate-fact-graph-v1.md`](./draft-candidate-fact-graph-v1.md) -
  MSP-07 closed M7 candidate-only fact graph, source-terminal provenance for
  zero-artifact B509/B524/B555 records, and deterministic replay contract
- [`multi-runtime-coexistence-no-drift-v1.md`](./multi-runtime-coexistence-no-drift-v1.md) -
  MSP-08 closed EEBUS-G18 coexistence, protected-view no-drift, and rollback
  contract
- [`leaf-promotion-dossier-lock-v1.md`](./leaf-promotion-dossier-lock-v1.md) -
  MSP-085 M8.5 per-leaf dossier lock
- [`captured-multi-leaf-promotion-v1.md`](./captured-multi-leaf-promotion-v1.md) -
  additive unreleased-V1 profile for restart-separated, per-candidate live
  promotion evidence and deterministic public-redacted results
- [`promoted-semantic-consumers-v1.md`](./promoted-semantic-consumers-v1.md) -
  M9 GraphQL, Portal, Home Assistant, and add-on projection contract for the
  exact eighteen locked semantic leaves
- [`live/msp-085-0.6.38/`](./live/msp-085-0.6.38/) - final source-bound live
  M8/M8.5 public-redacted intermediate outputs: `8` promoted and `10` withheld
- [`live/msp-085-0.6.40/`](./live/msp-085-0.6.40/) - final source-bound live
  M8/M8.5 public-redacted outputs: all `18` real leaves promoted, `0` withheld,
  and all promoted leaves still `LOCKED_NOT_EXPOSED` before M9
- [`live/fronius-m4-04-0.6.46/`](./live/fronius-m4-04-0.6.46/) - sanitized
  FMV3-M4-04 Fronius/SunSpec qualification evidence: registry-internal `GO`,
  terminal `STOP_ENVIRONMENTAL`, completed rollback, and M5 still blocked
- [`live/fronius-m4-04-0.6.47/`](./live/fronius-m4-04-0.6.47/) - immutable
  read-only rerun evidence: registry-internal `GO`, readiness and endpoint
  redaction regression passes, terminal `STOP_ENVIRONMENTAL`, and safe rollback
- [`live/fronius-m4-04-0.6.51/`](./live/fronius-m4-04-0.6.51/) - exact deployed
  read-only evidence: retained SunSpec and raw MCP parity, endpoint-free bounded
  reconnect, generation advance without gateway restart, and terminal `GO`
- [`eebus-ha-network-proof.md`](./eebus-ha-network-proof.md)
- [`eebus-interop-smoke.md`](./eebus-interop-smoke.md) - canonical G01/G17/G19
  evidence, authority, redaction, and promotion boundary
- [`msp-0625-public-acquisition-methodology.md`](./msp-0625-public-acquisition-methodology.md) -
  M6.25 public cross-seed for acquisition and evidence
  methodology; it does not own protocol, API, or architecture details

The publication-contract v2 canonical collection is the exact foundational
inventory of `cross-runtime-envelope.md`, `hash-auth-binding.md`,
`shared-registry-boundary.md`, `promotion-and-consumer-contract.md`, and
`ownership-validation.md`. The remaining pages are milestone-specific
operational contracts and are not silently added to that collection. The
G17/G19 smoke page cross-seeds only the platform evidence boundary; eeBUS-native
transport evidence remains with the protocol-owned companion.

The authoritative eeBUS ownership state is the versioned
[`manifests/eebus-doc-ownership.yaml`](./manifests/eebus-doc-ownership.yaml)
manifest. Its M6.25 entry sources the exact immutable public inputs through
[`manifests/msp-0625-public-inputs.yaml`](./manifests/msp-0625-public-inputs.yaml).

The M6.25 cross-seed is outside the foundational canonical collection. Its
implementation and live-evidence claims remain pending their separate gates.

Protocol-specific repositories may link here, but they must not duplicate these
contracts as normative text. Non-owning pages are summary-only.

## Transition Rule

This directory remains the platform-contract home until a separate
`helianthus-docs-platform` repository is created after the current eeBUS
raw-first bootstrap. The trigger is either:

- a later non-eBUS protocol reaches a promoted-leaf gate; or
- a cross-protocol contract changes for reasons unrelated to eBUS or the eeBUS
  VR940f raw-first track.

When that happens, platform pages move as a unit, this directory keeps stubs,
and canonical links are updated.
