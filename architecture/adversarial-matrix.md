# Adversarial Runtime Matrix

This is the immutable public `adversarial-runtime-report-v1` contract for gateway #198 and HA integration #105. It is evidence only: it neither executes a trigger nor authorizes a live action.

Gateway main at `ae85c5d91bd8e9dc1c9fe122de7eaa05dcd6c532` has definitions, report counting, JSON writing, and unit tests. It has no trigger, observer, baseline/end capture, recovery measurement, or threshold executor. It is therefore **definition/serialization-only** until gateway #198 is accepted. The fixtures here are offline contract evidence, not HA, adapter, network, or hardware evidence.

## Exact artifact

[`adversarial-runtime-report-v1.schema.json`](../docs/platform/schemas/adversarial-runtime-report-v1.schema.json) is the sole v1 schema. Its exact identifier is `https://raw.githubusercontent.com/Project-Helianthus/helianthus-docs-ebus/main/docs/platform/schemas/adversarial-runtime-report-v1.schema.json`. Consumers accept only that schema, `schema_version: 1`, suite ID `helianthus.adversarial.ADV01-04`, and suite version `1`. A changed threshold or scenario increments suite version; a changed required field, unit, outcome, or interpretation creates a new schema major.

All objects are closed with `additionalProperties: false`. Before schema validation the deterministic parser rejects invalid UTF-8, duplicate names, non-integer or non-finite numbers, and reports larger than 1 MiB. Counters, offsets, and durations are non-negative integers below `2^53`; every wire duration uses `*_ms`. Wall times use the exact `YYYY-MM-DDTHH:mm:ss.sssZ` form. The injected monotonic clock controls ordering and recovery. Each event/snapshot timestamp equals the scenario anchor plus its offset within 1 ms; wall-clock changes cannot alter a verdict.

The validator opens candidate paths non-blocking, admits only a regular report
descriptor, reads at most 1 MiB plus one byte, and parses/schema-validates/
semantically evaluates that one byte snapshot. Read or schema-validator launch
failures are normalized as invalid artifacts without exposing caller paths.

Provenance is a closed `subject` plus `producer` pair. The subject is always the
gateway, with its commit, source-tree state, `gateway-fixture-set` or
`gateway-binary` kind, and artifact SHA-256. The producer is either gateway
`internal/adversarial` / `go-test-binary`, or HA integration
`ha-adversarial-harness` / `ha-harness`, with its own commit and build digest.
Gateway production is only offline against a fixture-set subject and every event
is fixture sourced. HA offline requires a fixture-set subject plus an input
gateway-report SHA-256; HA operator-live requires a gateway-binary subject, null
input digest, and observer-sourced action evidence. `fixture_set_sha256` equals
the fixture subject digest and is null for a binary subject. All other pairings
are rejected.

## Canonical suite

| ID | Trigger and recovery anchor | Target | Duration | Max recovery | Epoch delta | Zones | DHW | Collision delta |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| ADV-01 | Restart HA Core/integration consumer while gateway remains stable; `consumer_stopped` | `ha_consumer_synchronized` | 180000 ms | 90000 ms | >= 2 | required | required | <= 5 |
| ADV-02 | Reset eBUS adapter while polling; `reset_started` | `gateway_live_ready` | 180000 ms | 120000 ms | >= 2 | required | not required | <= 20 |
| ADV-03 | Partition gateway-to-adapter transport for 60000 ms; `partition_cleared` | `gateway_live_ready` | 180000 ms | 90000 ms | >= 2 | required | not required | <= 10 |
| ADV-04 | Fresh isolated gateway boot with corrupted/truncated cache fixture; `runtime_started` | `gateway_live_ready` | 180000 ms | 120000 ms | >= 2 | required | required | <= 5 |

ADV-01 means the HA consumer restarts while the gateway stays up. It does not restart the gateway add-on. ADV-03 records `partition_active` and `partition_cleared`, and requires `abs(observed_ms - 60000) + partition_active_error_bound_ms + partition_cleared_error_bound_ms <= 1000`; recovery begins only after clearing the partition. ADV-04 takes its baseline from the newly constructed instrumented runtime before cache load. It never modifies production cache.

The fixed event orders are: ADV-01 `restart_requested`, `consumer_stopped`, `consumer_started`, `ha_consumer_synchronized`; ADV-02 `reset_requested`, `reset_started`, `transport_unavailable`, `transport_available`, `gateway_live_ready`; ADV-03 `partition_requested`, `partition_active`, `partition_cleared`, `gateway_live_ready`; ADV-04 `isolated_cache_staged`, `runtime_started`, `gateway_live_ready`. Events are only `fixture` or `observer` sourced.

Each definition serializes the canonical duration, maximum recovery, minimum
live-epoch delta, zone/DHW requirements, and maximum collision delta. Evaluation
repeats those values only as recomputable evidence; it cannot redefine a scenario
threshold.

A passing run keeps the full 180000 ms observation window, with scheduling error at most 1000 ms. Duration and snapshot timing use the scenario aggregate bound. Recovery uses the sum of its anchor-event and recovery-event bounds, so it passes only if `observed_ms + anchor_error_bound_ms + recovery_event_error_bound_ms <= maximum_ms`; each endpoint bound is 0..1000 ms. Baseline/end snapshots must use one `counter_epoch`; a changed epoch or negative delta is an execution error. The fixed snapshots contain counter epoch, timestamp/offset, documented startup FSM phase (`BOOT_INIT`, `CACHE_LOADED_STALE`, `LIVE_WARMUP`, `LIVE_READY`, or `DEGRADED`), live epoch, collision total, zone count, and DHW presence. The validator recomputes duration, action, recovery, live epoch, zones, DHW, collisions, outcome, summary, and verdict.

Startup phase is also scenario-bound: ADV-01, ADV-02, and ADV-03 require
`LIVE_READY` at both snapshots. ADV-04 requires `BOOT_INIT` at baseline and
`LIVE_READY` at end, proving the isolated boot path begins before cache load.
`counter_epoch` is a freshly generated lowercase UUIDv4 per run-local counter
epoch. It is opaque and independent of serials, hosts, devices, or accounts.

For an evaluated result, baseline capture is bound to scenario start and end
capture to scenario end, each within the declared aggregate timing uncertainty.
This prevents a short favorable tail from standing in for the full observation
window. The validator always uses the canonical schema bundled with this contract:
there is no public schema override, and it independently checks the exact schema
URI, schema version 1, suite ID, and suite version before gate semantics.

The executor is serial. The canonical report binds ADV-01 to 12:00–12:03,
ADV-02 to 12:03–12:06, ADV-03 to 12:06–12:09, and ADV-04 to 12:09–12:12
UTC. The first scenario starts at the run anchor, each next scenario starts at
the prior scenario end, and the last scenario ends at the run completion anchor.
Overlap, a gap, or an outer run-boundary forgery invalidates the artifact.
Aggregate scenario timing uncertainty is at least every event uncertainty and
equals evaluated duration uncertainty. Recovery and partition-duration
uncertainty are each the sum of their two endpoint bounds. A smaller evaluation
bound cannot turn a boundary failure into a pass.

Every nonempty action sequence is the canonical ordered prefix for its scenario:
an evaluated result carries the full sequence, while an execution-error may carry
only the prefix reached before failure. Event offsets and derived timestamps are
monotonic and remain within the scenario elapsed window. An infrastructure block
has no events and only the pre-action normalized error
`precondition` / `precondition_unavailable`; a trigger or observer error is not
an infrastructure block.

For `execution-error`, precondition errors are invalid because no adverse action
was executed. Trigger errors require exactly the first request/staging event; observer
errors require adverse action progress and may occur after the full sequence;
evaluation and artifact errors require the full canonical sequence. Until both
canonical recovery endpoints are present, `recovery_anchor`,
`recovery_observed`, and `recovery_ms` are all `null`. Once both exist, their
names and the offset delta are exact canonical values.

`counter_epoch_changed` and `negative_counter_delta` are the only execution
errors that retain metric snapshots. Each must be the sole evaluation error. They
require non-null baseline and end snapshots, null `delta` and `evaluation`, the
normal timestamp/order/window checks, and the scenario's canonical baseline and
end startup phases. The former proves differing epochs; the latter proves one
same-epoch counter decrease. Arrays that combine either continuity code with any
other error are invalid. All other execution-error codes keep every metric field
null.

The first adverse request/staging event is bound to scenario start within the
declared timing uncertainty, and the actual adverse transition offset plus its
event uncertainty must be no greater than 1000 ms after scenario start. The transition events are
`consumer_stopped`, `reset_started`, `partition_active`, and `runtime_started`
for ADV-01 through ADV-04 respectively; they cannot be deferred to the end of a
passing window. Observer errors require that transition to have occurred. Every
result kind binds `scenario_ended_at` to
`scenario_started_at + elapsed_ms` before result dispatch. Infrastructure reasons
are closed per scenario: ADV-01 permits `ha_harness_unavailable` or
`observer_unavailable`; ADV-02 permits `adapter_control_unavailable` or
`observer_unavailable`; ADV-03 permits `network_fault_injector_unavailable` or
`observer_unavailable`; ADV-04 permits `isolated_cache_sandbox_unavailable` or
`observer_unavailable`.

## Result variants and precedence

An `evaluated` result has complete non-null metrics and evaluation, empty errors, and `pass` only if every recomputed decision passes; otherwise it is `fail`. An `execution-error` has `fail`, at least one normalized error, and null non-evaluated fields. An `infrastructure-block` has `blocked-infra`, a closed infrastructure reason, null non-evaluated fields, and proves no adverse action began. An observer failure after any adverse action is an execution error, never an infrastructure block.

Allowed error phases are `precondition`, `trigger`, `observer`, `evaluation`, and `artifact`. Codes are closed: `precondition_unavailable`, `trigger_rejected`, `trigger_timeout`, `trigger_failed`, `observer_timeout`, `observer_failed`, `counter_epoch_changed`, `negative_counter_delta`, `action_duration_out_of_bounds`, and `evidence_incomplete`. `action_duration_out_of_bounds` is valid only for ADV-03 when the retained partition endpoint offsets and summed uncertainty exceed its 60000 +/- 1000 ms bound. Timing uncertainty beyond the schema's 1000 ms representable maximum is an invalid artifact, not an unsubstantiated execution-error code. Suite v1 names no expected limitation, so `xfail` is invalid. Parser/schema rejection outranks semantics; report precedence is `fail`, then `blocked-infra`, then `pass`. Summary is recomputed with total four, unknown zero, and xfailed zero. Dirty provenance is representable but cannot yield a passing consumer gate.

## Ownership and privacy

Gateway #198 owns the serial offline executor with immutable catalog, injected clock, typed trigger, and read-only observer. The default build may register fixture/sandbox triggers only. HA #105 owns the consumer restart/synchronization observer and consumes this artifact without importing gateway code.

`execution.mode` is `offline-fixture` or `operator-live`; it records evidence and cannot select/configure/authorize a trigger. Offline reports include a public fixture-manifest digest and live reports set it null. Any live restart, adapter reset, partition, damaged-state boot, or physical test requires separate action-time confirmation.

The public contract carries no credentials, tokens, hostnames, addresses, interfaces, serials, device fingerprints, paths, account data, raw captures, logs, command lines, or private evidence hashes.

## Offline validation

[`offline-all-pass.json`](../docs/platform/fixtures/adversarial-runtime/v1/positive/offline-all-pass.json) is the canonical all-pass report. [`negative-cases.json`](../docs/platform/fixtures/adversarial-runtime/v1/negative-cases.json) carries weakening mutations.
[`fixture-input-manifest.json`](../docs/platform/fixtures/adversarial-runtime/v1/fixture-input-manifest.json)
is the canonical public fixture-input manifest; its exact byte SHA-256 is bound
to the fixture-subject provenance. These documentation fixtures are hypothetical
contract vectors and never execution evidence.

```sh
python3 scripts/validate_adversarial_runtime_report_v1.py \
  docs/platform/fixtures/adversarial-runtime/v1/positive/offline-all-pass.json
python3 -m pytest -q tests/test_adversarial_runtime_report_v1.py
```

Tests cover malformed JSON, invalid UTF-8, duplicate keys, size and integer limits, versions, closed fields, missing/duplicate/order-drift scenarios, thresholds, wall/monotonic mismatch, counter reset/decrease, timing uncertainty, partial evidence, improper infrastructure downgrade, unauthorized xfail, forged summary, dirty provenance, and all three result variants.

- Gateway executor owner: `helianthus-ebusgateway` #198.
- HA consumer/harness owner: `helianthus-ha-integration` #105.
- [Startup FSM](./startup-semantic-fsm.md), [DHW freshness](./dhw-freshness-fsm.md), and [observability](./observability.md) remain the corresponding semantic references.
