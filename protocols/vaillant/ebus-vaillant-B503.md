# Vaillant B503 — diagnostic and service selector family

`PB=0xB5`, `SB=0x03`.

This document specifies the publishable, implementation-neutral wire contract for the observed Vaillant `B503` selector family. It does not define client lifecycle, deployment policy, or consumer presentation.

## Status and evidence

The selector catalog is based on the public `ebusd-configuration` TypeSpec sources listed in [References](#references). The observed response example is an evidence example for its stated device class only. Device coverage and write effects remain `Unknown` unless corroborated for the target device.

Beyond the public catalog this page records two further kinds of layout, both **Hypothesis** and unconfirmed on the wire:

- a *category form* of the `B5 03` request and reply, in which the two prefix bytes are read as an operation byte and a category byte (see [Category form](#category-form));
- *candidate layouts* for the appliance variants of `B5 03`, for operations `03` to `07` (see [Candidate operations 03 to 07](#candidate-operations-03-to-07)), and for the `B5 09 18` sensor and block bit-map read (see [B5 09 18 — sensor and block bit maps](#b5-09-18--sensor-and-block-bit-maps)).

The `B5 0E` logger service has its own page: [ebus-vaillant-B50E.md](ebus-vaillant-B50E.md).

Profile availability: each `B5 03` operation (`00` to `07`), `B5 09 18` and each `B5 0E` operation (`00` to `07`) is available under both the eBUS and the PeBUS profiles (candidate). No service of this family is available only on PeBUS (candidate, unconfirmed on the wire). This statement covers `B5 03 00..07`, `B5 09 18` and `B5 0E 00..07`.

## Wire shape

Each request begins with a two-byte `(family, selector)` prefix. The prefix identifies a catalog row; a device-specific request can append bytes after it. The payload is carried in a normal eBUS telegram and does not change eBUS framing, CRC, escaping, arbitration, or transaction rules.

```text
family   : byte   # 0x00 current; 0x01 history lookup; 0x02 clear command
selector : byte   # 0x01 error; 0x02 service; 0x03 HMU live monitor
```

The safety class is a property of the complete `(family, selector)` tuple. For example, `family=0x00` contains both read selectors and `00 03`, whose effect is stateful. Do not infer safety from the family byte alone.

For `family=0x01`, the response includes an index field. The mechanism that selects an indexed history record is device-class dependent; the TypeSpec does not establish one universal appended-request encoding.

### Category form

The same two prefix bytes can be read as an operation byte followed by a category byte, with an index byte for history lookups. This reading is **Hypothesis**, unconfirmed on the wire: it is a candidate responder layout, and no capture of a category-form exchange is recorded here.

| Operation | Request data | Meaning | Minimum request data length (operation byte included) |
|---|---|---|---:|
| `00` | `00 <category>` | read current codes | 2 |
| `01` | `01 <category> <index>` | read one history entry | 3 |
| `02` | `02 <category>` | clear history (state-changing) | 2 |

The length limits are minimums, not exact lengths: a longer request is not rejected for length alone (candidate, unconfirmed on the wire).

The category byte `1` to `5` selects one of five code lists; any other value selects no list (candidate).

The request data `00 03` (operation `00`, category `3`) is byte-identical to the public catalog selector `00 03`, which is classified `SERVICE_WRITE` (live monitor, state-changing). Until a target is qualified for the category form, treat `00 03` as state-changing and do not send it as a read.

| Category | Candidate meaning |
|---:|---|
| 1 | error |
| 2 | maintenance |
| 3 | status |
| 4 | limp-home (permanent) |
| 5 | limp-home (reversible) |

The meanings are candidate interpretations, unconfirmed on the wire.

Categories `1` and `2` occupy the byte position of the public catalog selectors `01` (error) and `02` (service). Category `3` selects the status list in this form, whereas the public catalog assigns `00 03` to the HMU live-monitor pair. The two readings of byte value `03` are not reconciled (see [Open questions](#open-questions)).

#### Category-form reply bodies

All bodies below are **Hypothesis**, unconfirmed on the wire.

- Operation `00`: a 10-byte body of five consecutive little-endian `uint16` code slots at body offsets 0, 2, 4, 6 and 8. `FF FF` marks an empty slot; at most five codes are active. An invalid category leaves all ten bytes `FF`. This is the same slot shape as the public catalog `00 01` response (see [Slot decoding](#slot-decoding)).
- Operation `01`: an 8-byte body.

  | Body offset | Field | Encoding |
  |---:|---|---|
  | 0 | marker | `01` or `02`; the meaning of the two values is unknown |
  | 1 | minute | BCD |
  | 2 | hour | BCD |
  | 3 | day | BCD |
  | 4 | month | BCD, 1 to 12 |
  | 5 | year component | BCD; calendar year minus 1800 (a value above 99 exceeds the published eBUS BCD range 00 to 99; this is a discrepancy with the published BCD type) |
  | 6 | code low byte | `uint16` little-endian code, low byte |
  | 7 | code high byte | `uint16` little-endian code, high byte |

  An absent entry, or a code of `FFFF`, gives `00 FF FF FF FF FF FF FF`. The index byte is zero-based; an index beyond the stored entries yields the no-item body rather than an error. The five timestamp bytes are the responder's local time; the time zone, calendar validation and the BCD handling of a year component above 99 are not characterised.
- Operation `02`: a 1-byte body `01`. The request deletes the stored history of the selected category and leaves the active-code list untouched. The body `01` does not certify that the change was stored, and the body alone does not show that a request with an invalid category cleared anything. The operation is state-changing.

Whether the bus reply carries an operation-echo byte in front of these bodies (which would make them 11, 9 and 2 bytes) is not established.

Candidate interpretation, unconfirmed on the wire: a stored record is a `uint16` code, a marker and five time bytes; the code is returned raw, with no lookup to F-codes or text, so a value in operation `00` or `01` is a native numeric code of the responder, not an appliance F-code. A history list is capped at 20 entries on insertion, and a duplicate of an active code is not inserted twice.

## Selector catalog

| Request payload | Direction | Name | Safety class | Response shape | Evidence | Falsification condition |
|---|---:|---|---|---|---|---|
| `00 01` | read | `Currenterror` | `READ` | five little-endian `uint16` error slots; `0xFFFF` is empty | public TypeSpec | A target response does not decode into five slots with that sentinel. |
| `01 01` | read | `Errorhistory` | `READ` | index plus error-history payload | public TypeSpec | Varying a documented index does not change the record, or no indexed record is returned. |
| `02 01` | write | `Clearerrorhistory` | `INSTALL_WRITE` | ACK and possible side effect | public TypeSpec | A qualified isolated test shows no history change after an acknowledged command. |
| `00 02` | read | `Currentservice` | `READ` | five little-endian `uint16` service slots | public TypeSpec | A target with a service message has no five-slot response. |
| `01 02` | read | `Servicehistory` | `READ` | index plus service-history payload | public TypeSpec | Indexed requests do not produce an indexed service-history record. |
| `02 02` | write | `Clearservicehistory` | `INSTALL_WRITE` | ACK and possible side effect | public TypeSpec | A qualified isolated test shows no history change after an acknowledged command. |
| `00 03` | stateful command/read pair | HMU `LiveMonitorMain` | `SERVICE_WRITE` | response begins with `status`, `function`; remaining bytes are reserved | public TypeSpec | The first two response bytes do not follow live-monitor status or function changes. |

`INSTALL_WRITE` denotes a command that can alter retained diagnostic history. An ACK is a wire outcome, not proof of the resulting device state. Any use of a write selector requires a separately established safety procedure and device-specific qualification.

### Candidate operations 03 to 07

Five further operations of `B5 03` exist as candidates for appliances. All are **Hypothesis**, unconfirmed on the wire. Each is state-changing, none is classified under the safety classes above, and none is documented as safe to send. Offsets count from the first byte of the service prefix: the three prefix bytes `B5 03 <operation>` (PB, SB and the operation byte; the two-byte prefix of the Wire shape section counts data bytes only) occupy offsets 0 to 2, so the first argument byte is at offset 3. How these offsets map onto the data bytes of a bus telegram is unconfirmed.

| Operation | Candidate meaning | Request layout | Reply layout |
|---|---|---|---|
| `03` | unlock a safety-relevant lockout | 8 ASCII bytes at offset 3, a `uint8` value at offset 11 | not established |
| `04` | block the boiler for 15 minutes | an ASCII block at offset 3; its length is not established | not established |
| `05` | block or unblock the boiler | an ASCII block, then a mode word whose value `FFFFFFFF` is dynamic; mode `0F` blocks and any other value unblocks | not established |
| `06` | remote reset | not established | feedback at offset 3: 0 accepted (reset pending), 1 unsupported, 2 limit reached, 3 ignored |
| `07` | write the error buffer | history-selection bits 0 to 4, then five little-endian `uint16` current errors at offsets 4, 6, 8, 10 and 12 | feedback value 1 means accepted |

The meaning of the ASCII blocks is not established.

For the current and history requests of appliance variants, candidate layouts exist separately for error, maintenance, status, limp-home and reversible limp-home lists. Their candidate current-list reply is a repeated little-endian `uint16` list up to the end of the data.

This list shape and the fixed 10-byte, five-slot body (category-form operation `00` above, and the public catalog row `00 01`, of which an observed reply is shown below) are two conflicting candidate shapes for a current-code reply. No target class, profile or request byte that selects one shape over the other is established; the conflict is unresolved (see [Open questions](#open-questions)). A 10-byte body is consistent with both shapes; a body of any other even length is consistent only with the list shape.

## Slot decoding

`00 01` and `00 02` contain five little-endian `uint16` slots. `0xFFFF` marks an empty slot. Empty slot N does not terminate parsing of subsequent slots.

The first non-empty slot, scanning from index zero upward, may be used as a derived diagnostic value. If all five slots are `0xFFFF`, that derived value is absent. This is a decoding rule only; it does not establish a manufacturer-wide mapping to UI fault labels.

### Observed decoding example

The following example is an observed response of a Vaillant boiler (gas appliance; its identification reply is `BAI00`) and does not establish a cross-device code mapping:

```text
REQ:  f1 08 b5 03 02 00 01
RESP: 0a 19 01 ff ff ff ff ff ff ff ff
```

The response length is `0x0a`; slot zero is little-endian `0x0119` (decimal 281), while slots one through four are empty (`0xFFFF`).

The request data `00 01` is read here under the public catalog (selector `00 01`). The same bytes also form a valid category-form request (operation `00`, category `1`), and the 10-byte reply carries no operation-echo byte; whether this exchange is a category-form exchange is not established (see [Open questions](#open-questions)).

### Code values and history validity

This page publishes no code-to-text table. No code-to-text mapping for appliance codes is established, so a code stays a numeric value: preserve it raw and do not label it with an F-code or message text without a mapping qualified for the target.

Candidate interpretation, unconfirmed on the wire: for appliance history lookups a validity field precedes the entry, with `0` meaning invalid, no error or out of buffer, `1` an error number only, and `2` a date plus an error number.

Candidate interpretation, unconfirmed on the wire: for one device profile, raw codes map to numbers as in the following example table, which is not a universal F-code mapping:

| Raw code | 1 | 2 | 3 | 4 | 11 | 13 | 15 | 17 | 20 | 21 | 30 | 31 | 32 | 36 | `FFFF` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Number | 2001 | 2002 | 2003 | 2004 | 2011 | 2013 | 2015 | 2017 | 2020 | 2021 | 2030 | 2031 | 2032 | 2036 | 65535 |

Which devices use this table is not established.

## Live-monitor response

`00 03` is classified as `SERVICE_WRITE` because enabling or disabling it can change target state. An observed status response begins with `status` and `function`; trailing bytes are reserved until supported by evidence for the target class. The native protocol evidence does not define caller ownership, timeout policy, retries, reconnect behavior, or a shared-client arbitration model.

## B5 09 18 — sensor and block bit maps

`B5 09 18` is an operation of the B509 family that carries no register address, unlike the register-access operations `0D` (read) and `0E` (write) with their 16-bit register id described on [ebus-vaillant-B509.md](ebus-vaillant-B509.md); this section holds its layout. The candidate name of the read is "read error block" of a target. Every layout in this section is **Hypothesis**, unconfirmed on the wire.

Request: operation byte `18` with no argument. By the B509 operation-byte convention the request data is the single byte `18` (`NN` = 1); this is unconfirmed on the wire.

Reply: offsets count from the first byte of the service prefix, so the prefix `B5 09 18` occupies offsets 0 to 2 and the candidate reply has 10 bytes in all. How these offsets map onto the data bytes of a bus telegram is unconfirmed; do not apply them to a bus reply without a qualified capture.

| Offset | Field | Encoding | Meaning |
|---:|---|---|---|
| 3 | sensor error block 1 | `uint8`, raw | bit map not defined |
| 4 | sensor error block 2 | `uint8`, raw | bit map not defined |
| 5 | sensor error block 3 | `uint8`, raw | bit map not defined |
| 6 | sensor error block 4 | `uint8`, raw | bit map not defined |
| 7, bit 0 | temperature error | 1 bit; 0 False, 1 True | setpoint temperature not reached within a preset time for this circuit |
| 7, bits 1 to 7 | reserved | 7 bits | reserved |
| 8 | temperature error block 1 | `uint8`, raw | bit map not defined |
| 9 | temperature error block 2 | `uint8`, raw | bit map not defined |

The temperature-error bit is a flag that a setpoint was not reached in time (candidate). It is not a temperature value and it does not establish a sensor fault. A candidate layout does not establish that a given target answers the service.

Candidate decoding rule, unconfirmed on the wire: retain the six block bytes raw; read bit 0 of the byte at offset 7 as the temperature-error flag and retain bits 1 to 7 raw as reserved. Do not attribute the block bits to particular sensors, and do not map them to F-codes of another device family.

No sensor or temperature block bit map, preset duration, circuit selector or reset method is established (see [Open questions](#open-questions)).

Profile availability: `B5 09 18` is available under both the eBUS and the PeBUS profiles (candidate); it is not available only on PeBUS.

## Response codes and invalid requests

- An ACK of a state-changing selector is a wire outcome, not proof of the resulting device state (see the selector catalog).
- Public catalog `00 01` on a boiler: an observed 10-byte body with the empty-slot sentinel `FFFF` (see the observed decoding example).
- Category form, candidate and unconfirmed on the wire: operation `02` returns the body `01`, which does not certify the change; an invalid category in operation `00` returns ten `FF` bytes; an absent history entry in operation `01` returns `00 FF FF FF FF FF FF FF`.
- Candidate feedback values, unconfirmed on the wire: operation `06` feedback 0 to 3 and operation `07` feedback 1 (see [Candidate operations 03 to 07](#candidate-operations-03-to-07)); `B5 0E 04` and `B5 0E 07` feedback values are on the [B50E page](ebus-vaillant-B50E.md).
- Candidate, unconfirmed on the wire: a category-form request with a wrong service byte, a wrong operation byte or a data length below the minimum produces no reply body from the responder. The bus-level result (error, empty reply or silence) is not established. No appliance reply to an invalid `B5 03` request is recorded on this page.

## Evidence labels

- **Public TypeSpec**: the cited upstream TypeSpec source.
- **Observed capture**: a publishable telegram observation with stated device context.
- **Inference**: a falsifiable interpretation of the preceding evidence.
- **Candidate layout**: a layout not confirmed on the wire; it carries **Hypothesis** or "unconfirmed on the wire" inline and a bullet under Open questions.

## Open questions

- Bus-level result of a category-form `B5 03` request with a wrong service byte, a wrong operation byte or too little data (error, empty reply or silence): not established; the responder writes no body. Hypothesis, unconfirmed on the wire.
- Whether the bus reply of the category form carries an operation-echo byte, and its CRC and ACK framing: not established. The observed boiler reply above (10 bytes for request data `00 01`) carries no echo byte; whether that exchange is a category-form exchange is not established.
- Which target address answers the category form, and the initiator or target role of that responder: not established on this page.
- No capture of a category-form reply exists: framing, operation echo, CRC and ACK, the behaviour for invalid requests and the answering address are unobserved; only candidate body layouts exist, unconfirmed on the wire.
- The meaning of the marker flag (`01` or `02`) in the history body is unknown.
- Time zone, calendar validation and BCD handling of a year component above 99 in the history timestamp are not characterised.
- Byte value `03` after the operation byte: the public catalog assigns `00 03` to the HMU live-monitor pair, while the category form selects the status list. The relation is unresolved.
- Categories 4 and 5 are candidate limp-home (permanent) and limp-home (reversible) lists; the correspondence is unresolved on the wire.
- The candidate layouts for operations `03` to `07`, the appliance current and history variants and the validity field have not been confirmed on any target; the reply layouts of `03` to `05` and the request layout of `06` are not established.
- Current-code reply shape: the fixed 10-byte, five-slot body and the repeated `uint16` list up to the end of the data are conflicting candidate shapes; which one a given target class or profile returns, and whether any request byte selects between them, is unresolved.
- Code-to-text mapping for appliance codes: none is established, and none is defined here.
- The example number table (the raw codes of the table, 1 to 36, map to 2001 to 2036; `FFFF` to 65535) is a candidate for one device profile; which devices use it is not established.
- The history cap of 20 entries on insertion and the rule that a duplicate of an active code is not inserted twice are candidates, unconfirmed on the wire.
- `B5 09 18`: the bit maps of the sensor error blocks and of the temperature error blocks, the preset duration, the circuit selector and the reset method are not established; the mapping of the offsets to a bus reply is unconfirmed; support by a given target is unconfirmed.
- `B5 0E` logger buffer record stride, timestamp layout and integrity contract: see the [B50E page](ebus-vaillant-B50E.md#open-questions).

## References

- [errors_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/errors_inc.tsp)
- [service_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/service_inc.tsp)
- [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- [eBUS wire overview](../ebus-services/ebus-overview.md)
- [Vaillant family index](ebus-vaillant.md)
- [Vaillant B509 register access](ebus-vaillant-B509.md)
- [Vaillant B50E logger service](ebus-vaillant-B50E.md)
