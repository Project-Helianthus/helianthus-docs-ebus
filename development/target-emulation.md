# Target Emulation (Identify Profiles + VR90 B509 Discovery)

This document tracks implemented Helianthus target-emulation behavior merged in:

- `helianthus-ebusgo` PR [#61](https://github.com/d3vi1/helianthus-ebusgo/pull/61), PR [#65](https://github.com/d3vi1/helianthus-ebusgo/pull/65), and PR [#69](https://github.com/d3vi1/helianthus-ebusgo/pull/69)
- `helianthus-tinyebus` PR [#10](https://github.com/d3vi1/helianthus-tinyebus/pull/10), PR [#14](https://github.com/d3vi1/helianthus-tinyebus/pull/14), and PR [#18](https://github.com/d3vi1/helianthus-tinyebus/pull/18)

## Licensing Boundary

- Protocol-generic field/layout docs stay in **CC0** under `protocols/`.
- Helianthus API names, presets, smoke commands, and package mapping stay in this **AGPL** page.

CC0 references for wire-level model:
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-overview.md#identify-only-profile-fields-generic`
- `protocols/ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27`

## Model Coverage (Helianthus API Surface)

Both implementations expose the same identify-only constructor profile:

- target identity: `address`, `manufacturer`, `device_id`, `software`, `hardware`
- response behavior: fixed response delay + timing envelope validation
- identify recognition rule: match identification query `PB=0x07`, `SB=0x04`
- VR90 optional discovery rule: match `PB=0xB5`, `SB=0x09`, `len(data)==1`, selector `0x24..0x27`

Current implementation constraints:

- identify-only behavior remains unchanged for all presets
- VR90 B509 discovery is opt-in via profile flag (`EnableB509Discovery`)
- unknown B509 selectors remain unmatched (no broad fallback)
- no thermostat/write/register/timer emulation in this profile
- `device_id` is normalized to a 5-byte ASCII slot (trim + truncate/pad)
- `scan_id` is normalized to a 32-byte ASCII slot (trim + truncate/pad with spaces)

## Supported Presets (Current Coverage)

| Preset | Address | Manufacturer | Device ID | Software | Hardware | Scope |
|---|---:|---:|---|---:|---:|---|
| VR90 | `0x15` | `0xB5` | `B7V00` | `0x0422` | `0x5503` | identify recognition + optional B509 scan.id chunk discovery |
| VR_71 | `0x26` | `0xB5` | `VR_71` | `0x0100` | `0x5904` | identify-only recognition |

Known limits:

- Presets are fixed defaults for recognition tests, not full device models.
- Additional profiles can be created through the generic constructor.
- B509 discovery coverage is currently only implemented for VR90 compatibility targets.
- Timing accuracy expectations remain firmware-first for strict response windows.

## Implementation Mapping

### `helianthus-ebusgo`

- Package: `emulation`
- Generic API:
  - `NewIdentifyOnlyTarget(profile IdentifyOnlyProfile)`
  - `PresetVR90IdentifyOnlyProfile()`
  - `PresetVR71IdentifyOnlyProfile()`
- VR90 compatibility API:
  - `DefaultVR90Profile()`
  - `NewVR90Target(profile VR90Profile)` (kept for backward compatibility)
  - `VR90Profile.EnableB509Discovery` (opt-in selector handling for `0x24..0x27`)
  - `VR90Profile.ScanID` (scan.id source, normalized to 32-byte chunk space)

Smoke commands:

```bash
cd /path/to/helianthus-ebusgo
./scripts/smoke-identify-only.sh
./scripts/smoke-vr90-minimal.sh
go test ./emulation -run '^TestSmokeVR90B509DiscoveryQuerySet$' -count=1 -v
```

Repository links:

- https://github.com/d3vi1/helianthus-ebusgo/blob/main/scripts/smoke-identify-only.sh
- https://github.com/d3vi1/helianthus-ebusgo/blob/main/scripts/smoke-vr90-minimal.sh

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

Smoke commands:

```bash
cd /path/to/helianthus-tinyebus
./scripts/smoke-vr90-minimal.sh vr90
./scripts/smoke-vr90-minimal.sh vr71
./scripts/smoke-vr90-minimal.sh all
GOWORK=off go test ./firmware/emulation -run '^TestSmokeVR90B509DiscoveryQuerySet$' -count=1 -v
```

Repository link:

- https://github.com/d3vi1/helianthus-tinyebus/blob/main/scripts/smoke-vr90-minimal.sh

## Timing Rationale

For strict target emulation, timing should run firmware-side (adapter MCU / TinyGo runtime) where response delay control is predictable.

Host-side relay paths (for example `ebusd-tcp`) are still useful for functional checks but can add scheduler/network jitter, so they should not be treated as cycle-accurate emulation backends.

See also: `protocols/ebusd-tcp.md#timing-caveat-for-target-emulation`.

## Out of Scope (Current Phase)

The following remain out of scope for the current identify + B509 profile abstraction:

- full VR90 thermostat/register coverage beyond identify + B509 scan.id chunk discovery
- full VR_71 command/register behavior beyond identify
- VR92, VR70, recoVAIR, VR50 full emulation
