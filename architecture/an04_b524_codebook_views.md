# AN04: selected B524 codebook views

**Proven software contract; candidate meanings Hypothesis; native qualification
Unknown.** This architecture contract specifies the proposed ab03an03 pure helper.
It adds an explicit selected-codebook interpreter, not a metadata listing API.
It is independently authorable alongside AN03 and imports no pending API.
Nothing here is stable before Helianthus 1.0. This page adds no namespace,
route, displayed label change, numeric constraint, family detection, UI update,
or edit permission. Existing eBUS MCP compatibility and GraphQL parity are
preserved: neither surface gains a method or a new projection through this work.

The public [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
comes first for wire facts, especially register reply shapes in section 2.2
and opcode-scoped selectors in section 3.1. This page specifies the proposed
software API contract; native family documentation and qualification stay
separate. The finite candidate tables below are issue-supplied hypotheses,
not measured evidence.
The [synthetic examples](fixtures/an04_b524_codebook_views.json) retain inputs
and independent expected outputs; no live equipment or private data is used.

## Hypothetical API and ownership

Use these hypothetical signatures consistently; they do not assert an existing
implementation or a routed method:

```text
ab03an03.InterpretSelectedCodebook(input: CodebookInput) -> CodebookResult
CodebookInput = {
  family, software, hardware, api_version, api_revision,
  op, gg, ii, rr, alternative,
  requested_gg, requested_rr, returned_gg, returned_rr,
  response_state, raw_value, raw_status
}
CodebookResult = {
  context: owned copy of CodebookInput,
  raw_integer, candidate_label, state,
  numeric_grade, semantic_grade, native_qualification,
  support, edit_permission, presence, freshness, execution
}
```

`raw_value` is an owned byte array for the value tail, never the entire response
or a status byte. `raw_status` independently retains status-only 00/FF.
All results own a deep copy of every input field, including bytes; neither input
nor result may alias the other or another invocation. No I/O, transport, clock,
cache, discovery, UI, mutation or authorization belongs in this helper.
Callers retain native response bytes outside this normalized value-tail input.

Family is explicit `controller-700`, `controller-720`, missing, or unknown;
no inference or cross-family fallback is permitted. Software and hardware are
opaque caller context, independent of the API version and API revision. None
of those four fields is a qualified version allowlist here. Changing any one
preserves that exact context without asserting a new native qualification.
OP/GG/II/RR are integers; II must be explicitly supplied in the byte range.
The normalized interface requires byte-range GG and 16-bit RR values.
The finite fixtures cover normalized fields, not a general wire parser.

`alternative` is exactly `u8`, `u16le`, or `signed8`, or an absent/unmatched
selection. `u16le` means two bytes, little endian; `signed8` is one byte,
two's complement. The chosen alternative must be among the selector's declared
alternatives for candidate interpretation. Never choose a union alternative
solely from length. GG03/RR001B has two independently selected forms, not an
automatic union decoder. GG03/RR001C FF is -1, never unsigned 255 under signed8.

## Deterministic result states

First decode only the explicitly chosen numeric alternative, independently of
semantic admission. An exact-width value yields `raw_integer` and numeric grade
`Proven` (software arithmetic only). Unknown selection yields null integer and
numeric `Unknown`. Any nonempty wrong width, or an empty value in an
`echo-payload`, yields `malformed-width`; do not trim extra bytes, pad truncated
bytes, or retry another alternative. Empty value in another response state is
`partial`. An unavailable alternative on a selector can still decode numerically
when it names a known numeric codec; it cannot receive a candidate label.

Then admit a candidate interpretation only when all of these hold:

- Explicit family matches a table below, OP is exactly 02, GG/RR match a row,
  II is explicit, and GG01/RR0003 has II00.
- Requested GG/RR equal selector GG/RR; response state is `echo-payload`;
  returned GG/RR exactly equal requested GG/RR. II is request context, not an
  echoed field or a discovered slot. Other rows accept any explicit byte II
  as caller context, never as evidence of presence or slot allocation.
- The selected alternative is declared by that row and its width is exact.

Applicable candidate interpretation has semantic grade `Hypothesis`, including
valid codes without labels. Named codes yield `interpreted` plus the exact
candidate label; other integers yield `unlabelled` with null label. Unknown codes
are not unsupported and are not writable. Missing family, unmatched selector,
missing alternative, wrong echo, status-only, or transport failure has no label
and semantic `Unknown`. Complete independently owned numeric bytes can still
survive these failures as `raw` with numeric `Proven`; empty incomplete replies
remain `partial` with null integer. Width errors take precedence over admission.
The fixture uses `empty`, `short`, `header-only`, `status-only`, and
`transport-failure` as distinct non-admissible response states. No status value
is converted to a register integer.

`native_qualification`, `support`, `edit_permission`, `presence`, `freshness`,
and `execution` are always `Unknown`. Qualification is independent of numeric
and semantic grades. A valid candidate label proves none of those properties.
These views never overwrite caller last-known-good state: a partial failure
retains its own context and bytes and fails closed for candidate admission.
Last-known-good storage and reconciliation remain outside this pure helper.

## Seven candidate selector codebooks per family

All rows use OP02. Dynamic II below means an explicit caller-supplied II,
not discovery. These are **Hypothesis** tables for both families; software,
hardware and independent API version/revision applicability remain **Unknown**.

| GG/RR | II | Alternative | controller-700 labels | controller-720 labels |
| --- | --- | --- | --- | --- |
| 01/0003 | 00 | u16le | 0 off; 1 automatic; 2 day | 0 off; 1 time-controlled; 2 manual |
| 03/0001 | explicit | u16le | 0 off; 1 automatic; 2 day | 0 off; 1 time-controlled; 2 manual |
| 03/0006 | explicit | u16le | 0 off; 1 automatic; 2 day; 3 setback | 0 off; 1 time-controlled; 2 manual |
| 02/0002 | explicit | u16le | 0 deactivated; 1 heating; 2 fixed-flow; 3 DHW; 4 return-flow; 5 pool | 0 deactivated; 1 heating; 2 fixed-flow; 3 DHW; 4 return-flow |
| 03/0013 | explicit | u16le | 0 none; 1 central; 2 remote-circuit-one; 3 remote-circuit-two; 4 remote-circuit-three; 5 remote-circuit-four; 6 remote-circuit-five; 7 remote-circuit-six; 8 remote-circuit-seven; 9 remote-circuit-eight | 0 none; 1 central; 2 remote-circuit-one; 3 remote-circuit-two; 4 remote-circuit-three; 5 remote-circuit-four |
| 03/001B | explicit | u8 or u16le, explicitly selected | 0 no-quick-mode; 1 ventilation-boost; 3 party; 4 quick-veto; 5 one-day-holiday; 6 one-day-bank-holiday; 7 holiday; 8 bank-holiday; 10 system-off | 0 no-special-function; 1 ventilation-boost; 4 quick-veto; 7 holiday; 10 system-off |
| 03/001C | explicit | signed8 | -1 unbound; 0 control-circuit-one; 1 control-circuit-two; 2 control-circuit-three | -1 unbound; 0 control-circuit-one; 1 control-circuit-two; 2 control-circuit-three; 3 control-circuit-four; 4 control-circuit-five; 5 control-circuit-six; 6 control-circuit-seven; 7 control-circuit-eight; 8 control-circuit-nine |

Family700 02/0002 `05 00` is candidate pool; family720 and unknown family
retain raw 5 without that label. Family700 03/0013 `09 00` is candidate
remote-circuit-eight; family720 retains an unlabelled 9. Raw 3 at 03/001B is
party only for family700. Selecting u16le with `03` is malformed even when
that row also declares u8. Under signed8, `FF` yields -1/unbound; selecting u8
there gives raw 255 with no candidate interpretation.

## Machine-checkable prohibitions

This normative policy block encodes the prohibited behaviors independently of
the example tables. `false` forbids the named behavior; it is not a feature flag.
Tests also parse the human selector table and validate every named value and
state against literal independent expectations, rather than comparing files.

```json
{
  "cross_family_fallback": false,
  "automatic_width_selection": false,
  "signed8_unsigned_reinterpretation": false,
  "controller_720_pool5": false,
  "merge_op02_op06": false,
  "unlabelled_is_unsupported": false,
  "unlabelled_is_writable": false,
  "native_qualification": "Unknown",
  "candidate_grade": "Hypothesis"
}
```

## Unknowns and companion boundary

No physical qualification, presence, freshness, execution, edit safety, discovery
range, software/hardware applicability, or independent API version/revision
qualification follows from these examples. Conflicting evidence would require a
separate native evidence change, not relabelling this API contract as Proven
native behavior. All raw codes outside the finite tables remain unlabelled.

Companion AN03 may implement `ab03an03.InterpretSelectedCodebook` against this
contract; this ordinary companion does not depend on its code and does not
import its tests or another pending API. Refs #865 and partial parent #736;
broader native/runtime work stays open. This documentation-only slice adds no
transport behavior or smoke-test claim.
