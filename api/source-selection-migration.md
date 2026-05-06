# Source-Selection Public API Migration

Status: Normative for the SAS M4 cleanup cycle.

This page records the public naming cleanup from startup-admission terminology
to source-selection terminology. The behavioral authority is unchanged:
normal Helianthus-owned paths use only the active-probe-passed source selected
by the gateway. Transport-specific diagnostics may use a caller supplied source
only for one explicit request and must not mutate gateway source authority.

## Artifact And MCP JSON Migration Matrix

| Old public name | New public name | Required consumer action |
| --- | --- | --- |
| `admission_path_selected` | `source_selection.mode` | Read the nested source-selection mode instead of the legacy flat field. |
| `join` mode | `source_selection` mode | Treat this as gateway automatic source selection plus validation, not an eBUS protocol membership operation. |
| `override` mode | `explicit_validate_only` mode | Treat exact configured source as validation-only; candidate search is bypassed but active validation remains mandatory. |
| `degraded_transport_blind` mode | `degraded_transport_blind` mode under `source_selection.mode` | Preserve the degraded classification; only the field path changes. |
| `degraded_no_events` mode | `degraded_no_events` mode under `source_selection.mode` | Preserve the degraded classification; only the field path changes. |
| `startup_admission_degraded_total` | `startup_source_selection_degraded_total` | Rename metrics dashboards and alert queries. |
| `startup_admission_state` | `startup_source_selection_state` | Rename metrics dashboards and alert queries. |
| `startup_admission_override_active` | `startup_source_selection_explicit_source_active` | Track exact-source validation mode instead of legacy override wording. |
| `startup_admission_warmup_events_seen` | `startup_source_selection_warmup_events_seen` | Track passive observation evidence collected before active validation. |
| `startup_admission_warmup_cycles_total` | `startup_source_selection_warmup_cycles_total` | Track source-selection cycles. |
| `startup_admission_override_bypass_total` | `startup_source_selection_explicit_validate_only_total` | Track exact-source validation cycles. |
| `startup_admission_override_conflict_detected` | `startup_source_selection_explicit_source_conflict_detected` | Track advisory disagreement for exact-source validation. |
| `startup_admission_degraded_escalated` | `startup_source_selection_degraded_escalated` | Rename degraded escalation flag. |
| `startup_admission_degraded_since_ms` | `startup_source_selection_degraded_since_ms` | Rename degraded entry timestamp. |
| `startup_admission_consecutive_rejoin_failures` | `startup_source_selection_consecutive_failures` | Track failed reselection or validation cycles without protocol rejoin wording. |
| `startup_admission_degraded_cumulative_ms` | `startup_source_selection_degraded_cumulative_ms` | Rename degraded cumulative duration. |

## GraphQL Migration

GraphQL does not expose `source_selection.mode`. Gateway GraphQL consumers that
previously queried the removed `busAdmission` compatibility alias must query
`busSummary.status.bus_admission.source_selection` instead and use the fields
defined in [`graphql.md`](./graphql.md), especially `state`, `outcome`,
`selected_source`, `companion_target`, and `reason`.

## Consumer Rules

- MCP, GraphQL, Portal, semantic pollers, schedulers, and gateway-owned NM
  runtime must use the admitted active source selected by the gateway.
- GraphQL keeps its existing camelCase convention outside this narrow source-
  selection status surface. For this migration, the gateway schema exposes
  `busSummary.status.bus_admission.source_selection`; the removed compatibility
  alias is `busAdmission`.
- Portal explorer is a gateway-owned path and must not provide its own source
  address.
- Transport-specific MCP diagnostics may accept an explicit source address for
  that request only. They must label the request as a diagnostic override and
  must not change the gateway's active source.
- External proxy clients are separate transport sessions. They may choose their
  own source address according to their own protocol handling and adapter-mux
  lease.

## Removed Compatibility Surface

The M4 cleanup intentionally removes legacy camelCase and startup-admission
aliases from source-selection admission/status public API surfaces. Consumers
must use source-selection terminology and the field casing defined by each
surface's current schema. This page does not rename unrelated GraphQL fields
that remain camelCase under `api/graphql.md`.
