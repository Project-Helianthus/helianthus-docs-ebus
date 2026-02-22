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

## Privacy and secrets

No adapter IPs or credentials are stored in repo artifacts by default. Config files reference environment placeholders (`MATRIX_*`), and command strings must be provided at runtime via local operator context.
