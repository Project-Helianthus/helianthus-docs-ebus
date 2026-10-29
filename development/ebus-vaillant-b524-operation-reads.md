# VRC Explorer: B524 Schedule and Event Reads

This contract covers B524 operations outside the OP02/OP06 scalar scan. It
preserves exact request identity and raw response evidence. It does not
qualify target support, native Event semantics, a setter, or a scalar RR
namespace.

## Finite registry read and offline plan results

The public [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
defines the opcode-scoped identities and the limits of native evidence. Its
[timer selector evidence](../protocols/vaillant/fixtures/b524-op03-op04-program-selectors.csv)
and [Event selector candidates](../protocols/vaillant/fixtures/b524-event-selector-candidates.csv)
retain unresolved assignments; a library result does not resolve them. The
contracts below are **Proven implementation contracts**, including offline byte
shapes, rather than proof that a device family supports an operation. Candidate
native interpretations remain **Hypothesis**; unqualified semantics and physical
support remain **Unknown**. Codec qualification is independent of that evidence
grade. These contracts carry no pre-1.0 stability promise.

This section describes registry library results, not additional Explorer
artifact fields or operation-selection schema entries. Explorer records retain
their existing schemas and qualification rules below. A successful library
parse or offline plan must not promote native qualification, register a router,
or add a runtime transmit route. Event execution remains **Unknown** and is not
admitted by an offline result.

| API/result boundary | Finite result and explicit acceptance condition |
| --- | --- |
| Scalar read request and normalized result | Request `[OP,00,GG,II,RRlo,RRhi]`, with OP02 and OP06 kept separate; normalized reply `[FLAGS,GG,RRlo,RRhi,VALUE...]`. A usable requested value requires exact GG and full RR correlation. II remains request context, never an echoed reply field. A GG or RR mismatch is uncorrelated, never usable for the requested identity: retain both identities and raw bytes, without attaching requested bounds. |
| Scalar no-value result | Empty means exactly zero payload bytes. A one-byte status is retained as status with no value; neither outcome establishes presence, absence, or codec qualification. Other incomplete headers are not usable scalar values. |
| Explicit-codec helper | The caller supplies the codec; its exact value width must match. A label or byte count never selects a codec automatically. Return the interpretation, evidence grade and codec qualification separately, preserving raw fallback on absent, unqualified or failed decoding. Successful decoding alone promotes none of them. |
| OP03 timer result | Exactly seven bytes: raw configuration plus three start/stop pairs; `slot_count: 3`, never seven. Codes are decimal 0..144 (`00..90` hex), in ten-minute steps. Only `90 90` hex is unused. An active pair requires `start < stop <= 144`; invalid pairs retain raw bytes and have no minute projection for either endpoint. |
| OP04 offline timer plan | Exactly eleven bytes `[04,GG,II,ADDRESS,DAY,START1,STOP1,START2,STOP2,START3,STOP3]`. ADDRESS precedes DAY; DAY is 0..6. Active pairs require `start < stop <= 144`; unused pairs are `90 90`. Retain an exact seven-byte OP03 baseline and matching family/channel/instance/day identity. A six-byte baseline or mismatched identity rejects the plan; no execution route is added. |
| OP08 raw result | Exactly eight bytes, in order: binding, special function, heating mode, cooling mode, status, frost protection, raw temperature 1, raw temperature 2. Length alone qualifies neither temperature codec nor field semantics or physical support. |
| OP09/OP0B paired raw results | Each is exactly eight bytes: raw configuration plus seven raw values. Pair identity includes family, instance, system type (GG), address and raw code. Every identity field must match; a raw code is never automatically a weekday. Keep both baselines and all values schema-unqualified. |
| OP0A/OP0C offline Event plans | Each is twelve bytes: the five-byte prefix `[OP,GG,II,ADDRESS,RAW_CODE]` followed by seven explicit raw values. OP0A corresponds to OP09 and OP0C to OP0B; retain both matched eight-byte paired baselines with the complete pair identity. Missing, wrong-length or mismatched baselines reject the plan. Event semantics stay schema-unqualified; execution is **Unknown**. An OP0A offline result cannot authorize execution, and OP0C has the same boundary. |

Failed, partial, empty or uncorrelated results preserve their own evidence and
each useful prior field with its original identity and qualification. They do
not erase last-known-good values, replace them with invented defaults, or
present retained values as fresh observations. Unknown stays Unknown; plan
admission fails closed when required identity or baseline evidence is missing.

### Finite synthetic examples

All bytes below are synthetic payloads after transport normalization, in hex.
They establish only software/document contracts, with no device observation or
native qualification implied.

- Scalar request `02 00 03 02 34 12` retains identity
  `(OP=02, GG=03, II=02, RR=1234)`. Reply `01 03 34 12 2A 00`
  correlates GG/RR. An explicitly supplied unsigned 16-bit little-endian codec
  can interpret its two value bytes as 42 without proving native meaning or
  bounds. Replies `01 01 34 12 2A 00` and `01 03 35 12 2A 00`
  independently mismatch GG and RR: retain the requested and returned
  identities and complete raw payloads, with no requested bounds. An empty
  payload and status `00` are distinct no-value results. A one-byte value
  `2A` fails that explicitly selected two-byte codec; `2A 00` without an
  explicit codec stays raw.
- For the VRC700 family, timer identity `channel=zone-heating, instance=02,
  day=04` retains baseline `A5 06 0C 12 18 90 90`: seven bytes, raw
  configuration `A5`, and three slots. The first two pairs project to
  60..120 and 180..240 minutes; the third is unused. Pair `91 92` is invalid
  and has no minute projection; neither does `0C 06`. Pair `06 90` is active
  through minute 1440, not unused. The offline payload
  `04 03 02 02 04 06 0C 12 18 90 90` is eleven bytes, with ADDRESS `02`
  before DAY `04`, retaining that exact baseline and identity. Baseline
  `A5 06 0C 12 18 90` is six bytes and must be rejected. Three pairs are
  not seven slots, and these bytes do not establish timer support.
- OP08 payload `01 02 03 04 05 06 07 08` has exactly eight raw fields;
  the final `07` and `08` stay raw temperatures without an explicit qualified
  codec. No enum meaning is inferred from the other six bytes.
- Paired Event identity `(family=VRC700 family, instance=02, system_type=03,
  address=01, raw_code=07)` retains OP09 baseline
  `A0 01 02 03 04 05 06 07` and OP0B baseline
  `B0 08 09 0A 0B 0C 0D 0E`, each eight bytes. Offline OP0A payload
  `0A 03 02 01 07 11 12 13 14 15 16 17` and OP0C payload
  `0C 03 02 01 07 21 22 23 24 25 26 27` each contain five prefix bytes
  and seven explicit raw values. Each retains both exact paired baselines.
  Changing any one of family, instance, system type, address or raw code
  breaks the pair; matching lengths do not repair it. Raw code `07` is not
  assigned a weekday. Both plans remain schema-unqualified and confer no
  execution permission.

## Automatic Event programs

Normal scans offer Event programs through selected planner configuration. After
scalar instance discovery, candidates come from
System, availability-confirmed native DHW, and concrete present zones. The
documented profile/address catalogs below supply the program selectors. OP00
capacity alone does not create zone instances, and a scalar anchor does not
prove that its instance byte supports Event.

Each program initially probes the raw selector window **`0x00..0x07`
inclusive**. This is a visible, editable candidate window, not a protocol
maximum or a qualified Monday-to-Sunday encoding. No weekday names are assigned.
Every selected code is attempted: an empty response at `0x00` does not suppress
later codes, addresses, instances, or profiles. A completed window with no value
means only **not observed in the candidate window**, never unsupported, absent,
or no events. Codes outside the selected window remain unscanned.

The visual planner groups all codes and their paired setpoint reads into one
program row. Tab and Shift+Tab cycle through nonempty Local, Remote, and Event
panes. Space toggles the complete program; Enter or `d` edits its raw-code set
within `0x00..0xFF`. The classic planner also groups programs and accepts
`codes N <raw range>` for an automatic program. Worst-case request counts include
both reads for every selected code; the planner records actual requests.

An automatic `GetEventSetPoint` runs only after a matching `GetEvent` produces
a structurally valid eight-byte, raw-correlated value for the exact same
`(profile, instance, address, weekday_code)`. Empty, negative, malformed, failed,
or unattempted Event reads retain their evidence, and the conditional setpoint
record remains unattempted with its precondition reason. No meaning is invented
for `PARAM_CONFIG`, all-zero replies, or all-`FF` replies. A structurally valid
reply remains schema-unqualified; it does not establish native support.

Automatic candidates require a known target EID and manufacturer from the
identity probe. Missing identity or missing scalar anchors leave automatic
Event work unscheduled, not unsupported. Existing interruption and recovery
boundaries preserve all unsent selected requests.

## Selected operation scope

The planner may retain an internal JSON operation-selection shape conforming to
[the version 1 schema](fixtures/b524-operation-read-plan-schema-v1.json) for
runtime compatibility and offline replay. It is not a public command-driven
plan or preview interface. Operation derives the wire opcode, so a selected item never
supplies a redundant opcode field. Scope, finite selection, and actual request
accounting are planner configuration. Historical plan artifacts remain readable
without reactivating their former public policy.

There is no implicit weekday meaning. A selected Event request carries an
explicit raw `weekday_code`. Explicit setpoint requests retain their independent
acquisition behavior; the automatic OP09 precondition applies only to
automatically constructed pairs.

| Operation | Required selector fields | Boundary |
| --- | --- | --- |
| `ReadTimer` | `channel`, `instance`, `weekday` | The seven channel names are `ventilation`, `noise-reduction`, `tariff`, `dhw`, `circulation`, `zone-cooling`, and `zone-heating`. Non-zone channels require `instance: 0`; zone instances remain explicit `u8` values. VRC700 profile handling applies. |
| `ReadVR91` | none | Opcode-only VRC700 operation. |
| `GetEvent` | `profile`, `instance`, `address`, `weekday_code` | `system` admits addresses `1..3`; `dhw` and `zone` admit `1..2`. The instance stays an explicit `u8`; Event support and weekday-code semantics remain experimental and unqualified. |
| `GetEventSetPoint` | `profile`, `instance`, `address`, `weekday_code` | `system` admits addresses `1..3`; `dhw` and `zone` admit `1..2`. The instance stays an explicit `u8`; Event support and weekday-code semantics remain experimental and unqualified. |

The planner retains every selected program's exact requests and their progress. Replay preserves
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
family-specific address catalogs as reads. UI exports use the same plan shape.

An internal operation-edit artifact can default to an offline preview and diff.
It derives the target from its required `destination_address`. Missing or invalid
targets fail closed rather than falling back to a target. A live Browser action
fails closed unless a matching
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
