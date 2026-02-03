# Smoke Test

The gateway includes a **smoke test harness** that connects to a real ENH socket, performs a bus scan, and executes **read-only** method invocations for each discovered plane.

## Entry Point

- Binary: `cmd/smoke`
- Gate: runs only when `EBUS_SMOKE=1` is set.

## Configuration

The smoke harness reads `AGENT-local.md` from the repo root and extracts **YAML** blocks. Required fields:

```yaml
enh:
  type: unix|tcp
  path: /path/to/ebusd.socket   # required for unix
  host: <EBUS_TCP_HOST>         # required for tcp
  port: 9999                    # required for tcp
  timeout_sec: 10

smoke:
  verbose_frames: false
  scan_timeout_sec: 5
  method_timeout_sec: 10

expected_devices:
  - address: 0x08
    description: "ecoTEC BAI"
    manufacturer: ""
    device_id: ""
    sw_version: ""
    hw_version: ""
```

If `EBUS_SMOKE=1` is set and `AGENT-local.md` is missing or invalid, the test **fails** with an error.

## Run

```bash
EBUS_SMOKE=1 go run ./cmd/smoke
```

## Behavior

1. Build gateway stack (transport → bus → registry → router).
2. Scan the bus with a per-device timeout.
3. Log discovered devices and compare against `expected_devices`.
4. Invoke **read-only** methods for each discovered plane.
5. Start a **passive broadcast listener** on a separate ENH/ENS connection after the scan.
6. Log **semantic energy totals** as B516 broadcasts arrive (if present on the bus).

Notes:

- If `expected_devices` is empty/omitted, the harness performs a full scan over the default address range.
- On a multi-master bus, arbitration collisions can occur during scan. The scan logic retries collided targets in later passes (bounded) instead of aborting the entire scan.
- Default providers include Vaillant **system**, **heating**, and **DHW** planes; solar is opt-in.

The smoke test never writes to the bus.
