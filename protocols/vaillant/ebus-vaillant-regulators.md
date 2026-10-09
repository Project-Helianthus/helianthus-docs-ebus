# Vaillant Regulators

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This is the entry point for Vaillant regulator identities and related protocol
families. Its bounded crosswalk identifies a catalog row only when the **EID
and decoded SW/SPN value match as a pair**. An EID by itself does not classify
a regulator, prove model identity, or prove that a protocol is supported by the
connected device.

The discovery flow that supplies the identity fields is described in
[eBUS discovery](../ebus-services/ebus-overview.md#identification-scan-0x07-0x04)
and [Vaillant discovery](ebus-vaillant.md#vaillant-scanid-chunks-qq0x240x27).
Use this crosswalk after preserving the raw identity values in the discovery
record.

## Scope and Related Protocols

The crosswalk distinguishes model rows from protocol-family labels:

- `VRC720` is a protocol-family label for the listed VRC720, VRT380, VRC710,
  and VR940 model rows. B524 scalar/discovery operations and B555 schedules
  remain candidate capabilities subject to their own qualification. A matching
  pair does not establish support for either one.
- `VRC700` is a separate family. A matching VRC700 row selects a candidate
  family description; B524 `ReadTimer`, `WriteTimer`, and `ReadVR91` remain
  subject to an operation's existing identity and response checks.

Protocol details remain in their owning documents:

- [B524 operation specification](ebus-vaillant-B524.md)
- [B524 register map](ebus-vaillant-B524-register-map.md)
- [B524 profile discovery and descriptions](ebus-vaillant-b524-profile-discovery-and-descriptions.md)
- [B524 bounded survey methodology](ebus-vaillant-b524-survey-methodology.md)
- [B555 timer/schedule protocol](ebus-vaillant-b555-timer-protocol.md)

## SW to SPN Representation

`SW` is the software field (`0704`). The `SPN` column preserves its decoded
PIN value as a four-digit hexadecimal `u16`; it is not derived from hardware
version, a product code, serial number, or any other identity field.

The eBUS `PIN` codec is BCD: the wire order is most-significant BCD byte first.
Therefore the wire bytes `04 17` decode as decimal `417`, represented here as `0x01A1`; `04 63`
decodes as decimal `463`, represented as `0x01CF`. Raw wire SW and the decoded
SPN must both be retained. Do not interpret raw `04 17` as `0x0417`, and do not
invent a catalog row for an invalid BCD value or an unlisted decoded value. For
example, raw `05 07` decodes to decimal `507` (`0x01FB`), which is unknown to
this bounded crosswalk.

The codec behavior is specified by the public
[archived `broadcast.csv` software field](https://github.com/john30/ebusd-configuration/blob/9c3ed3a0d487dc5898c611ab18f8313792659020/archived/en/broadcast.csv)
and [ebusd `PIN` datatype implementation](https://github.com/john30/ebusd/blob/38db2d28bd5622cadb6078c1662c6f7da5cef891/src/lib/ebus/datatype.cpp).

## Exact EID and SW/SPN Crosswalk

**Hypothesis as native-model evidence pending observations.** These 38 exact
pairs are a bounded naming and family catalog. They do not independently establish a device model, native
protocol support, or the availability of any operation on a connected target.
Treat an unlisted or malformed pair as unknown rather than extending this table
by inference.

| EID | SW (SPN hex `u16`) | Model row | Protocol family |
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
- raw SW bytes;
- decoded SW/SPN value and decoding state; and
- crosswalk result (`matched`, `unlisted`, or `invalid`).

For a matched row, retain the native `0x07/0x04` EID, SW, and decoded raw SPN
separately from `assigned_model`. Set
the assignment as catalog material rather than a native model observation.

An empty, malformed, or unavailable SW field leaves the crosswalk result
unknown. It must not be replaced with a guessed model or protocol family.
