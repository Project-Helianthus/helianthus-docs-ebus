# Vaillant B503 — diagnostic and service selector family

`PB=0xB5`, `SB=0x03`.

This document specifies the publishable, implementation-neutral wire contract for the observed Vaillant `B503` selector family. It does not define client lifecycle, deployment policy, or consumer presentation.

## Status and evidence

The selector catalog is based on the public `ebusd-configuration` TypeSpec sources listed in [References](#references). The observed response example is an evidence example for its stated device class only. Device coverage and write effects remain `Unknown` unless corroborated for the target device.

## Wire shape

Each request begins with a two-byte `(family, selector)` prefix. The prefix identifies a catalog row; a device-specific request can append bytes after it. The payload is carried in a normal eBUS telegram and does not change eBUS framing, CRC, escaping, arbitration, or transaction rules.

```text
family   : byte   # 0x00 current; 0x01 history lookup; 0x02 clear command
selector : byte   # 0x01 error; 0x02 service; 0x03 HMU live monitor
```

The safety class is a property of the complete `(family, selector)` tuple. For example, `family=0x00` contains both read selectors and `00 03`, whose effect is stateful. Do not infer safety from the family byte alone.

For `family=0x01`, the response includes an index field. The mechanism that selects an indexed history record is device-class dependent; the TypeSpec does not establish one universal appended-request encoding.

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

## Slot decoding

`00 01` and `00 02` contain five little-endian `uint16` slots. `0xFFFF` marks an empty slot. Empty slot N does not terminate parsing of subsequent slots.

The first non-empty slot, scanning from index zero upward, may be used as a derived diagnostic value. If all five slots are `0xFFFF`, that derived value is absent. This is a decoding rule only; it does not establish a manufacturer-wide mapping to UI fault labels.

### Observed decoding example

The following example is an observed BAI00 response and does not establish a cross-device code mapping:

```text
REQ:  f1 08 b5 03 02 00 01
RESP: 0a 19 01 ff ff ff ff ff ff ff ff
```

The response length is `0x0a`; slot zero is little-endian `0x0119` (decimal 281), while slots one through four are empty (`0xFFFF`).

## Live-monitor response

`00 03` is classified as `SERVICE_WRITE` because enabling or disabling it can change target state. An observed status response begins with `status` and `function`; trailing bytes are reserved until supported by evidence for the target class. The native protocol evidence does not define caller ownership, timeout policy, retries, reconnect behavior, or a shared-client arbitration model.

## Evidence labels

- **Public TypeSpec**: the cited upstream TypeSpec source.
- **Observed capture**: a publishable telegram observation with stated device context.
- **Inference**: a falsifiable interpretation of the preceding evidence.

## References

- [errors_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/errors_inc.tsp)
- [service_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/service_inc.tsp)
- [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- [eBUS wire overview](../ebus-services/ebus-overview.md)
- [Vaillant family index](ebus-vaillant.md)
