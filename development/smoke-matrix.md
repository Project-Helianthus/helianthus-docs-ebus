# 42-Topology Smoke Matrix Runner

This runbook documents the matrix runner from `helianthus-ebusgateway` (`cmd/matrix-runner`) used to plan/execute the 42 topology combinations.

## Matrix coverage

The matrix is generated as cases `T01..T42`:

- `T01..T03`: direct gateway access to adapter via `ENS`, `ENH`, `UDP`.
- `T04..T06`: gateway via `ebusd-tcp`, where `ebusd` connects southbound via `ENS`, `ENH`, `UDP`.
- `T07..T15`: gateway via proxy (single client), with `gateway->proxy` x `proxy->adapter` (`3 x 3`).
- `T16..T42`: gateway + `ebusd` simultaneously through proxy (`3 x 3 x 3`).

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

## Verdict semantics

`verdict.json` status values:

- `planned`: dry-run mode.
- `passed`: execute mode and all configured commands succeeded.
- `failed`: at least one configured command failed.

Each command step is logged with command string, timestamps, status, and exit code (when available).

## Privacy and secrets

No adapter IPs or credentials are stored in repo artifacts by default. Config files reference environment placeholders (`MATRIX_*`), and command strings must be provided at runtime via local operator context.
