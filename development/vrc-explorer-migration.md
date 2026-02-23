# VRC-Explorer Deprecation and Migration Guide

## Scope

This guide defines the deprecation path from **VRC-Explorer (Python)** to the
**Helianthus Portal (gateway-native, Go-first)**.

It applies to:
- reverse-engineering workflows
- evidence collection workflows
- issue authoring workflows

It does not change:
- eBUS transport behavior
- gateway semantic contract ownership
- HA integration responsibility boundaries

## Deprecation Policy

- VRC-Explorer is marked **deprecated** as of **2026-02-24**.
- Portal is the strategic replacement surface.
- VRC-Explorer receives only critical fixes during migration window.
- New feature work lands in Portal only.

## Rollout Timeline

1. **Notice + freeze start (2026-02-24)**
   - docs + portal deprecation banner published
   - VRC-Explorer set to maintenance mode
2. **Soft transition (2026-03-10)**
   - internal workflows default to Portal
   - VRC-Explorer retained for fallback only
3. **Hard transition (2026-04-15)**
   - VRC-Explorer removed from primary runbooks/tooling
   - Portal issue bundle workflow mandatory for new reverse-engineering work
4. **Archive target (2026-05-15)**
   - VRC-Explorer archived or clearly marked legacy-only

## Migration Gates

All gates must be green before hard transition:

- `portal_read_path_stable`
- `snapshot_diff_available`
- `issue_export_bundle_available`
- `migration_guide_published`

## Feature Mapping

| VRC-Explorer capability | Portal replacement |
|---|---|
| Live register browsing | `registry` + `projection` views |
| Telemetry change tracking | `stream` + `timeline/events` |
| Provenance reasoning | `provenance/events` |
| Manual snapshot capture | `snapshots/capture` + `snapshots` |
| Before/after comparison | `snapshots/diff` |
| Investigation context persistence | `sessions/save` + `sessions/load` |
| Manual issue drafting | `issues/draft` + `issues/export` |

## Operator Migration Steps

1. Open Portal at `/portal`.
2. Validate bootstrap capabilities from `/portal/api/v1/bootstrap`.
3. Recreate previous VRC-Explorer workflow:
   - capture snapshots
   - compare diffs
   - save session state
   - generate issue draft/export bundle
4. Use exported Markdown + JSON bundle in GitHub issue creation.

## Fallback Plan

If a blocking Portal defect appears before hard transition:

1. Mark defect with severity and reproduction evidence.
2. Use VRC-Explorer as temporary fallback only for impacted workflow.
3. Open a Portal issue with bundle evidence.
4. Remove fallback once fix is merged and validated.

## Validation Checklist

- [ ] Portal endpoint health verified
- [ ] Stream/timeline/provenance usable with real gateway data
- [ ] Snapshot capture + diff verified on at least one real scenario
- [ ] Session save/load verified
- [ ] Issue draft/export bundle accepted by maintainers
- [ ] Team runbooks updated to Portal-first
