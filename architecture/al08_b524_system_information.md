# Bounded B524 system information results

This architecture contract covers only pure request construction and representation
of an already transport-normalized reply. It is a partial slice of
[issue #736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736),
defined by [issue #862](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/862).
Nothing here is stable before Helianthus 1.0.

## Evidence and grades

The public native contract comes first: [B524 section 4.1](../protocols/vaillant/ebus-vaillant-B524.md#41-0x00-readsysteminformation)
and its [identifier evidence](../protocols/vaillant/fixtures/b524-op00-system-information-ids.csv).
This is OP=0x00 with a 16-bit information identifier, not an OP=0x02 or
OP=0x06 `(opcode, group, instance, register)` namespace. Group, instance and
register are not supplied by this API; an identifier must not be substituted
for any of them.

**Proven:** the pure API shape and synthetic binary32 arithmetic specified
below. These are representation assertions, not evidence of native effects.
**Hypothesis:** the normalized candidate layout applies to a particular physical
reply or device family. It does not qualify arbitrary families or physical reply
offsets. **Unknown:** presence, physical qualification, freshness and execution
remain independent of a finite decode. No code result or full parity is claimed
before the companion's own checks.

## Pure helper contract

`Ab42BuildInformation(identifier uint16) []byte` returns a fresh three-byte
buffer `[00, IDlo, IDhi]`. Identifier 0x1234 builds `00 34 12`.
`Ab42DecodeInformation(requestContext, raw) result` accepts exactly four
transport-normalized bytes and decodes little-endian IEEE binary32.
Every new context/result field uses the `ab42` prefix. The following JSON block
is the bounded declaration checked alongside the synthetic examples:

```json
{
  "ab42RequestOrder": ["00", "IDlo", "IDhi"],
  "ab42ReplyLength": 4,
  "ab42Representation": "little-endian IEEE binary32",
  "ab42ContextFields": ["ab42Family", "ab42Software", "ab42Hardware", "ab42APIVersion", "ab42APIRevision", "ab42Identifier"],
  "ab42ResultFields": ["ab42Context", "ab42Raw", "ab42State", "ab42Value", "ab42Capacity", "ab42CapacityState"],
  "ab42InvalidLengths": [0, 1, 2, 3, 5],
  "ab42NonFinite": ["NaN", "positive infinity", "negative infinity"],
  "ab42CapacityRule": "finite nonnegative integer",
  "ab42Cardinality": "supported capacity; never discovered cardinality or slot presence",
  "ab42InterpretationGrade": "Hypothesis"
}
```

The result owns a copy of `ab42Raw` and a snapshot of all six context fields.
Caller mutation cannot change a returned result; mutation of one returned buffer
cannot change caller input or any other result. Each build also owns its buffer.
Family, software, hardware, API version, API revision and numeric identifier
remain independent, including on invalid replies. API version and API revision
are distinct fields; neither replaces the other.

`ab42State` is `decoded`, `invalid_length` or `invalid_non_finite`.
`ab42Value` is a finite number only for `decoded`, otherwise null. Invalid
lengths and NaN or either infinity retain owned raw bytes with explicit invalid
state. Never fabricate a terminal discovery marker. Partial failure retains
context and raw evidence rather than discarding independently useful fields.
There is no discovery-state update here, so existing last-known-good state is
not replaced by an invalid decode.

`ab42CapacityState` is `decoded` only for identifiers 0x0000 and 0x0001 with a
finite nonnegative integer value; `ab42Capacity` then contains that integer.
Otherwise capacity is `Unknown` and null. A finite fractional or negative value
remains decoded while capacity is Unknown. Zero is numeric zero, not absence.
IDs 0x0000 and 0x0001 describe supported circuit/zone capacities, never
 discovered cardinality or slot presence. Capacity does not create slots or
qualify a device. There is no implicit count label for an unknown identifier;
preserve 0xFFFF numerically. ID 0x000D heat-pump count and separate eligibility
checks are independent; the competing candidate interpretation in the native
reference remains unresolved. This helper assigns no eligibility from that ID.

## Synthetic controls and companion boundary

The [small synthetic example set](fixtures/al08_b524_system_information.json)
is neither a complete dictionary nor a native profile. Its values include 1.0,
1.5, -1.0 and zero; the scoped test generates invalid lengths, non-finite bits,
and independent context variations. Tests check this page and examples without
importing another repository. Their local evaluator is only a specification
oracle; passing it establishes no companion implementation behavior.

No transport normalization, framed packet, registry descriptor, routed invocation
or runtime profile integration is added. No new transmit route, polling default,
automatic native qualification or write admission follows. Admission remains
fail-closed: representation alone grants no physical or write eligibility.
eBUS MCP compatibility and GraphQL parity remain companion verification duties;
this page changes neither surface. Navigation and runtime integration are carried
separately. The companion may be built now and merges after or with this page.
