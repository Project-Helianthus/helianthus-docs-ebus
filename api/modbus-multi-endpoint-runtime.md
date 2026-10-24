# Modbus multi-endpoint runtime

Status: proposed pre-implementation contract for
[docs issue #746](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/746).
It is the documentation gate for the gateway composition in
[gateway issue #1362](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1362)
and for the add-on options in
[add-on issue #275](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/275).
This page claims neither implementation. Nothing on it is stable before 1.0:
every MCP namespace, including `modbus.v1.*`, stays pre-stable under the
[MCP policy](./mcp.md#current-status), and no authorization gate applies before
0.9. The contract is read-only. It adds no write function, no control
capability and no write-adjacent setting.

The single-endpoint contract in
[`modbus-v1-addon-runtime.md`](./modbus-v1-addon-runtime.md) stays frozen. This
page adds a second configuration shape beside it, called **configuration v2**:
a bounded list of Modbus TCP endpoints in which every entry becomes its own
managed driver instance. Configuration v2 is unrelated to the qualification
records V1 to V3 on that page.

## Scope and ownership

| Concern | Owner |
| --- | --- |
| Option ingestion, atomic validation, protected document materialization and one direct gateway launch | Home Assistant add-on, as the frozen single-endpoint page already states |
| Reading the document, composing instances, registration, lifecycle and publication | Gateway |
| Transport requests, scheduling and reconnect | `helianthus-modbus` |
| Family qualification, profiles and detectors | `helianthus-modbusreg` |
| Protocol facts of every family | [Public Modbus documentation](https://github.com/Project-Helianthus/helianthus-docs-modbus) |
| Semantic mappings | [Public semantic documentation](https://github.com/Project-Helianthus/helianthus-docs-semantic) and SemReg |
| Editing endpoints in the Portal | Outside this contract |

This page introduces no protocol fact. A vendor family appears only as an
identifier in a closed table; its identity, child routing, monitoring facts and
pacing observations come from its own native contract. This page qualifies no
device, family or endpoint and promotes no semantic field.

## Evidence labels

**Proven** means an inspected software seam or published document exists; it
does not qualify an installation. **Hypothesis** means a proposed behavior or
value that awaits implementation evidence. Every new rule, bound and default on
this page is a Hypothesis until tests in the implementing repository exercise
it; the page does not promote itself. **Unknown** means evidence or a decision
is absent.

Every table below carries a Grade column, and each paragraph that states a rule
says its own grade. Definitions and non-claims are not graded. The labels are
separate from native qualification decisions (`GO`, `NO_GO`, `STOP`), from the
instance qualification posture defined below, from lifecycle observed states,
from admission and from `support_claim`. A Proven row about composition says
nothing about a device. Examples are synthetic illustrations of Hypothesis rows,
not observations.

## Baseline: configuration v1

| Statement | Grade |
| --- | --- |
| The add-on accepts `modbus_tcp_enabled`, `modbus_tcp_endpoint` (a protected endpoint) and `modbus_tcp_dial_timeout`, validates the enabled set atomically, materializes one owner-only endpoint file and passes the gateway only its path. | Proven by [the single-endpoint page](./modbus-v1-addon-runtime.md) |
| The gateway reads that file through `-modbus-tcp-endpoint-file` and accepts only a regular file that is not a link, owned by its effective user, with mode `0400` or `0600`, between 1 and 512 bytes, whose whole content is one valid `tcp://host:port` endpoint. The inline endpoint flag and the file flag are mutually exclusive. | Proven by [the endpoint file handling](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/modbus_endpoint_file.go) |
| The gateway always registers one southbound managed driver, `modbus.sunspec`, enabled only when the Modbus runtime is enabled. It owns exactly one source, derived from the DriverID and the instance GUID. The DriverManager V1 proposal's slot name `modbus.tcp.default` is not a registered ID. | Proven by [the sidecar composition](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/managed_sidecar_composition.go) and its [architecture page](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/architecture/managed-sidecar-composition.md) |
| The SunSpec worker addresses unit 1 with FC03 only, bounds each read at two seconds and repeats its cycle every 15 seconds. | Proven by [the SunSpec runtime](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/modbus_sunspec_runtime.go) and the qualification records on the single-endpoint page |
| The transport allows one connection and up to four requests in flight, with a deterministic reconnect backoff between 1 s and 30 s and no jitter. | Proven by [the transport configuration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/modbus_runtime_config.go) |
| The SunSpec runtime publishes one PV asset per endpoint; its identifier follows the existing PV publication rule. | Proven by [the PV publication core](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/modbusadapter/semreg_pv_publication_core.go) |
| The gateway's provider table contains the family identifiers `huawei.smartlogger`, `huawei.emma` and `huawei.sdongle` in the withheld state. | Proven by [the provider table](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/modbus_provider_registry.go) |
| The three vendor status tools `modbus.v1.huawei.smartlogger.status.get`, `modbus.v1.huawei.emma.identity.get` and `modbus.v1.huawei.sdongle.status.get` accept an empty argument object and resolve to one provider per server. | Proven by [the tool registrations](https://github.com/Project-Helianthus/helianthus-ebusgateway/tree/main/mcp) |
| `modbus.v1.raw.read` and `modbus.v1.profile.observation.get` address the one configured endpoint; raw reads share a quota of four per one-second window. | Proven by [the Modbus MCP page](./modbus-v1-mcp.md) |
| Registration validates a complete descriptor set, disabled entries included, before any factory call, and a duplicate driver or source refuses the set without hub mutation. | Proven by [the registration contract](../architecture/runtime-driver-lifecycle.md#s0a1-typed-compiled-driver-registration) |

## Selecting configuration v1 or v2

The add-on keeps `modbus_tcp_enabled` as the single main switch. It adds one
list option, `modbus_tcp_endpoints`, whose entries carry exactly the members of
an endpoints-document entry, with the same names, types and bounds.

| Add-on state | Gateway arguments | Result | Grade |
| --- | --- | --- | --- |
| `modbus_tcp_enabled` is false | None; the list and every scalar are ignored and not validated | Inert path, exactly as today: `modbus.sunspec` is registered disabled | Proven for the scalars, Hypothesis for the list |
| Enabled, list empty or absent | Exactly the v1 flags | Configuration v1, unchanged | Proven |
| Enabled, list non-empty, `modbus_tcp_endpoint` empty and `modbus_tcp_dial_timeout` at `5s` | Only `-modbus-tcp-endpoints-file` with the document path | Configuration v2 | Hypothesis |
| Enabled, list non-empty, `modbus_tcp_endpoint` non-empty or `modbus_tcp_dial_timeout` not `5s` | None; startup fails closed before the gateway launches | Rejected as `MIXED_CONFIGURATION` | Hypothesis |

The gateway applies the same exclusivity. `-modbus-tcp-endpoints-file` together
with any of `-modbus-tcp-enabled`, `-modbus-tcp-endpoint`,
`-modbus-tcp-endpoint-file` or `-modbus-tcp-dial-timeout` is rejected as
`MIXED_CONFIGURATION` before anything is registered. For enabled startup the
add-on verifies that the gateway advertises `modbus-tcp-endpoints-file` before
it launches the gateway; absent support fails closed, as partial v1 flag
support does today. Disabled startup inspects no Modbus flag support. These
selection rules are a Hypothesis.

## Endpoints document

### Protected materialization

| Property | Rule | Grade |
| --- | --- | --- |
| Input | The single v2 flag `-modbus-tcp-endpoints-file <path>`. There is no inline form. | Hypothesis |
| Carrier | One JSON document that the add-on writes and the gateway reads once at process start. There is no reload: a change is a gateway restart performed by the add-on. | Hypothesis |
| Directory and file | A runtime directory with mode `0700` and a regular file with mode `0600`, written to a staging file in the same directory and renamed atomically, as the v1 endpoint file is. The gateway accepts a regular file that is not a link, owned by its effective user, with mode `0400` or `0600`. | Hypothesis, mirroring Proven v1 checks |
| Size | 1 to 16384 bytes. | Hypothesis |
| Stale material | The add-on removes any earlier document before validation, so a failed validation leaves no document. | Hypothesis, mirroring the Proven v1 behavior |
| Exposure | Endpoints never appear in process arguments, environment variables or logs. Only the document path is an argument. | Proven for v1, Hypothesis for the document |
| Redaction classes | Unchanged. Logs and results are categorical only and never carry an endpoint, raw error text, serial data, model data, firmware data, model-chain data or sample payload. Labels and families are not endpoint material and may appear in categorical output. | Proven for the classes, Hypothesis for the document |
| Disabled path | No flag and no file. | Proven |

The carrier is a structured document, not a line-oriented file. An entry has an
optional list member and an optional object member, and both sides can produce
and validate JSON without a custom line grammar: the gateway with strict
decoding, the add-on with the same parser that already reads its options
document. The single-line v1 file is not extended, so its parser, its flag and
its checks stay untouched. This rationale is a Hypothesis.

A label is a public identifier. It becomes part of a driver ID that every
runtime surface shows, so an operator must not encode an address, serial number
or private site detail in it. The gateway cannot verify that.

### Document shape

The example is synthetic: the hosts use a reserved invalid domain and no value
describes an installation.

```json
{
  "contract": "helianthus.modbus-tcp-endpoints.v2",
  "endpoints": [
    {
      "label": "default",
      "family": "sunspec",
      "endpoint": "tcp://sunspec-a.example.invalid:502",
      "dial_timeout": "5s",
      "units": [1],
      "pacing": {
        "gap_ms": 200,
        "settle_ms": 1000,
        "cycle_s": 15,
        "backoff_floor_s": 5,
        "backoff_ceiling_s": 300
      }
    },
    {
      "label": "roof",
      "family": "sunspec",
      "endpoint": "tcp://sunspec-b.example.invalid:1502"
    }
  ]
}
```

The document is a single UTF-8 JSON object without a byte-order mark. The
decoder rejects duplicate keys at any depth, unknown members at any depth,
`null` values, fractional or exponent numbers, control characters in strings
and any data after the object. All of this is a Hypothesis.

### Members and bounds

| Member | Type | Rule | Grade |
| --- | --- | --- | --- |
| `contract` | string | Required; exactly `helianthus.modbus-tcp-endpoints.v2`. | Hypothesis |
| `endpoints` | array | Required; 1 to 8 entries. The maximum is a proposal. | Hypothesis |
| `label` | string | Required; matches `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, 1 to 32 bytes, unique in the document. The grammar is the driver-ID segment grammar narrowed to start with a letter, use hyphens only as separators and exclude dots. `default` is reserved for the unsuffixed driver ID. | Hypothesis |
| `family` | string | Required; a value of the closed family table below. | Hypothesis |
| `endpoint` | string | Required; at most 288 bytes. Scheme `tcp`; host an IP literal or a DNS name; port 1 to 65535; no userinfo, path, query, fragment, control characters or surrounding whitespace. Unique after normalization: lowercase host, one trailing dot removed, canonical IP spelling, decimal port without leading zeros. | Proven for the v1 endpoint grammar, Hypothesis for the length bound and the uniqueness rule |
| `dial_timeout` | string | Optional, default `5s`; integer `ms` or `s` duration from 100 ms through 30 s. | Proven for the v1 bound, Hypothesis for the per-entry placement |
| `units` | array of integers | Optional; 1 to 32 distinct integers from 1 to 247. It is an allowlist for routed child units. It narrows what a family contract discovers and never widens it. A unit that a family reports but the allowlist excludes is withheld, and an allowlisted unit that the family does not report is withheld with its reason. For `sunspec` the member is absent or exactly `[1]`, because the acquisition records on the single-endpoint page fix unit 1. | Hypothesis |
| `pacing` | object | Optional; closed members `gap_ms`, `settle_ms`, `cycle_s`, `backoff_floor_s`, `backoff_ceiling_s`, all optional integers; see the pacing profile below. | Hypothesis |

### Closed family table

| `family` | Driver ID base | Native qualification | Admission in the gateway composition | Grade |
| --- | --- | --- | --- | --- |
| `sunspec` | `modbus.sunspec` | The registry-selected SunSpec qualification (record V3 on the single-endpoint page) | Composed: one worker per instance | Proven |
| `huawei.smartlogger` | `modbus.huawei.smartlogger` | The family's own native contract | Withheld until that contract admits a qualification | Proven that the table withholds it, Unknown for the qualification |
| `huawei.emma` | `modbus.huawei.emma` | The family's own native contract | Withheld until that contract admits a qualification | Proven that the table withholds it, Unknown for the qualification |
| `huawei.sdongle` | `modbus.huawei.sdongle` | The family's own native contract | Withheld until that contract admits a qualification | Proven that the table withholds it, Unknown for the qualification |

No family identifier is a dot-separated prefix of another. A value outside this
table is rejected as `UNKNOWN_FAMILY`. Adding a family is a documented revision
of this table together with the family's native contract. Case, spacing and
aliases are not normalized.

### Validation and the rejection table

Validation is atomic over the whole document. Nothing is registered,
constructed or dialed until every check has passed, and the first failing check
decides the single reported category. The add-on runs the checks that apply to
its options and the gateway runs all of them on the document; the gateway never
relies on the add-on. The check order is:

1. Selection: exclusivity of v1 and v2 inputs.
2. Document: file safety, size, encoding, syntax, duplicate keys, null values,
   fractional numbers, trailing data.
3. Top level: required members, unknown members, the `contract` value, then
   the entry count.
4. Each entry in document order: required members, unknown members at any depth
   inside the entry, label, family, endpoint, dial timeout, allowlist, pacing.
5. Across entries, after every entry passed: duplicate label, duplicate
   endpoint, duplicate driver ID.

A rejection names one static category and, for an entry-local case, the
zero-based entry position. It never echoes a document value, endpoint, label or
raw parser text. A member of the wrong JSON type is rejected with that member's
own category. A rejected document registers no Modbus TCP instance and
constructs, dials and publishes nothing. The process-level consequence is the
one the v1 endpoint file already has: fail closed before the gateway launches in
the add-on, and protocol-local once the DriverManager successor is in place.
This page adds no third posture. All of this is a Hypothesis.

Rejection table:

| Case | Category | Synthetic example cause | Grade |
| --- | --- | --- | --- |
| Duplicate label | `DUPLICATE_LABEL` | Two entries both labelled `roof` | Hypothesis |
| Duplicate endpoint | `DUPLICATE_ENDPOINT` | Two entries whose endpoints are equal after normalization | Hypothesis |
| Unknown family | `UNKNOWN_FAMILY` | `family` is `Sunspec` or a vendor name outside the table | Hypothesis |
| List too long | `TOO_MANY_ENTRIES` | Nine entries | Hypothesis |
| Missing field | `MISSING_FIELD` | An entry without `endpoint`, or a document without `endpoints` | Hypothesis |
| v1 and v2 mixed | `MIXED_CONFIGURATION` | The list option together with a scalar endpoint, or the endpoints flag together with a v1 flag | Hypothesis |
| Label not matching the driver ID pattern | `INVALID_LABEL` | `Roof_1`, `1roof`, `roof-`, `a.b`, an empty label, or a label longer than 32 bytes | Hypothesis |
| Empty list | `EMPTY_LIST` | `"endpoints": []` | Hypothesis |
| Unknown member | `UNKNOWN_MEMBER` | `"enabled": true` in an entry, or an unlisted member inside `pacing` | Hypothesis |
| Unreadable or unsafe document | `INVALID_DOCUMENT` | Wrong mode, a link, a size outside the bound, invalid syntax, a duplicate key, a null value, a fractional or exponent number, trailing data, or a `contract` value other than the stated one | Hypothesis |
| Invalid endpoint | `INVALID_ENDPOINT` | A path, userinfo or a missing port | Hypothesis |
| Invalid dial timeout | `INVALID_TIMEOUT` | `50ms` or `45s` | Hypothesis |
| Invalid allowlist | `INVALID_UNITS` | `[0]`, a repeated unit, or `[2]` for `sunspec` | Hypothesis |
| Invalid pacing | `INVALID_PACING` | A value outside its bound, or a floor above the ceiling | Hypothesis |
| Duplicate driver ID | `DUPLICATE_DRIVER_ID` | Defense in depth: a derived ID that equals another | Hypothesis |

### Migration table

| v1 input | Gateway mapping when v1 is selected | Operator-written v2 equivalent | Identity, state and behavior | Grade |
| --- | --- | --- | --- | --- |
| `modbus_tcp_enabled` false | No instance configured; `modbus.sunspec` registered disabled | Same switch; list ignored | No difference | Proven |
| One endpoint through `modbus_tcp_endpoint` or a single-line endpoint file | One entry with label `default`, family `sunspec` and that endpoint | The same entry written in `modbus_tcp_endpoints` | Same driver ID `modbus.sunspec`, same source, same durable desired state and revision, same PV asset rule, same tools | Hypothesis |
| `modbus_tcp_dial_timeout` | `dial_timeout` of that entry | `dial_timeout` | Same grammar and bounds | Hypothesis |
| Fixed unit 1 and FC03 | `units` absent, meaning `[1]` | `units` absent or `[1]` | No difference | Hypothesis |
| Transport limits, 15 s cycle, 1 s to 30 s reconnect backoff | Kept as they are today | An entry without `pacing` takes the production defaults below, except that the `sunspec` cycle stays 15 s | The one intended behavior difference of an operator move to v2: one request in flight and a gap between requests. An operator who needs the v1 transport limits stays on v1. | Hypothesis |
| Single-line endpoint file and its flag | Unchanged: same checks, same flag, same driver | Not applicable: v2 uses the endpoints document | A single-line file behaves exactly as today | Hypothesis |
| `modbus.v1.raw.read` and `modbus.v1.profile.observation.get` | Address the instance of the v1 slot | Address the instance with family `sunspec` and label `default` while it is configured; otherwise `UNAVAILABLE` as for any unconfigured provider | No difference while that entry exists | Hypothesis |
| Portal driver selection and runtime-control durable state, keyed by driver ID | Keyed by `modbus.sunspec` | Same key for the `default` entry; every other label is a new driver with no record | Existing state is kept for the migrated entry | Hypothesis |
| Reverse move | Not automated | A document with exactly one `default` entry for `sunspec`, default allowlist and default pacing is equivalent to v1 | Other instances are removed under the lifecycle contract's removal rule | Hypothesis |

## Driver instances

### Driver ID

The driver ID is the family's base from the closed family table, followed by a
dot and the label unless the label is `default`.

| Family | Label | Driver ID | Grade |
| --- | --- | --- | --- |
| `sunspec` | `default` | `modbus.sunspec` | Proven for the existing ID |
| `sunspec` | `roof` | `modbus.sunspec.roof` | Hypothesis |
| `huawei.smartlogger` | `site-a` | `modbus.huawei.smartlogger.site-a` | Hypothesis |
| `huawei.emma` | `default` | `modbus.huawei.emma` | Hypothesis |
| `huawei.sdongle` | `site-b` | `modbus.huawei.sdongle.site-b` | Hypothesis |

| Rule | Grade |
| --- | --- |
| Every derived ID matches `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$` and is at most 128 bytes, the canonical pattern of the [registration contract](../architecture/runtime-driver-lifecycle.md#s0a1-typed-compiled-driver-registration). The label grammar and the family bases guarantee this. | Hypothesis |
| The derivation is injective: labels contain no dot and no family is a dotted prefix of another. | Hypothesis |
| IDs are stable across restart and gateway rename. A different label or family is a different driver, not a rename. | Hypothesis |
| An endpoint, host, port, serial number, model or firmware value never enters an ID. | Proven for the DriverID rule, Hypothesis for the label |

### Registration

Each entry produces one descriptor in descriptor format `v1`, so the descriptor
format and the registration clauses are unchanged.

| Descriptor field | Value for an instance | Grade |
| --- | --- | --- |
| `DriverID` | Derived as above | Hypothesis |
| Direction | `southbound` | Proven for the existing SunSpec descriptor |
| Disposition | Enabled unless the existing Portal driver enable/disable selection for that DriverID disables it. Eligibility stays separate from desired and observed state. | Proven for the selection seam |
| `NativeContractRef` | The public transport owner, contract and exact linked module version of the existing SunSpec descriptor; no endpoint | Proven for the existing descriptor |
| Lifecycle adapter | A typed factory that captures the entry's validated configuration. Registration stores it without invoking it, and the frozen construction material carries no endpoint. | Proven for the pattern, Hypothesis for the capture |
| Owned `SourceID` set | Exactly one source, derived from the DriverID and the configured owner identity exactly as the v1 SunSpec source is, never from an endpoint or label alone | Proven for v1, Hypothesis for new instances |
| Hooks | Empty | Proven |

| Registration rule | Grade |
| --- | --- |
| All Modbus TCP instances are validated and registered as one set before any factory call. A duplicate label, endpoint or driver ID, or a source collision, refuses the set with zero factory calls and no hub mutation. | Hypothesis |
| Disabled and withheld entries stay registered and listed. A disabled instance constructs and dials nothing. | Proven for disabled listing, Hypothesis for the instance set |
| `helianthus.runtime.list` returns instances sorted bytewise by DriverID, independent of document order. | Proven |
| Registration of the Modbus TCP set is independent of `ebus.primary`, `eebus.primary` and the serial Growatt driver: a refusal of the set withholds only the set. | Hypothesis |

### Lifecycle

| Rule | Grade |
| --- | --- |
| Instances are controlled with the existing `helianthus.runtime.{list,get,start,stop,restart}` tools of the [G5 contract](./mcp.md#g5-runtime-lifecycle-mcp-contract-d4). The `DriverID` argument is the instance's driver ID. There is no per-instance tool, no new argument and no new lifecycle surface. | Hypothesis |
| Desired state, desired revision, epoch, generation, retry budget and safety quarantine belong to one DriverID. START, STOP or RESTART of one instance changes none of these for another. A restart of one instance leaves every other instance's generation unchanged. | Hypothesis |
| First-time bootstrap seeds enabled instances `RUNNING`. An instance added after bootstrap has no record, reads `STOPPED`, and starts only after an accepted START that carries the read-back revision. Whether the add-on should request that START is not decided here. | Proven as a consequence of the lifecycle contract, Unknown for the operator experience |
| An entry removed from the document is not registered at the next start. Removing its record is the lifecycle contract's mark-only durable decision, and re-adding the same family and label continues above every earlier revision. | Proven as a consequence of the lifecycle contract |
| START and RESTART of a disabled instance are refused with `FAILED_PRECONDITION`. | Proven |
| An unregistered driver ID is `NOT_FOUND` without construction or endpoint access. | Proven |
| Reads of status perform no endpoint I/O. | Proven |

### Qualification

The declared family selects the native qualification. The following rules
bind every instance.

| Rule | Grade |
| --- | --- |
| The declared family is the only candidate. The gateway does not try other families in turn, sends no read that belongs to another family, and never switches an instance to another family on its own. There is no auto-detection across families. | Hypothesis |
| A family's qualification may recognize another family's identity only from the responses to its own bounded read set. The recognition withholds the instance; it never changes the family. | Hypothesis |
| Anything not positively admitted is withheld. An unknown family value is rejected at validation. | Hypothesis |
| `sunspec` uses the registry-selected qualification of record V3 on the single-endpoint page, with unit 1, FC03 only, the two-second read bound and the attempt bounds recorded there. Each instance has its own worker and its own attempt counters. | Proven for a single instance, Hypothesis for several |
| A vendor family is withheld as `FAMILY_NOT_ADMITTED` until its own native contract admits a qualification in the gateway composition. A withheld instance of this kind sends no request. | Hypothesis |
| Qualification evidence is per instance. The admission of one instance never admits another, and a decision is qualification evidence only. `GO` grants no support claim, no write authority and no automatic activation. | Proven for the decision semantics, Hypothesis for the per-instance scope |
| Before the first completed attempt after a start, an instance is withheld as `INSUFFICIENT_EVIDENCE`. An admission never survives a driver generation change. | Hypothesis |

The instance qualification posture is separate from the lifecycle observed
state and from the evidence labels:

| Posture | Closed reason | Meaning | Grade |
| --- | --- | --- | --- |
| `ADMITTED` | None | The family's native decision admits the instance. Publication is allowed. | Hypothesis |
| `WITHHELD` | `FAMILY_NOT_ADMITTED` | The gateway composition has no admitted qualification for the declared family; nothing is sent. | Hypothesis |
| `WITHHELD` | `FOREIGN_FAMILY_IDENTITY` | Within the declared family's own reads, the peer presented another family's identity. | Hypothesis |
| `WITHHELD` | `AMBIGUOUS_RESULT` | The result is ambiguous or incoherent: more than one match or conflicting identity facts. | Hypothesis |
| `WITHHELD` | `TUPLE_NOT_ADMITTED` | The result is complete but the observed identity tuple is not an admitted exact one. | Hypothesis |
| `WITHHELD` | `INSUFFICIENT_EVIDENCE` | The bounded attempt ended without enough evidence, including a timeout, a truncated read or a transport error. | Hypothesis |
| `WITHHELD` | `ASSET_CONFLICT` | The hub refused an asset because another instance already owns it. | Hypothesis |

For `sunspec` the record V3 decisions map as follows: `GO` is `ADMITTED`; a
`NO_GO` is `TUPLE_NOT_ADMITTED`, except that the capability reason
`AMBIGUOUS_SOURCE` is `AMBIGUOUS_RESULT`; a `STOP` caused by an incoherent or
ambiguous snapshot is `AMBIGUOUS_RESULT`; a `STOP` caused by a runtime or
transport error is `INSUFFICIENT_EVIDENCE`. Each vendor family's native contract
supplies its own mapping onto the same closed reasons. A withheld instance
publishes nothing and starts no new publication. Facts published earlier follow
the existing freshness and retention rules and are never refreshed by a
withheld instance. Raw evidence stays with its native owner. These mappings are
a Hypothesis. The posture is observable through the family status tool for that
instance and through categorical log lines, never through an endpoint.

### Failure isolation

Per instance: the connection and its scheduler, the gap and reconnect timers,
the work goroutines, the source, epoch and driver generation, the publication
handle, the durable record, the retry budget and the quarantine flag. Shared:
the process, the HTTP and MCP listeners, the semantic hub (which serializes per
asset), the logging sink, and the raw-read quota of the v1 slot. This split
is a Hypothesis.

| Event on instance A | Effect on A | Effect on every other instance | Effect on eBUS, eeBUS, HTTP and MCP | Grade |
| --- | --- | --- | --- | --- |
| Dial failure, timeout or connection loss | `STARTING`, `DEGRADED` or `BACKOFF` under its own retry policy and reconnect backoff | None | None | Hypothesis |
| Exception response or malformed frame | Counted in A's own pacing; never retried within the cycle | None | None | Hypothesis |
| Withheld by qualification | Posture `WITHHELD` with its reason; no publication; A's published assets fence under the existing generation rules | None | None | Hypothesis |
| START, STOP or RESTART of A | A's desired revision, epoch and generation change | Desired state, epoch, generation, retry budget and assets unchanged | None | Hypothesis |
| Unproven close on A | `FAILED` with `CLOSE_UNCONFIRMED` and the safety quarantine flag; A is blocked until process restart | None; A's connection is never shared | None | Proven for the quarantine semantics, Hypothesis for the instance scope |
| Restore failure of A's durable recovery material | `FAILED` until repair; the restore error names only A | Keep running | Keep running | Proven |
| Semantic publication refused for A's asset | A's publication is fenced | None | None | Hypothesis |
| Two instances reach the same asset | The second claimant is withheld as `ASSET_CONFLICT`; the first keeps the asset | The first is unaffected | None | Hypothesis |
| Disabled by the Portal driver selection | `DISABLED`, listed, nothing constructed or dialed | None | None | Proven for the selection seam |
| Entry removed from the document | Unregistered at the next start; its record is removed under the lifecycle rule | None | None | Hypothesis |
| Rejected document | No instance is registered | Not applicable | As the v1 endpoint file | Hypothesis |
| Internal failure inside A's work | Contained at the instance boundary; A is `FAILED` with a categorical reason | None | None | Hypothesis |
| Endpoint unreachable at process start | A is not ready; process readiness is unaffected | None | None | Proven for the process readiness rule |

## Pacing profile

The profile is the `pacing` object of an entry. These values are the contract's
recommendation for production sites. They are proposals from sanitized pacing
observations, not measured guarantees, and no site is known to tolerate them.

| Invariant | Grade |
| --- | --- |
| Exactly one connection per endpoint. Instances never share a connection, scheduler or gap timer. | Hypothesis |
| Exactly one request in flight per instance. The next request is not sent until the previous one completes or times out. | Hypothesis |
| Every request of the instance passes the same gate: the worker, qualification, retries and any on-demand read. | Hypothesis |
| The gateway may hold one connection to each of up to eight distinct endpoints. | Hypothesis |
| The v1 mapping keeps today's transport limits and is the only place where more than one request may be in flight. | Proven for the limits, Hypothesis for the exception |

| Member | Meaning | Bound | Production default | Grade |
| --- | --- | --- | --- | --- |
| `gap_ms` | Minimum idle time between the completion of one transaction and the start of the next on the connection | 50 to 2000 | 200 | Hypothesis |
| `settle_ms` | Wait after each successful connect before the first request | 0 to 10000 | 1000 | Hypothesis |
| `cycle_s` | Interval between the starts of successive acquisition cycles | 15 to 3600 | 30; for `sunspec` 15, the cycle it has today | Hypothesis, and Proven for the SunSpec value |
| `backoff_floor_s` | First reconnect delay after a transport failure; each further failure doubles the delay | 1 to 300 | 5 | Hypothesis |
| `backoff_ceiling_s` | Largest reconnect delay; at least the floor | 5 to 3600 | 300 | Hypothesis |

| Rule | Grade |
| --- | --- |
| A family contract may narrow a bound and raise a default; it never widens a bound. Vendor-specific values belong to that contract. | Hypothesis |
| Pacing never extends a read bound or an attempt bound of a qualification. When a gap leaves a bounded sequence incomplete, the attempt ends as it would at its bound. | Hypothesis |
| A Modbus exception response is a completed transaction and is not retried within a cycle. | Hypothesis |
| For a family that routes several children, a child that times out three consecutive times is backed off alone, while the instance still serializes every request. | Hypothesis |
| Recommended bring-up for a production site: start with a one-unit allowlist, observe the status, then widen the allowlist. | Hypothesis |
| What each cycle reads belongs to the family's native contract. Pacing bounds only the rhythm. | Proven as a statement of ownership |
| Whether 200 ms is compatible with every SunSpec chain inside its attempt bound is not established. | Unknown |
| The maximum sustained cycle, latency distribution, settle time and effect of another client on any site are not established. | Unknown |

## Asset and publication keying

| Level | Rule | Grade |
| --- | --- | --- |
| Source | Exactly one per instance, as above | Hypothesis |
| Asset of a single-asset family | `sunspec` publishes one PV asset per instance. Its ID follows the existing PV publication rule, which the migrated `default` entry keeps unchanged. A further `sunspec` instance follows the same rule for its own device. | Proven for one instance, Hypothesis for several |
| Assets of a multi-asset instance | One asset per admitted child device and class, each with the instance's source | Hypothesis |
| Publication scope | Every asset carries its instance's source, epoch and driver generation. Fencing or retiring an instance acts on every asset of its source and on no other source's assets. | Proven for the hub seam, Hypothesis for the instances |

The ID of an asset of a multi-asset instance never derives from a serial number
or an ESN. It is the class's asset prefix, a hyphen, and the first 32 lowercase
hexadecimal characters of the SHA-256 digest of these UTF-8 fields in order,
each followed by a NUL byte: the domain tag `helianthus.modbus.asset.v1`, the
configured instance label, the class token, and the routed unit in decimal.
The prefix for PV is `pv-asset`; other classes use their lowercase class token
followed by `-asset`. The inputs are the label, the class and the routed unit
only. Endpoint, host, port, address, model, firmware and listing order are not
inputs. A family that cannot give its children distinct class and unit pairs
withholds the ambiguous children rather than inventing an ordinal. The rule is
a Hypothesis. The operator-selected alternative, an operator-configured ID for
every asset, is not part of this contract.

Re-addressing consequences:

| Change | Effect on asset IDs | Grade |
| --- | --- | --- |
| Rename the label | Every ID of the instance changes, together with its driver ID and source; the old assets are withdrawn and no alias is kept | Hypothesis |
| Change the routed unit of a child | The IDs of that child change; other children keep theirs | Hypothesis |
| Remove a child from `units` and add it back | The same label, class and unit give the same ID again | Hypothesis |
| Point the same label at another endpoint | IDs stay; the endpoint is not an input, so only qualification guards what answers there | Hypothesis |
| Replace a device in the same slot | IDs stay; identity changes appear as facts, not as an ID | Hypothesis |
| Reach one device through two labels | Two sets of IDs | Hypothesis |
| Reach one `sunspec` device through two endpoints | The second instance is withheld as `ASSET_CONFLICT` | Hypothesis |

## Observability

Status is required per endpoint on every surface that reports Modbus or driver
status. This page defines no member beyond the `instance` argument below; every
other member is owned by the existing pages and by the golden envelopes of the
gateway. The requirement is a Hypothesis.

| Surface | Requirement | Grade |
| --- | --- | --- |
| `helianthus.runtime.list` and `get` | Every instance appears, disabled and withheld ones included, with the closed G5 driver projection and no new field | Hypothesis |
| `modbus.v1.huawei.smartlogger.status.get`, `modbus.v1.huawei.emma.identity.get`, `modbus.v1.huawei.sdongle.status.get` | Gain the optional string argument `instance`, described below. A pre-1.0 schema change with updated goldens. | Hypothesis |
| `modbus.v1.sunspec.status.get` (new) | A cached, read-only status tool for the `sunspec` family with the same optional `instance` argument. It reports, for the selected `sunspec` instance, the qualification posture with its closed reason, the child routing and the published asset IDs, so a second `sunspec` instance is observable without the single-slot retained-observation tool or the closed G5 projection. Pre-stable, with goldens. | Hypothesis |
| `semantic.v1.snapshot.get` and GraphQL `semanticSnapshot` | The semantic reads for every multi-asset instance, by opaque asset ID, as in the [shared snapshot contract](./semantic-snapshot-read.md). A deployment may publish more than 32 assets; consumers select in groups of at most 32. | Hypothesis, building on a Proven contract |
| `semantic.v1.pv.current.get` | Remains the single-asset SunSpec projection, serving the asset of the v1 slot only; it answers as an unavailable provider when no such entry exists | Hypothesis |
| Canonical PV M2M projection and the Portal semantic PV panel | Keep addressing their one configured asset reference | Hypothesis |
| GraphQL status | Where GraphQL exposes a per-instance Modbus status fact that MCP exposes, it presents the same fact from the same cached view. No lifecycle GraphQL API is added. | Hypothesis |
| Portal | Shows per-instance status keyed by DriverID and uses the existing driver enable/disable selection. It neither edits nor displays endpoints. | Hypothesis |
| Logs | Categorical lines may carry a label or driver ID and never an endpoint | Hypothesis |
| eBUS MCP tools | Unchanged: envelopes, names and goldens | Hypothesis |

The `instance` argument:

| Rule | Grade |
| --- | --- |
| It is a string with the label grammar and names the entry's label. | Hypothesis |
| It applies to the three vendor status tools and to `modbus.v1.sunspec.status.get`. It is optional. When omitted it resolves to the only configured instance of the tool's family; with none the tool answers `UNAVAILABLE` as for an unconfigured provider, and with more than one it answers `INVALID_ARGUMENT`. | Hypothesis |
| A label that names no configured instance of the tool's family is `INVALID_ARGUMENT` with a static message that does not reveal whether the label exists for another family. | Hypothesis |
| The tool reads cached state and performs no wire I/O. | Hypothesis |
| For the selected instance it reports the child routing and the published asset IDs, and the posture with its closed reason. The member names and shape are owned by the gateway golden envelopes of those tools. | Hypothesis |
| The golden envelopes cover omitted instance, valid instance, wrong family, unknown label, a disabled instance and a withheld instance, each with two instances configured. | Hypothesis |
| Every other `modbus.v1` tool, apart from the new SunSpec status tool, is unchanged by this contract. Raw reads and retained observations address the v1 slot only, because a raw read bypasses family qualification and would bypass a vendor family's pacing. Whether a raw read may select an instance is not decided here. | Hypothesis, Unknown for the open question |

## Acceptance obligations

These are test obligations for the implementing repositories, not executed
tests. Every obligation is a Hypothesis.

| Obligation | Section | Grade |
| --- | --- | --- |
| A v1 configuration is golden-equivalent to today's behavior, including driver ID, source and durable state | Migration table | Hypothesis |
| A `sunspec` entry and a vendor entry register two instances | Registration | Hypothesis |
| Each rejection category is produced by its case with zero factory calls, in the stated order | Rejection table | Hypothesis |
| A dial failure on one instance leaves the other running, with eBUS, eeBUS, HTTP and MCP unaffected | Failure isolation | Hypothesis |
| Restarting one instance leaves the other's generation unchanged | Lifecycle | Hypothesis |
| An endpoint appears in no log, error, argument, environment variable or status | Protected materialization | Hypothesis |
| A withheld instance is listed with its closed reason, sends nothing when `FAMILY_NOT_ADMITTED`, and publishes nothing | Qualification | Hypothesis |
| Under concurrent callers, one instance never has more than one request in flight and honors the gap and the settle wait | Pacing profile | Hypothesis |
| Asset IDs change when, and only when, the label, class or routed unit changes | Asset and publication keying | Hypothesis |
| The status tools answer for each `instance` case listed above | Observability | Hypothesis |
| The add-on emits exact document content and modes for a valid list, rejects each invalid case with a redacted message, rejects a mixed configuration, and produces byte-identical v1 arguments for a v1-only configuration | Selection and document | Hypothesis |

## Open questions

| Question | Grade |
| --- | --- |
| Whether an entry added after bootstrap should start without an operator START | Unknown |
| Whether a raw read or retained observation may select an instance | Unknown |
| Whether the maximum of eight entries fits every deployment | Unknown |
| Whether two names for one device, such as a host name and an address, can be detected | Unknown |
| Vendor-specific pacing minimums, defaults and child routing | Unknown here; owned by each family's native contract |
| Portal-managed endpoint setup | Unknown; outside this contract and a separate decision |

This page claims no physical validation, no support for any family, no
semantic promotion and no stability before 1.0.
