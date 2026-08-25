# VRC Explorer And Portal Workflow Guide

## Scope

This guide defines the boundary between **VRC Explorer (Python)** and the
**Helianthus Portal (gateway-native, Go-first)**.

VRC Explorer is not deprecated. It remains a standalone, community-facing tool
for focused VRC/eBUS exploration, `ebusd` users, and investigations that do not
need a running Helianthus gateway.

Portal replaces only selected internal Helianthus workflows that benefit from
gateway-native state and APIs:

- projection and semantic views
- timeline, provenance, and snapshot workflows
- investigation sessions tied to a gateway runtime
- issue drafts and evidence export bundles

This boundary does not change eBUS transport behavior, gateway semantic
contract ownership, Home Assistant responsibilities, or VRC Explorer's own
release and maintenance policy.

## Product Policy

- VRC Explorer remains an active standalone/community-facing project.
- Portal is the preferred surface for the selected gateway-internal workflows
  listed above.
- Either tool may receive feature work appropriate to its own audience and
  architecture.
- A Portal capability does not, by itself, deprecate or archive the
  corresponding VRC Explorer capability.

## Workflow Mapping

| Investigation need | Portal workflow | VRC Explorer position |
|---|---|---|
| Gateway registry and projection browsing | `registry` + `projection` views | Standalone register exploration remains valid |
| Gateway telemetry change tracking | `stream` + `timeline/events` | Focused tool-native observation remains valid |
| Gateway provenance reasoning | `provenance/events` | Independent raw/register evidence remains valid |
| Gateway snapshot capture | `snapshots/capture` + `snapshots` | Tool-local captures remain valid |
| Gateway before/after comparison | `snapshots/diff` | Tool-local comparisons remain valid |
| Gateway investigation context | `sessions/save` + `sessions/load` | Standalone sessions remain outside gateway ownership |
| Helianthus issue bundle creation | `issues/draft` + `issues/export` | Community reports may use VRC Explorer evidence directly |

The table maps selected internal workflows; it is not a product replacement or
feature-parity schedule.

## Adopting Portal For An Internal Workflow

1. Open Portal at `/portal` on the intended gateway runtime.
2. Validate bootstrap capabilities from `/portal/api/v1/bootstrap`.
3. Confirm that the required gateway-native workflow is available:
   - capture snapshots
   - compare diffs
   - save session state
   - generate an issue draft/export bundle
4. Preserve raw eBUS evidence and provenance in any exported Markdown and JSON
   bundle.
5. Continue to use VRC Explorer when its standalone or community-facing scope is
   the better fit.

## Coexistence And Failure Handling

If a Portal workflow is unavailable or defective:

1. Record the defect severity and reproduction evidence.
2. Use another evidence-capable workflow, including VRC Explorer when
   appropriate; do not describe that use as a deprecated fallback.
3. Open a Portal issue when the missing behavior is gateway-owned.
4. Keep evidence from the two tools distinguishable and do not claim parity
   without direct validation.

## Validation Checklist

- [ ] Portal endpoint health verified for the selected internal workflow
- [ ] Stream/timeline/provenance checked against real gateway evidence when used
- [ ] Snapshot capture and diff verified for the claimed scenario when used
- [ ] Session save/load verified when used
- [ ] Issue draft/export bundle accepted when used
- [ ] Raw eBUS evidence remains available beside semantic interpretation
- [ ] Public wording does not describe VRC Explorer as deprecated or replaced
