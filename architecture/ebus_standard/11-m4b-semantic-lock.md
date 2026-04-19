# M4B Semantic Lock — Read & Decode Surfaces

Status: Normative (lock artifact)
Milestone: M4B_read_decode_lock
Plan reference: `ebus-standard-l7-services-w16-26.implementing/00-canonical.md`
Canonical SHA-256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`
Gateway anchor commit: `92fb98cc` (helianthus-ebusgateway#505, merged 2026-04-19)
Consult: cruise-consult dual-vendor (Claude + Codex), 2 rounds, joint verdict
`option_a_prime` / `option_d_decode_scaffold_lock_with_reserved_typed_decode`
(functionally identical; "lock-as-shipped with explicit additive-openness").

## Purpose

This chapter freezes the exact semantic contracts delivered by
**M4_GATEWAY_MCP** against breaking change, gating consumer rollout in
**M5_PORTAL** (vrc-explorer) and **M5b_HA_NOOP_COMPAT** (ha-integration).

Every normative clause below is a hard lock. Any change breaking a lock
post-merge requires a new locked-plan amendment decision. Additive
extension under `v1.minor` is permitted by §6 without amendment.

## Scope

This lock covers, exactly and exhaustively:

1. The MCP envelope shape across the 4 first-delivery surfaces:
   `ebus.v1.ebus_standard.services.list`,
   `ebus.v1.ebus_standard.commands.list`,
   `ebus.v1.ebus_standard.command.get`,
   `ebus.v1.ebus_standard.decode`.
2. The `safety_class` enum and its emission locations.
3. The error schema (wrap-chain, sentinel contract, boundary
   domain translation).
4. The `decode` surface payload shape (scaffold lock with reserved
   typed-decode extension points).
5. Catalog-version reporting (`meta.consistency.catalog_version`,
   `meta.consistency.plan_sha256`).

Out of scope (deferred to later lock artifacts):

- Responder lane (M4b2 / M4c1 / M4c2 / M4D) — covered by follow-up Q2.
- Live invocation surfaces (`ebus.v1.rpc.invoke`) — already locked by
  `10-rpc-source-113.md` (source=113 invariant) and by the execution
  policy module in `05-execution-safety.md`.

## Canonical reference fixtures

The canonical JSON shape for each surface is the golden fixture set
shipped by gateway commit `92fb98cc`:

| Surface | Golden fixture path |
|---|---|
| `services.list` | `helianthus-ebusgateway/mcp/ebus_standard/testdata/services_list.golden.json` |
| `commands.list` (filtered) | `helianthus-ebusgateway/mcp/ebus_standard/testdata/commands_list_pb03.golden.json` |
| `command.get` | `helianthus-ebusgateway/mcp/ebus_standard/testdata/command_get_alpha.golden.json` |
| `decode` | `helianthus-ebusgateway/mcp/ebus_standard/testdata/decode_alpha.golden.json` |

These fixtures, at that commit, are the authoritative wire shape. Any
future producer-side change MUST keep every one of these fixtures
byte-identical (modulo `data_timestamp` and fields explicitly flagged
additive-open in §6).

## §1 — Envelope (locked)

### §1.1 Top-level object

Every MCP response (success or failure) for every covered surface MUST
be a single JSON object with exactly three top-level members in this
key set:

```
{
  "meta":  <object, required, non-null>,
  "data":  <surface-specific object, always present, never null>,
  "error": <null on success, structured object on failure per §3>
}
```

No other top-level keys are permitted. `additionalProperties: false`
is locked at the top level.

`data` MUST always be a surface-specific typed JSON object; it MUST
NOT be `null` or omitted, on success OR on failure. On failure, `data`
is the partial typed body when available, otherwise the empty typed
body for that surface (consistent with `09-mcp-envelope.md` §Envelope
Shape). The success/failure signal is carried by `error` per §3.1,
never by `data` nullability.

### §1.2 `meta` shape

`meta` is a locked object with the following required members and
their locked semantics:

| Key | Type | Lock |
|---|---|---|
| `meta.contract.name` | string | `"helianthus-ebus-mcp"` (literal, locked) |
| `meta.contract.major` | integer | `1` (locked; bump = v2 breaking change) |
| `meta.contract.minor` | integer | `0` at this lock; MAY increment per §6 |
| `meta.consistency.mode` | string | `"LIVE"` (enum; see §1.3) |
| `meta.consistency.catalog_version` | string | SemVer of the `ebus_standard` catalog emitted for this response |
| `meta.consistency.plan_sha256` | string | Canonical plan SHA-256 (lower-hex, 64 chars) |
| `meta.data_timestamp` | string | RFC 3339 UTC timestamp at response-assembly time |
| `meta.data_hash` | string | Canonical-JSON SHA-256 of `data` per §1.4 |

`additionalProperties: true` is LOCKED on `meta` itself — additional
meta keys MAY be added under §6. Consumers MUST accept unknown `meta.*`
keys and MUST NOT fail on them.

### §1.3 `meta.consistency.mode` enum

Locked open enum. Known values at v1.0:

- `"LIVE"` — response assembled from live catalog state at request
  time.

Future additions (e.g. `"CACHED"`, `"DEGRADED"`, `"SNAPSHOT"`) are
permitted under §6 as additive minor changes. Consumers MUST accept
unknown string values and treat them as degraded/unknown consistency,
not as a parse error.

### §1.4 `meta.data_hash` determinism

`meta.data_hash` MUST be the SHA-256 (lower-hex, 64 chars) of the
canonical-JSON encoding of the `data` member, where canonical JSON is:

- Keys sorted lexicographically at every object depth.
- Compact numbers (shortest round-trip form, no trailing zeroes except
  as required by integer encoding).
- No insignificant whitespace.
- UTF-8, no BOM.

`data` is never emitted as the JSON literal `null` under this lock
(§1.1): failure paths emit the empty typed body for the surface, so
the hash is always computed over a canonical-JSON object encoding.
Producers and consumers that compute the hash MUST use the same
canonical-JSON implementation; the gateway fixture set at `92fb98cc`
is the reference.

`meta.data_hash` is locked as a wire-visible determinism invariant: a
byte-identical `data` MUST always produce a byte-identical
`meta.data_hash` across gateway versions within `v1.*`.

## §2 — `safety_class` enum (locked)

The `safety_class` enum is locked with exactly these values:

```
read_only_safe
read_only_bus_load
mutating
destructive
broadcast
memory_write
```

Lock properties:

- Case is locked as `lower_snake_case`.
- Set is locked-open: new values MAY be added per §6; existing values
  MUST NOT be removed, renamed, or have their semantics changed.
- Consumers MUST accept unknown `safety_class` string values and treat
  them as at-least-as-restrictive as `destructive` (fail closed).

Emission locations (locked):

- `commands.list` — each item MUST carry its `safety_class`.
- `command.get` — the response MUST carry the command's `safety_class`.

`safety_class` MUST NOT be omitted from any service or command
described by the read surfaces.

## §3 — Error schema (locked)

### §3.1 Presence rule (locked)

`error` is present in every response.

- On success: `error` is the JSON literal `null`. This is locked and is
  the primary success signal for consumers.
- On failure: `error` is a structured object (never `null`, never
  absent, never a string).

### §3.2 Failure-object shape (locked)

On failure, `error` is an object with:

| Key | Type | Lock |
|---|---|---|
| `error.code` | string | locked UPPER_SNAKE_CASE at the MCP boundary |
| `error.message` | string | human-readable; non-empty |
| `error.retriable` | boolean | locked; `false` at v1.0 for all current codes |

`additionalProperties: true` is LOCKED on `error` — future optional
fields (e.g. `error.cause`, `error.hint`, `error.retry_after_ms`) MAY
be added per §6. Consumers MUST accept unknown `error.*` keys.

### §3.3 `error.code` values

`error.code` values at v1.0 follow the taxonomy shipped in
`helianthus-ebusgateway` at `92fb98cc` (derived from the gateway
`classifyErr` boundary translator). The enum is locked-open:

- New UPPER_SNAKE codes MAY be added per §6.
- Existing codes MUST NOT be removed, renamed, or have their semantics
  changed.
- Consumers MUST accept unknown UPPER_SNAKE codes and treat them as a
  generic failure class (fail closed).

### §3.4 Wrap-chain / sentinel contract (locked)

On the producer side, gateway errors MUST flow through the execution
policy module's `ErrSafetyClassDenied` and related sentinels
(`errors.Is`-compatible) as documented in `05-execution-safety.md`.
This is a producer-side invariant; it is visible to consumers only via
`error.code`. Consumers MUST NOT depend on exact wrap-chain structure,
only on `error.code`.

### §3.5 Dual-domain translation (locked)

The MCP boundary uses **UPPER_SNAKE_CASE** for `error.code`. The
internal `ebusgo/types.DecodeError.Code` domain uses
`lower_snake_case`. This dual-domain split is intentional and locked:

- `ebusgo/types` lower_snake codes are an INTERNAL concern and MUST
  NOT leak through the MCP boundary.
- The gateway `classifyErr` translator is the sole authorized boundary
  crossing.

## §4 — `decode` surface (scaffold lock with reserved typed-decode)

### §4.1 `data` shape (locked scaffold)

The `decode` response `data` is a locked object with:

| Key | Type | Lock |
|---|---|---|
| `data.fields` | array<DecodedField> | locked type; empty `[]` permitted at v1.0 per §4.2 |
| `data.validity` | string (open enum) | locked per §4.3 |
| `data.replacement_value` | boolean | locked per §4.4 |

`additionalProperties: true` is LOCKED on `data` and on every future
`DecodedField` object. This is the critical forward-compat clause:
generated clients using `oapi-codegen`, `quicktype`, or
`openapi-generator` MUST be configured in non-strict mode for
`decode.data` so that additive enrichment under §6 does not break
consumers.

Consumer guidance: implementations SHOULD use open-schema / catch-all
mapping (Go `map[string]any` tail, Python `extra="allow"`, TypeScript
`[key: string]: unknown`, Rust `#[serde(flatten)]` or equivalent) for
any decoded field not explicitly modeled.

### §4.2 `data.fields` empty-array semantics (locked)

At v1.0, `data.fields` is emitted as `[]`. This value is normatively
defined as:

> "**No per-field decode is available at this catalog / plan
> version.**" — NOT "**there are no fields.**"

Consumers MUST NOT interpret `[]` as "decoded successfully with zero
fields". The correct interpretation is "decode scaffold returned; no
structured field projection yet; consult raw / replacement status via
`data.validity` and `data.replacement_value`."

Populated `fields[*]` entries MAY land under §6 without plan
amendment, provided their element shape is itself
`additionalProperties: true` so further enrichment remains
additive-compatible.

### §4.3 `data.validity` open enum (locked)

`data.validity` is typed as `string` (NOT a closed JSON Schema enum).
At v1.0 the only known value is `"catalog_identified"`.

Lock clauses:

- Consumers MUST accept arbitrary string values.
- Consumers MUST treat unknown string values as degraded / unknown
  validity (fail safe, not parse error).
- Reserved future values (non-normative, informative only):
  `"wire_decoded"`, `"wire_mismatch"`, `"stale_catalog"`,
  `"replacement"`. Producers MAY adopt these (or any other) additional
  string values under §6.

### §4.4 `data.replacement_value` (locked boolean)

`data.replacement_value` is a boolean. At v1.0 it is always `false`.

The value `true` is RESERVED for future wire-decode replacement
semantics. v1.x producers MUST NOT emit `true`. When richer
replacement metadata is required (e.g. `replacement_reason`,
`replacement_source`), it MUST land as sibling fields on `data` (per
§4.1 additionalProperties allowance), not by widening this boolean.

### §4.5 Producer-side reference type

The producer-side reference is
`helianthus-ebusgo/protocol/ebus_standard/types.Value`:

```go
type Value struct {
    Raw         []byte
    Value       any
    Valid       bool
    Replacement bool
    Err         *DecodeError
}
```

This is the internal Go-level shape. The MCP wire representation is
the §4.1 scaffold; the two are NOT required to be structurally
identical. The internal `Err *DecodeError` surfaces at the MCP
boundary via `error.code` (§3), not via `data`.

## §5 — Catalog-version reporting (locked)

Every response from every covered surface MUST include:

- `meta.consistency.catalog_version` — SemVer of the `ebus_standard`
  catalog used to assemble the response.
- `meta.consistency.plan_sha256` — SHA-256 of the canonical plan
  anchoring the catalog.

These fields are locked as mandatory; omission is a contract
violation. Consumers MAY key cache invalidation off the pair
`(catalog_version, plan_sha256)`.

## §6 — Versioning policy

### §6.1 v1.0.0 baseline

`(contract.major=1, contract.minor=0)` = this lock, emitted by
gateway `92fb98cc`.

### §6.2 v1.minor (additive, no plan amendment)

The following changes MAY land under a `contract.minor` bump without
any plan amendment:

- New `meta.*` keys (per §1.2 `additionalProperties: true`).
- New `safety_class` enum values (per §2).
- New `meta.consistency.mode` values (per §1.3).
- New `error.code` UPPER_SNAKE values; new optional `error.*` fields
  (per §3.3).
- Population of `data.fields[*]` in the `decode` surface (per §4.2).
- New `data.validity` string values (per §4.3).
- New sibling fields on `decode.data` (per §4.1) and on any
  `DecodedField` object.

All such changes MUST preserve the §7 conformance-test invariants.

### §6.3 v2 (breaking, requires plan amendment)

Any of the following is a v2 change and requires a new locked-plan
amendment decision:

- Removal or rename of any locked top-level key.
- Narrowing of any `additionalProperties: true` lock to `false`.
- Removal or semantic change of any existing `safety_class` value,
  `error.code`, or `meta.consistency.mode` value.
- Narrowing `data.validity` from open string to closed enum.
- Widening `data.replacement_value` beyond boolean.
- Any change that makes a previously-valid v1.x payload parse-fail
  under the v2 schema.

### §6.4 Stage-2 re-entry (informative)

When `ebusgo/types.Value{}` projection lands end-to-end and the
`decode` surface begins emitting populated `data.fields[*]`, that
change lands under §6.2 as a v1.minor bump with:

- A new golden fixture covering the populated shape.
- A schema-version bump (`meta.contract.minor`).
- No plan amendment.

This is the explicit stage-2 trigger for the decode surface.

## §7 — Conformance test suite (locked)

The following tests are normative and MUST exist in the gateway repo:

1. **Golden fixtures** — byte-identical comparison of each of the 4
   surfaces' responses against the fixture set in
   `helianthus-ebusgateway/mcp/ebus_standard/testdata/`, modulo
   `meta.data_timestamp`. The v1.0 reference fixture set is the one
   shipped at gateway commit `92fb98cc`. Each subsequent additive
   `v1.minor` change (§6.2) MUST land together with updated fixtures
   that include the additive content; the byte-identical invariant
   applies against the fixture set **of the same `meta.contract.minor`
   version**, not against the v1.0 set. Removing or mutating any field
   that was present in a prior `v1.minor` fixture set is a §6.3 v2
   breaking change.

2. **`data_hash` determinism**: for each golden fixture, recomputing
   canonical-JSON SHA-256 over `data` MUST yield
   `meta.data_hash` exactly.

3. **Forward-compat consumer golden** (added by this lock): a
   synthetic response containing:
   - an unknown `meta.*` key,
   - an unknown `safety_class` value (in `commands.list`),
   - an unknown `data.validity` value (in `decode`),
   - an unknown `error.code` (in a failure envelope),
   - an unknown `DecodedField` key (in a populated decode payload),

   MUST parse without error under the canonical consumer decoder, and
   the unknown values MUST be preserved / surfaced as "unknown"
   classes per the relevant section's consumer rule.

Test (3) is the load-bearing invariant for §6.2. Breaking it is a
regression against this lock.

## §8 — Consumer guidance (informative)

Reference consumer snippets SHOULD appear in M5 / M5b documentation
when those milestones land. Illustrative patterns:

- **Go**: use `map[string]json.RawMessage` for `data`, then selectively
  decode known keys; unknown keys remain available.
- **Python**: Pydantic models with `model_config = ConfigDict(extra="allow")`.
- **TypeScript**: interface with `[key: string]: unknown` index
  signature; disable codegen strict mode for `decode.data`.
- **Rust**: `#[serde(deny_unknown_fields)]` MUST NOT be set for any
  type under `decode.data`.

Languages with closed-sum-type idioms (Rust enums, Kotlin sealed
classes) SHOULD model `safety_class`, `meta.consistency.mode`,
`data.validity`, and `error.code` as `String` with a mapper function,
not as closed enums, to preserve forward-compat.

## §9 — Residual risks (acknowledged)

1. `additionalProperties: true` is only enforced by schema; strict
   codegen configurations can still be misused downstream. Mitigation
   in §8 consumer guidance.
2. `data.fields: []` semantics (§4.2) are a JSON-Schema-invisible
   convention. Mitigation via §7 test (3) and normative wording.
3. `error.code` UPPER_SNAKE boundary assumes every internal
   `ebusgo/types` domain code has an UPPER_SNAKE equivalent at the
   gateway. If that invariant is violated in future, the translator
   must grow a new code rather than leak lower_snake.
4. `data.replacement_value` is a weak (boolean) extension point;
   richer replacement metadata will arrive as sibling fields, not as a
   widening.
5. Conformance golden (§7.3) must be mirrored across consumer repos
   (M5, M5b). Gateway repo is the source of truth for the synthetic
   unknown payload.

## §10 — Sign-off

- Decision process: cruise-consult dual-vendor (Claude + Codex), 2
  rounds, both vendors converged on joint "lock-as-shipped with
  explicit additive-openness" verdict.
- Evidence: gateway commit `92fb98cc` + golden fixture set + this
  lock document.
- Supersedes: nothing (first M4B artifact).
- Amendment policy: any change violating §1–§5 or §7 requires a new
  locked-plan amendment per the Helianthus execution-plan protocol.
