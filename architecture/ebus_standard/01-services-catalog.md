# ebus_standard Services Catalog

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Scope

The locked plan states:

> Services in `ebus_standard` first lock baseline:
>
> - `0x03` Service Data
> - `0x05` Burner Control
> - `0x07` System Data (includes `0x04` Identification and optional `0x03` /
>   `0x05` capability discovery)
> - `0x08` Controller-to-Controller
> - `0x09` Memory Server
> - `0x0F` Test Commands
> - `0xFE` General Broadcast
> - `0xFF` Network Management (including `FF 00`, `FF 01`, `FF 02`, `FF 03`,
>   `FF 04`, `FF 05`, `FF 06`)

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

`safety_class` values are defined in
[`05-execution-safety.md`](./05-execution-safety.md). These classifications
govern live invocation. Passive decode of an observed frame is always
non-invoking and does not by itself originate bus traffic.

Protocol command names and payload summaries are sourced from the local
standard-service protocol documents:

- [`../../protocols/ebus-services/ebus-service-03h.md`](../../protocols/ebus-services/ebus-service-03h.md)
- [`../../protocols/ebus-services/ebus-service-05h.md`](../../protocols/ebus-services/ebus-service-05h.md)
- [`../../protocols/ebus-services/ebus-service-07h.md`](../../protocols/ebus-services/ebus-service-07h.md)
- [`../../protocols/ebus-services/ebus-service-08h.md`](../../protocols/ebus-services/ebus-service-08h.md)
- [`../../protocols/ebus-services/ebus-service-09h.md`](../../protocols/ebus-services/ebus-service-09h.md)
- [`../../protocols/ebus-services/ebus-service-0Fh.md`](../../protocols/ebus-services/ebus-service-0Fh.md)
- [`../../protocols/ebus-services/ebus-service-FEh.md`](../../protocols/ebus-services/ebus-service-FEh.md)
- [`../../protocols/ebus-services/ebus-service-FFh.md`](../../protocols/ebus-services/ebus-service-FFh.md)

## Service `0x03` - Service Data

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x03` | `0x04` | Start Counts | Initiator -> target; target response | addressed request/response | `read_only_bus_load` |
| `0x03` | `0x05` | Operating Time Level 1 | Initiator -> target; target response | addressed request/response | `read_only_bus_load` |
| `0x03` | `0x06` | Operating Time Level 2 | Initiator -> target; target response | addressed request/response | `read_only_bus_load` |
| `0x03` | `0x07` | Operating Time Level 3 | Initiator -> target; target response | addressed request/response | `read_only_bus_load` |
| `0x03` | `0x08` | Fuel Quantity Counter | Initiator -> target; target response | addressed request/response | `read_only_bus_load` |
| `0x03` | `0x10` | Meter Reading | Initiator -> target; target response or initiator telegram response | addressed request/response or initiator/initiator | `read_only_bus_load` |

Service `0x03` methods are diagnostic reads. They are not mutating, but
live invocation still consumes bus capacity and is therefore
`read_only_bus_load`, not `read_only_safe`.

## Service `0x05` - Burner Control

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x05` | `0x00` | Operational Data Request, burner to controller | Burner -> controller | addressed operational control | `mutating` |
| `0x05` | `0x01` | Operational Data, controller to burner | Controller -> burner | addressed operational control | `mutating` |
| `0x05` | `0x02` | Operational Data Request, controller to burner | Controller -> burner | addressed operational control | `mutating` |
| `0x05` | `0x03` | Operational Data, burner to controller, block 1 | Burner -> controller | addressed operational data | `mutating` |
| `0x05` | `0x03` | Operational Data, burner to controller, block 2 | Burner -> controller | addressed operational data, selector `block_number=0x02` | `mutating` |
| `0x05` | `0x04` | Control Stop Response | Burner -> controller | addressed operational control | `mutating` |
| `0x05` | `0x05` | Barred | None | invalid/reserved | `destructive` |
| `0x05` | `0x06` | Operational Data Request, channel B, burner to controller | Burner -> controller | addressed operational control | `mutating` |
| `0x05` | `0x07` | Operational Data, channel B, controller to burner | Controller -> burner | addressed operational control | `mutating` |
| `0x05` | `0x08` | Operational Data Request, channel B, controller to burner | Controller -> burner | addressed operational control | `mutating` |
| `0x05` | `0x09` | Operational Data, channel B, block 1 | Burner -> controller | addressed operational data, selector `block_number=0x01` | `mutating` |
| `0x05` | `0x09` | Operational Data, channel B, block 2 | Burner -> controller | addressed operational data, selector `block_number=0x02` | `mutating` |
| `0x05` | `0x09` | Operational Data, channel B, block 3 | Burner -> controller | addressed operational data, selector `block_number=0x03` | `mutating` |
| `0x05` | `0x0A` | Configuration Data Request | Controller -> burner; burner response via `0x05 0x0B` | addressed request/response | `read_only_bus_load` |
| `0x05` | `0x0B` | Configuration Data Response | Burner -> controller | addressed response | `read_only_safe` |
| `0x05` | `0x0C` | Operational Requirements | Burner -> controller | addressed operational control | `mutating` |
| `0x05` | `0x0D` | Operational Data, extended controller to burner | Controller -> burner | addressed operational control | `mutating` |

Operational burner-control methods can start, stop, or alter cyclic
control behavior. They are default-denied for user-facing invocation.

## Service `0x07` - System Data

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x07` | `0x00` | Date/Time Broadcast | Controller 0 -> all | broadcast | `broadcast` |
| `0x07` | `0x01` | Set Date/Time | PC/clock -> controller | addressed write/control | `mutating` |
| `0x07` | `0x02` | Set Outside Temperature | Service tool -> controller | addressed write/control | `mutating` |
| `0x07` | `0x03` | Query Supported Commands | Any initiator -> target; target response | addressed capability query | `read_only_bus_load` |
| `0x07` | `0x04` | Identification | Any initiator -> target; target response | addressed identity query | `read_only_bus_load` |
| `0x07` | `0x04` | Identification self-broadcast | Device -> all | broadcast identity announcement | `broadcast` |
| `0x07` | `0x05` | Query Supported Commands, extended | Any initiator -> target; target response | addressed capability query | `read_only_bus_load` |
| `0x07` | `0xFE` | Inquiry of Existence | Any initiator -> all, usually broadcast | broadcast inquiry | `broadcast` |
| `0x07` | `0xFF` | Sign of Life | Any initiator -> all, usually broadcast | broadcast sign-of-life | `broadcast` |

`0x07 0x03` and `0x07 0x05` are opt-in capability-discovery surfaces;
see [`04-capability-discovery.md`](./04-capability-discovery.md).
`0x07 0x04` produces the canonical Identification descriptor defined in
[`03-identification.md`](./03-identification.md).

## Service `0x08` - Controller-to-Controller

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x08` | `0x00` | Target Values | Secondary controller -> controller 0 | broadcast | `broadcast` |
| `0x08` | `0x01` | Operational Data | Controller 0 -> all | broadcast | `broadcast` |
| `0x08` | `0x02` | Control Commands | Controller 0 -> all | broadcast | `broadcast` |
| `0x08` | `0x03` | Boiler Parameters | Controller 0 -> all | broadcast | `broadcast` |
| `0x08` | `0x04` | System Remote Control | PC/modem/clock -> controller | addressed remote control | `mutating` |

All broadcast variants are default-denied for user-facing invocation.
The addressed system remote control method is mutating and is also
default-denied.

## Service `0x09` - Memory Server

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x09` | `0x00` | Read RAM | Initiator -> target; target response | addressed service-mode memory read | `read_only_bus_load` |
| `0x09` | `0x01` | Write RAM | Initiator -> target | addressed service-mode memory write | `memory_write` |
| `0x09` | `0x02` | Read EEPROM | Initiator -> target; target response | addressed service-mode memory read | `read_only_bus_load` |
| `0x09` | `0x03` | Write EEPROM | Initiator -> target | addressed service-mode memory write | `memory_write` |

Memory Server methods remain service-mode methods. Writes are
`memory_write`. Reads are not synthetic capabilities; they stay
`read_only_bus_load` unless a later locked plan introduces stricter
read policy.

## Service `0x0F` - Test Commands

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0x0F` | `0x01` (`NN=0x02`) | Start of Test | Test system -> test device | addressed or initiator/initiator test control | `destructive` |
| `0x0F` | `0x01` (`NN=0x01`) | Ready | Test device -> test system | addressed or broadcast test response | `destructive` |
| `0x0F` | `0x02` | Test Message | Varies by test function | variable test carrier | `destructive` |
| `0x0F` | `0x03` | End of Test | Test device -> test system | addressed or initiator/initiator test control | `destructive` |

Test commands can put devices into factory/service test behavior, copy
or echo telegrams, and originate follow-on traffic. They are
default-denied.

## Service `0xFE` - General Broadcast

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0xFE` | `0x01` | Error Message | Any initiator -> all | broadcast | `broadcast` |

`0xFE 0x01` is explicitly outside the first NM baseline in the adopted
NM participant policy. It is cataloged as a standard service but not
made available through first-delivery user invocation.

## Service `0xFF` - Network Management

| PB | SB | Method | Direction | Telegram class | safety_class |
|---:|---:|---|---|---|---|
| `0xFF` | `0x00` | Reset Status NM | Joining node -> all | broadcast | `broadcast` |
| `0xFF` | `0x01` | Reset Target Configuration NM | Any initiator -> all | broadcast | `broadcast` |
| `0xFF` | `0x02` | Failure Message | Detecting node -> all | broadcast | `broadcast` |
| `0xFF` | `0x03` | Net Status Query request | Any initiator -> target | addressed NM query | `read_only_bus_load` |
| `0xFF` | `0x03` | Net Status Query response | NM target -> initiator | addressed responder reply | `read_only_safe` |
| `0xFF` | `0x04` | Monitored Participants Query request | Any initiator -> target | addressed NM query | `read_only_bus_load` |
| `0xFF` | `0x04` | Monitored Participants Query response | NM target -> initiator | addressed responder reply, block-paginated | `read_only_safe` |
| `0xFF` | `0x05` | Failed Nodes Query request | Any initiator -> target | addressed NM query | `read_only_bus_load` |
| `0xFF` | `0x05` | Failed Nodes Query response | NM target -> initiator | addressed responder reply, block-paginated | `read_only_safe` |
| `0xFF` | `0x06` | Required Services Query request | Any initiator -> target | addressed NM query | `read_only_bus_load` |
| `0xFF` | `0x06` | Required Services Query response | NM target -> initiator | addressed responder reply, block-paginated | `read_only_safe` |

The NM runtime state machine remains owned by the gateway runtime. The
wire services above are catalog entries consumed by that runtime. The
exact `system_nm_runtime` whitelist for first delivery is defined in
[`05-execution-safety.md`](./05-execution-safety.md).
