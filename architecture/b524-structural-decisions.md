# Vaillant B524 Structural Decision Catalog

This page documents the **implemented structural decisions** in `helianthus-ebusgateway` for B524-backed semantic discovery.

Each entry records:

- the source of evidence;
- any supporting regulator-document statement used to constrain or explain the rule;
- the scope in which the rule is considered valid;
- how the gateway evaluates that evidence;
- what public semantic effect the decision has;
- whether the rule is `PROVEN`, `HEURISTIC`, `COMPOSITE`, or `UNKNOWN`.

This document is authoritative for Phase 1 structural discovery and complements, rather than replaces, the raw register map:

- raw register catalog: [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md)
- architecture flow: [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md)
- current vs deferred functional-module architecture: [`../architecture/functional-modules.md`](../architecture/functional-modules.md)

## Evidence Status Meanings

| Status | Meaning |
| --- | --- |
| `PROVEN` | Backed directly by current registers, or by an explicitly implemented gateway mechanism whose chain of structural inputs is documented in this catalog and terminates at direct register evidence |
| `HEURISTIC` | Implemented rule is not directly proven by registers; gateway currently uses a convenience or naming rule |
| `COMPOSITE` | Aggregates evidence from constituent decisions; no independent register or mechanism evidence of its own |
| `UNKNOWN` | Gateway intentionally avoids inventing a stronger claim |

## Scope of Validity Meanings

| Scope | Meaning |
| --- | --- |
| `PROTOCOL` | Intended as protocol-level behavior, not tied to one regulator family or one lab topology |
| `PROFILE` | Constrained by regulator-family documentation or profile-specific behavior; not protocol-wide by default |
| `LAB` | Confirmed on the current live lab tuple/topology only |
| `GATEWAY_POLICY` | Local gateway policy or publication rule, even when motivated by protocol/profile evidence |

## Regulator-Document Constraint Strength Meanings

| Strength | Meaning |
| --- | --- |
| `DESCRIPTIVE` | Background or terminology only; does not materially constrain the semantic rule |
| `CORROBORATING` | Supports a relationship already visible in registers or code, but does not define it by itself |
| `CONSTRAINING` | Narrows the plausible interpretation space for a profile/configuration |
| `NON_AUTHORITATIVE` | Useful context, but must not be treated as hard proof for the semantic rule |

## B524-SD-01 — B524 Semantic Root Availability

| Field | Value |
| --- | --- |
| Semantic effect | Enables or disables B524-backed structure discovery for zones, circuits, radio devices, FM5, solar, and cylinders |
| Source registers | No single register. This is a capability-discovery rule over B524 request/response behavior on candidate slave addresses. |
| Reference | [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md), [`../architecture/b524-semantic-root-discovery.md`](../architecture/b524-semantic-root-discovery.md) |
| Source document title | None. Product identity and regulator branding are not required to prove B524 semantic-root availability. |
| Source section | None |
| Supporting statement | None. Identity enrichment and branding classification are separate from the structural precondition that a slave endpoint responds coherently as a B524 semantic root. |
| Constraint strength | None |
| Scope of validity | `PROTOCOL` for the capability gate; `GATEWAY_POLICY` for candidate ordering and multi-root selection policy |
| Evaluation rule | B524-backed structure discovery is allowed once at least one candidate slave address responds coherently to B524 discovery probes. Scan may start at `0x15` for convenience, but it must not be limited to `0x15` and must not require known product identity. |
| Fallback / unknown behavior | If no candidate slave proves B524 capability, B524-backed families remain unavailable. Unknown identity does not block discovery once capability is proven. |
| Published effect | `zones`, `circuits`, `radioDevices`, `fm5SemanticMode`, `solar`, and `cylinders` are eligible for structural evaluation once a B524 semantic root is available. |
| Evidence status | `PROVEN` for the capability gate; candidate ordering remains `GATEWAY_POLICY` |
| Code anchors | Canonical contract: `refreshDiscovery()` root-discovery phase. Current implementation still uses `findDeviceAddressByPrefix()` and therefore diverges from this contract. |

Current implementation note: the gateway still uses `findDeviceAddressByPrefix("BASV")` in `refreshDiscovery()`. This is documented as code debt and must not be read as the semantic contract.

## B524-SD-02 — Zone Instance Discovery

| Field | Value |
| --- | --- |
| Semantic effect | Determines which zone instances exist and are eligible for publication |
| Source registers | `GG=0x03 RR=0x001C` (`zone_index`) |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance) |
| Source document title | `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica`; `Vaillant VRC 700/6 -- Operating Instructions` |
| Source section | `Distribucion de zonas y circuitos de calefaccion`; `3.3 Zones` |
| Supporting statement | In the section `Distribucion de zonas y circuitos de calefaccion`, the multiMATIC training states "Con un VR 71: Hasta 3 zonas" and "Con un VR 71 + VR 70 (hasta 3): Hasta 9 circuitos de calefaccion de mezcla y 9 zonas". In `3.3 Zones`, the VRC 700 operating instructions state "If more than one zone is available, the system control controls the available zones". These statements constrain plausible zone cardinality but do not replace the direct B524 presence probe. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `PROTOCOL` for direct B524 probe path; `GATEWAY_POLICY` for `ebusd grab` fallback |
| Evaluation rule | `refreshDiscovery()` probes instances `0x00..0x0A`; any readable non-`0xFF` index marks the instance as present |
| Fallback / unknown behavior | If direct probes yield no present zones, gateway may hydrate zone presence from `ebusd grab`; that fallback is not a B524-native proof path |
| Published effect | Present instances enter the zone presence FSM and can become `zones[]` entries; absent instances are not published |
| Evidence status | `PROVEN` for direct B524 probes, `HEURISTIC` for `ebusd grab` fallback |
| Code anchors | `refreshDiscovery()`, `reconcileDiscoveryPresence()` |

## B524-SD-03 — Zone Publication Is Controlled by Zone Presence FSM

| Field | Value |
| --- | --- |
| Semantic effect | Prevents transient probe misses from adding/removing zone instances immediately |
| Source registers | Inherited structural input from SD-02, whose primary register is `GG=0x03 RR=0x001C` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance), [`../architecture/zone-presence-fsm.md`](../architecture/zone-presence-fsm.md) |
| Source document title | `Vaillant VRC 700/6 -- Operating Instructions` |
| Source section | `3.3 Zones` |
| Supporting statement | In `3.3 Zones`, the operating instructions describe zones as installation-level structure that the control manages when available, but they do not document hit/miss hysteresis. The structural input for this FSM is the zone-presence evidence described in SD-02; the hysteresis behavior itself remains an explicit gateway mechanism rather than a regulator-documented rule. |
| Constraint strength | `DESCRIPTIVE` |
| Scope of validity | `GATEWAY_POLICY` |
| Evaluation rule | `markZonePresentLocked()` and `markZoneMissingLocked()` apply hit/miss hysteresis to the zone-presence evidence established by SD-02 before creating or deleting `p.zones[instance]` |
| Fallback / unknown behavior | Thresholds are runtime configuration, not protocol data |
| Published effect | `zones[]` reflects stable semantic presence, not one-shot probe results |
| Evidence status | `PROVEN` for the implemented FSM behavior |
| Code anchors | `applyZonePresenceProbes()`, `markZonePresentLocked()`, `markZoneMissingLocked()` |

## B524-SD-04 — Zone Name Resolution and Fallback

| Field | Value |
| --- | --- |
| Semantic effect | Determines `zones[].name` |
| Source registers | `GG=0x03 RR=0x0016` (`name`), `RR=0x0017` (`name_prefix`), `RR=0x0018` (`name_suffix`) |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance) |
| Source document title | `Vaillant VRC 700/6 -- Operating Instructions`; `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica` |
| Source section | `5.2.15 Changing a zone name`; `Menu Ajustes basicos` |
| Supporting statement | In `5.2.15 Changing a zone name`, the VRC 700 operating instructions say "You can now modify the factory-set zone names as you wish". In `Menu Ajustes basicos`, the multiMATIC training lists "Introducir nombre de zona (por zona)". This supports the existence of user-configurable zone names, but the fallback label `Zone N` remains a local publication convenience. |
| Constraint strength | `CORROBORATING` |
| Scope of validity | `PROTOCOL` for register-backed names; `GATEWAY_POLICY` for the `Zone N` fallback |
| Evaluation rule | `refreshConfig()` prefers `RR=0x0016`; otherwise it composes `prefix + suffix`; `publishZones()` falls back to `Zone N` if the merged name is still blank |
| Fallback / unknown behavior | `Zone N` is a local publication fallback, not a protocol-provided name |
| Published effect | Every published zone has a stable display name even when no B524 name string is available |
| Evidence status | `PROVEN` for register reads, `HEURISTIC` for `Zone N` fallback |
| Code anchors | `refreshConfig()`, `composeZoneName()`, `publishZones()` |

## B524-SD-05 — Room Temperature Zone Mapping

| Field | Value |
| --- | --- |
| Semantic effect | Defines `zones[].config.roomTemperatureZoneMapping` and feeds later attachment decisions |
| Source registers | `GG=0x03 RR=0x0013` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance), [`ebus-vaillant-B524-register-map.md#zmapping--zone-room-temperature-sensor-mapping`](./ebus-vaillant-B524-register-map.md#zmapping--zone-room-temperature-sensor-mapping) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `4.2.1 VR 92 Remote Control Unit` |
| Supporting statement | In `4.2.1 VR 92 Remote Control Unit`, the VRC 720 training says "Each VR 92 is assigned to a specific zone". This corroborates the existence of explicit zone-to-room-sensor attachment semantics, but the authoritative proof path remains the B524 register `GG=0x03 RR=0x0013`. The remote-side `zone_assignment` on `GG=0x09/0x0A RR=0x0025` is documented as a corroboration opportunity, not as a formal validation gate. |
| Constraint strength | `CORROBORATING` |
| Scope of validity | `PROTOCOL` |
| Evaluation rule | `refreshState()` reads the raw value; `publishZones()` exposes the decoded integer via `decodeRoomTemperatureZoneMapping()` |
| Fallback / unknown behavior | Missing or undecodable values are published as absent rather than synthesized |
| Published effect | Consumers receive explicit zone-to-room-sensor mapping data instead of guessing |
| Evidence status | `PROVEN` |
| Code anchors | `refreshState()`, `decodeRoomTemperatureZoneMapping()`, `publishZones()` |

## B524-SD-06 — Zone-to-Circuit Index Derivation

| Field | Value |
| --- | --- |
| Semantic effect | Derives `zones[].config.associatedCircuit` from the raw zone mapping value when the current lab-backed conversion applies |
| Source registers | Primary source `GG=0x03 RR=0x0013` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance) |
| Source document title | `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica`; `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `Zonas 1 a 9`; `Installer Level -- Zones 1 to 9` |
| Supporting statement | In `Zonas 1 a 9`, the multiMATIC training exposes `Asignacion de zona` for each zone. In `Installer Level -- Zones 1 to 9`, the VRC 720 training also exposes `Zone assignment`. These statements corroborate the existence of explicit zone-to-circuit assignment, but they do not prove the current `value - 1` zero-based circuit-index derivation formula. |
| Constraint strength | `CORROBORATING` |
| Scope of validity | `LAB` |
| Evaluation rule | `resolveAssociatedCircuitInstance()` reuses the same `GG=0x03 RR=0x0013` value documented in SD-05 and currently interprets values `1..0x20` as one-based circuit assignments, mapped to zero-based circuit instances via `value - 1`. |
| Fallback / unknown behavior | If the current derivation does not yield a usable circuit instance, control passes to SD-07. |
| Published effect | `associatedCircuit` becomes explicit without consumer-side re-derivation when the current lab-backed formula applies |
| Evidence status | `PROVEN` |
| Code anchors | `refreshState()`, `resolveAssociatedCircuitInstance()`, `publishZones()` |

## B524-SD-07 — Zone-to-Circuit Fallback

| Field | Value |
| --- | --- |
| Semantic effect | Provides `zones[].config.associatedCircuit` when SD-06 does not yield a usable circuit instance |
| Source registers | No independent register. This decision consumes the outcome of SD-06. |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance) |
| Source document title | `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica`; `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `Zonas 1 a 9`; `Installer Level -- Zones 1 to 9` |
| Supporting statement | The regulator documents corroborate explicit zone assignment, but they do not define a universal default when the gateway cannot confidently resolve a circuit instance from the raw mapping value. The fallback-to-zone-instance branch is therefore an explicit gateway policy. |
| Constraint strength | `NON_AUTHORITATIVE` |
| Scope of validity | `GATEWAY_POLICY` |
| Evaluation rule | For `nil`, `0`, `0xFF`, or out-of-range mapping values, `resolveAssociatedCircuitInstance()` falls back to the zone instance. |
| Fallback / unknown behavior | Falling back to the zone instance is a local convenience rule and may not reflect physical topology on every installation. |
| Published effect | `associatedCircuit` remains populated even when the current lab-backed derivation does not apply |
| Evidence status | `HEURISTIC` |
| Code anchors | `resolveAssociatedCircuitInstance()`, `publishZones()` |

## B524-SD-08 — Circuit Instance Discovery

| Field | Value |
| --- | --- |
| Semantic effect | Determines which heating circuit instances exist and whether they are active or inactive |
| Source registers | `GG=0x02 RR=0x0002` (`circuit_type`) |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance), [`ebus-vaillant-B524-register-map.md#mctype--circuit-type`](./ebus-vaillant-B524-register-map.md#mctype--circuit-type) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document`; `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica` |
| Source section | `6.2.2 Settings in the Installation Wizard`; `Distribucion de zonas y circuitos de calefaccion` |
| Supporting statement | In `6.2.2 Settings in the Installation Wizard`, the VRC 720 training documents "Enter the number of heating circuits" as `0-3` with VR 71 and up to `0-9` with VR 71 plus VR 70 expansion. In `Distribucion de zonas y circuitos de calefaccion`, the multiMATIC training states "Hasta 9 circuitos de calefaccion de mezcla y 9 zonas". This constrains expected circuit cardinality, while the gateway still relies on direct `circuit_type` probes for actual publication. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `PROTOCOL` |
| Evaluation rule | `refreshCircuits()` probes instances `0x00..0x0A`; readable `0x0000`, `0x00FF`, and `0xFFFF` are treated as inactive, any other value creates/keeps an active circuit snapshot |
| Fallback / unknown behavior | No synthetic circuit count is invented if type reads never succeed. Helianthus intentionally does **not** derive primary circuit inventory from functional-module topology or hydraulic-scheme inference, because B524 is treated as the authoritative aggregation surface for this structure. The inactive markers `0x00FF` and `0xFFFF` align with common invalid/uninitialized conventions, while `0x0000` is treated as inactive based on current lab observation rather than protocol specification. |
| Published effect | `circuits[]` contains only active discovered instances |
| Evidence status | `PROVEN` |
| Code anchors | `refreshCircuits()`, `mergeCircuitSnapshotNonDestructive()`, `publishCircuits()` |

## B524-SD-09 — Circuit Ownership via `managingDevice`

| Field | Value |
| --- | --- |
| Semantic effect | Defines `circuits[].managingDevice` instead of using a global FM5 threshold |
| Source registers | `GG=0x00 RR=0x0036` (`system_scheme`), `GG=0x00 RR=0x002F` (`module_configuration_vr71`) plus the evaluated `fm5SemanticMode` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x00--systemregulator`](./ebus-vaillant-B524-register-map.md#gg0x00--systemregulator), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcircuitsget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcircuitsget) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `4.3.1 VR 71 Main Connection Center`; `5.2 System Requirements` |
| Supporting statement | In `4.3.1 VR 71 Main Connection Center`, the VRC 720 training says the VR 71 is the "main wiring center" that provides relay outputs for pumps and mixing valves. In `5.2 System Requirements`, the same document says VR 71 is required for systems with more than one heating circuit. This supports the architectural role of VR 71 as a circuit-managing function module, but it does not prove ownership for every controller tuple; unvalidated tuples therefore remain `UNKNOWN`. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `LAB` for the currently validated live tuple; `PROFILE` for the documented VR71 role model; broader tuples remain `UNKNOWN` |
| Evaluation rule | `deriveCircuitManagingDevice()` emits `FUNCTION_MODULE / VR_71 / 0x26` only when `systemScheme == 1`, `moduleConfigurationVR71 == 2`, and `fm5SemanticMode == INTERPRETED`; otherwise it emits `UNKNOWN` |
| Fallback / unknown behavior | Gateway intentionally does not guess another owner for unproven topologies. A documented profile such as `moduleConfigurationVR71 = 3` ("3x mixer circuit") still implies VR 71 circuit ownership in regulator documentation, but the current implementation emits `UNKNOWN` because ownership is presently coupled to `fm5SemanticMode == INTERPRETED`. This is a known implementation gap, not an evidence-free topology. |
| Published effect | GraphQL/MCP/Portal expose explicit per-circuit ownership; HA can parent circuits without global threshold heuristics |
| Evidence status | `PROVEN` for the current live tuple, `UNKNOWN` for all other tuples |
| Code anchors | `refreshSystem()`, `deriveCircuitManagingDevice()`, `publishCircuits()` |

## B524-SD-10 — Radio Device Inclusion and `slot_mode`

| Field | Value |
| --- | --- |
| Semantic effect | Determines which OP=0x06 device slots appear in the published device slot list and how they are classified |
| Source registers | Currently polled: `GG=0x09/0x0A/0x0C RR=0x0001` (`device_connected`), with identity reads `0x0002`, `0x0004`, `0x0023`, and telemetry `0x0019`, `0x0025`, `0x000F`, `0x0007`. Topology contract also defines `GG=0x01/0x02/0x0E/0x0F` as device slot groups — these are not yet polled by the gateway but share the same `device_connected` gating contract |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x09--radio-sensors-vrc7xx-multi-instance-dual-opcode`](./ebus-vaillant-B524-register-map.md#gg0x09--radio-sensors-vrc7xx-multi-instance-dual-opcode), [`ebus-vaillant-B524-register-map.md#gg0x0a--radio-sensors-vr92-multi-instance-dual-opcode`](./ebus-vaillant-B524-register-map.md#gg0x0a--radio-sensors-vr92-multi-instance-dual-opcode), [`ebus-vaillant-B524-register-map.md#gg0x0c--remote-accessories-vr71fm5-multi-instance-remote-only`](./ebus-vaillant-B524-register-map.md#gg0x0c--remote-accessories-vr71fm5-multi-instance-remote-only) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document`; `Vaillant VRC 430f -- Operating and Installation Manual` |
| Source section | `4.2.1 VR 92 Remote Control Unit`; `Learn` screen note in expert-technician material |
| Supporting statement | In `4.2.1 VR 92 Remote Control Unit`, the VRC 720 training documents the VR 92 as a zone-assigned remote control with room temperature and humidity measurement. In the VRC 430f expert-technician material, the note for the `Learn` screen says it is used for training replacement components in the wireless network. This supports the existence of connected remote inventory, but not the gateway-specific heuristic that disconnected `0x0C` entries with identity evidence should be published as inventory. |
| Constraint strength | `CORROBORATING` for connected remote roles; `NON_AUTHORITATIVE` for disconnected inventory inference |
| Scope of validity | `PROTOCOL` for connected-slot publication; `GATEWAY_POLICY` for disconnected inventory inclusion |
| Evaluation rule | `refreshRadioDevices()` always includes connected `0x09/0x0A` slots; for `0x0C` it also includes disconnected entries when `hasRemoteIdentityEvidence()` succeeds; disconnected `0x0C` entries become `slot_mode = "inventory"` |
| Fallback / unknown behavior | `hasRemoteIdentityEvidence()` accepts non-empty firmware or non-zero/non-`0xFFFF` hardware as identity evidence, which is stronger than pure connection state but still heuristic as a “real device” proof. Group-to-device-type assignments used by consumers should be read through the B524 register map, where those mappings are explicitly qualified as current-lab correlations rather than standalone protocol specification. |
| Published effect | `radioDevices[]` contains both active remotes and inventory-evidenced FM5-related accessories, with enough metadata for consumer-side parent resolution |
| Evidence status | `PROVEN` for connected slots, `HEURISTIC` for inventory inclusion |
| Code anchors | `refreshRadioDevices()`, `hasRemoteIdentityEvidence()`, `publishRadioDevices()` |

## B524-SD-11 — FM5 Semantic Mode

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether FM5-backed families are absent, partially evidenced, or fully interpretable |
| Source registers | `GG=0x00 RR=0x002F` (`module_configuration_vr71`), radio inventory/evidence from `GG=0x09/0x0A/0x0C`, plus solar/cylinder readability checks in `GG=0x04` and `GG=0x05` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x00--systemregulator`](./ebus-vaillant-B524-register-map.md#gg0x00--systemregulator), [`ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit`](./ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit), [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `4.3.1 VR 71 Main Connection Center`; `Installer Level -- Solar Circuit` |
| Supporting statement | In `4.3.1 VR 71 Main Connection Center`, the VRC 720 training gives explicit VR 71 configuration meanings: `1` and `2` are solar-related, `3` is "3x mixer circuit", and `6` is `allSTOR exclusive`. In `Installer Level -- Solar Circuit`, it also documents that the solar circuit is shown only for `VR 71 = 1, 2`. This materially strengthens the semantic interpretation of the FM5 tuple, but does not prove all possible controller/profile combinations beyond the documented configurations. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `GATEWAY_POLICY` for the current decision tree; `PROFILE` for the documented VR71 configuration meanings; unvalidated controller tuples remain `UNKNOWN` |
| Evaluation rule | `deriveFM5SemanticMode()` returns `INTERPRETED` only when controller is reachable, `module_configuration_vr71 <= 2`, solar is readable, and cylinders are readable; if not interpreted but FM5 evidence exists, mode is `GPIO_ONLY`; otherwise `ABSENT` |
| Fallback / unknown behavior | `module_configuration_vr71 <= 2` is currently used as the family gate; broader meaning on other controller profiles is not yet proven |
| Published effect | Controls `fm5SemanticMode` and gates publication of `solar`, `cylinders`, and FM5-backed circuit ownership |
| Evidence status | `PROVEN` for the implemented decision tree, `UNKNOWN` for unvalidated controller tuples |
| Code anchors | `refreshFM5Semantic()`, `deriveFM5SemanticMode()`, `publishFM5Semantic()` |

## B524-SD-12 — Solar Family Publication Gate

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether the `solar` family is published at all |
| Source registers | `GG=0x04 RR=0x0001`, `0x0002`, `0x0003`, `0x0007`, `0x0008`, `0x0009`, `0x000B`, gated by FM5 mode |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit`](./ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit), [`ebus-vaillant-B524-register-map.md#ebusv1semanticsolarget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticsolarget) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document`; `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica` |
| Source section | `Installer Level -- Solar Circuit`; `Circuito solar 1` |
| Supporting statement | In `Installer Level -- Solar Circuit`, the VRC 720 training says the `Solar circuit` screen is shown only for `VR 71 = 1, 2`. In `Circuito solar 1`, the multiMATIC training documents solar pump, collector, and solar tank parameters under VR 71-based systems. This strongly supports the family gate for solar-capable VR 71 configurations. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `GATEWAY_POLICY` for the publication gate; `PROFILE` for the documented solar-capable VR71 configurations |
| Evaluation rule | `publishFM5Semantic()` publishes `solar` only when `fm5SemanticMode == INTERPRETED`; otherwise it clears the family |
| Fallback / unknown behavior | No partial solar contract is exposed for `GPIO_ONLY` |
| Published effect | `solar` is either fully present or absent |
| Evidence status | `PROVEN` |
| Code anchors | `readSolarSnapshot()`, `publishFM5Semantic()` |

## B524-SD-13 — Cylinder Family Gate

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether `cylinders[]` may be published at all |
| Source registers | Cylinder family reads come from `GG=0x05`, but family publication is gated by `fm5SemanticMode` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document`; `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica` |
| Source section | `Installer Level -- Solar Circuit`; `Deposito solar 1`; ACS/accumulator sections in multiMATIC training |
| Supporting statement | In `Installer Level -- Solar Circuit`, the VRC 720 training states `Solar accumulator 1 if VR 71 = 2, solar accumulator 1 and solar accumulator 2 if VR 71 = 1`. In `Deposito solar 1` and the ACS/accumulator sections, the multiMATIC training documents solar tank and accumulator parameters under VR 71-based solar configurations. This supports using the FM5/VR71 tuple as the family gate for cylinder-related solar storage semantics. |
| Constraint strength | `CONSTRAINING` |
| Scope of validity | `GATEWAY_POLICY` for the publication gate; `PROFILE` for the documented accumulator-capable VR71 configurations |
| Evaluation rule | `publishFM5Semantic()` publishes cylinder instances only when `fm5SemanticMode == INTERPRETED`; otherwise it clears the family |
| Fallback / unknown behavior | No synthetic “potential cylinders” family is exposed when FM5 is not interpreted |
| Published effect | `cylinders[]` is absent outside interpreted FM5 mode |
| Evidence status | `PROVEN` |
| Code anchors | `refreshFM5Semantic()`, `publishFM5Semantic()` |

## B524-SD-14 — Individual Cylinder Instance Publication

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether a specific cylinder instance is real enough to appear in `cylinders[]` |
| Source registers | `GG=0x05 RR=0x0004` (`temperatureC`), with optional config from `RR=0x0001..0x0003` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget) |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document` |
| Source section | `Installer Level -- Solar Circuit` |
| Supporting statement | In `Installer Level -- Solar Circuit`, the VRC 720 training constrains cardinality at configuration level (`solar accumulator 1` vs `1 and 2` depending on VR 71 config), but it does not document a "config-only cylinder" publication concept. The gateway's stronger rule that a cylinder must have live `temperatureC` evidence remains the actual semantic proof path. |
| Constraint strength | `NON_AUTHORITATIVE` |
| Scope of validity | `GATEWAY_POLICY` |
| Evaluation rule | `hasLiveCylinderEvidence()` requires a decodable `temperatureC`; config-only payloads do not create a cylinder instance |
| Fallback / unknown behavior | Gateway does not publish “config-only cylinders” as maybe-present |
| Published effect | `Cylinder 2`-style ghost instances do not appear unless live temperature evidence exists |
| Evidence status | `PROVEN` |
| Code anchors | `readCylinderSnapshots()`, `hasLiveCylinderEvidence()`, `publishFM5Semantic()` |

## B524-SD-15 — Structural Subordination Contract

| Field | Value |
| --- | --- |
| Semantic effect | Defines the public fields that consumers should use for hierarchy/parenting decisions |
| Source registers | Composite of SD-05, SD-06, SD-07, SD-09, SD-10, SD-11, SD-12, SD-13, and SD-14 |
| Reference | See the source decision entries above |
| Source document title | `Vaillant sensoCOMFORT (VRC 720) -- Training Document`; `Vaillant multiMATIC VRC 700/4f, VRC 700/5 - Control por compensacion climatica` |
| Source section | `4.2.1 VR 92 Remote Control Unit`; `4.3.1 VR 71 Main Connection Center`; `Installer Level -- Zones 1 to 9`; `Installer Level -- Solar Circuit`; `Distribucion de zonas y circuitos de calefaccion`; `Zonas 1 a 9`; `Circuito solar 1`; `Deposito solar 1` |
| Supporting statement | Across `4.2.1 VR 92 Remote Control Unit`, `4.3.1 VR 71 Main Connection Center`, `Installer Level -- Zones 1 to 9`, `Installer Level -- Solar Circuit`, and the multiMATIC sections `Distribucion de zonas y circuitos de calefaccion`, `Zonas 1 a 9`, `Circuito solar 1`, and `Deposito solar 1`, the regulator documents consistently present structure as explicit relationships: zones have room controls and circuit assignments, circuits have types and actuator state, VR 71 owns relay-backed functions, and solar/cylinder screens appear only for certain configurations. This matches the gateway design choice to publish explicit structural fields instead of hidden thresholds, but it does not widen the scope beyond the underlying decisions. This entry is exhaustive only for the currently published structure-bearing fields named below. |
| Constraint strength | `CORROBORATING` |
| Scope of validity | `GATEWAY_POLICY`; each constituent field inherits the narrower scope of its underlying decision |
| Evaluation rule | Gateway publishes structure-bearing fields instead of hidden thresholds: `roomTemperatureZoneMapping`, `associatedCircuit`, `radioDevices[]`, `fm5SemanticMode`, `circuits[].managingDevice`, and gated `solar`/`cylinders` (including per-instance cylinder evidence from SD-14) |
| Fallback / unknown behavior | Consumer-specific parent trees remain consumer behavior; this catalog documents the semantic contract they must consume |
| Published effect | GraphQL/MCP/Portal expose enough structure for consumers such as HA to build explainable parent-child hierarchy without inventing local thresholds |
| Evidence status | `COMPOSITE` |
| Code anchors | `publishZones()`, `publishCircuits()`, `publishRadioDevices()`, `publishFM5Semantic()` |

## Explicit Out of Scope

These are intentionally **not** structural decisions for Phase 1:

- zone operating mode / preset / HVAC action
- DHW mode derivation
- energy merge semantics
- direct-boiler B509 logic

If a future decision touches instance discovery, family gating, or parent/ownership fields, it should be added here instead of remaining implicit in code.
