Canonical source: this page.

# Cross-Runtime Envelope Contract

## Scope

This page defines the language-neutral envelope shared by protocol runtimes.
It does not define eeBUS, SHIP, SPINE, eBUS, or any implementation API. A
runtime may use native types internally, but every value crossing the platform
boundary uses this versioned envelope.

## Envelope Version 1

The closed logical fields are:

| Field | Meaning |
| --- | --- |
| `envelope_version` | Integer contract version, currently `1`. |
| `runtime_id` | Stable adapter-instance identifier within one installation. |
| `runtime_kind` | Protocol adapter family, used for routing rather than semantics. |
| `captured_at` | RFC 3339 UTC instant supplied by the capture clock. |
| `scope` | Versioned request or snapshot scope. |
| `payload` | Language-neutral data conforming to the named payload schema. |
| `status` | `ok`, `partial`, `unavailable`, or `rejected`. |
| `provenance` | Source identity and evidence references needed for replay. |

Unknown fields are rejected at a frozen envelope version. Producers never
encode implementation pointers, native error objects, host paths, credentials,
network endpoints, or private device identifiers. Numeric units, nullability,
ordering, and stale behavior belong to the payload schema and are not inferred
from a runtime's native representation.

`partial` preserves valid leaves and identifies unavailable leaves. It is not
coerced to `ok` or replaced wholesale. `unavailable` and `rejected` are explicit
negative states and never become an empty successful payload.

## Compatibility

Additive envelope fields require a new envelope version because the field set
is closed. A consumer rejects an unsupported version before reading `payload`.
Payload schema evolution is independently versioned and cannot silently change
the meaning, unit, scope, or provenance of an existing leaf.

Serialization syntax is transport-owned. JSON, Go, Python, and future runtimes
must represent the same logical fields and validation rules.
