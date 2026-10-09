# B524 Explicit Operation Reads

This contract covers B524 operations outside the OP02/OP06 scalar scan. It
preserves explicit request identity and raw response evidence. It does not
qualify target support, native Event semantics, a setter, or a scalar RR
namespace.

## Explicit read plan

`--b524-read-plan` accepts a JSON object conforming to
[the version 1 schema](fixtures/b524-operation-read-plan-schema-v1.json).
Every request is explicit. The plan does not enumerate channels, instances,
event addresses, or weekday codes. Operation determines the wire opcode, so an
item never supplies a redundant opcode field. `--preview-read-plan` validates
and displays normalized selectors without transport I/O.

Standalone Event commands require an explicit `--weekday-code`; there is no
implicit value of zero and no assigned weekday meaning for this selector.

There is no new implicit request cap. The shared scanner budget counts actual
attempts for selected operation reads with the normal scan work. Ordinary scalar
presets do not expand this plan or construct Event selectors.

| Operation | Required selector fields | Boundary |
| --- | --- | --- |
| `ReadTimer` | `channel`, `instance`, `weekday` | The seven channel names are `ventilation`, `noise-reduction`, `tariff`, `dhw`, `circulation`, `zone-cooling`, and `zone-heating`. Non-zone channels require `instance: 0`; zone instances remain explicit `u8` values. VRC700 profile handling applies. |
| `ReadVR91` | none | Opcode-only VRC700 operation. |
| `GetEvent` | `profile`, `instance`, `address`, `weekday_code` | `system` admits addresses `1..3`; `dhw` and `zone` admit `1..2`. The instance stays an explicit `u8`; Event support and weekday-code semantics remain experimental and unqualified. |
| `GetEventSetPoint` | `profile`, `instance`, `address`, `weekday_code` | `system` admits addresses `1..3`; `dhw` and `zone` admit `1..2`. The instance stays an explicit `u8`; Event support and weekday-code semantics remain experimental and unqualified. |

The planner lists only selected requests and their progress. Replay preserves
the same operation records without transport I/O. Browser and HTML show Event
candidate interpretations beside raw values with an explicit experimental,
`schema_unqualified` marker. A response of the expected length does not qualify
native Event semantics.

## Additive artifact records

Events retain the explicit instance byte. The fixed system/DHW `II=00` rule
of the Timer profile is not projected onto Event selectors; native Event
instance support remains unqualified.

Operation reads are additive to an artifact with outer `schema_version: "2.3"`.
They use `b524_operation_reads_schema_version: 1` and
`b524_operation_reads`, validated by the
[additive artifact schema](fixtures/b524-operation-reads-artifact-schema-v1.json).
Each record contains the operation, normalized opcode, selector, request and
raw response payloads, response state, decoded value or `null`, qualification,
request-context correlation, attempt count, and optional error. Replay records
may also retain `trace_seq`. Known Timer and Event selectors use their
canonical selector shapes; unknown OP03/09/0B replay selectors use
`selector: {}` with a raw `raw_selector` and remain raw-only. Known Event
records may retain the same canonical `pair_context`; when present it must
match the selector. Raw-only records retain `decoded: null` and
`schema_unqualified`.

`response_state` is one of `value`, `empty`, `nack`, `timeout`,
`transport_error`, `malformed`, or `unattempted`. A `value` record has at least
one attempt and retains the operation-specific raw reply: seven bytes for
`ReadTimer`, and eight bytes for `ReadVR91`, `GetEvent`, or
`GetEventSetPoint`. Raw-only replay records may therefore be `value` while
keeping `decoded: null`. A `malformed` record retains its nonempty wrong-length
raw reply and keeps `decoded: null`; states without a decodable reply also keep
`decoded: null`. An `unattempted` record
has zero attempts and retains an `error` reason when budget exhaustion,
recovery, or interruption leaves a selector unsent. Once an admitted attempt
has started, budget/recovery/interruption failure is `transport_error` with an
error reason. `selector_correlation` is always
`request_context`: these replies do not provide enough selector echo to infer
the selector from a reply. `decoded.parameter_config`, when present, is raw and
does not prove writability. Timer or VR91 decoding may use `profile_vrc700` only
when `meta.resolved_identity` retains the target probe's `manufacturer: 0xB5`
and matching `device_id`/`eid` of `70000` or `B7S00`. Records without that
evidence remain `schema_unqualified`, including decoded synthetic fixtures and
conservative replay. `ReadVR91` has its own eight-field decoded shape and does
not contain `parameter_config`. Events remain `schema_unqualified` until native
confirmation.

Standalone `b524 read-timer` and `b524 read-vr91` output retains the same guard
as `target_qualification`: `service: 07/04`, destination address, manufacturer,
matching EID/device ID, raw software and hardware bytes, and the complete raw
identity payload. This object contains no serial or private transport endpoint.
Its absence keeps the direct decode `schema_unqualified`.

For a known selector with `response_state: value`, the decoded object uses the
complete operation-specific shape and is mechanically correlated to every
retained reply byte. Timer slot `start_raw`, `stop_raw`, minute projections,
`unused`, `parameter_config`, and `raw_hex` must all agree with the seven-byte
reply. Invalid Timer pairs remain raw with both minute fields `null`; only
`0x90 0x90` is marked unused. VR91 and both Event decoded shapes follow the
same raw-correlation rule. This proves internal format consistency only. It
does not qualify target support, Event semantics, writable behavior, or any
physical device state.

## Editors and writes

`WriteTimer`, `SetEvent`, and `SetEventSetPoint` use an
[edit-plan schema](fixtures/b524-operation-edit-plan-schema-v1.json). A timer
plan requires the artifact target as an integer `destination_address` byte, has
three raw `[start, stop]` pairs or `null` slots, and retains one seven-byte OP03
baseline. Timer slots use time codes `0x00..0x90`; `null` is the editor
representation of an unused `0x90 0x90` slot. For an explicit pair, start is
`0x00..0x8F`, stop is `0x00..0x90`, and the operation parser requires start to
be strictly lower than stop before constructing a payload. The JSON Schema
enforces the structural byte bounds; the parser enforces that sibling-value
ordering. Non-zone Timer selectors require `instance: 0`. Event plans have seven raw bytes and both eight-byte OP09 and OP0B
baselines. Their selectors retain an explicit `u8` instance and the same
profile-specific address catalogs as reads. UI exports use the same plan shape.

`b524 apply-operation --plan FILE` defaults to an offline preview and diff.
It derives the target from the required plan `destination_address`; an explicit
`--dst` must identify the same byte or the command fails before transport opens.
Missing or invalid targets fail closed rather than falling back to `0x15`.
`--execute` fails closed unless a matching
[native-write qualification](fixtures/b524-native-write-qualification-schema-v1.json)
and exact confirmation text are supplied. Before a native write it verifies raw
EID and SW through `0x07/0x04`; the qualification supplies `profile` and two
raw SW bytes as `software_raw_hex`, alongside scope, manufacturer, EID, model,
selector, evidence reference, and a Boolean `native_qualified`. The schema
accepts both values so negative fixtures and templates remain structurally
checkable. Runtime admission requires literal `true`, and that value is valid
only when the cited native evidence supports the exact target and selector.
The bundled synthetic qualification uses `false` and cannot admit a write.
Qualification
selectors are exact: OP04 uses `channel`, `instance`, and `weekday`; OP0A/OP0C
use `profile`, `instance`, `address`, and `weekday_code`. Qualification evidence
remains separate from operator consent. Schema validation and a literal `true`
claim neither prove native support nor authorize execution. An unchanged edit is
still valid for offline preview and export, but execution validation rejects it
before transport opens. Every returned execution outcome retains the integer
`destination_address` and `verified_confirmation`, the exact confirmation text
that passed equality validation before I/O. A permitted execution is one send
without automatic retry, with retained raw feedback and separate readback of
the exact selector. A timeout, ambiguous feedback, or partial result remains
unknown and must not trigger an automatic repeat or rollback.

Event execution stays disabled pending a qualified native Event contract, even
though its offline editor and backend payload builders are available.
