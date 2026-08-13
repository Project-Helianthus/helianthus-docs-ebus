# Modbus V1 Add-on Runtime

This page freezes the public deployment and recovery contract for the first
read-only Modbus TCP runtime. It is the documentation companion for
FMV3-M4-03. The bounded MCP data surface remains specified by
[`modbus-v1-mcp.md`](./modbus-v1-mcp.md).

## Scope And Ownership

The Home Assistant add-on owns option ingestion, protected endpoint
materialization, child-process supervision, health publication, bounded
startup recovery, and rollback to the packaged previous gateway. The current
gateway owns Modbus endpoint-file consumption and read-only runtime behavior.
The transport and profile facts remain owned by `helianthus-modbus` and
`helianthus-modbusreg` respectively.

The Modbus runtime is disabled by default and opt-in only. This contract does
not qualify a real inverter, authorize a write function, or promote a PV
semantic field.

## Closed Configuration

The add-on accepts these three options:

| Option | Rule |
| --- | --- |
| `modbus_tcp_enabled` | Boolean, default `false`. When false, the other two values are ignored and no Modbus argument or endpoint file reaches a gateway. |
| `modbus_tcp_endpoint` | A Supervisor password field containing one `tcp://host:port` endpoint. Userinfo, paths, queries, fragments, control characters, missing ports, and non-TCP schemes are rejected. |
| `modbus_tcp_dial_timeout` | Integer `ms` or `s` duration from 100 ms through 30 s; default `5s`. |

Enabled startup uses atomic validation: all active options are parsed and
admitted before a gateway child starts. A malformed options document or any
invalid active field fails closed. Disabled startup does not validate retained
endpoint or timeout text, so an operator can always restore the inert path by
setting `modbus_tcp_enabled=false`.

## Endpoint And Redaction Boundary

After successful enabled validation, the add-on atomically materializes the
endpoint in a runtime directory with mode `0700` and a current-UID endpoint
file with mode `0600`. The endpoint never appears in process arguments and
never appears in environment variables. The current gateway receives only the
endpoint-file path and reads the value from that file.

Logs and health expose only an `endpoint_ref` of the form
`sha256:<16 lowercase hex>`. Current-gateway stdout and stderr pass through two
private synchronized redaction pipes. Each redactor replaces the full endpoint,
network location, and hostname before output can be published. A redactor setup,
liveness, or cleanup failure terminates and reaps the child process and removes
the endpoint instead of allowing unfiltered output.

The validator, both redactor processes, the current gateway, and the fallback
gateway are explicit supervisor-owned children. Temporary validator output,
redaction FIFOs, ready files, health files, and endpoint files are private and
atomically replaced where persistent observation is required.

## Capability Admission

Before enabled launch, the wrapper verifies that the current gateway advertises
the complete endpoint-file flag set: enable, endpoint-file, and dial-timeout.
Partial support fails closed. The packaged previous gateway is checked
independently for non-Modbus options whose loss would invalidate the active
runtime: the complete eeBUS flag set when eeBUS is enabled, an active adapter
proxy listener, and explicit source-address override validation. Missing support
for any of those required options fails closed. Fallback does not receive any
Modbus flag.

Three rollback-compatibility options are intentionally best-effort:
`enable-static-seed-table`, `semantic-cache-path`, and
`instance-guid-source`. Each is forwarded when the previous gateway advertises
its flag and omitted otherwise. `FALLBACK_ACTIVE` therefore proves fallback
liveness, not parity for these optional seed, cache, or provenance features.

## Health Contract

Health is a closed JSON object under contract
`helianthus.modbus-addon-health.v1`. It contains only `contract`, `enabled`,
`endpoint_ref`, `state`, `attempt`, `max_attempts`, `binary`, and `reason`.
`binary` is `current` or `fallback`; the endpoint itself is never published.

The closed state set is:

| State | Meaning |
| --- | --- |
| `DISABLED` | Explicit inert path; the current gateway runs without Modbus flags. |
| `CONFIG_VALIDATED` | Enabled configuration passed atomic admission for this current-gateway attempt. |
| `RUNNING` | The current gateway survived its bounded startup window. |
| `RECOVERY_RETRY` | A current-gateway attempt exited inside the startup window and another bounded attempt will start. |
| `FALLBACK_STARTING` | All current attempts failed; the endpoint has been removed and the previous gateway is starting. |
| `FALLBACK_ACTIVE` | The previous gateway survived the same startup window. |
| `FALLBACK_EXITED` | The fallback exited before or after its startup window; health must not remain falsely active. |
| `EXITED_AFTER_STARTUP_WINDOW` | The current gateway exited after it had reached `RUNNING`; this is terminal and does not start fallback. |
| `STOPPED` | A terminal operator or supervisor `TERM`/`INT` stop was observed. |

Health updates use a private `0600` temporary file, flush and sync it, then
atomically replace the visible health file. A health-write failure is terminal:
the supervisor stops and reaps owned processes and removes runtime material
rather than reporting a stale success state.

## Bounded Recovery

The closed recovery limits are:

| Key | Value |
| --- | --- |
| `current_startup_attempts` | `3` |
| `retry_delays_seconds` | `1,2` |
| `startup_window_min_seconds` | `5` |
| `startup_window_max_seconds` | `40` |

Enabled startup gives the current gateway exactly three attempts. The startup
window is derived from the dial timeout and bounded from five through forty
seconds. An exit within that window produces `RECOVERY_RETRY` while attempts
remain. An exit after the window produces `EXITED_AFTER_STARTUP_WINDOW` and is
not reclassified as a startup failure.

After three startup failures, the endpoint file is removed before fallback and
the previous gateway starts with Modbus disabled. It receives the admitted
required non-Modbus runtime configuration plus the supported subset of the three
best-effort rollback options, but no endpoint-file or dial-timeout argument. The
fallback reaches `FALLBACK_ACTIVE` only after surviving the startup window; any
fallback exit is recorded as `FALLBACK_EXITED`.

## Stop And Cleanup

`TERM` and `INT` are terminal during validation, disabled launch, current
startup, retry sleep, redactor drain, and fallback. Signals received in the
short spawn-to-PID-registration interval are deferred only until ownership is
recorded, then forwarded immediately. The supervisor performs bounded
`TERM/KILL/wait` cleanup, reaps every owned process, removes endpoint and
redaction material, and prevents retries or fallback after a stop request.

Normal process exit, validation failure, redactor failure, health failure, and
signal handling all fail closed with respect to endpoint cleanup. No path may
leave an endpoint file for the previous gateway or a later disabled restart.

## Phase Boundary

This contract and its implementation tests use synthetic endpoints and fake
processes. FMV3-M4-04 remains the hard stop for a real Fronius TCP read-only
smoke, disconnect/reconnect proof, raw MCP parity, and recovery validation.

No GraphQL, Portal, Home Assistant semantic, Matter, eeBUS binding, canonical
PV freshness, source-precedence, or Modbus write surface is introduced here.
