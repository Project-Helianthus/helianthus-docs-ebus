# Capability Discovery

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Policy

The locked plan states:

> `0x07 0x03` and `0x07 0x05` are opt-in discovery surfaces.
> Devices that do not answer remain `capability=unknown`, which is a
> valid terminal state. No synthetic capability is invented.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

Capability discovery is never mandatory for `ebus_standard` identity,
decode, or NM operation.

## Methods

| PB | SB | Name | Invocation policy | safety_class |
|---:|---:|---|---|---|
| `0x07` | `0x03` | Query Supported Commands | Opt-in addressed query only | `read_only_bus_load` |
| `0x07` | `0x05` | Query Supported Commands, extended | Opt-in addressed query only | `read_only_bus_load` |

`0x07 0x03` response mapping is fixed to PB `0x05..0x0C`.
`0x07 0x05` response mapping depends on the requested PB block.

## Capability State Model

| State | Meaning | Terminal |
|---|---|---|
| `unknown` | No capability query has been run, or the device did not provide a usable answer | Yes |
| `known` | A valid response was decoded and mapped to supported PB/SB bits | Yes |
| `invalid_response` | A response was received but failed strict decoding | Yes for that observation |
| `not_attempted` | Operator or policy has not opted in | No; transitions to `unknown` if stored as device state |

`unknown` is not an error. It is the required terminal state for
non-answering devices.

## No Synthetic Capability

The provider MUST NOT infer capability support from:

1. Observing a device transmit a command.
2. Seeing a successful `0x07 0x04` Identification response.
3. Manufacturer or model identity.
4. Vaillant `0xB5` provider metadata.
5. NM target configuration.
6. Home Assistant or registry consumer needs.

Observed behavior MAY be stored as evidence, but it MUST be labeled as
observation evidence rather than as a capability-discovery result.

## Opt-In Requirements

An active `0x07 0x03` or `0x07 0x05` query requires an explicit caller
or runtime policy decision. The decision record MUST include:

- target address
- selected method (`0x07 0x03` or `0x07 0x05`)
- caller context
- reason
- timestamp
- bus-load accounting window

The default discovery pipeline MAY decode passively observed capability
responses. Passive decode does not authorize active probing.

## Error Handling

1. Timeout or no answer records `capability=unknown`.
2. NACK, arbitration failure, or transport failure records
   `capability=unknown` plus transport diagnostics.
3. Malformed response records `invalid_response` for that observation
   and MUST NOT create synthetic support bits.
4. Unsupported PB/SB bits outside the catalog are preserved as raw bits
   with source labels, not converted into catalog methods.

