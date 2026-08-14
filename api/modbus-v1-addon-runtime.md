# Modbus V1 Add-on Runtime

This page freezes the public deployment and recovery contract for the first
read-only Modbus TCP runtime. It is the documentation companion for
FMV3-M4-03. The bounded MCP data surface remains specified by
[`modbus-v1-mcp.md`](./modbus-v1-mcp.md).

## Scope And Ownership

The Home Assistant add-on owns option ingestion, protected endpoint
materialization, child-process supervision, health publication, and bounded
startup recovery with a fallback to the packaged previous gateway binary in the
current add-on. The current gateway owns Modbus endpoint-file consumption,
read-only runtime behavior, and qualification-result logging. A
post-qualification rollback of a gateway/add-on pair is a separate,
operator-controlled deployment procedure; it is not an automatic gateway or
add-on-supervisor action.
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

## M4-03 Phase Boundary

The deployment and recovery contract above is FMV3-M4-03. Its implementation
tests use synthetic endpoints and fake processes. FMV3-M4-04 is separately
authorized for one bounded read-only qualification; the pre-live contract for
that work follows. Neither section claims that a real-device smoke has passed.

No GraphQL, Portal, Home Assistant semantic, Matter, eeBUS binding, canonical
PV freshness, source-precedence, or Modbus write surface is introduced here.

## FMV3-M4-04 Pre-Live SunSpec Qualification

This is the public behavior contract for gateway PR
[`#808`](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/808).
It defines the allowed bounded qualification behavior before live evidence is
published. It is not a claim that any endpoint, device, model, firmware, or
smoke outcome has been observed.

This #435 page remains a legacy qualification harness. It preserves the
existing profile identity pair `sunspec.phase1` version `1.0.0` exactly and
does not claim Fronius support, select a capability profile or vendor flavor,
or publish a live result. The shorthand `sunspec.phase1@1.0.0` denotes that
pair; it is not a replacement literal for `profile_id`.
A future registry-selected outcome is outside this suspended gateway #808
scope.

### Normative Contract Record

The following closed record is normative. Terms such as `UNAVAILABLE` describe
the existing MCP retained-observation state, not canonical PV availability.

```json
{
  "contract": "helianthus.modbus-sunspec-live-qualification.v1",
  "phase": "FMV3-M4-04",
  "activation": {
    "disabled_by_default": true,
    "worker_start_condition": "complete_explicit_modbus_opt_in"
  },
  "acquisition": {
    "transport": "modbus_tcp",
    "unit_id": 1,
    "function_code": 3,
    "writes_permitted": false,
    "profile_id": "sunspec.phase1",
    "profile_version": "1.0.0",
    "chain_qualification": "dynamic_bounded_existing_profile_contracts",
    "qualifications_per_attempt": 1,
    "per_read_timeout_seconds": 2,
    "attempt_timeout_seconds": 30
  },
  "recovery": {
    "max_qualification_attempts": 2,
    "retry_trigger": ["transport_error", "endpoint_reconnect_required"],
    "endpoint_owned_backoff_reconnect_max": 1,
    "final_attempt_requires_new": ["poll_generation_id", "deadline_identity"],
    "periodic_retries": false
  },
  "decision_map": {
    "supported": {
      "decision": "GO",
      "profile_observation": "RETAINED"
    },
    "unsupported_or_deferred_model": {
      "includes_model_ids": [113],
      "decision": "NO_GO",
      "raw_mcp": "USABLE",
      "profile_observation": "UNAVAILABLE"
    },
    "incoherent_capture": {
      "decision": "STOP"
    },
    "any_error": {
      "decision": "STOP"
    }
  },
  "result_redaction": {
    "logs_and_results": "categorical_only",
    "forbidden": [
      "endpoint",
      "raw_error",
      "serial_payload",
      "model_payload",
      "firmware_payload",
      "model_chain_payload",
      "sample_payload"
    ]
  },
  "shutdown": {
    "required_order": ["worker_cancel", "worker_join", "adapter_close"]
  },
  "rollback": {
    "trigger": "explicit_operator_controlled_post_qualification_procedure",
    "disable_modbus_endpoint": true,
    "restore": "operator_selected_prior_gateway_addon_pair",
    "automatic_on_stop_or_no_go": false,
    "separate_from_startup_fallback": true,
    "startup_fallback_parity": "not_guaranteed"
  },
  "live_evidence": {
    "owner_phase": "FMV3-M4-05",
    "prerequisite_phase": "FMV3-M4-04",
    "required_tuple": ["endpoint_ref", "model", "firmware", "model_chain", "outcome"],
    "published_here": false
  }
}
```

### Activation And Acquisition

The Modbus path remains disabled by default. The qualification worker starts
only after the complete explicit Modbus opt-in has admitted the endpoint; an
incomplete option set and the disabled path do not start it. It performs one
dynamically bounded SunSpec chain qualification per permitted attempt, using
the existing `sunspec.phase1` version `1.0.0` profile contracts. The fixed
protocol surface is Modbus TCP, unit 1, and FC03. It is read-only: it never
issues a write function and does not widen the profile contract.

Each read has a two-second bound. The total bound for each qualification attempt
is thirty seconds, including the dynamically discovered chain reads.

### Recovery And Decisions

There is an initial qualification attempt and at most one final attempt. The
final attempt is allowed only when the first attempt has both a transport error
and `ReconnectRequired` from the endpoint. In that case, the endpoint owns at
most one backoff/reconnect; the final attempt receives new poll-generation and
deadline identities. No third attempt, periodic retry, or retry for a
qualification result is permitted.

An admitted supported chain yields `GO` and retains the profile observation.
An unsupported or deferred model, including model 113, yields `NO_GO`: raw MCP
remains usable while the profile observation is intentionally `UNAVAILABLE`.
An incoherent capture or any error yields `STOP`.

Qualification logs and result records are categorical only. They must not
contain an endpoint, raw error text, serial data, model data, firmware data,
model-chain data, or sample payload. This scoped rule does not change the
separate add-on health contract's endpoint-reference field.

### Shutdown, Rollback, And Evidence Boundary

Shutdown cancels and joins the worker before the adapter closes. `STOP` and
`NO_GO` are qualification decisions: the gateway records their categorical
result and does not automatically disable the Modbus endpoint or restore a
gateway/add-on pair. An operator may subsequently choose the separate
post-qualification rollback procedure: disable the Modbus endpoint and select
the prior gateway/add-on pair through the normal deployment controls. This
procedure is explicit and operator-controlled; it is not a qualification-worker
side effect.

That procedure is distinct from the add-on's startup fallback. Startup fallback
occurs only after the current gateway has exhausted its bounded startup attempts;
the current add-on then starts its packaged previous gateway binary with Modbus
disabled. It does not restore a prior add-on, and `FALLBACK_ACTIVE` proves only
fallback liveness. It does not prove configuration or feature parity, including
the three best-effort seed, cache, and provenance options described above.

FMV3-M4-05, after FMV3-M4-04, owns publication of sanitized actual
`endpoint_ref`, model, firmware, model-chain, and outcome evidence. This
pre-live page deliberately contains none of that evidence and must not be read
as a completed live-smoke claim.

## Registry-Selected V2 Successor

The V1 record above remains the immutable contract of suspended gateway PR
`#808`. New qualification runs use the versioned V2 successor below. V2 does
not reinterpret V1, and the historical statement that Model `113` was deferred
under `sunspec.phase1@1.0.0` remains true for V1 only.

V2 consumes the generic SunSpec model-chain, capability, and flavor contracts
implemented by `helianthus-modbusreg v0.1.0`. It does not select a result from a
gateway-owned model-ID range. In particular, Model `113` is neither an
automatic `GO` nor an automatic `NO_GO`: the registry must validate the entire
snapshot, admit the complete capability, and match the exact observed flavor.

### Registry-Selected V2 Contract Record

```json
{
  "contract": "helianthus.modbus-sunspec-live-qualification.v2",
  "phase": "FMV3-M4-04",
  "legacy_contract": "helianthus.modbus-sunspec-live-qualification.v1",
  "supersedes_for_new_runs": "helianthus.modbus-sunspec-live-qualification.v1",
  "registry_dependency": {
    "module": "github.com/Project-Helianthus/helianthus-modbusreg",
    "version": "v0.1.0",
    "merge": "0567cac9db3749086c46f05b2c4c0a24c2371763"
  },
  "activation": {
    "disabled_by_default": true,
    "worker_start_condition": "complete_explicit_modbus_opt_in"
  },
  "acquisition": {
    "transport": "modbus_tcp",
    "unit_id": 1,
    "function_code": 3,
    "qualifications_per_attempt": 1,
    "per_read_timeout_seconds": 2,
    "attempt_timeout_seconds": 30
  },
  "selection": {
    "input": "complete_terminal_verified_SunSpecChainSnapshot",
    "decoder_dispatch": "exact_registry_key",
    "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
    "required_flavor": "sunspec.flavor.fronius.gen24.float.observed@1.0.0",
    "hardcoded_model_id_rules": false
  },
  "decision_precedence": [
    "capability",
    "flavor_only_if_capability_ADMITTED"
  ],
  "capability_decision_map": {
    "INVALID_CHAIN": "STOP",
    "AMBIGUOUS_SOURCE": "NO_GO",
    "SOURCE_ABSENT": "NO_GO",
    "SOURCE_UNSUPPORTED": "NO_GO",
    "INVALID_REQUIRED_FACT": "NO_GO",
    "ADMITTED": "CONTINUE_FLAVOR"
  },
  "flavor_decision_map": {
    "MATCHED": "GO",
    "COMMON_IDENTITY_MISMATCH": "NO_GO",
    "FIRMWARE_MISMATCH": "NO_GO",
    "CHAIN_MISMATCH": "NO_GO",
    "CAPABILITY_NOT_ADMITTED": "STOP_INCOHERENT",
    "AMBIGUOUS_SOURCE": "STOP_INCOHERENT"
  },
  "runtime_or_transport_error": "STOP",
  "recovery": {
    "max_qualification_attempts": 2,
    "retry_trigger": ["transport_error", "endpoint_reconnect_required"],
    "endpoint_owned_backoff_reconnect_max": 1,
    "final_attempt_requires_new": ["poll_generation_id", "deadline_identity"],
    "periodic_retries": false
  },
  "result": {
    "logs_and_results": "categorical_only",
    "retained_on_go": ["capability_id", "capability_reason", "flavor_id", "flavor_reason", "sample_id"],
    "raw_mcp_on_no_go": "USABLE",
    "registry_observation_on_no_go": "UNAVAILABLE"
  },
  "shutdown": {
    "required_order": ["worker_cancel", "worker_join", "adapter_close"]
  },
  "go_authority": "qualification_evidence_only",
  "support_claim": false,
  "live_result_published_here": false,
  "writes_permitted": false
}
```

### V2 Activation, Recovery, And Evidence Boundary

V2 preserves V1's explicit opt-in, FC03-only reads, two-second read bound,
thirty-second attempt bound, at-most-one reconnect, new generation identities
for the final attempt, worker-cancel/join ordering, categorical redaction, and
operator-controlled rollback. It adds no periodic polling and no retry after a
completed qualification decision.

The capability result is evaluated first and is final unless it is `ADMITTED`.
For every other capability reason, the flavor result is ignored and the
capability decision map supplies the result. `INVALID_CHAIN` and runtime or
transport errors are `STOP` because no coherent semantic input exists. Other
non-admitted capability reasons are `NO_GO`; raw MCP remains available, but no
registry qualification observation is retained.

Only an `ADMITTED` capability proceeds to flavor evaluation. `MATCHED` is `GO`;
an identity, firmware, or chain mismatch is `NO_GO`. A flavor result that says
the capability was not admitted or that the source was ambiguous after the
capability result was already `ADMITTED` is internally inconsistent and maps
through `STOP_INCOHERENT` to `STOP`. Thus capability `ADMITTED` together with
flavor `MATCHED` is the only `GO` for this bounded test tuple.

`GO` is qualification evidence only. It does not claim support for a product
family, authorize writes or automatic activation, publish canonical PV
semantics, or release a private binding. FMV3-M4-05 still owns publication of
the sanitized endpoint reference, Common identity, ordered chain, capability
and flavor reasons, unknown occurrences, recovery outcome, and final live
decision. This page contains no live result.

## Registry-Selected V3 Successor

The V2 record remains immutable for runs selecting exactly the V1 observed
flavor. New runs against the currently observed chain use V3. V3 adds no
model-ID rule and does not treat Model `123` as a vendor extension: the registry
must dispatch it through the exact standard-core decoder key before evaluating
one exact flavor contract.

### Registry-Selected V3 Contract Record

```json
{
  "contract": "helianthus.modbus-sunspec-live-qualification.v3",
  "phase": "FMV3-M4-04",
  "supersedes_for_new_runs": "helianthus.modbus-sunspec-live-qualification.v2",
  "selection": {
    "input": "complete_terminal_verified_SunSpecChainSnapshot",
    "decoder_dispatch": "exact_registry_key",
    "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
    "supported_flavors": [
      "sunspec.flavor.fronius.gen24.float.observed@1.0.0",
      "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
    ],
    "required_exact_match_count": 1,
    "current_live_target": "sunspec.flavor.fronius.gen24.float.observed@1.1.0",
    "hardcoded_model_id_rules": false
  },
  "model_123": {
    "decoder_key": [123, 24, "sunspec.models@7abdf898-v1"],
    "ownership": "standard_sunspec_core",
    "access": "read_only_decode",
    "writes_permitted": false
  },
  "go_authority": "qualification_evidence_only",
  "support_claim": false,
  "writes_permitted": false,
  "m5_gate": "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"
}
```

V3 requires exactly one of the two closed flavor contracts to match. Zero
matches is `NO_GO`; more than one match is incoherent and `STOP`. The current
live target is V1.1, but V3 does not broaden either flavor or choose one by
preference order. Model `123/L24` may be decoded read-only for typed retained
facts and provenance; its upstream RW metadata does not permit FC06, FC16, or
any other write operation.

V3 retains V2's explicit opt-in, FC03-only acquisition, bounded reads and
attempts, reconnect rules, categorical redaction, shutdown ordering, and
operator-controlled rollback. FMV3-M4-05 remains the owner of sanitized live
evidence. M5 remains blocked until the deployed exact gateway and registry
combination returns `GO`; a preliminary or deployed `NO_GO` remains evidence
but does not authorize semantic publication.
