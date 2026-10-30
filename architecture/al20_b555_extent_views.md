# B555 bounded extent views

This finite library contract concerns VRC720-family B555 normalized reply
representations. The public native contract comes first:
[A4 requester policy](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#521-a4-reply-acceptance-by-a-requester-candidate),
[A5 requester policy](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#531-a5-reply-acceptance-by-a-requester-candidate),
and the [native field table](../protocols/vaillant/fixtures/b555-a4a5-fields.csv).
These references supply candidate interpretations; this page adds storage bounds,
not new native evidence or a second native profile. Nothing here is stable before
Helianthus 1.0.

## Pure API and grades

**Proven (declared pure API contract):**
`Ab52DecodeA4(declaredCount, availableRaw)` and
`Ab52DecodeA5(declaredCount, availableRaw)` return owned raw bytes, explicit
incomplete/error state, and independently valid bounded fields. Neither routine
invokes or replaces existing timer methods. Inputs are a nonnegative byte count
and a byte sequence; offsets below are normalized storage indices, not physical
offset assertions. The supplied bytes are copied, including any surplus bytes;
a field is exposed only when its entire width fits both extents.

**Hypothesis:** all candidate status meanings, day/count interpretations, time
interpretations, and the numeric /10 interpretation below. **Proven:** synthetic
byte arithmetic and the bounded representation shape only. **Unknown:** physical
qualification, presence, freshness, native execution, readback, persistence, and
unit/sentinel qualification for an unspecified program context. These grades are
independent of each other and of field availability. A decoded status is not
acceptance. A bounded view is not a full weekly refresh.

## Normative ab52 policy

The following small policy is machine checked with the examples. All new result
and fixture keys use `ab52`; the two API names and their input parameter names
above are the prescribed exceptions.

```json
{
  "ab52_extent_rule": "both",
  "ab52_a4_week_extent": 8,
  "ab52_a4_eighth_extent": 9,
  "ab52_weekday_count": 7,
  "ab52_a4_day_limit": 12,
  "ab52_a4_accepted_status": 0,
  "ab52_a4_unavailable_status": 3,
  "ab52_eighth_role": "24-hour-count",
  "ab52_a5_word_extent": 7,
  "ab52_a5_status_gate": false,
  "ab52_a5_time_range_gate": false,
  "ab52_ffff_universally_unavailable": false
}
```

For each field ending at exclusive index `ab52_end`, access requires
`declaredCount >= ab52_end AND len(availableRaw) >= ab52_end`.
Extent contradictions are incomplete, never permission to read past storage.
An announced extent larger than storage sets `ab52_incomplete`, even if some
useful fields fit. A short required view also sets it. Surplus storage is retained
in `ab52_raw` but cannot enlarge the declared extent. `ab52_errors` contains
`ab52_extent_incomplete` for such incompleteness; candidate rejection can
add `ab52_week_rejected` independently. Missing fields are null, never zero-filled.

### A4

| Result | Candidate normalized view and independent validity |
| --- | --- |
| `ab52_status` | Byte 0 if both extents reach 1; 0 accepted, 3 unavailable. Other values do not admit a complete week. |
| `ab52_day_counts` | Available bounded prefix of bytes 1 through 7, in Monday through Sunday order; retain unaffected counts even when another exceeds 12. |
| `ab52_complete_week` | Both extents reach 8, status is 0, and every one of seven day counts is at most 12. |
| `ab52_eighth_count` | Byte 8 only when both extents reach 9; a distinct 24-hour count, never an eighth weekday. |

The seven-day view needs both extents at least 8. Count 12 is admissible;
count 13 invalidates the complete-week view without erasing raw counts.
Status 3 rejects that view without erasing bounded counts. The optional eighth
count does not affect weekday cardinality or the weekday limit. Declared 8 with
available 9 does not expose byte 8; declared 9 with available 8 is incomplete for
the eighth count but can retain an independently valid seven-day view.

### A5

| Result | Candidate normalized view and independent validity |
| --- | --- |
| `ab52_status` | Byte 0 when bounded; preserved without an acceptance decision. |
| `ab52_start_hour`, `ab52_start_minute` | Bytes 1 and 2 independently, when bounded. |
| `ab52_end_hour`, `ab52_end_minute` | Bytes 3 and 4 independently, when bounded. |
| `ab52_setpoint_raw` | Bytes 5 and 6 as LEu16, only with both extents at least 7. |
| `ab52_setpoint_candidate_numeric` | Raw numeric /10, separately from unit and sentinel qualification. |

A5 decoding does not evaluate status or range-check time bytes. The synthetic
bytes `03 17 3B 18 3C FF FF` retain status 3 and time bytes 23, 59, 24, 60.
They yield raw 65535 and candidate numeric 6553.5. Unit and sentinel meaning
remain context dependent; FFFF is not universally unavailable. The low byte
alone never yields a word. Incomplete words do not erase bounded time fields.

## Controls and integration boundary

The [small synthetic example set](fixtures/al20_b555_extent_views.json) covers
8/8, 8/9 and 9/8 A4 extents, the 12/13 boundary, unavailable A4 status, the
literal A5 example, and a partial word. It is not a full dictionary.
The [scoped test](../tests/test_al20_b555_extent_views.py) checks the declared
page policy and examples using a local reference projection, including declared
6/7/8 crossed with available lengths 0 through 8 for both routines. It varies
every day position, the optional count, status, every time byte and each word
byte independently. Its checks establish documentation consistency, not a
companion implementation result or full parity.

The companion can be built now and merges after or with this page. Runtime
integration must retain eBUS MCP compatibility and GraphQL parity; neither is
claimed before its own checks. This page introduces no transmit route, polling
default, automatic native qualification or write admission. Navigation and
runtime integration are carried separately. Refs #872 and #736; this is a
partial child and does not close the parent.
