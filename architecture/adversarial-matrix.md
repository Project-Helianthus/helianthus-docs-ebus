# Adversarial Runtime Matrix

This page documents the adversarial runtime scenarios used to validate gateway resilience under failure conditions.

## Overview

The adversarial matrix defines a set of chaos-like runtime scenarios, each with explicit durations and pass/fail thresholds. Scenarios are executed against a live gateway+HA stack during smoke testing. The framework is standalone and testable without hardware — scenario definitions and report generation are unit-tested independently.

## Threshold Semantics

All counter-based thresholds (`MinLiveEpoch`, `MaxCollisions`) are evaluated as **deltas** from a baseline snapshot taken at scenario start. The runner captures `expvar` values before injecting the adverse event and computes the delta at evaluation time. This prevents monotonic counter accumulation across scenarios from producing false passes or fails.

## Scenario Matrix

| ID | Name | Duration | Max Recovery | Min Live Epoch Δ | Zones Required | DHW Required | Max Collisions Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADV-01 | HA restart while gateway stable | 3m | 90s | 2 | yes | yes | 5 |
| ADV-02 | Bus reset mid-flight | 3m | 120s | 2 | yes | no | 20 |
| ADV-03 | 60s partition and recovery | 3m | 90s | 2 | yes | no | 10 |
| ADV-04 | Cache corruption boot path | 3m | 120s | 2 | yes | yes | 5 |

### ADV-01: HA Restart While Gateway Stable

**Trigger:** Gateway is in LIVE_READY, HA supervisor restarts the add-on container.

**Rationale:** The most common adverse event in production. The gateway must recover from a clean restart and reach LIVE_READY within 90 seconds, with both zone and DHW data available.

**Why DHW required:** A clean HA restart preserves the semantic cache, so DHW data should survive via cache hydration.

### ADV-02: Bus Reset Mid-Flight

**Trigger:** The eBUS adapter is power-cycled while the gateway is actively polling.

**Rationale:** Adapter power loss causes the bus connection to drop. The read circuit breaker should trip, suppress failing reads, and recover when the adapter comes back. Higher collision tolerance (20) accounts for bus arbitration noise during adapter reboot.

**Why DHW not required:** The bus outage may exceed the DHW stale TTL (10 minutes), causing DHW to expire before the bus recovers.

### ADV-03: 60s Network Partition and Recovery

**Trigger:** Network partition for 60 seconds between the gateway and the eBUS adapter, then recovery.

**Rationale:** Network partitions cause the gateway to enter DEGRADED state via the boot live timeout. After recovery, the startup FSM must reach LIVE_READY again.

**Why DHW not required:** The 60-second partition may overlap with DHW stale expiry, depending on when the last DHW update occurred.

### ADV-04: Cache Corruption Boot Path

**Trigger:** Gateway boots with a corrupted or truncated `semantic_cache.json`.

**Rationale:** Cache corruption tests the cold-boot path where no stale data is available. The gateway must reach LIVE_READY purely from live bus data within 120 seconds.

**Why DHW required:** With no cache, DHW must be populated from live bus data. If the bus is healthy, DHW should appear within the recovery window.

## Verdict Outcomes

| Outcome | Meaning |
| --- | --- |
| `pass` | All thresholds met within the scenario duration |
| `fail` | One or more thresholds violated |
| `xfail` | Expected failure — known limitation documented in the scenario |
| `blocked-infra` | Infrastructure prevented execution (e.g., adapter not connected) |

## Report Format

The adversarial report is a JSON artifact consumed by the tester gate:

```json
{
  "generated_at": "2026-02-26T12:00:00Z",
  "scenarios": [
    {
      "scenario_id": "ADV-01",
      "name": "HA restart while gateway stable",
      "outcome": "pass",
      "duration": "1m30s",
      "metrics": {
        "live_epoch": 3,
        "collisions": 1
      }
    }
  ],
  "summary": {
    "total": 4,
    "passed": 3,
    "failed": 0,
    "xfailed": 1,
    "blocked": 0,
    "unknown": 0
  }
}
```

The summary maintains the invariant: `total == passed + failed + xfailed + blocked + unknown`.

## Cross-Links

- Scenario definitions: `internal/adversarial/scenarios.go`
- Report generation: `internal/adversarial/report.go`
- Startup FSM: [`architecture/startup-semantic-fsm.md`](./startup-semantic-fsm.md)
- DHW freshness: [`architecture/dhw-freshness-fsm.md`](./dhw-freshness-fsm.md)
- Observability: [`architecture/observability.md`](./observability.md)
- Read circuit breaker: [`architecture/semantic-read-circuit-breaker.md`](./semantic-read-circuit-breaker.md)
