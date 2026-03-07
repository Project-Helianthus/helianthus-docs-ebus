# Functional Module Semantics

This page documents the current and target architecture for **functional modules** in Helianthus.

It exists because the current implementation exposes a useful but family-specific surface around `VR71/FM5`, while the longer-term architecture must also accommodate other module families such as:

- `VR70 / FM3`
- `VR66`
- legacy module families in older controller ecosystems

This page separates:

- the **current implemented contract**
- the **current evidence inventory**
- the **deferred generic target**

The target documented here is intentionally **inventory-first** and **provenance-first**. It is not a claim that Helianthus already has a generic functional-module contract in code.

## Current Implemented Contract

The currently implemented functional-module surface is centered on `VR71/FM5`.

The main exposed fields are:

- `system.properties.moduleConfigurationVR71`
- `fm5SemanticMode`
- `circuits[].managingDevice`

Current behavior:

- `moduleConfigurationVR71` is the raw configuration input currently read from B524
- `fm5SemanticMode` is the gateway's semantic verdict for the current FM5 interpretation path
- `circuits[].managingDevice` is the explicit ownership output already published on each circuit

The current implementation also gates:

- `solar`
- `cylinders`

through `fm5SemanticMode`.

This is valid as a **current implementation contract**, but it is not the right long-term architectural center for all functional modules.

## Provenance Discipline for Functional Modules

This page uses the same evidence discipline as the structural decision catalog, but applies it directly to the functional-module target.

- `PROVEN_PROTOCOL`
  - direct B524 register/group truth as documented in the B524 register map
- `PROVEN_PROFILE`
  - authoritative product-family/controller-ecosystem facts from official Vaillant manuals and training material
- `PROVEN_LAB`
  - facts validated only on the current Helianthus lab topology
- `HEURISTIC`
  - useful design or gateway-policy interpretation that goes beyond direct proof
- `UNKNOWN`
  - no defensible claim yet

For functional modules, the most important distinction is:

- **protocol truth** for B524 register existence and encoding
- **profile truth** for controller-family concepts such as `VR71 config`, `VR70 addr. 1..3`, or legacy module support
- **product identification** vs **B524-observed semantics**

The target contract must preserve that distinction rather than flatten it.

## Why the Current FM5-Centered Model Is Not Enough

The current model does not scale cleanly because:

1. it is named after one module family (`FM5`);
2. it behaves like a singleton semantic surface;
3. it mixes configuration, capability, interpretation state, and family gating;
4. it does not generalize naturally to modules that may exist:
   - without `FM5`
   - multiple times
   - with different capability sets

This is already visible in the existing evidence:

- `VR70/FM3` may exist together with `VR71/FM5`
- `VR70/FM3` may also be used on its own
- `VR66` is documented as a distinct control-centre/module concept in older regulator documentation

## Known Functional-Module Families and Current Evidence

### `VR71 / FM5`

Current evidence level:

- `PROVEN_PROTOCOL` for the existence and encoding of B524-facing registers and groups currently used in the FM5 path
- `PROVEN_PROFILE` for interpreting those registers as `VR71/FM5` role/configuration semantics in the documented controller ecosystems
- `PROVEN_LAB` for the currently validated live tuple and slot correlation used by Helianthus today

What we already have:

- B524 raw/system evidence:
  - `GG=0x00 RR=0x002F` (`module_configuration_vr71`)
  - `GG=0x0C` remote-accessory slot evidence currently correlated with `VR71/FM5`
- semantic contract:
  - `fm5SemanticMode`
  - `circuits[].managingDevice`
  - FM5-gated `solar`
  - FM5-gated `cylinders`
- regulator documentation evidence:
  - `Vaillant sensoCOMFORT VRC 720/3 -- Operating and Installation Instructions`
    - sections `4.3 System with FM5 and FM3 functional modules`, `4.4.1 Connection assignment for the FM5 functional module`, and `5.1 Prerequisites for starting up`
  - `Vaillant VRC 700/6 -- Installation Instructions`
    - section `7.4.2 Configuring the inputs and outputs of the VR 71` and appendices with `Config.: VR71`

Current architectural interpretation:

- `VR71/FM5` is the only functional-module family with explicit semantic gating and ownership effects in the implemented contract.
- `VR71/FM5` role semantics must remain **profile-scoped** unless separately proven at protocol level.
- `GG=0x0C` is protocol truth as a group namespace, but its interpretation as a `VR71/FM5` family signal remains profile/lab-scoped.
- In a generic target, `FM5` is better treated as a profile label around the concrete product code rather than as a primary contract field.

### `VR70 / FM3`

Current evidence level:

- `PROVEN_PROFILE` for standalone use, multi-instance support, addressing, and per-address configuration
- `PROVEN_PROTOCOL` only for the existence of raw B524-side status registers currently listed in Helianthus docs
- not yet promoted to a canonical semantic family in the public contract

Evidence in docs:

- `Vaillant sensoCOMFORT VRC 720/3 -- Operating and Installation Instructions`
  - section `4.2 System with FM3 functional module`
  - section `4.4.2` and `4.4.3` for the standalone and FM5+FM3 system profiles
  - section `4.6 Connection assignment for the FM3 functional module`
  - section `5.1 Prerequisites for starting up`
- `Vaillant VRC 700/6 -- Installation Instructions`
  - section `7.4.3 Configuring the inputs and outputs of the VR 70`
  - section `7.4.4 Configuring the VR 70's multi-function output`
  - appendices with `Config.: VR70 addr. 1 to 3`

Evidence already visible in B524 docs:

- `GG=0x00 RR=0x0067` (`vr70_module_status_1`)
- `GG=0x00 RR=0x0068` (`vr70_module_status_2`)

Important architectural consequence:

- `VR70/FM3` must not be modeled as “just another scalar like `fm5SemanticMode`”
- it can exist as an extension to `FM5`
- it can also exist as a standalone functional module
- multiple `FM3` modules may exist
- it has explicit per-module addressing in the documented controller ecosystem
- it has explicit per-address configuration in the documented controller ecosystem
- In a generic target, `FM3` is better treated as a profile label around `VR70` rather than as a primary contract field.

### `VR66`

Current evidence level: product/profile-level evidence only.

Evidence in docs:

- `Vaillant calorMATIC 350 -- Operating Instructions`
  - section `3.2.3 VR 66 Control Centre`

This is enough to justify architectural awareness of `VR66` as a function-module family, but not enough to define a B524 semantic contract for it yet.

Current architectural interpretation:

- `VR66` is a known function-module/control-centre family that the long-term architecture should be able to represent.
- It does **not** currently justify a concrete semantic API in the implemented contract.

### Legacy module families

Known examples in attached controller documentation include:

- `VR61`
- `VR68`
- `VR 2/7`
- `VR27`

Current evidence level:

- `PROVEN_PROFILE` for their existence as controller-ecosystem module families
- `UNKNOWN` for any B524 semantic mapping in the current Helianthus contract

Architectural consequence:

- the long-term model must allow additional families to exist without forcing premature semantic detail
- inventory may be known even when structure/ownership semantics remain unknown

## Deferred Generic Target

The deferred target is to replace family-specific singleton thinking with a generic inventory:

- `functionalModules[]`

Illustrative minimal shape only; not current API:

```text
functionalModules[]:
  - key
  - productCode
  - profileAddressIndex
  - busAddress
  - configurationSetValue
  - inventoryPresence
  - provenance
  - notes
```

Suggested field semantics:

- `key`
  - stable identifier for the module entry
  - not necessarily identical to eBUS address
- `productCode`
  - concrete product identifier or product-family code used for interpretation, such as `VR70`, `VR71`, `VR66`, `VR61`, `VR68`
  - this is the field that actually matters for per-product semantic implementation
- `profileAddressIndex`
  - optional controller/profile address index when the documented ecosystem exposes per-module addressing
  - example: `VR70 addr. 1..3`
- `busAddress`
  - optional physical eBUS slave address when proven
  - not interchangeable with `profileAddressIndex`
- `configurationSetValue`
  - optional profile-scoped configuration value when proven
- `inventoryPresence`
  - inventory-level presence claim for the module entry
  - not a publication/freshness/runtime-health state
- `provenance`
  - structured provenance per populated claim, not a single flat label
  - at minimum the contract should be able to express separate provenance for:
    - `productCode`
    - `profileAddressIndex`
    - `busAddress`
    - `configurationSetValue`
    - `inventoryPresence`
- `notes`
  - compact rationale for unknowns, scope limits, or profile constraints

This target is deliberately narrower than a capability-rich or policy-rich module contract.

It also deliberately separates:

- concrete product identification
- profile/controller address indexing
- physical bus addressing
- B524-observed semantics

It deliberately does **not** introduce a generic `instance` field in the minimal target, because that would blur:

- internal inventory ordinal
- protocol/group instance index
- profile/controller address index
- physical bus address

If a future family needs an explicit instance concept, that should be added in a family-specific detail layer with a precise meaning.

## Design Rules for the Target

### 1. Per module, not per-family scalar or taxonomy

The target should be per-module/per-instance, not a single global scalar such as:

- `fm3SemanticMode`
- `fm5SemanticMode`

It should also avoid inventing a generic family taxonomy when the actual discriminator for interpretation is the concrete product identity plus the observed B524 surface.

### 2. Inventory-first and provenance-first

Consumers should rely on:

- explicit module inventory
- explicit provenance and scope
- explicit ownership on the thing being owned

They should not infer topology from synthetic thresholds or from a module list that over-claims meaning.

### 3. Explicit ownership stays explicit

`functionalModules[]` is context, not a replacement for ownership fields.

For example:

- `circuits[].managingDevice` should remain explicit

The same principle should apply to future ownership relationships where useful.

### 4. Unknown is acceptable

The target should prefer visible `UNKNOWN` over overfitted heuristics.

That means it is better to publish:

- known inventory
- limited configuration facts
- explicit `UNKNOWN` provenance

than to over-claim structural meaning from weak evidence.

This is also why provenance cannot be modeled as a single coarse label on the whole module entry. Different populated fields may be supported by different evidence classes.

### 5. Profile-scoped configuration must stay profile-scoped

Configuration set values such as `VR71 config` or per-address `VR70 config` are useful data, but they are not protocol-wide truth by themselves.

If they are ever exposed in a generic module inventory, they must remain:

- explicitly profile-scoped
- provenance-labeled
- separate from protocol-level B524 register truth

## Relationship to the Current FM5 Surface

If the generic target is implemented later:

- `fm5SemanticMode` should be treated as a transitional family-specific convenience surface
- the more fundamental source of truth for module inventory, identity, and provenance should become the corresponding `functionalModules[]` entries
- `fm5SemanticMode` may still remain the family-specific semantic verdict until a richer family-specific layer exists
- consumers should gradually move from singleton FM5-centric interpretation toward generic module inventory plus explicit ownership semantics

This does **not** mean `fm5SemanticMode` must disappear immediately. It means the architectural center should stop being one family-specific scalar.

## Deferred / Premature Fields

The following ideas remain deferred because they risk leaking gateway policy or over-interpreting profile-level evidence:

- `capabilities`
  - attractive as design language, but premature unless every capability is backed by explicit evidence
- `semanticState`
  - useful internally, but too easy to mistake for protocol truth if published as a core field
- family-specific semantic detail beyond identity/config/presence/provenance
  - should arrive only after stable per-family evidence exists

If introduced later, these fields should be layered on top of the generic inventory rather than baked into the minimal target.

## Layered Model

A safer long-term model is:

- Layer 1: generic inventory
  - `functionalModules[]`
  - identity, instance/address, configuration, presence, provenance
- Layer 2: family-specific detail
  - optional and only when enough evidence exists to define stable semantics

This avoids using generic inventory as a hidden backdoor for topology inference.

## Non-Goals

This page does not currently define:

- the final GraphQL/MCP field names for `functionalModules[]`
- a complete capability taxonomy for every future module family
- an implementation timeline
- a complete B524 proof model for `VR66`

## Status

- current FM5-centered contract: `IMPLEMENTED`
- generic `functionalModules[]` target: `DEFERRED`

## Cross-Links

- Current structural flow: [`semantic-structure-discovery.md`](./semantic-structure-discovery.md)
- Current configuration gates: [`semantic-configuration-gates.md`](./semantic-configuration-gates.md)
- B524 decision catalog: [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md)
- B524 register map: [`../protocols/ebus-vaillant-B524-register-map.md`](../protocols/ebus-vaillant-B524-register-map.md)
