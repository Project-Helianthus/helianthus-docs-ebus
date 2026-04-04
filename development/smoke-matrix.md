# 88-Topology Smoke Matrix Runner

This runbook documents the matrix runner from `helianthus-ebusgateway` (`cmd/matrix-runner`) used to plan/execute the full 88 topology combinations.

## Matrix coverage

The matrix is generated as cases `T01..T88` with transport set:

- `ENS`
- `ENH`
- `UDP-plain`
- `TCP-plain`

Case families:

- `T01..T04`: direct gateway access to adapter (`4` transports).
- `T05..T08`: gateway via `ebusd-tcp`, where `ebusd` southbound uses `4` transports.
- `T09..T24`: gateway via proxy (single client), with `gateway->proxy` x `proxy->adapter` (`4 x 4 = 16`).
- `T25..T88`: gateway + `ebusd` simultaneously through proxy (`gateway->proxy` x `proxy->adapter` x `ebusd->proxy` = `4 x 4 x 4 = 64`).

Total: `4 + 4 + 16 + 64 = 88`.

## Artifacts

Each case writes artifacts under:

```text
results/Txx/
  configs/
    helianthus.json
    proxy.json      # only for proxy topologies
    ebusd.json      # only when ebusd is part of topology
  logs/
    runner.log
  verdict.json
```

The runner also writes an aggregated `results/index.json`.

## CLI usage

Dry-run planning (no service commands executed):

```bash
go run ./cmd/matrix-runner --output-dir results --target local
```

Execute a subset with explicit commands:

```bash
go run ./cmd/matrix-runner \
  --target ha-addon \
  --cases T16,T17,T18 \
  --execute \
  --start-gateway "<start gateway command>" \
  --stop-gateway "<stop gateway command>" \
  --start-proxy "<start proxy command>" \
  --stop-proxy "<stop proxy command>" \
  --start-ebusd "<start ebusd command>" \
  --stop-ebusd "<stop ebusd command>" \
  --smoke-command "<smoke validation command>"
```

Optional expected-failure inputs:

- `--expected-failures T07,T08` with a shared reason from `--expected-failure-reason`.
- `--expected-failures-file expected_failures.json` where JSON format is:

```json
{
  "T07": "gentle-join not verifiable via ebusd-tcp",
  "T33": "known udp southbound limitation"
}
```

### Full run recommendation

For transport/protocol merges, run the complete set (`T01..T88`) and keep `results/index.json` as the merge-gate artifact:

```bash
go run ./cmd/matrix-runner \
  --target ha-addon \
  --execute \
  --start-gateway "<start gateway command>" \
  --stop-gateway "<stop gateway command>" \
  --start-proxy "<start proxy command>" \
  --stop-proxy "<stop proxy command>" \
  --start-ebusd "<start ebusd command>" \
  --stop-ebusd "<stop ebusd command>" \
  --smoke-command "<smoke validation command>"
```

`smoke` should include the Home Assistant inventory verifier (`helianthus-ha-integration/scripts/ha_inventory_verifier.py`) so each case validates both transport behavior and HA-visible inventory consistency.

### Current expected-fail categories

`matrix-runner` currently marks these families as expected failures by default:

- `T05..T08` (`via-ebusd-tcp`): gentle-join cannot be verified when Helianthus uses `ebusd-tcp`.
- `proxy-dual-client` with `ebusd->proxy = udp`: bus-traffic visibility is not reliable for the current proxy behavior.
- `proxy-dual-client` with `proxy->adapter = udp` or `proxy->adapter = tcp`: dual-client cohabitation is currently unstable across these southbound modes.

When running the gate, treat `xfail` as known limitations only if the reason is explicitly listed in the attached expected-failure inventory.

### Infrastructure-blocked outcome

When a case cannot run due adapter infrastructure state (for example adapter preflight reports `eBUS signal is not acquired`), matrix verdict uses:

- `outcome = blocked-infra`
- `infra_reason = adapter_no_signal`

Transport gate accepts `blocked-infra` only with `infra_reason=adapter_no_signal`.

## Verdict semantics

`verdict.json` status values:

- `planned`: dry-run mode.
- `passed`: execute mode and all configured commands succeeded.
- `failed`: at least one configured command failed.

Each command step is logged with command string, timestamps, status, and exit code (when available).

`verdict.json` outcome values:

- `pass`: expected pass and case passed.
- `fail`: expected pass and case failed.
- `xfail`: expected fail and case failed.
- `xpass`: expected fail but case passed.
- `blocked-infra`: run blocked by infrastructure precondition (see `infra_reason`).
- `planned`: dry-run outcome.

## Observe-First Proof Note

This runbook documents the current `T01..T88` transport gate and the bounded
observe-first proof shape used by `P03` on the passive suite.

Canonical `P03` bounded proof contract:

- topology: gateway `ENS` → proxy `ENS` → adapter (`proxy-single-client`)
- passive mode: `required`
- proof mode captures the usual `start_*` observability snapshots first
- the canary `start` phase is deferred until the runtime is both smoke-healthy
  and `status.startup.phase == LIVE_READY`
- only the `start` phase may seed `canary_baseline.json`
- later `sample_####` and `end` phases are fail-closed if the seeded baseline is
  missing
- the canonical P03 canary manifest is topology-specific to the proxy-backed
  ENS path and uses a stable mixed B524/B509 set

Canonical proof artifacts for a successful bounded `P03` run:

- `index.json`
- `P03/verdict.json`
- `P03/logs/runner.log`
- `matrix-runner.stdout.log`
- `P03/logs/proof_artifacts/canary_manifest_validation.json`
- `P03/logs/proof_artifacts/canary_baseline.json`
- `P03/logs/proof_artifacts/canary_phase_start.json`
- `P03/logs/proof_artifacts/canary_phase_sample_0001.json`
- `P03/logs/proof_artifacts/canary_phase_end.json`
- `P03/logs/proof_artifacts/canary_summary.json`
- `P03/logs/proof_artifacts/canary_verdict.json`

These artifacts are evidence for the bounded
`proxy-single-client / passive_mode=required / ens / no-ebusd` family only.
They do not imply a universal default flip; the canonical non-promotion
decision for unproven or deployment-ambiguous families lives in
[`Project-Helianthus/helianthus-ebusgateway#439`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/439).

Current factual references:

- passive-capability signals and troubleshooting:
  [`../architecture/observability.md`](../architecture/observability.md)
- bounded proof gate and rollout decision:
  [`Project-Helianthus/helianthus-ebusgateway#400`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/400),
  [`Project-Helianthus/helianthus-ebusgateway#439`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/439)
- canonical bounded proof artifact (outside this docs repo; from a
  `Project-Helianthus/helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260315T070147Z-gw15-proof-p03-canonical-rerun/index.json`
- bounded passive follow-up artifact (outside this docs repo; from the same
  `helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260315T073335Z-passive-suite-followup-gate/index.json`
- transport caveats that decide passive-capable vs unavailable topologies:
  [`../deployment/full-stack.md#passive-observe-first-transport-contract`](../deployment/full-stack.md#passive-observe-first-transport-contract)
- canonical end-to-end smoke order for the matrix `--smoke-command`:
  [`end-to-end-smoke.md`](./end-to-end-smoke.md)
- runtime adversarial scenarios that remain outside the transport gate:
  [`../architecture/adversarial-matrix.md`](../architecture/adversarial-matrix.md)

## Proxy-Semantics Adjunct Gate (`PX01..PX12`)

`T01..T88` remains the primary transport gate. For proxy transport/protocol
merges, a required adjunct proof subset is evaluated in addition to `T01..T88`:

- `PX01`: stale `STARTED` absorb with matching result inside absorb window
- `PX02`: stale `STARTED` absorb expiry with bounded fail path
- `PX03`: `SYN` while waiting for command `ACK` reopens arbitration immediately
- `PX04`: `SYN` while waiting for target response reopens arbitration immediately
- `PX05`: lower initiator wins same-boundary competition
- `PX06`: lower initiator arriving before next round closes beats queued higher
- `PX07`: requeue-after-timeout by former owner still wins over higher
- `PX08`: equal-initiator FIFO ordering is preserved
- `PX09`: local target sees request only from echoed `RECEIVED`, never `SEND`
- `PX10`: local emulated target response inside responder window remains coherent
- `PX11`: late local target response is rejected and counted
- `PX12`: non-owner and non-responder send is rejected during active transaction

### Gate policy with `PX` adjunct

- `T01..T88` verdict remains the primary merge gate for transport/protocol work.
- `PX01..PX12` is a required adjunct for proxy wire-semantics scope.
- Merge requires no unexpected `fail` and no unexpected `xpass` across both
  gate sets.
- `xfail` must stay bound to a documented expected-failure inventory with case
  IDs and reasons.

### Expected artifact shape for proxy-semantics proof runs

Proof runs must include an attached artifact bundle shaped as:

```text
results/
  index.json
  proxy-semantics/
    index.json
    PX01/
      verdict.json
      logs/runner.log
    PX02/
      verdict.json
      logs/runner.log
    ...
    PX12/
      verdict.json
      logs/runner.log
```

`proxy-semantics/index.json` must summarize `PX01..PX12` outcomes and expected
failure annotations used for that run.

### Deferred ESERA passive validation note

The current matrix gate does not require hardware-backed ESERA passive proof
before merge for this workstream. That validation remains tracked as a deferred
follow-up in:

- `FOLLOWUP-01` docs lane: [Project-Helianthus/helianthus-docs-ebus#241](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/241)
- execution-plan lane: [Project-Helianthus/helianthus-execution-plans#7](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/7)

## Privacy and secrets

No adapter IPs or credentials are stored in repo artifacts by default. Config files reference environment placeholders (`MATRIX_*`), and command strings must be provided at runtime via local operator context.
