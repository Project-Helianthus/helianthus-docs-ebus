# Explicit B524 system scalar bindings

## Authority and scope

Start with the public [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
and [register catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md).
They own framing, operation-scoped selectors, response shapes and the warning
that a family label cannot qualify a codec. This page owns only an application
API proposal and a synthetic example package. It supplies no new native evidence.
The finite candidate types and units below are **Hypothesis**. The explicitly
selected pure interpreter contract is **Proven** software behavior in this
executable example, independently of physical qualification. Physical support,
presence, freshness, effects, persistence, delivery and execution are **Unknown**.
A successful synthetic decode does not establish any of them.

## Finite candidates

All opcode, group, instance and register notation in this table is hexadecimal.
Every register expands to a distinct tuple; no other binding is implied.
All rows have opcode `02`, group `00`, little-endian encoding and grade Hypothesis.
`Unknown` is a declared unit with no semantic unit supplied.

| Family | II rule | Codec | Declared unit | Registers |
| --- | --- | --- | --- | --- |
| controller-720 | 00 | float32 | °C | 0002 0022 0023 0026 0038 0046 004B 0067 0068 0073 0095 009D 009E 009F 00A0 00EF |
| controller-720 | 00 | uint16 | min | 0004 0017 0018 |
| controller-720 | 00 | float32 | K | 0029 |
| controller-720 | 00 | uint16 | Unknown | 002F 0036 |
| controller-720 | 00 | float32 | bar | 0039 |
| controller-700 | 00 | float32 | °C | 0002 0022 0023 0026 0038 0046 004B 0067 0068 0073 0095 009D 009E 009F 00A0 |
| controller-700 | 00 | uint16 | Unknown | 0006 002F 0036 |
| controller-700 | 00 | uint16 | min | 0017 |
| controller-700 | 00 | float32 | K | 0029 |
| controller-700 | 00 | float32 | bar | 0039 |
| controller-700 | dynamic | uint16 | Unknown | 0042 0043 |

II rule `00` accepts only the concrete byte zero. `dynamic` requires a concrete
caller-supplied byte, including zero; it neither enumerates installed instances
nor asserts that any instance is supported. OP06 is a distinct namespace and
has no binding here. Do not choose by width, name, another family or a fallback.

## Input and output contract

Call `interpret(context, reply, codec_grade, bindings)` explicitly. `bindings`
is the immutable finite declaration set in the [synthetic package](fixtures/am02_b524_system_scalars.json).
It is not a caller extension point. Context has exactly nine keys: `family`,
`software`, `hardware`, `api_version`, `api_revision`, `opcode`, `group`,
`instance`, `register`. Family is an explicit candidate selection, never
qualified device identity. Software, hardware, API version and API revision
are independent opaque caller context: a nonempty string or nonnegative integer
is accepted, including explicit zero; missing, null, booleans and empty strings
are incomplete. They do not select a binding and are never inferred.
Opcode, group and instance are integers in 0..255; register is in 0..65535.
Booleans are not integers for this API. Missing differs from explicit zero.

Reply has exactly `kind`, `group`, `register`, `value`. Kind is a normalized
reply classification supplied by the caller, not inferred from byte length.
Returned group/register are echoed identity, independently retained, with the
same byte/word domains as request group/register. II is request context, never
an echoed value. `value` is the caller-owned bytes or bytearray supplied to the
normalizer's result: for echo_payload it is only the value tail; for other
kinds it preserves whatever partial/status bytes are available. This API does
not parse a telegram or reconstruct missing framing, FLAGS or value bytes.
Non-buffer values are retained as malformed input but cannot be interpreted.
Missing/extra keys or malformed fields return raw-only; even an extra echoed
instance is rejected rather than used as request context.

Only `echo_payload`, matching returned GG/RR, a listed selector, complete context,
exact codec width and known codec grade can yield a candidate. `Hypothesis` and
`Proven` codec grades are eligible requests; output is always capped at
Hypothesis. Unknown, missing or unrecognized codec grade is raw-only. Omission uses null.
The declared unit is kept separately whenever the selector resolves, even if
reply validation or arithmetic fails. An unresolved selector has unit Unknown.

Every result has independently owned `context`, `reply`, `raw`, `codec_grade`,
`value`, `grade`, `unit` and `outcome`. Context and reply retain all supplied
fields, including unknown keys, nulls and independent returned identity.
`raw` copies reply value; both it and reply value own separate memory. Neither
caller mutation nor returned-result mutation may alter the other, or a later
result. Raw-only has value null, grade Unknown and outcome raw-only; successful
output has outcome candidate and grade Hypothesis. Failure does not erase raw
bytes or independently useful context, and does not replace a prior good value.

Uint16 uses exactly two little-endian unsigned bytes. Float32 uses exactly four
little-endian IEEE binary32 bytes and only finite results. No clipping, Celsius
offset, added 273.15, sentinel invention or bounds import is allowed. Declared
K is retained as K; Unknown stays Unknown. The example's integer 65535 is a
number, with no inferred sentinel meaning.

## Executable software example

This standard-library reference example defines the proposed pure behavior;
it is not a production implementation or automatic admission path. The focused
tests execute this block and check the page table and package independently.

```python
import copy
import math
import struct

CONTEXT_KEYS = {"family", "software", "hardware", "api_version", "api_revision",
                "opcode", "group", "instance", "register"}
REPLY_KEYS = {"kind", "group", "register", "value"}


def unsigned(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def interpret(context, reply, codec_grade=None, bindings=()):
    result = dict(context=copy.deepcopy(context), reply=copy.deepcopy(reply),
                  raw=copy.deepcopy(reply.get("value")),
                  codec_grade=copy.deepcopy(codec_grade), value=None,
                  grade="Unknown", unit="Unknown", outcome="raw-only")
    complete = set(context) == CONTEXT_KEYS
    for key in ("software", "hardware", "api_version", "api_revision"):
        value = context.get(key)
        complete = complete and ((type(value) is str and bool(value)) or
                                 (type(value) is int and value >= 0))
    for key, maximum in (("opcode", 255), ("group", 255),
                         ("instance", 255), ("register", 65535)):
        complete = complete and unsigned(context.get(key), maximum)
    if not complete:
        return result
    binding = next((b for b in bindings
                    if b["family"] == context["family"]
                    and b["opcode"] == context["opcode"]
                    and b["group"] == context["group"]
                    and b["register"] == context["register"]
                    and (b["instance_rule"] == "dynamic" or
                         context["instance"] == 0)), None)
    if binding is None:
        return result
    result["unit"] = binding["unit"]
    if (set(reply) != REPLY_KEYS or reply.get("kind") != "echo_payload"
            or not unsigned(reply.get("group"), 255)
            or not unsigned(reply.get("register"), 65535)
            or reply["group"] != context["group"]
            or reply["register"] != context["register"]
            or codec_grade not in ("Hypothesis", "Proven")):
        return result
    raw = result["raw"]
    width = {"uint16": 2, "float32": 4}.get(binding["codec"])
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != width:
        return result
    if binding["codec"] == "uint16":
        value = int.from_bytes(raw, "little", signed=False)
    elif binding["codec"] == "float32":
        value = struct.unpack("<f", raw)[0]
        if not math.isfinite(value):
            return result
    else:
        return result
    result.update(value=value, grade="Hypothesis", outcome="candidate")
    return result
```

## Synthetic controls and limits

For every listed tuple the package has a complete valid example. Its `controls`
section also declares the shared numeric vectors and control categories below. The tests also
exercise each tuple with the following independent controls; raw-only always
retains the supplied bytes and context.

| Case | Input | Expected |
| --- | --- | --- |
| float positive | 00 00 C0 3F | 1.5; Hypothesis; declared unit |
| float negative | 00 00 80 BF | -1; Hypothesis; declared unit |
| float nonfinite | 00 00 80 7F (bits 7F800000 LE) | raw-only |
| uint16 positive | 34 12 | 4660; Hypothesis; declared unit |
| uint16 maximum | FF FF | 65535; Hypothesis; no sentinel inference |
| width minus/plus one | truncated or extra byte | raw-only |
| unlisted neighbor | nearest unlisted RR | raw-only |
| different operation | OP06, other inputs valid | raw-only |
| unknown family | otherwise valid selector | raw-only |
| fixed instance | II00 versus II01 | candidate versus raw-only |
| dynamic instance | concrete II00 versus II01 | both candidate; II retained |
| changed echo | different returned GG or RR | raw-only |
| non-echo kind | empty, status_only, short, header_only, nack_or_crc, timeout, transport_error, failed, unknown | raw-only, even at valid width |
| grade | Hypothesis or Proven request | Hypothesis output |
| unknown grade | Unknown, null, absent request or other label | raw-only |
| memory | mutate input or returned storage | independent snapshots |
| context-only change | software, hardware, API version or API revision | unchanged arithmetic; changed context retained |
| partial/malformed/extra | absent or null context, invalid domains or extra key | raw-only; supplied fields retained |

B524 is the fixed variant and normalized reply the sole direction of this API;
there is no variant or direction inference or transmit input. Unexpected such
fields fail the exact-key contract. A family change may select another listed
candidate only when that exact tuple exists there. It never falls back to the
original family, even for same-width bytes.

No route, poll, writer, profile change, cached-value replacement, bounds import
or presence assertion is added. Preserve partial last-known-good state and
fail-closed admission in consumers. Existing explicit codec helpers, name
annotations, codebooks, calendar groups, special scalar alternatives, command
roles and numeric edit candidates keep their responsibilities. Existing eBUS
MCP compatibility and GraphQL parity remain required; this pure example adds
no endpoint, transport or schema change. No new major or experimental namespace
is created; nothing is stable before Helianthus 1.0.

Companion AM01 in ebusreg implements the corresponding software behavior and
holds its merge for this page; this page has no code dependency. Refs #857 and
#736; this is a partial child and does not close the umbrella.
