# Smoke Test

The gateway now includes a **smoke test harness** that connects to a real ENH socket, performs a scan, and executes **read-only** method invocations for each discovered plane.

## Entry Point

- Binary: `cmd/smoke`
- Gate: runs only when `EBUS_SMOKE=1` is set.

## Configuration

The smoke harness reads `AGENT-local.md` from the repo root and extracts YAML blocks. Required fields:

```yaml
enh:
  type: unix|tcp
  path: /path/to/ebusd.socket   # required for unix
  host: 192.168.100.2           # required for tcp
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

If `EBUS_SMOKE=1` is set and `AGENT-local.md` is missing or invalid, the test **fails**.

## Behavior

1. Build gateway stack (transport → bus → registry → router).
2. Scan the bus using `0x07/0x04`.
3. Log `DeviceInfo` for each device and warn on missing/unexpected expected devices.
4. For each discovered plane, invoke the **first read-only method**.
5. If no providers are configured, a read-only **identify** request is used as fallback.
6. Errors are aggregated and returned at the end.

## Running Locally

```bash
EBUS_SMOKE=1 go test ./... -run SmokeTest -v -timeout 120s
```

Or run the binary directly:

```bash
EBUS_SMOKE=1 go run ./cmd/smoke
```
