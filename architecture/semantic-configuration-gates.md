# Semantic Configuration Gates (B524)

This page documents the **structural gates** that determine whether semantic families, instances, and structure-bearing fields are allowed to appear in the B524 semantic model.

It is intentionally different from:

- state machines that control startup or freshness timing;
- per-field state derivation such as operating mode or HVAC action;
- transport-level retry and bus arbitration behavior.

Use this page to answer questions of the form:

- Why does this semantic family exist at all?
- Why is this instance published or absent?
- Which gate must be satisfied before a structural field becomes meaningful?

The authoritative rule-by-rule source remains the decision catalog:

- [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md)

## Gate Classes

| Gate class | Purpose |
| --- | --- |
| Precondition gate | Determines whether B524 structure discovery can run at all |
| Family gate | Determines whether a semantic family may be published |
| Instance gate | Determines whether an individual instance exists and may be published |
| Structural output gate | Determines whether a published structure-bearing field is emitted, meaningful, or `UNKNOWN` |

## Gate Summary Matrix

| Gate | Decision IDs | Inputs | Output | Scope |
| --- | --- | --- | --- | --- |
| B524 semantic root precondition | `SD-01` | B524 capability probes on candidate slave addresses | Enables or suppresses B524 structure discovery families | `PROTOCOL` for capability; `GATEWAY_POLICY` for candidate ordering |
| Zone instance gate | `SD-02`, `SD-03` | `GG=0x03 RR=0x001C` + zone presence FSM | Zone instance becomes present/absent | `PROTOCOL` for direct probe path; `GATEWAY_POLICY` for hysteresis/fallback |
| Zone naming gate | `SD-04` | `GG=0x03 RR=0x0016/0x0017/0x0018` | Zone name becomes explicit or falls back | Mixed `PROTOCOL` + `GATEWAY_POLICY` |
| Zone room-sensor mapping gate | `SD-05` | `GG=0x03 RR=0x0013` | `roomTemperatureZoneMapping` becomes available | `PROTOCOL` |
| Zone-to-circuit derivation gate | `SD-06` | `GG=0x03 RR=0x0013` + current lab-backed `value - 1` derivation | `associatedCircuit` becomes explicit from raw mapping value | `LAB` |
| Zone-to-circuit fallback gate | `SD-07` | outcome of `SD-06` | `associatedCircuit` remains populated via fallback-to-zone-instance | `GATEWAY_POLICY` |
| Circuit instance gate | `SD-08` | `GG=0x02 RR=0x0002` | Circuit active/inactive | `PROTOCOL` |
| Circuit ownership gate | `SD-09` | `systemScheme`, `moduleConfigurationVR71`, `fm5SemanticMode` | `managingDevice` explicit or `UNKNOWN` | Mixed `LAB` / `PROFILE` / `UNKNOWN` |
| Radio inclusion gate | `SD-10` | `GG=0x09/0x0A/0x0C` slot evidence | Remote/radio device published | Mixed `PROTOCOL` + `GATEWAY_POLICY` |
| FM5 interpretation gate | `SD-11` | VR71 config + radio/FM5 evidence + solar/cylinder readability | `fm5SemanticMode` | Mixed `GATEWAY_POLICY` + `PROFILE` |
| Solar family gate | `SD-12` | `fm5SemanticMode` + `GG=0x04` readability | `solar` family published/cleared | Mixed `GATEWAY_POLICY` + `PROFILE` |
| Cylinder family gate | `SD-13` | `fm5SemanticMode` + `GG=0x05` readability | `cylinders[]` family published/cleared | Mixed `GATEWAY_POLICY` + `PROFILE` |
| Individual cylinder gate | `SD-14` | `GG=0x05 RR=0x0004` (`temperatureC`) | Individual cylinder instance published/omitted | `GATEWAY_POLICY` |

## B524 Semantic Root Gate

- Structural role: enables or suppresses the entire B524 structure-discovery pipeline.
- Current rule source: [`SD-01`](../protocols/ebus-vaillant-B524-structural-decisions.md#b524-sd-01--b524-semantic-root-availability)
- Root-discovery contract: [`b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Identity enrichment contract: [`regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)

This page does not restate the root-discovery or identity-enrichment rationale. It only treats B524 semantic-root availability as the precondition that decides whether B524-backed families can be evaluated at all.

## Zone Gates

### Zone instance gate

- Primary evidence: `GG=0x03 RR=0x001C`
- Structural effect: a zone instance is eligible for publication only when presence evidence exists
- Gate owner:
  - direct B524 probe path -> protocol evidence
  - zone presence hysteresis -> gateway structural policy

### Zone naming gate

- Primary evidence: `GG=0x03 RR=0x0016/0x0017/0x0018`
- Structural effect: every published zone has a stable display name
- Note: the `Zone N` fallback is a publication convenience, not protocol evidence

### Zone room-sensor mapping gate

- Primary evidence: `GG=0x03 RR=0x0013`
- Structural effect: publishes `roomTemperatureZoneMapping`
- Cross-check path: remote-side `zone_assignment` from `GG=0x09/0x0A RR=0x0025`

### Zone-to-circuit derivation gate

- Primary evidence: `GG=0x03 RR=0x0013`
- Structural effect: publishes `associatedCircuit` from the current lab-backed `value - 1` derivation
- Scope: `LAB`
- Important: the derivation is intentionally documented as a lab-validated formula rather than protocol truth

### Zone-to-circuit fallback gate

- Primary evidence: none independent; this gate consumes the outcome of the derivation gate
- Structural effect: keeps `associatedCircuit` populated through fallback-to-zone-instance
- Scope: `GATEWAY_POLICY`
- Important: the existence of the resolved field is part of the semantic contract, but fallback behavior remains gateway policy rather than protocol truth

## Circuit Gates

### Circuit instance gate

- Primary evidence: `GG=0x02 RR=0x0002`
- Structural effect: circuits appear only when active circuit-type evidence exists
- No synthetic circuit count is published if the type path does not prove activity

### Circuit ownership gate

- Primary inputs: `systemScheme`, `moduleConfigurationVR71`, `fm5SemanticMode`
- Structural effect: publishes `circuits[].managingDevice`
- Output rule:
  - explicit managing device when current tuple is supported
  - `UNKNOWN` when ownership is not proven

## Radio Inventory Gate

### Connected-slot gate

- Primary evidence: `GG=0x09/0x0A/0x0C` slot data such as `device_connected`, `device_class_address`, firmware, temperature, humidity
- Structural effect: connected remote/radio devices appear in `radioDevices[]`

### Inventory-style inclusion gate

- Current gateway rule: certain disconnected `0x0C` slots may still appear when identity evidence is considered strong enough
- This is a gateway policy, not a pure protocol proof path

## FM5 Gate

- Primary inputs:
  - `GG=0x00 RR=0x002F` (`module_configuration_vr71`)
  - radio/FM5 inventory evidence
  - solar readability
  - cylinder readability
- Structural effect:
  - publishes `fm5SemanticMode`
  - controls whether FM5-backed families are interpreted or withheld

This is the bridge gate between raw controller/module evidence and higher-level family publication.

Important architectural note:

- this is the **current implemented FM5-specific gate**
- it is not yet the final generic architecture for all functional-module families

See:

- [`functional-modules.md`](./functional-modules.md)

## Solar Gate

- Primary inputs:
  - `fm5SemanticMode`
  - `GG=0x04` solar readability
- Structural effect:
  - publishes or clears the `solar` family as a whole
- Current contract:
  - no partial `solar` family in non-interpreted FM5 mode

## Cylinder Gates

### Cylinder family gate

- Primary inputs:
  - `fm5SemanticMode`
  - `GG=0x05` family readability
- Structural effect:
  - publishes or clears the `cylinders[]` family

### Individual cylinder gate

- Primary evidence:
  - `GG=0x05 RR=0x0004` (`temperatureC`)
- Structural effect:
  - only instances with live temperature evidence are published
- Important:
  - config-only payloads do not create cylinder instances in the current gateway contract

## Structure-Bearing Outputs

These do not create families by themselves, but they are the outputs consumers must use instead of inventing local thresholds:

- `roomTemperatureZoneMapping`
- `associatedCircuit`
- `radioDevices[]`
- `fm5SemanticMode`
- `circuits[].managingDevice`

## Cross-Links

- Structure discovery flow: [`semantic-structure-discovery.md`](./semantic-structure-discovery.md)
- Structure mechanism map: [`semantic-structure-fsm-map.md`](./semantic-structure-fsm-map.md)
- Decision catalog: [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md)
