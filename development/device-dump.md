# Device Dump Pipeline

This document describes the **implemented** device dump pipeline in `helianthus-ebusgateway`. The pipeline is used to read register values from a target device and write **log** + **JSON** artifacts for later analysis.

## Entry Point

The dump runs inside the smoke harness:

- Binary: `cmd/smoke`
- Gate: `EBUS_SMOKE=1`
- Trigger: `smoke.register_dump_tsp` set in `AGENT-local.md`

Execution order (high level):

1. Build gateway stack (transport → bus → registry → router).
2. Scan the bus and build device registry entries.
3. Refresh router planes and optionally start the broadcast listener.
4. **Run register dump** (this pipeline).
5. Continue with read-only method invocations.

## Input: TSP Register Definitions

`smoke.register_dump_tsp` points to a `.tsp` file **path** or **HTTP/HTTPS URL**. The loader expands `@include("...")` directives, resolving relative includes against the base file/URL.

Supported directives for dump requests:

- `@zz(0xNN)` sets the default target address (used when `register_dump_target` is not provided).
- `@base(secondary, prefix, [group, instance, addr_lo])` establishes a base context.
- `@ext(...)` lines consume the current `@base` context and emit a register request.
- A `model ... {` line **immediately following** an `@ext` attaches the model name to that entry (used for decoding).

Only these methods are emitted:

- Secondary `0x09` → `get_register`
- Secondary `0x24` with prefix `0x02` → `get_ext_register`

Everything else is ignored by the dump parser.

## Configuration (AGENT-local.md)

The dump is configured under the `smoke:` YAML block. Common fields:

```yaml
smoke:
  register_dump_tsp: ./data/vaillant/15.720.annotated.tsp
  register_dump_target: 0x15
  register_dump_output: ./register_dump.log
  register_dump_json_output: ./register_dump.json
  register_dump_timeout_sec: 10
  register_dump_limit: 0
  register_dump_retry_empty: true
  register_dump_retry_delay_ms: 200
  identify_b509_28xx: false
```

Optional probe mode (range scan) is controlled by:

- `register_dump_probe`, `register_dump_probe_start`, `register_dump_probe_end`
- `register_dump_probe_group`, `register_dump_probe_instance`
- `register_dump_probe_method`, `register_dump_probe_timeout_ms`, `register_dump_probe_delay_ms`
- `register_dump_probe_output`, `register_dump_probe_only`, `register_dump_probe_manufacturer`

## Output Artifacts

### Text Log

Log path resolution (`register_dump_output`):

- If set → use that path.
- Else if `smoke.wire_log_path` is set → `<wire_log_path>.dump.log`
- Else → `./register_dump.log`

Each log line is prefixed with an RFC3339Nano timestamp and includes the target, group, instance, address, payload, and decoded fields (if any).

### JSON Artifact

JSON path resolution (`register_dump_json_output`):

- If set → use that path.
- Else → derive from the dump log path:
  - If the log ends with `.log`, strip the suffix.
  - Append `.json`.

Schema:

```json
{
  "metadata": {
    "timestamp": "2026-02-11T08:12:34.123456789Z",
    "target": "0x15",
    "tsp_source": "./data/vaillant/15.720.annotated.tsp",
    "entry_count": 1234
  },
  "entries": [
    {
      "method": "get_ext_register",
      "group": "0x01",
      "instance": "0x00",
      "address": "0x0400",
      "raw": "0401004000000000",
      "decoded": "field_a=12.3,field_b=1",
      "result": "ok"
    }
  ]
}
```

Field notes:

- `target`, `group`, `instance`, `address` are **hex strings** with `0x` prefix.
- `raw` is the payload as **lowercase hex** without a `0x` prefix. It can be empty if no payload was returned.
- `decoded` is a comma-separated `name=value` string derived from TSP `model` definitions. It is empty when no model matches or decoding fails.
- `result` is the request outcome string (e.g. `"ok"`, `"timeout"`, `"error"`). Present in each entry to distinguish successful reads from failures without inspecting `raw`.
- For `get_ext_register`, the first 4 bytes of `raw` are the response header (`TT GG RR_LO RR_HI`). Decoding uses only the data bytes that follow.

If a request fails, the corresponding entry remains in `entries` with empty `raw`/`decoded`; the error is captured in the text log.

## Upload Flow

The gateway implements two opt-in upload mechanisms, both disabled by default:

### Register Dump Upload

Uploads the B524 register scan JSON to a remote endpoint after smoke-test completion.

| Config | CLI Flag | Default | Purpose |
|---|---|---|---|
| `Smoke.RegisterDumpUploadURL` | (YAML field) | `""` (disabled) | Client: POST JSON to this URL after register dump |
| `DumpUploadPath` | `-dump-upload-path` | `""` (disabled) | Server: mount upload handler at this HTTP path |
| `DumpOutputDir` | `-dump-output-dir` | `"./dumps"` | Local directory for received dump files |

- **Server handler** (`NewRegisterDumpUploadHandler`): accepts POST with JSON body (10 MiB limit), validates metadata, writes to `{outputDir}/register_dumps/register_dump_{target}_{timestamp}.json`, returns 201.
- **Client** (`uploadRegisterDumpJSON`): POSTs the JSON file with 20-second timeout.

### Unknown Device Dump Upload

Uploads a ZIP bundle with full device scan data for unrecognized devices.

| Config | CLI Flag | Default | Purpose |
|---|---|---|---|
| `DumpUploadURL` | `-dump-upload-url` | `""` (disabled) | Client: POST multipart bundle to this URL |
| `DumpIncludePII` | `-dump-include-pii` | `false` | Include device identifiers in the bundle |

- **Client** (`uploadDumpBundle`): builds multipart form with ZIP file, manifest JSON, and metadata (`bundle_id`, `address`, `created_at`, `include_pii`). 20-second timeout.
- When `DumpUploadURL` is empty, the gateway logs a hint: "set DumpUploadURL to upload this bundle for analysis."

### Privacy Model

All upload flows are **opt-in**: empty URL = no upload. Device identifiers (serial numbers, product IDs) are stripped from unknown device bundles unless `-dump-include-pii=true` is explicitly set. The manifest includes a `Privacy.IncludePII` field for the receiving endpoint.
