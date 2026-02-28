# Target Emulation (Identify Profiles + VR90/VR92 B509 + Mapped Commands)

This document tracks implemented Helianthus target-emulation behavior merged in:

- `helianthus-ebusgo` PR [#61](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/61), PR [#65](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/65), PR [#69](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/69), PR [#71](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/71), and PR [#78](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/78)
- `helianthus-tinyebus` PR [#10](https://github.com/Project-Helianthus/helianthus-tinyebus/pull/10), PR [#14](https://github.com/Project-Helianthus/helianthus-tinyebus/pull/14), PR [#18](https://github.com/Project-Helianthus/helianthus-tinyebus/pull/18), and PR [#20](https://github.com/Project-Helianthus/helianthus-tinyebus/pull/20)

## Licensing Boundary

- Protocol-generic field/layout docs stay in **CC0** under `protocols/`.
- Helianthus API names, presets, smoke commands, and package mapping stay in this **AGPL** page.

CC0 references for wire-level model:
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-overview.md#identify-only-profile-fields-generic`
- `protocols/ebus-vaillant.md#register-access-0xb5-0x09`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`

## Model Coverage (Helianthus API Surface)

Both implementations expose the same identify-only constructor profile:

- target identity: `address`, `manufacturer`, `device_id`, `software`, `hardware`
- response behavior: fixed response delay + timing envelope validation
- identify recognition rule: match identification query `PB=0x07`, `SB=0x04`
- VR90/VR92 optional discovery rule: match `PB=0xB5`, `SB=0x09`, `len(data)==1`, selector `0x24..0x27`
- VR90/VR92 optional mapped-command rules: match `PB/SB` plus optional payload matcher (exact or prefix), then return deterministic response bytes

Current implementation constraints:

- identify-only behavior remains unchanged for all presets
- VR90/VR92 B509 discovery is opt-in via profile flag (`EnableB509Discovery`)
- VR90/VR92 mapped-command behavior is opt-in via profile map entries (`MappedCommands`)
- unknown B509 selectors remain unmatched (no broad fallback)
- unknown mapped commands remain unmatched (`ErrNoMatchingRule`)
- no thermostat/write/register/timer state machine emulation in this profile
- `device_id` is normalized to a 5-byte ASCII slot (trim + truncate/pad)
- `scan_id` is normalized to a 32-byte ASCII slot (trim + truncate/pad with spaces)

## Supported Presets (Current Coverage)

| Preset | Address | Manufacturer | Device ID | Software | Hardware | Scope |
|---|---:|---:|---|---:|---:|---|
| VR90 | `0x15` | `0xB5` | `B7V00` | `0x0422` | `0x5503` | identify recognition + optional B509 scan.id chunk discovery + optional mapped commands |
| VR92 | `0x30` | `0xB5` | `VR_92` | `0x0514` | `0x1204` | identify recognition + optional B509 scan.id chunk discovery + optional mapped commands |
| VR_71 | `0x26` | `0xB5` | `VR_71` | `0x0100` | `0x5904` | identify-only recognition |

Known limits:

- Presets are fixed defaults for recognition tests, not full device models.
- Additional profiles can be created through the generic constructor.
- B509 discovery and mapped-command coverage are implemented for VR90 and VR92 compatibility targets.
- For VR92, enabling B509 discovery requires an explicit `ScanID` value in profile configuration.
- Mapped responses are deterministic byte payloads and do not model register-side effects.
- Timing accuracy expectations remain firmware-first for strict response windows.

## Mapped-Command Model (VR90/VR92 Compatibility)

Each mapped-command entry adds one deterministic match/response rule inside the VR90 profile:

- command key: `Primary` + `Secondary`
- optional payload matcher:
  - `PayloadExact`: request payload must match exactly
  - `PayloadPrefix`: request payload must start with the configured prefix
  - no payload matcher: any payload matches for that `Primary`/`Secondary`
- response payload: `ResponseData` bytes returned as-is
- rule label: `Name` (if empty, an auto-generated name is assigned during normalization)

All mapped-command responses use the same profile response delay and timing envelope checks as identify and B509 responses.

## Rule Precedence and Fallback

Matching order is deterministic and shared across both implementations:

1. built-in identify rule (`0x07/0x04`)
2. built-in B509 scan.id rule (`0xB5/0x09`, selector `0x24..0x27`) when enabled
3. mapped-command rules in declaration order

Implications:

- built-in rules keep precedence over mapped collisions on the same `PB/SB`
- mapped rules are first-match-wins; declaration order matters (a broad prefix rule can shadow a later exact rule)
- if no rule matches, emulation returns `ErrNoMatchingRule`

## Validation Constraints

Profile-level normalization and validation:

- response delay must satisfy the configured timing envelope
- `device_id` is required after trim and normalized to 5 ASCII bytes
- `scan_id` is normalized to 32 ASCII bytes (trim + truncate/pad with spaces)

Mapped-command validation:

- `PayloadExact` and `PayloadPrefix` are mutually exclusive (setting both is invalid)
- `ResponseData` must be non-empty
- input byte slices are copied during normalization to keep response payloads immutable from caller mutations

## Smoke Path (Mapped Command Coverage)

Canonical VR90 mapped-command smoke sequence:

1. identify query: `PB=0x07`, `SB=0x04`
2. B509 discovery query: `PB=0xB5`, `SB=0x09`, selector `0x24`
3. mapped-command query: example `PB=0xB5`, `SB=0x06`, data prefix `0x01 0x00 ...`
4. verify all responses remain within the configured timing envelope

## Implementation Mapping

### `helianthus-ebusgo`

- Package: `emulation`
- Generic API:
  - `NewIdentifyOnlyTarget(profile IdentifyOnlyProfile)`
  - `PresetVR90IdentifyOnlyProfile()`
  - `PresetVR92IdentifyOnlyProfile()`
  - `PresetVR71IdentifyOnlyProfile()`
- VR90 compatibility API:
  - `DefaultVR90Profile()`
  - `NewVR90Target(profile VR90Profile)` (kept for backward compatibility)
  - `VR90Profile.EnableB509Discovery` (opt-in selector handling for `0x24..0x27`)
  - `VR90Profile.ScanID` (scan.id source, normalized to 32-byte chunk space)
  - `VR90Profile.MappedCommands` (optional deterministic command map)
  - `VR90MappedCommand` (`Name`, `Primary`, `Secondary`, `PayloadExact`, `PayloadPrefix`, `ResponseData`)
- VR92 compatibility API:
  - `DefaultVR92Profile()`
  - `NewVR92Target(profile VR92Profile)`
  - `VR92Profile.EnableB509Discovery` (opt-in selector handling for `0x24..0x27`)
  - `VR92Profile.ScanID` (required when B509 discovery is enabled)
  - `VR92Profile.MappedCommands` (optional deterministic command map)
  - `VR92MappedCommand` (`Name`, `Primary`, `Secondary`, `PayloadExact`, `PayloadPrefix`, `ResponseData`)

Smoke commands:

```bash
cd /path/to/helianthus-ebusgo
./scripts/smoke-identify-only.sh
./scripts/smoke-vr90-minimal.sh
go test ./emulation -run '^TestSmokeVR90MappedCommandQuerySet$' -count=1 -v
```

Repository links:

- https://github.com/Project-Helianthus/helianthus-ebusgo/blob/main/scripts/smoke-identify-only.sh
- https://github.com/Project-Helianthus/helianthus-ebusgo/blob/main/scripts/smoke-vr90-minimal.sh

### `helianthus-tinyebus`

- Package: `firmware/emulation`
- Generic API:
  - `NewIdentifyOnlyTarget(profile IdentifyOnlyProfile)`
  - `PresetVR90IdentifyOnlyProfile()`
  - `PresetVR71IdentifyOnlyProfile()`
- VR90 compatibility API:
  - `DefaultVR90Profile()`
  - `NewVR90Target(profile VR90Profile)` (kept for backward compatibility)
  - `VR90Profile.EnableB509Discovery` (opt-in selector handling for `0x24..0x27`)
  - `VR90Profile.ScanID` (scan.id source, normalized to 32-byte chunk space)
  - `VR90Profile.MappedCommands` (optional deterministic command map)
  - `VR90MappedCommand` (`Name`, `Primary`, `Secondary`, `PayloadExact`, `PayloadPrefix`, `ResponseData`)

Smoke commands:

```bash
cd /path/to/helianthus-tinyebus
./scripts/smoke-vr90-minimal.sh vr90
./scripts/smoke-vr90-minimal.sh vr71
./scripts/smoke-vr90-minimal.sh all
GOWORK=off go test ./firmware/emulation -run '^TestSmokeVR90MappedCommandQuerySet$' -count=1 -v
```

Repository link:

- https://github.com/Project-Helianthus/helianthus-tinyebus/blob/main/scripts/smoke-vr90-minimal.sh

## Timing Rationale

For strict target emulation, timing should run firmware-side (adapter MCU / TinyGo runtime) where response delay control is predictable.

Host-side relay paths (for example `ebusd-tcp`) are still useful for functional checks but can add scheduler/network jitter, so they should not be treated as cycle-accurate emulation backends.

See also: `protocols/ebusd-tcp.md#timing-caveat-for-target-emulation`.

## Out of Scope (Current Phase)

The following remain out of scope for the current identify + B509 + mapped-command profile abstraction:

- full VR90 thermostat/register coverage beyond identify + B509 scan.id chunk discovery + deterministic mapped responses
- full VR_71 command/register behavior beyond identify
- VR70, recoVAIR, VR50 full emulation
