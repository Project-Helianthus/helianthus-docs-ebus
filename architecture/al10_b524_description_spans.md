# Exact B524 description spans and context

This finite architecture contract is a partial slice of #866; Refs #736.
The public [native description contract](../protocols/vaillant/ebus-vaillant-B524.md#42-0x01-describeparameter-and-0x07-describedeviceparameter)
comes first. This page defines a pure library representation, not a new native
profile. Nothing is stable before Helianthus 1.0.

## Pure helper contract

**Proven — representation shape:** `Ab44BuildDescription(context)` produces
`[OP,GG,II,RRlo,RRhi]` only for OP01/07. Other operations or incomplete contexts
produce no request and an explicit reason. Legacy `01 GG RR` is incomplete.
`Ab44DecodeDescription(context, explicitCodec, explicitWidth, grade, raw)`
retains the complete request identity and original raw bytes on every outcome.
The JSON spelling of each context field has an `ab44_` prefix: family,
software, hardware, API version, API revision, OP, GG, II and full 16-bit RR.
No identity field is inferred. Each field independently distinguishes contexts;
identical replies from different contexts must remain separate results.

The normalized reply is `[GG,RRlo,RRhi,MIN,MAX,STEP]`: exactly three equal
spans of the explicitly selected width `w`, exactly `3+3w` bytes overall.
GG and both RR bytes must match. II remains request context and is never an
echo. OP01 corresponds only to OP02 local metadata; OP07 only to OP06 remote
metadata. Reply similarity cannot merge these namespaces or instances.

**Hypothesis — typed interpretations:** UCH is unsigned width1; UIN is
little-endian unsigned width2; EXP is little-endian binary32 width4. An
explicit Hypothesis or Proven codec grade is necessary for typed interpretation;
length never selects a codec. These candidate mappings remain Hypothesis even
when synthetic arithmetic and implementation shape are Proven. An explicit
Proven grade is an input backed elsewhere, not a promotion performed here.

Unknown/unsupported codecs, wrong codec/width pairs, invalid width, bad echo,
absent or Unknown grade and malformed bytes remain unqualified/raw with an
explicit reason. Preserve any independently available header and exact spans
alongside the original raw bytes; malformed input must not fabricate spans.
Nonfinite limits (including step), min > max or negative step invalidate
interpreted limits while preserving raw spans. Step zero means literal zero,
never an invented no-limit sentinel. Date/time width3 retains three raw spans;
its step meaning is Unknown and supplies no numeric edit validation.

Grade and implementation-valid state are independent. A Hypothesis numeric
interpretation can be structurally valid while physically unqualified. Even a
matching numeric description grants no presence or write authority. Physical
qualification, freshness and execution remain independent and Unknown here.
Failure cannot erase useful prior qualified fields or last-known-good state;
this pure result describes failure without replacing that state. Admission
remains fail-closed.

## Machine-readable representation assertions

These finite assertions constrain this page and its examples, not a dictionary
or runtime implementation. All new fixture and test identifiers use `ab44`.

```json
{
  "ab44_request_ops": [
    1,
    7
  ],
  "ab44_metadata_ops": {
    "1": 2,
    "7": 6
  },
  "ab44_context_fields": [
    "ab44_family",
    "ab44_software",
    "ab44_hardware",
    "ab44_api_version",
    "ab44_api_revision",
    "ab44_op",
    "ab44_gg",
    "ab44_ii",
    "ab44_rr"
  ],
  "ab44_reply_header": [
    "GG",
    "RRlo",
    "RRhi"
  ],
  "ab44_span_count": 3,
  "ab44_length": "3+3w",
  "ab44_infer_codec": false,
  "ab44_echo": [
    "GG",
    "RRlo",
    "RRhi"
  ],
  "ab44_ii_echo": false,
  "ab44_typed_grades": [
    "Hypothesis",
    "Proven"
  ],
  "ab44_codecs": {
    "UCH": 1,
    "UIN": 2,
    "EXP": 4,
    "date/time": 3
  },
  "ab44_nonfinite_valid": false,
  "ab44_reversed_valid": false,
  "ab44_negative_step_valid": false,
  "ab44_zero_step": "literal zero",
  "ab44_date_numeric_permission": false,
  "ab44_presence_authority": false,
  "ab44_write_authority": false
}
```

## Synthetic controls and boundary

The [small fixture](fixtures/al10_b524_description_spans.json) contains only
synthetic contexts and bytes. OP01/GG02/II01/RR0002 builds `01 02 01 02 00`;
`02 02 00 00 00 04 00 01 00` under explicit UIN/2 yields 0, 4, 1.
The same reply with EXP/4 is raw-only. An EXP/4 example encodes -20, 20, 1
in 15 bytes. Date/time preserves raw step bytes without numeric permission.

The scoped standard-library tests use independently specified expected bytes
and values, varying every context field (including both register bytes), each
echo byte, each span, opcode, width, codec and grade separately. They cover
negative and zero step, nonfinite values, reversed bounds and malformed spans.
These are representation controls; no companion code result, native effect or
full parity is established before its own checks.

No shared codec replacement, routed method, admission integration, transmit
route, polling default, automatic native qualification or write admission is
added. Existing eBUS MCP compatibility and GraphQL parity are unchanged by this
page; runtime integration and navigation are carried elsewhere. The companion
may be built now and merges after or with this page. Full CI and independent
committed-change review remain later merge requirements.
