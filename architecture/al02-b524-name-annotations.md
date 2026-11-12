# B524 name annotations and typed values

The public [native naming contract](../protocols/vaillant/ebus-vaillant-b524-register-map.md#register-name-correspondence-fixture),
[OP02 names](../protocols/vaillant/fixtures/b524-op02-register-names.csv) and
[correspondence annotations](../protocols/vaillant/fixtures/b524-register-name-correspondence.csv)
precede this application representation. They remain the source for labels;
this page does not establish a new native profile or a typed-value dictionary.
The catalog prerequisite must merge before this companion page. Its merge and
runtime results are not established by these documentation checks. This is a
partial child of issue #736, tracked by issue #1021.

**Proven — finite software contract:** retain exactly **368 OP02 name keys**,
**334 differing legacy aliases**, **2 OP06 annotation-only keys**, and thus
**370 correspondence identities**. Both canonical and previous names on one
row label one identity. Native-label columns are annotations, never additional
registers. Identical labels on different exact keys do not merge those keys.

**Hypothesis:** candidate native meaning remains a candidate even when a label
looks descriptive. **Unknown:** unresolved meaning, polarity, class or
writability remains open. The supplied OP02 `unresolved` Boolean records an
open question, without copying its descriptive prose. A false flag does not
qualify a codec or establish physical support. OP06 has no supplied canonical
or legacy name or unresolved Boolean; retain null rather than inventing them.

## Exact identity and annotation boundary

The logical lookup key has the following six axes. This table specifies the
representation boundary, without asserting an unprovided Go struct layout.

| Axis | Representation | Match rule |
| --- | --- | --- |
| opcode | integer, 0..255 | exact operation namespace; OP02 is 2, OP06 is 6 |
| group | integer, 0..255 | exact group, including zero |
| register | integer, 0..65535 | exact register, including zero |
| instance_scope | string `unqualified` | explicit lack of instance qualification |
| family | string `unqualified` | annotation scope only; no qualified-family fallback |
| variant | string `unqualified` | annotation scope only; no variant qualification |

There is no instance inventory. Missing, null, Boolean and numeric zero are
distinct; none is a wildcard. An unknown identity cannot authorize lookup into
a qualified family table. OP02 and OP06 stay distinct even with equal group
and register. Canonical names, legacy names and display aliases are outside
the key; neither a name nor the byte width of an unrelated value selects a
codec, instance, presence or writable state.

Representative controls, not a complete dictionary:

| OP | GG | RR | Canonical name | Legacy name / display alias | Unresolved |
| --- | --- | --- | --- | --- | --- |
| 02 | 00 | 0001 | dhw_outdoor_bivalence_temperature_limit | system_dhw_bivalence_point | false |
| 02 | 00 | 0007 | unknown_11 | system_off | true |
| 02 | 00 | 0009 | automatic_cooling_enabled | automatic_cooling_enabled | false |
| 02 | 00 | 0016 | ventilation_operating_mode | system_ventilation_operating_mode | false |
| 02 | 09 | 0002 | ventilation_operating_mode | ventilation_operating_mode | false |
| 02 | 03 | 0007 | heating_zone_room_comfort_temperature_setpoint | zone_comfort_room_temperature_setpoint_heating | true |
| 06 | 0A | 0007 | absent | RoomHumidity | absent |
| 06 | 0A | 000F | absent | RoomTemp | absent |

## Ab36Entries and Ab36Lookup

**Proven — declared API behavior:** `Ab36Entries` returns the complete JSON
array, with one row per correspondence identity. `Ab36Lookup` returns one whole
row, found true, and no error for an exact key. Absence returns no bytes, found
false, and no error. Invalid JSON, a non-array, malformed rows, missing axes,
duplicate keys or forbidden typed metadata return an error and no admitted
bytes; lookup also returns found false. Validate the entire array before a
matching early row can escape. Empty arrays cannot stand in for the complete
catalog. Malformed queries return an error; well-formed nonmatching queries
return ordinary absence. No wildcard, nearest-name or cross-namespace fallback
is permitted.

Every entries buffer and every row buffer is independently owned. Changing a
returned byte must affect neither outstanding results nor later calls through
either API. These are byte buffers holding JSON annotations, not measurements.
Do not silently rename raw method results or attach a codec from a name.
Consumers preserve raw evidence and independent useful fields and partial
last-known-good state on admission failure; failed annotations do not admit a
new typed value. This page adds no state updater.

The following executable reference makes these semantics reviewable. It takes
the stored JSON bytes explicitly, unlike the companion's storage-backed API;
it is not a cross-repository runtime import or evidence of Go implementation
parity. It validates either the small synthetic example array or a projected
full catalog; completeness and exact labels are checked separately by the
independent tuple oracle in the focused test. No Go signature is inferred.

```python
import json

AXES = ("opcode", "group", "register", "instance_scope", "family", "variant")
FIELDS = {"key", "canonical_name", "legacy_name", "display_alias", "unresolved"}


def checked_key(key, stored=False):
    if type(key) is not dict or set(key) != set(AXES):
        raise ValueError("incomplete identity")
    for axis, maximum in (("opcode", 255), ("group", 255), ("register", 65535)):
        if type(key[axis]) is not int or not 0 <= key[axis] <= maximum:
            raise ValueError("invalid numeric identity")
    for axis in ("instance_scope", "family", "variant"):
        if type(key[axis]) is not str or not key[axis]:
            raise ValueError("invalid annotation scope")
        if stored and key[axis] != "unqualified":
            raise ValueError("qualified identity not supplied")
    return tuple(key[axis] for axis in AXES)


def checked_rows(encoded):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = value
        return result

    if not isinstance(encoded, (bytes, bytearray)):
        raise ValueError("JSON byte buffer required")
    rows = json.loads(encoded, object_pairs_hook=unique_object)
    if type(rows) is not list or not rows:
        raise ValueError("nonempty annotation array required")
    seen = set()
    for row in rows:
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError("annotation fields only")
        identity = checked_key(row["key"], stored=True)
        if identity in seen:
            raise ValueError("duplicate correspondence identity")
        seen.add(identity)
        if row["key"]["opcode"] == 2:
            if any(type(row[name]) is not str or not row[name]
                   for name in ("canonical_name", "legacy_name")):
                raise ValueError("OP02 labels required")
            if type(row["unresolved"]) is not bool or row["display_alias"] is not None:
                raise ValueError("OP02 annotation shape")
        elif row["key"]["opcode"] == 6:
            if any(row[name] is not None
                   for name in ("canonical_name", "legacy_name", "unresolved")):
                raise ValueError("no supplied OP06 canonical semantics")
            if type(row["display_alias"]) is not str or not row["display_alias"]:
                raise ValueError("OP06 display alias required")
        else:
            raise ValueError("operation namespace not supplied")
    return rows


def encoded_copy(value):
    return bytearray(json.dumps(value, ensure_ascii=True, sort_keys=True).encode())


def Ab36Entries(encoded):
    try:
        rows = checked_rows(encoded)
    except (ValueError, TypeError, UnicodeError) as error:
        return None, str(error)
    return encoded_copy(rows), None


def Ab36Lookup(encoded, key):
    try:
        rows = checked_rows(encoded)
        identity = checked_key(key)
    except (ValueError, TypeError, UnicodeError) as error:
        return None, False, str(error)
    for row in rows:
        if checked_key(row["key"]) == identity:
            return encoded_copy(row), True, None
    return None, False, None
```

## Independent controls and limits

The [small synthetic JSON set](fixtures/al02_b524_name_annotations.json) contains
only the eight representative controls above. It is neither a second complete
dictionary nor a native profile. Its grades keep software behavior Proven,
candidate meaning Hypothesis and unresolved semantics Unknown, independently
of qualification, presence, freshness and execution (all Unknown).

The [standard-library test](../tests/test_al02_b524_name_annotations.py) checks
all 368 public OP02 tuples, independently counts 334 differing labels, and
checks both OP06 identities against frozen expectations. It executes only
synthetic JSON buffers, without importing another repository. Per-row controls
vary each axis independently with an otherwise valid key:

| Axis or scenario | Independent change | Production mutation detected by that control |
| --- | --- | --- |
| opcode | another operation, retaining GG/RR | ignore opcode or merge OP02/OP06 |
| group | neighboring group, retaining OP/RR | ignore group |
| register | neighboring register, retaining OP/GG | ignore register |
| instance_scope | `unqualified` to `00` | invent an instance or ignore scope |
| family | `unqualified` to `controller-family` | qualified-family fallback |
| variant | `unqualified` to `other-variant` | ignore variant |
| canonical_name | change one label, preserving key | rename or silently replace a raw result |
| legacy_name | change one label or promote it to a row | lose an alias or create a register |
| display_alias | change either OP06 label | invent a canonical OP06 name or conflate aliases |
| unresolved | flip or erase each supplied flag | discard an open question |
| row cardinality | omit or duplicate any row | lose keys or count labels as keys |
| typed metadata | add codec, value, presence or writable | infer semantics from labels |
| admission | malformed later row after valid first row | return before whole-array validation |
| returned memory | mutate entries and row buffers, then repeat both calls | share returned buffers |

These controls and executed page/fixture mutants establish the documentation
reference only. Native effects and full companion parity require their own
checks. Full Gate D and independent committed-change review remain merge
requirements. eBUS MCP compatibility and GraphQL parity are unchanged: this
page adds no endpoint, transmit route, polling default, write admission or
automatic native qualification. Nothing is stable before Helianthus 1.0; no
new major or experimental namespace is introduced.
