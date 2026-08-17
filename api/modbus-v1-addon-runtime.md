# Modbus V1 Add-on Runtime

This page freezes the public deployment contract for the first
read-only Modbus TCP runtime. It is the documentation companion for
FMV3-M4-03. The bounded MCP data surface remains specified by
[`modbus-v1-mcp.md`](./modbus-v1-mcp.md).

## Scope And Ownership

The Home Assistant add-on owns option ingestion, validation, protected endpoint
materialization, and one direct launch of the packaged current gateway. The
wrapper is not a process supervisor. It does not own gateway readiness,
protocol retries, log processing, fallback binaries, or health state machines.

The gateway owns protocol composition and keeps eBUS, eeBUS, HTTP, and MCP
independent from the optional Modbus runtime. A Modbus startup or reconnect
failure is protocol-local: it may make Modbus unavailable, but it must not
restart, replace, or terminate the shared gateway. Generic reconnect behavior
belongs to `helianthus-modbus`; chain parsing, profiles, and vendor flavors
belong to `helianthus-modbusreg`.

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

## Endpoint Boundary

After successful enabled validation, the add-on atomically materializes the
endpoint in a runtime directory with mode `0700` and a current-UID endpoint
file with mode `0600`. The endpoint never appears in process arguments and
never appears in environment variables. The current gateway receives only the
endpoint-file path and reads the value from that file.

Endpoint-bearing errors are sanitized by the component that owns the error
before they reach the logger. The add-on does not post-process stdout or stderr,
does not create redaction FIFOs, and does not publish a Modbus-specific process
health document. The endpoint file is runtime input, not an authorization or
supervision mechanism.

## Capability Admission

For enabled startup only, the wrapper verifies that the current gateway
advertises the complete endpoint-file flag set: enable, endpoint-file, and
dial-timeout. Partial support fails closed before `exec`. Disabled startup does
not inspect Modbus flag support and executes the shared gateway without Modbus
arguments.

## Single Process Lifecycle

Enabled and disabled configurations converge on the same final operation:

```text
s6 -> exec helianthus-gateway
```

When Modbus is disabled, the endpoint file is absent and no Modbus flag is
passed. When enabled, the three admitted Modbus flags are appended to the same
gateway argument vector. The wrapper then replaces itself with the current
gateway. It does not retain a parent shell, launch log redactors, probe local
listeners, retry the complete gateway, or start a previous binary.

Rollback of an add-on or gateway release remains an explicit operator action.
Normal `TERM` and `INT` handling belongs to s6 and the gateway process, matching
the non-Modbus lifecycle.

## M4-03 Phase Boundary

The deployment contract above is FMV3-M4-03. Its implementation tests use
synthetic endpoints. FMV3-M4-04 is separately
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
    "automatic_on_stop_or_no_go": false
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
model-chain data, or sample payload. Endpoint-bearing transport errors are
sanitized by their owning runtime before logging.

### Shutdown, Rollback, And Evidence Boundary

Shutdown cancels and joins the worker before the adapter closes. `STOP` and
`NO_GO` are qualification decisions: the gateway records their categorical
result and does not automatically disable the Modbus endpoint or restore a
gateway/add-on pair. An operator may subsequently choose the separate
post-qualification rollback procedure: disable the Modbus endpoint and select
the prior gateway/add-on pair through the normal deployment controls. This
procedure is explicit and operator-controlled; it is not a qualification-worker
side effect.

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
