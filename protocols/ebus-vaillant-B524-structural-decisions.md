# Vaillant B524 Structural Decision Catalog

This page documents the **implemented structural decisions** in `helianthus-ebusgateway` for B524-backed semantic discovery.

Each entry records:

- the source of evidence;
- how the gateway evaluates that evidence;
- what public semantic effect the decision has;
- whether the rule is `PROVEN`, `HEURISTIC`, or `UNKNOWN`.

This document is authoritative for Phase 1 structural discovery and complements, rather than replaces, the raw register map:

- raw register catalog: [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md)
- architecture flow: [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md)

## Evidence Status Meanings

| Status | Meaning |
| --- | --- |
| `PROVEN` | Backed directly by current registers and implemented behavior |
| `HEURISTIC` | Implemented rule is not directly proven by registers; gateway currently uses a convenience or naming rule |
| `UNKNOWN` | Gateway intentionally avoids inventing a stronger claim |

## B524-SD-01 — Controller Presence Gates B524 Structure Discovery

| Field | Value |
| --- | --- |
| Semantic effect | Enables or disables B524-backed structure discovery for zones, circuits, radio devices, FM5, solar, and cylinders |
| Source registers | None |
| Reference | Not a B524 register rule; source is registry discovery |
| Evaluation rule | `refreshDiscovery()` uses `findDeviceAddressByPrefix(p.reg, "BASV")`; when not found, controller becomes `0`, B524-backed families are cleared/reset, and FM5 mode becomes `ABSENT` |
| Fallback / unknown behavior | Prefix match on `BASV` is a naming heuristic, not a protocol proof of controller role |
| Published effect | `zones`, `circuits`, and `radioDevices` publish as empty/cache-backed; `fm5SemanticMode` becomes `ABSENT`; `solar` and `cylinders` are cleared |
| Evidence status | `HEURISTIC` |
| Code anchors | `refreshDiscovery()`, `findDeviceAddressByPrefix()` |

## B524-SD-02 — Zone Instance Discovery

| Field | Value |
| --- | --- |
| Semantic effect | Determines which zone instances exist and are eligible for publication |
| Source registers | `GG=0x03 RR=0x001C` (`zone_index`) |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance) |
| Evaluation rule | `refreshDiscovery()` probes instances `0x00..0x0A`; any readable non-`0xFF` index marks the instance as present |
| Fallback / unknown behavior | If direct probes yield no present zones, gateway may hydrate zone presence from `ebusd grab`; that fallback is not a B524-native proof path |
| Published effect | Present instances enter the zone presence FSM and can become `zones[]` entries; absent instances are not published |
| Evidence status | `PROVEN` for direct B524 probes, `HEURISTIC` for `ebusd grab` fallback |
| Code anchors | `refreshDiscovery()`, `reconcileDiscoveryPresence()` |

## B524-SD-03 — Zone Publication Is Controlled by Zone Presence FSM

| Field | Value |
| --- | --- |
| Semantic effect | Prevents transient probe misses from adding/removing zone instances immediately |
| Source registers | Primary source remains `GG=0x03 RR=0x001C` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance), [`../architecture/zone-presence-fsm.md`](../architecture/zone-presence-fsm.md) |
| Evaluation rule | `markZonePresentLocked()` and `markZoneMissingLocked()` apply hit/miss hysteresis before creating or deleting `p.zones[instance]` |
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
| Evaluation rule | `refreshState()` reads the raw value; `publishZones()` exposes the decoded integer via `decodeRoomTemperatureZoneMapping()` |
| Fallback / unknown behavior | Missing or undecodable values are published as absent rather than synthesized |
| Published effect | Consumers receive explicit zone-to-room-sensor mapping data instead of guessing |
| Evidence status | `PROVEN` |
| Code anchors | `refreshState()`, `decodeRoomTemperatureZoneMapping()`, `publishZones()` |

## B524-SD-06 — Associated Circuit Derivation for Zones

| Field | Value |
| --- | --- |
| Semantic effect | Defines `zones[].config.associatedCircuit` |
| Source registers | Primary source `GG=0x03 RR=0x0013`; supporting lookup `GG=0x02 RR=0x0002` for circuit type on the resolved circuit instance |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance), [`ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance) |
| Evaluation rule | `resolveAssociatedCircuitInstance()` maps `roomTemperatureZoneMapping` values `1..0x20` to zero-based circuit instances and falls back to the zone instance for `nil`, `0`, `0xFF`, or out-of-range values |
| Fallback / unknown behavior | Falling back to the zone instance is a local convenience rule and may not reflect physical topology on every installation |
| Published effect | `associatedCircuit` is explicit in the semantic contract and is available to consumers without re-derivation |
| Evidence status | `PROVEN` for the mapping value, `HEURISTIC` for the fallback-to-zone-instance branch |
| Code anchors | `refreshState()`, `resolveAssociatedCircuitInstance()`, `publishZones()` |

## B524-SD-07 — Circuit Instance Discovery

| Field | Value |
| --- | --- |
| Semantic effect | Determines which heating circuit instances exist and whether they are active or inactive |
| Source registers | `GG=0x02 RR=0x0002` (`circuit_type`) |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance), [`ebus-vaillant-B524-register-map.md#mctype--circuit-type`](./ebus-vaillant-B524-register-map.md#mctype--circuit-type) |
| Evaluation rule | `refreshCircuits()` probes instances `0x00..0x0A`; readable `0x0000`, `0x00FF`, and `0xFFFF` are treated as inactive, any other value creates/keeps an active circuit snapshot |
| Fallback / unknown behavior | No synthetic circuit count is invented if type reads never succeed |
| Published effect | `circuits[]` contains only active discovered instances |
| Evidence status | `PROVEN` |
| Code anchors | `refreshCircuits()`, `mergeCircuitSnapshotNonDestructive()`, `publishCircuits()` |

## B524-SD-08 — Circuit Ownership via `managingDevice`

| Field | Value |
| --- | --- |
| Semantic effect | Defines `circuits[].managingDevice` instead of using a global FM5 threshold |
| Source registers | `GG=0x00 RR=0x0036` (`system_scheme`), `GG=0x00 RR=0x002F` (`module_configuration_vr71`) plus the evaluated `fm5SemanticMode` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x00--systemregulator`](./ebus-vaillant-B524-register-map.md#gg0x00--systemregulator), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcircuitsget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcircuitsget) |
| Evaluation rule | `deriveCircuitManagingDevice()` emits `FUNCTION_MODULE / VR_71 / 0x26` only when `systemScheme == 1`, `moduleConfigurationVR71 == 2`, and `fm5SemanticMode == INTERPRETED`; otherwise it emits `UNKNOWN` |
| Fallback / unknown behavior | Gateway intentionally does not guess another owner for unproven topologies |
| Published effect | GraphQL/MCP/Portal expose explicit per-circuit ownership; HA can parent circuits without global threshold heuristics |
| Evidence status | `PROVEN` for the current live tuple, `UNKNOWN` for all other tuples |
| Code anchors | `refreshSystem()`, `deriveCircuitManagingDevice()`, `publishCircuits()` |

## B524-SD-09 — Radio Device Inclusion and `slot_mode`

| Field | Value |
| --- | --- |
| Semantic effect | Determines which remote/radio devices appear in `radioDevices[]` and how they are classified |
| Source registers | `GG=0x09/0x0A/0x0C RR=0x0001`, `0x0002`, `0x0004`, `0x0023`, with supporting telemetry reads such as `0x0019`, `0x0025`, `0x000F`, `0x0007` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x09--radio-sensors-vrc7xx-multi-instance-dual-opcode`](./ebus-vaillant-B524-register-map.md#gg0x09--radio-sensors-vrc7xx-multi-instance-dual-opcode), [`ebus-vaillant-B524-register-map.md#gg0x0a--radio-sensors-vr92-multi-instance-dual-opcode`](./ebus-vaillant-B524-register-map.md#gg0x0a--radio-sensors-vr92-multi-instance-dual-opcode), [`ebus-vaillant-B524-register-map.md#gg0x0c--remote-accessories-vr71fm5-multi-instance-remote-only`](./ebus-vaillant-B524-register-map.md#gg0x0c--remote-accessories-vr71fm5-multi-instance-remote-only) |
| Evaluation rule | `refreshRadioDevices()` always includes connected `0x09/0x0A` slots; for `0x0C` it also includes disconnected entries when `hasRemoteIdentityEvidence()` succeeds; disconnected `0x0C` entries become `slot_mode = "inventory"` |
| Fallback / unknown behavior | `hasRemoteIdentityEvidence()` accepts non-empty firmware or non-zero/non-`0xFFFF` hardware as identity evidence, which is stronger than pure connection state but still heuristic as a “real device” proof |
| Published effect | `radioDevices[]` contains both active remotes and inventory-evidenced FM5-related accessories, with enough metadata for consumer-side parent resolution |
| Evidence status | `PROVEN` for connected slots, `HEURISTIC` for inventory inclusion |
| Code anchors | `refreshRadioDevices()`, `hasRemoteIdentityEvidence()`, `publishRadioDevices()` |

## B524-SD-10 — FM5 Semantic Mode

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether FM5-backed families are absent, partially evidenced, or fully interpretable |
| Source registers | `GG=0x00 RR=0x002F` (`module_configuration_vr71`), radio inventory/evidence from `GG=0x09/0x0A/0x0C`, plus solar/cylinder readability checks in `GG=0x04` and `GG=0x05` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x00--systemregulator`](./ebus-vaillant-B524-register-map.md#gg0x00--systemregulator), [`ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit`](./ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit), [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance) |
| Evaluation rule | `deriveFM5SemanticMode()` returns `INTERPRETED` only when controller is reachable, `module_configuration_vr71 <= 2`, solar is readable, and cylinders are readable; if not interpreted but FM5 evidence exists, mode is `GPIO_ONLY`; otherwise `ABSENT` |
| Fallback / unknown behavior | `module_configuration_vr71 <= 2` is currently used as the family gate; broader meaning on other controller profiles is not yet proven |
| Published effect | Controls `fm5SemanticMode` and gates publication of `solar`, `cylinders`, and FM5-backed circuit ownership |
| Evidence status | `PROVEN` for the implemented decision tree, `UNKNOWN` for unvalidated controller tuples |
| Code anchors | `refreshFM5Semantic()`, `deriveFM5SemanticMode()`, `publishFM5Semantic()` |

## B524-SD-11 — Solar Family Publication Gate

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether the `solar` family is published at all |
| Source registers | `GG=0x04 RR=0x0001`, `0x0002`, `0x0003`, `0x0007`, `0x0008`, `0x0009`, `0x000B`, gated by FM5 mode |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit`](./ebus-vaillant-B524-register-map.md#gg0x04--solar-circuit), [`ebus-vaillant-B524-register-map.md#ebusv1semanticsolarget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticsolarget) |
| Evaluation rule | `publishFM5Semantic()` publishes `solar` only when `fm5SemanticMode == INTERPRETED`; otherwise it clears the family |
| Fallback / unknown behavior | No partial solar contract is exposed for `GPIO_ONLY` |
| Published effect | `solar` is either fully present or absent |
| Evidence status | `PROVEN` |
| Code anchors | `readSolarSnapshot()`, `publishFM5Semantic()` |

## B524-SD-12 — Cylinder Family Gate

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether `cylinders[]` may be published at all |
| Source registers | Cylinder family reads come from `GG=0x05`, but family publication is gated by `fm5SemanticMode` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget) |
| Evaluation rule | `publishFM5Semantic()` publishes cylinder instances only when `fm5SemanticMode == INTERPRETED`; otherwise it clears the family |
| Fallback / unknown behavior | No synthetic “potential cylinders” family is exposed when FM5 is not interpreted |
| Published effect | `cylinders[]` is absent outside interpreted FM5 mode |
| Evidence status | `PROVEN` |
| Code anchors | `refreshFM5Semantic()`, `publishFM5Semantic()` |

## B524-SD-13 — Individual Cylinder Instance Publication

| Field | Value |
| --- | --- |
| Semantic effect | Determines whether a specific cylinder instance is real enough to appear in `cylinders[]` |
| Source registers | `GG=0x05 RR=0x0004` (`temperatureC`), with optional config from `RR=0x0001..0x0003` |
| Reference | [`ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance`](./ebus-vaillant-B524-register-map.md#gg0x05--cylinders-multi-instance), [`ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget`](./ebus-vaillant-B524-register-map.md#ebusv1semanticcylindersget) |
| Evaluation rule | `hasLiveCylinderEvidence()` requires a decodable `temperatureC`; config-only payloads do not create a cylinder instance |
| Fallback / unknown behavior | Gateway does not publish “config-only cylinders” as maybe-present |
| Published effect | `Cylinder 2`-style ghost instances do not appear unless live temperature evidence exists |
| Evidence status | `PROVEN` |
| Code anchors | `readCylinderSnapshots()`, `hasLiveCylinderEvidence()`, `publishFM5Semantic()` |

## B524-SD-14 — Structural Subordination Contract

| Field | Value |
| --- | --- |
| Semantic effect | Defines the public fields that consumers should use for hierarchy/parenting decisions |
| Source registers | Composite of SD-05, SD-08, SD-09, SD-10, SD-11, and SD-13 |
| Reference | See the source decision entries above |
| Evaluation rule | Gateway publishes structure-bearing fields instead of hidden thresholds: `roomTemperatureZoneMapping`, `associatedCircuit`, `radioDevices[]`, `fm5SemanticMode`, `circuits[].managingDevice`, and gated `solar`/`cylinders` |
| Fallback / unknown behavior | Consumer-specific parent trees remain consumer behavior; this catalog documents the semantic contract they must consume |
| Published effect | GraphQL/MCP/Portal expose enough structure for consumers such as HA to build explainable parent-child hierarchy without inventing local thresholds |
| Evidence status | `PROVEN` as a contract statement built from the decisions above |
| Code anchors | `publishZones()`, `publishCircuits()`, `publishRadioDevices()`, `publishFM5Semantic()` |

## Explicit Out of Scope

These are intentionally **not** structural decisions for Phase 1:

- zone operating mode / preset / HVAC action
- DHW mode derivation
- energy merge semantics
- direct-boiler B509 logic

If a future decision touches instance discovery, family gating, or parent/ownership fields, it should be added here instead of remaining implicit in code.
