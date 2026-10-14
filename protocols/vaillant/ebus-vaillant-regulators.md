# Vaillant Regulators

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This is the entry point for Vaillant regulator identities and related protocol
families. Its bounded crosswalk identifies a catalog row only when the **EID
and decoded SPN value match as a pair**. An EID by itself does not classify
a regulator, prove model identity, or prove that a protocol is supported by the
connected device.

The discovery flow that supplies the identity fields is described in
[eBUS discovery](../ebus-services/ebus-overview.md#identification-scan-0x07-0x04)
and [Vaillant discovery](ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27).
Use this crosswalk after preserving the raw identity values in the discovery
record.

## Scope and Related Protocols

The crosswalk distinguishes model rows from protocol-family labels:

- `VRC720` is a protocol-family label for the VRC720, VRT380 and VRC710 model
  rows below and for the `CTLX0` / `0194` row, whose model-row cell `VR940` is
  a label that the Vaillant internet gateway emits for the pair (see
  [the `CTLX0` / `0194` row](#the-ctlx0--0194-row)). B524 scalar/discovery
  operations and B555 schedules remain candidate capabilities subject to their
  own qualification. A matching pair does not establish support for either one.
- `VRC700` is a separate family. A matching VRC700 row selects a candidate
  family description; B524 `ReadTimer`, `WriteTimer`, and `ReadVR91` remain
  subject to an operation's existing identity and response checks.

Protocol details remain in their owning documents:

- [B524 operation specification](ebus-vaillant-B524.md)
- [B524 register map](ebus-vaillant-B524-register-map.md)
- [B524 profile discovery and descriptions](ebus-vaillant-b524-profile-discovery-and-descriptions.md)
- [B524 bounded survey methodology](ebus-vaillant-b524-survey-methodology.md)
- [B555 timer/schedule protocol](ebus-vaillant-b555-timer-protocol.md)

## SPN Field (`07 04` bytes 8-9) Representation

The `07 04` identification reply carries two distinct two-byte BCD fields:
the software-version field (bytes 6-7) and the SPN field (bytes 8-9). The
eBUS standard calls the second field the hardware version, but Vaillant
regulators use it to carry the software product number. The `SPN` column
preserves that field's decoded value as a four-digit hexadecimal `u16`; it
is not derived from the software-version field, a product code, serial
number, or any other identity field.

The eBUS `PIN` codec is BCD: the wire order within this field is
least-significant BCD byte first. Therefore the wire bytes `17 04` decode as
decimal `417` (digits `04`+`17` with the second-transmitted byte holding the
more significant digits), represented here as `0x01A1`; `63 04` decodes as
decimal `463`, represented as `0x01CF`. Raw software version and the raw
SPN field (bytes 8-9) must both be retained; do not interpret either field's raw bytes
as a literal hex `u16`, and do not invent a catalog row for an invalid BCD
value or an unlisted decoded value.

A controller reporting software version `05 07` and SPN field `17 04`
therefore has the decoded SPN `01A1`. The crosswalk lists that value under two
identity strings, so the pair, not the number alone, selects a row. A reader
can reproduce this decoding from a read-only identification query against a
regulator reporting those fields. The software-version field (`0507` here) is
retained alongside the identity but does not itself decode to a catalog `SPN`.

Candidate, unconfirmed on the wire: a VRC720-family controller reports software
`0507` and product-number field `1704`.

The codec behavior is specified by the public
[archived `broadcast.csv` software field](https://github.com/john30/ebusd-configuration/blob/9c3ed3a0d487dc5898c611ab18f8313792659020/archived/en/broadcast.csv)
and [ebusd `PIN` datatype implementation](https://github.com/john30/ebusd/blob/38db2d28bd5622cadb6078c1662c6f7da5cef891/src/lib/ebus/datatype.cpp)
for how the standard names and encodes these two fields; the field selection
and little-endian byte order above are specific to Vaillant regulators as
observed, not restatements of the ebusd/eBUS citations.

## Exact EID and SPN Crosswalk

**Hypothesis as native-model evidence pending observations.** These 38 exact
pairs are a bounded naming and family catalog. They do not independently establish a device model, native
protocol support, or the availability of any operation on a connected target.
Treat an unlisted or malformed pair as unknown rather than extending this table
by inference.

| EID | SPN (hex `u16`) | Model row | Protocol family |
| --- | --- | --- | --- |
| `70000` | `0141` | VRC700 R1 | VRC700 |
| `70000` | `0155` | VRC700 R2 | VRC700 |
| `70000` | `015A` | VRC700 R4 | VRC700 |
| `70000` | `016C` | VRC700 R5 | VRC700 |
| `70000` | `0171` | VRC700 R6 | VRC700 |
| `70000` | `01D8` | VRC700 R6 | VRC700 |
| `72000` | `0179` | VRC720 | VRC720 |
| `B7V00` | `0163` | VRC700 R4 | VRC700 |
| `BASS0` | `0184` | VRC720 | VRC720 |
| `BASS0` | `0193` | VRT380 | VRC720 |
| `BASS2` | `01A1` | VRC720 | VRC720 |
| `BASS2` | `01CF` | VRC720 | VRC720 |
| `BASS3` | `01B0` | VRT380 | VRC720 |
| `BASS3` | `01BB` | VRC720 | VRC720 |
| `BASS3` | `01D0` | VRT380 | VRC720 |
| `BASS3` | `01D9` | VRC720 | VRC720 |
| `BASV0` | `0184` | VRC720 | VRC720 |
| `BASV0` | `0193` | VRT380 | VRC720 |
| `BASV2` | `01A1` | VRC720 | VRC720 |
| `BASV2` | `01CF` | VRC720 | VRC720 |
| `BASV3` | `01B0` | VRT380 | VRC720 |
| `BASV3` | `01BB` | VRC720 | VRC720 |
| `BASV3` | `01D0` | VRT380 | VRC720 |
| `BASV3` | `01D9` | VRC720 | VRC720 |
| `CTLS0` | `0188` | VRT380 | VRC720 |
| `CTLS0` | `0189` | VRC720 | VRC720 |
| `CTLS2` | `019D` | VRC720 | VRC720 |
| `CTLS3` | `01AF` | VRT380 | VRC720 |
| `CTLS3` | `01B6` | VRC720 | VRC720 |
| `CTLS3` | `01E1` | VRC720 | VRC720 |
| `CTLV0` | `0187` | VRT380 | VRC720 |
| `CTLV2` | `019B` | VRC720 | VRC720 |
| `CTLV3` | `01AE` | VRT380 | VRC720 |
| `CTLV3` | `01B5` | VRC720 | VRC720 |
| `CTLV3` | `01DC` | VRC720 | VRC720 |
| `CTLV3` | `01E0` | VRC720 | VRC720 |
| `CTLX0` | `0194` | VR940 | VRC720 |
| `EMM00` | `0181` | VRC710 | VRC720 |

The reported native identity `Vaillant;CTLX0;0127;0404` resolves to the
`CTLX0` / `0194` row: the SPN field is `04 04`, which decodes as decimal `404`
(`0x0194`), the catalog `SPN` in the table above. Raw software version `01 27` is
retained separately and does not itself decode to a catalog `SPN`. In
particular, there is no `CTLX0` row for SPN `007F` (decimal 127): that value
appears only if the software-version field is misread as the SPN field. This is
a reported naming association, not evidence of protocol support or
compatibility with another controller's parameter limits.

### The `CTLX0` / `0194` row

The pair (`CTLX0`, SPN 404 = `0x0194`) is bound as a VRC720-family controller
(candidate): its protocol-family cell is `VRC720`. Its model-row cell `VR940` is a
label that the Vaillant internet gateway emits for the pair. The physical
product behind that label is **Unknown**, and the association of the string
`VR940` with any product is not established. No row gives `VRC720` as the model
for SPN 404; the family cell of this row reflects the VRC720-family binding only
(candidate), not a model statement.

The pair (`CTLX0`, SPN 196 = `0x00C4`) has no row in the crosswalk, and the
product behind it is **Unknown**; the same holds for the pair that combines SPN
196 with a second `CTL`-series identity string (candidate). SPN 196 also occurs
under the identity strings `05000` and `_E100` (candidate); a lookup is keyed by
the pair and never by the SPN alone.

## VRC700 Operation Profile

The crosswalk includes the supplied `B7V00` / `0163` VRC700 R4 row. A matching
VRC700 row selects a candidate family description; it does not qualify a
request, a response, or the availability of a channel on a connected regulator.
It does not replace existing command identity guards. Follow the
operation-specific evidence requirements in
[B524 sections 4.4 and 4.6](ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules).

## Discovery Record

Retain at least:

- target address;
- EID as received;
- raw bytes 6-7 (software version) and raw bytes 8-9 (the product-number
  field), separately;
- decoded SPN value and decoding state; and
- crosswalk result (`matched`, `unlisted`, or `invalid`).

For a matched row, retain the native `0x07/0x04` EID, raw software version,
and decoded raw SPN separately from `assigned_model`. Set the assignment as
catalog material rather than a native model observation.

An empty, malformed, or unavailable SPN field leaves the crosswalk result
unknown; the software-version field alone never selects a row. It must not
be replaced with a guessed model or protocol family.

## Open questions

- The physical product behind the `CTLX0` / `0194` pair (emitted by the
  Vaillant internet gateway under the label `VR940`) is **Unknown**; the pair is
  bound as a VRC720-family controller (candidate), and the family cell of that
  row reflects this binding only.
- The physical product behind the pair (`CTLX0`, SPN 196), and behind the pair
  that combines SPN 196 with a second `CTL`-series identity string, is
  **Unknown**; no article number is known for the pair, and which product the
  identity strings `05000` and `_E100` denote for SPN 196 is not established.
- The family cell of every row is a candidate family name. Which operations a
  matching device supports is not established by the crosswalk.
