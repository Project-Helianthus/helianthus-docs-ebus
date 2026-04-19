# MCP Envelope Contract

Status: Normative
Milestone: M4_GATEWAY_MCP
Plan reference: ebus-standard-l7-services-w16-26.implementing/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Purpose

This chapter defines the envelope contract for the first-delivery
`ebus_standard` MCP surfaces in `helianthus-ebusgateway`.

The canonical plan requires the following first-delivery MCP surfaces:

> `ebus.v1.ebus_standard.services.list`
> `ebus.v1.ebus_standard.commands.list`
> `ebus.v1.ebus_standard.command.get`
> `ebus.v1.ebus_standard.decode`

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.implementing/00-canonical.md`,
SHA-256 `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

Live invocation remains outside these read/decode surfaces and routes
through `ebus.v1.rpc.invoke`; see
[`05-execution-safety.md`](./05-execution-safety.md) and
[`10-rpc-source-113.md`](./10-rpc-source-113.md).

## Envelope Shape

Every MCP response for the first-delivery surfaces — successful or
failed — MUST be a single JSON object with these top-level members:

1. `meta`: envelope metadata.
2. `data`: the per-method typed response body. On failure, `data` is
   the partial typed body when available, otherwise the empty typed
   body for that method.
3. `error`: the typed error shape. `error` MUST be present in every
   response. On success, `error` MUST be emitted as the JSON literal
   `null`. On failure, `error` MUST be a structured object as defined
   below.

The `error` field is mandatory in all responses. It MUST NOT be
omitted on success, MUST NOT be an empty string, and MUST NOT be any
non-object primitive other than `null`. Producers MUST emit
`error: null` on success and a structured error object on failure;
consumers MUST rely on the field being present.

This rule aligns with, and does not depart from, the existing envelope
baseline documented in
[`architecture/mcp-first-development.md`](../mcp-first-development.md)
("MCP Contract Baseline") which lists `error` as "null or structured",
and in [`api/mcp.md`](../../api/mcp.md) ("Shared Request and Envelope
Rules") which enumerates `error` as part of the standard envelope.
Those documents remain the canonical baseline for the wire contract;
this chapter tightens emission discipline for the `ebus_standard`
first-delivery surfaces (mandatory `error: null` on success) without
changing the baseline shape.

### `meta`

`meta` carries envelope metadata and MUST include:

- method identifier for the MCP surface being served
- request identifier
- request/response timestamp fields
- `data_hash`

`meta.data_hash` is the SHA-256 digest defined in
[`#data_hash-semantics`](#data_hash-semantics). Timestamp field names
and any additional metadata remain implementation-owned until
`M4B_read_decode_lock`, but they MUST be emitted in a stable order and
covered by golden fixtures.

### `data`

`data` is the response body for the MCP method. Its shape is typed by
method:

- `ebus.v1.ebus_standard.services.list`
- `ebus.v1.ebus_standard.commands.list`
- `ebus.v1.ebus_standard.command.get`
- `ebus.v1.ebus_standard.decode`

The method-specific `data` schema MUST NOT be inferred from object
iteration order. Ordering rules are explicit and are defined in
[`#deterministic-ordering`](#deterministic-ordering).

### `error`

`error` is a typed failure body. It MUST include a stable machine code
and a human-readable message. Implementations MAY add structured fields
such as catalog identity, caller context, or disabled-provider state
when relevant.

For safety denials surfaced through `rpc.invoke`, error classification
MUST preserve the `ErrSafetyClassDenied` contract in
[`05-execution-safety.md`](./05-execution-safety.md#errsafetyclassdenied).

## Deterministic Ordering

MCP envelope JSON MUST be emitted deterministically.

The stable field order for the top-level envelope is:

1. `meta`
2. `data`
3. `error` (always present; `null` on success, structured object on failure)

Within `meta`, fields MUST be emitted in a documented stable order, with
`data_hash` present at `meta.data_hash`. Within `data`, every JSON
object used as a map MUST sort keys by raw ASCII-lexicographic order
before serialization. Arrays preserve their semantic sequence and MUST
NOT be sorted unless the method schema explicitly defines array sorting.

The map-key sorting rule applies recursively to all map/object values
inside `data` before serialization.

## `data_hash` Semantics

`meta.data_hash` is computed from the canonical JSON serialization of
the `data` block only.

Canonical JSON for this contract means:

1. Object keys are sorted by raw ASCII-lexicographic order at every
   nested object level.
2. Number rendering is stable across platforms and Go toolchain patch
   versions. Integers MUST render as decimal integers. Non-integer
   values MUST use the implementation's documented canonical renderer
   and MUST NOT depend on map iteration or locale.
3. No insignificant whitespace is emitted.
4. String escaping is deterministic.
5. Arrays preserve the sequence defined by the method schema.

The hash function is SHA-256. The digest is lower-case hexadecimal and
is emitted at `meta.data_hash`.

Changing a field value, object key, array order, or canonical number
rendering inside `data` MUST change `meta.data_hash`. Changing envelope
metadata outside `data` MUST NOT change `meta.data_hash`.

## Golden Fixture Discipline

Each MCP surface protected by this contract MUST have golden fixtures in
the gateway repository:

```text
<gateway>/mcp/ebus_standard/testdata/*.golden.json
```

Golden fixtures MUST contain the full envelope, not only the `data`
block. They therefore protect:

- top-level envelope shape
- `meta` field order and required metadata
- canonical `data` ordering
- `meta.data_hash`
- typed `error` shape for failure fixtures

Fixture regeneration MUST be explicit. The gateway test command MAY use
`UPDATE=1` or a `-update` flag, but either path is a fixture update and
MUST be called out in the PR body. The PR body MUST explain why the
golden output changed and whether the change is schema-additive,
behavioral, or a bug fix.

A rationale-free golden regeneration is a contract violation.

## Stability Guarantee

`M4_GATEWAY_MCP` introduces the first live read/decode surfaces. The
follow-up milestone `M4B_read_decode_lock` freezes the public envelope
shape for:

- `ebus.v1.ebus_standard.services.list`
- `ebus.v1.ebus_standard.commands.list`
- `ebus.v1.ebus_standard.command.get`
- `ebus.v1.ebus_standard.decode`

After `M4B_read_decode_lock` merges, these envelope shapes are frozen.
Changes are schema-additive only unless a later locked-plan decision
explicitly authorizes a breaking change.

Schema-additive means:

- adding optional fields whose absence remains valid
- adding enum values only when existing consumers have an unknown-value
  handling rule
- adding new typed error detail fields without changing stable error
  codes

Renaming fields, removing fields, changing `data_hash` semantics,
changing map-key ordering, changing stable error codes, or changing the
meaning of an existing field is not schema-additive.

## Related Documents

- [`05-execution-safety.md`](./05-execution-safety.md) - safety classes,
  default-deny policy, and shared policy function.
- [`08-provider-contract.md`](./08-provider-contract.md) - provider
  contract and disabled-provider behaviour surfaced through MCP.
- [`10-rpc-source-113.md`](./10-rpc-source-113.md) - gateway
  `rpc.invoke` source byte invariant.
