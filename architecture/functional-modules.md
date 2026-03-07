# Functional Module Semantics

This page documents the current and target architecture for **functional modules** in Helianthus.

It exists because the current implementation exposes a useful but family-specific surface around `VR71/FM5`, while the longer-term architecture must also accommodate other module families such as:

- `VR70 / FM3`
- `VR66`
- additional future or older function-module families

This page separates:

- the **current implemented contract**
- the **current evidence inventory**
- the **deferred generic target**

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

Current evidence level: strongest of all currently discussed module families.

What we already have:

- B524 raw/system evidence:
  - `GG=0x00 RR=0x002F` (`module_configuration_vr71`)
  - `GG=0x0C` remote-accessory/VR71-facing slot evidence
- semantic contract:
  - `fm5SemanticMode`
  - `circuits[].managingDevice`
  - FM5-gated `solar`
  - FM5-gated `cylinders`
- regulator documentation evidence:
  - `Vaillant sensoCOMFORT VRC 720/3 -- Operating and Installation Instructions`
  - `Vaillant VRC 700 -- Installation Instructions`

Current architectural interpretation:

- `VR71/FM5` is the only functional-module family with explicit semantic gating and ownership effects in the implemented contract.

### `VR70 / FM3`

Current evidence level: present in documentation and partially visible in B524/system data, but not yet promoted to a canonical semantic family.

Evidence in docs:

- `Vaillant sensoCOMFORT VRC 720/3 -- Operating and Installation Instructions`
  - section `4.2 System with FM3 functional module`
  - section `4.6 Connection assignment for the FM3 functional module`
- `Vaillant VRC 700 -- Installation Instructions`
  - section `7.4.3 Configuring the inputs and outputs of the VR 70`
  - section `7.4.4 Configuring the VR 70's multi-function output`

Evidence already visible in B524 docs:

- `GG=0x00 RR=0x0067` (`vr70_module_status_1`)
- `GG=0x00 RR=0x0068` (`vr70_module_status_2`)

Important architectural consequence:

- `VR70/FM3` must not be modeled as “just another scalar like `fm5SemanticMode`”
- it can exist as an extension to `FM5`
- it can also exist as a standalone functional module
- multiple `FM3` modules may exist

### `VR66`

Current evidence level: product/profile-level evidence only.

Evidence in docs:

- `Vaillant calorMATIC 350 -- Operating Instructions`
  - section `3.2.3 VR 66 Control Centre`

This is enough to justify architectural awareness of `VR66` as a function-module family, but not enough to define a B524 semantic contract for it yet.

Current architectural interpretation:

- `VR66` is a known function-module/control-centre family that the long-term architecture should be able to represent.
- It does **not** currently justify a concrete semantic API in the implemented contract.

## Deferred Generic Target

The deferred target is to replace family-specific singleton thinking with a generic inventory:

- `functionalModules[]`

Illustrative shape only; not current API:

```graphql
type FunctionalModule {
  family: FunctionalModuleFamily!
  deviceId: String
  address: Int
  instance: Int
  configuration: Int
  semanticState: FunctionalModuleSemanticState!
  capabilities: [FunctionalModuleCapability!]!
  evidenceScope: FunctionalModuleEvidenceScope!
}
```

Suggested semantics:

- `family`
  - `FM3`
  - `FM5`
  - `UNKNOWN`
- `semanticState`
  - `ABSENT`
  - `PRESENT`
  - `GPIO_ONLY`
  - `INTERPRETED`
  - `UNKNOWN`
- `capabilities`
  - `CIRCUIT_MANAGEMENT`
  - `SOLAR`
  - `CYLINDERS`
  - `MIXER_CIRCUITS`
  - `MULTI_FUNCTION_OUTPUT`
- `evidenceScope`
  - `PROTOCOL`
  - `PROFILE`
  - `LAB`
  - `UNKNOWN`

## Design Rules for the Target

### 1. Per module, not per family scalar

The target should be per-module/per-instance, not a single global scalar such as:

- `fm3SemanticMode`
- `fm5SemanticMode`

### 2. Capability-driven, not threshold-driven

Consumers should rely on:

- explicit module inventory
- explicit capabilities
- explicit ownership on the thing being owned

They should not infer topology from synthetic thresholds.

### 3. Explicit ownership stays explicit

`functionalModules[]` is context, not a replacement for ownership fields.

For example:

- `circuits[].managingDevice` should remain explicit

The same principle should apply to future ownership relationships where useful.

### 4. Unknown is acceptable

The target should prefer visible `UNKNOWN` over overfitted heuristics.

That means it is better to publish:

- known inventory
- limited capabilities
- `UNKNOWN` semantic state

than to over-claim structural meaning from weak evidence.

## Relationship to the Current FM5 Surface

If the generic target is implemented later:

- `fm5SemanticMode` should be treated as a transitional family-specific convenience surface
- the more fundamental source of truth should become the corresponding `functionalModules[]` entries
- consumers should gradually move from singleton FM5-centric interpretation toward generic module inventory + capability semantics

This does **not** mean `fm5SemanticMode` must disappear immediately. It means the architectural center should stop being one family-specific scalar.

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
