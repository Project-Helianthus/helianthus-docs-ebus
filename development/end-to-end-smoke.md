# Canonical End-to-End Smoke Runbook

This runbook defines the canonical smoke topology and execution order across gateway, add-on, and Home Assistant integration.

## Topology

```mermaid
flowchart LR
  HA[Home Assistant]
  ADDON[helianthus-ha-addon]
  GATEWAY[helianthus-ebusgateway]
  EBUSD[ebusd tcp endpoint]
  INTEGRATION[helianthus-ha-integration]

  HA --> ADDON
  ADDON --> GATEWAY
  GATEWAY --> EBUSD
  INTEGRATION --> GATEWAY
  HA --> INTEGRATION
```

## Execution order

Run in order and stop on first failure:

1. **Gateway smoke** (`helianthus-ebusgateway`, issue [#85](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/85)).
2. **Add-on smoke** (`helianthus-ha-addon`, issue [#24](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/24)).
3. **HA integration smoke** (`helianthus-ha-integration`, issue [#52](https://github.com/Project-Helianthus/helianthus-ha-integration/issues/52)).

## Artifacts, logs, pass/fail

| Stage | Expected artifacts/logs | Pass criteria | Fail criteria |
| --- | --- | --- | --- |
| Gateway (#85) | `artifacts/smoke-report.json` and smoke stdout | JSON `success=true`, `read_only=true`, and `startup/scan/graphql/mcp.ok=true` | missing report, `success=false`, or any required check `ok=false` |
| Add-on (#24) | exported add-on logs file and checklist output from `scripts/smoke_addon_checklist.py` | checklist ends with `OVERALL PASS` and exits `0`; required log markers present | checklist exits `1` or any `CHECK_*` line is `FAIL` |
| HA integration (#52) | checklist output from `custom_components.helianthus.smoke_profile` | checklist ends with `OVERALL PASS` (or JSON `ok=true`) and exits `0` | checklist exits `1` or any smoke check fails |

## Repo-specific runbooks

- Gateway smoke runbook: `helianthus-ebusgateway` README smoke section
  https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/README.md#smoke-test-context-and-limits
- Add-on smoke runbook: `helianthus-ha-addon/SMOKE_RUNBOOK.md`
  https://github.com/Project-Helianthus/helianthus-ha-addon/blob/main/SMOKE_RUNBOOK.md
- Integration smoke runbook: `helianthus-ha-integration` README smoke section
  https://github.com/Project-Helianthus/helianthus-ha-integration/blob/main/README.md#smoke-profile-local-gateway-graphql

## Operational rule

End-to-end smoke is **PASS** only when all three stages pass in sequence with no skipped stage.

## Observe-First Validation Note

This runbook documents only the current end-to-end smoke chain on `main`. It
does not yet define dedicated observe-first proof artifacts beyond the
gateway/add-on/integration stages above.

The `helianthus-tinyebus` target-emulation path is a parallel
timing/observability validation track, not a substitute for the canonical
gateway/add-on/integration smoke chain.

Current factual references:

- bus observability and passive-capability signals:
  [`../architecture/observability.md`](../architecture/observability.md)
- transport caveats that decide passive-capable vs unavailable topologies:
  [`../deployment/full-stack.md#passive-observe-first-transport-contract`](../deployment/full-stack.md#passive-observe-first-transport-contract)
- parallel firmware-side target-emulation track:
  [`target-emulation.md#helianthus-tinyebus`](./target-emulation.md#helianthus-tinyebus)

Related validation surfaces:

- topology matrix runner: [`smoke-matrix.md`](./smoke-matrix.md)
- runtime adversarial scenarios:
  [`../architecture/adversarial-matrix.md`](../architecture/adversarial-matrix.md)
