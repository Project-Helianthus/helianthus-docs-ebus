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
| `ReadTimer` | `channel`, `instance`, `weekday` | The seven channel names are `ventilation`, `noise-reduction`, `tariff`, `dhw`, `circulation`, `zone-cooling`, and `zone-heating`; VRC700 profile handling applies. |
| `ReadVR91` | none | Opcode-only VRC700 operation. |
| `GetEvent` | `profile`, `instance`, `address`, `weekday_code` | Event support and weekday-code semantics remain experimental and unqualified. |
| `GetEventSetPoint` | `profile`, `instance`, `address`, `weekday_code` | Event support and weekday-code semantics remain experimental and unqualified. |

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
`transport_error`, `malformed`, or `unattempted`. An `unattempted` record
has zero attempts and retains an `error` reason when budget exhaustion,
recovery, or interruption leaves a selector unsent. Once an admitted attempt
has started, budget/recovery/interruption failure is `transport_error` with an
error reason. `selector_correlation` is always
`request_context`: these replies do not provide enough selector echo to infer
the selector from a reply. `decoded.parameter_config`, when present, is raw and
does not prove writability. Timer decoding may use `profile_vrc700` only when
the existing target/profile qualification is satisfied. `ReadVR91` has its
own eight-field decoded shape and does not contain `parameter_config`. Events
remain `schema_unqualified` until native confirmation.

## Editors and writes

`WriteTimer`, `SetEvent`, and `SetEventSetPoint` use an
[edit-plan schema](fixtures/b524-operation-edit-plan-schema-v1.json). A timer
plan has three raw `[start, stop]` pairs or `null` slots and one seven-byte OP03
baseline. Event plans have seven raw bytes and both eight-byte OP09 and OP0B
baselines. UI exports use the same plan shape.

`b524 apply-operation --plan FILE` defaults to an offline preview and diff.
`--execute` fails closed unless a matching
[native-write qualification](fixtures/b524-native-write-qualification-schema-v1.json)
and exact confirmation text are supplied. Before a native write it verifies raw
EID and SW through `0x07/0x04`; the qualification supplies `profile` and two
raw SW bytes as `software_raw_hex`, alongside scope, manufacturer, EID, model,
selector, evidence reference, and `native_qualified: true`. Qualification
selectors are exact: OP04 uses `channel`, `instance`, and `weekday`; OP0A/OP0C
use `profile`, `instance`, `address`, and `weekday_code`. Qualification evidence
remains separate from operator consent. A permitted execution is one send without automatic retry,
with retained raw feedback and separate readback of the exact selector. A
timeout, ambiguous feedback, or partial result remains unknown and must not
trigger an automatic repeat or rollback.

Event execution stays disabled pending a qualified native Event contract, even
though its offline editor and backend payload builders are available.
