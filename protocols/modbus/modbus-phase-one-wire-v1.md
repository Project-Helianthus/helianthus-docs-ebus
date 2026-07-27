# Modbus Phase-One Wire Reference V1

## License And Scope

This implementation-neutral reference is covered by
[`protocols/LICENSE`](../LICENSE), CC0-1.0. It summarizes the public wire facts
needed for FC03, FC04, FC2B/MEI0E, Modbus TCP, and Modbus RTU. It contains no
Helianthus scheduler, profile, qualification, gateway, or semantic policy.

The normative upstream sources are:

1. [MODBUS Application Protocol Specification V1.1b3](https://www.modbus.org/file/secure/modbusprotocolspecification.pdf)
2. [MODBUS Messaging on TCP/IP Implementation Guide V1.0b](https://www.modbus.org/file/secure/messagingimplementationguide.pdf)
3. [MODBUS over Serial Line Specification and Implementation Guide V1.02](https://www.modbus.org/file/secure/modbusoverserial.pdf)

Those source documents are not redistributed here. If this summary conflicts
with an upstream source, the upstream source controls the wire protocol and
this reference requires correction.

## Common PDU

Multi-byte numerical PDU fields are encoded most-significant byte first. A
Modbus PDU is at most 253 bytes:

```text
request PDU   = function_code || request_data
response PDU  = function_code || response_data
exception PDU = (request_function_code | 0x80) || exception_code
```

An exception PDU is exactly two bytes. Its function byte is the requested
function with bit 7 set. The second byte is the exception code.

## FC03 And FC04

Read Holding Registers uses function `0x03`. Read Input Registers uses function
`0x04`. Their request layout is:

```text
function_code       1 byte
starting_address    2 bytes
quantity_registers  2 bytes
```

The quantity is in `1..125`. The 16-bit starting address is the zero-based PDU
address. The requested inclusive range must not wrap the 16-bit address space.

A successful response is:

```text
function_code  1 byte, equal to the request function
byte_count     1 byte, equal to 2 * requested quantity
register_data  byte_count bytes
```

Each register occupies two bytes in most-significant-byte-first order. FC03 and
FC04 are different functions and different logical tables even when their
numeric address and returned words are equal.

## FC2B/MEI0E Read Device Identification

### Request

The request PDU is exactly:

```text
function_code       1 byte = 0x2B
mei_type            1 byte = 0x0E
read_device_id_code 1 byte = 0x01, 0x02, 0x03, or 0x04
object_id           1 byte
```

The access codes are:

| Code | Access |
| --- | --- |
| `0x01` | basic stream |
| `0x02` | regular stream |
| `0x03` | extended stream |
| `0x04` | one specific object |

The first transaction of a stream traversal requests object `0x00`. Each
continuation requests the exact `next_object_id` from the preceding response.
Individual access uses the requested object's identifier directly.

### Objects

| Range | Category |
| --- | --- |
| `0x00` | VendorName, mandatory basic object |
| `0x01` | ProductCode, mandatory basic object |
| `0x02` | MajorMinorRevision, mandatory basic object |
| `0x03` | VendorUrl, optional regular object |
| `0x04` | ProductName, optional regular object |
| `0x05` | ModelName, optional regular object |
| `0x06` | UserApplicationName, optional regular object |
| `0x07..0x7F` | reserved |
| `0x80..0xFF` | extended product-dependent objects |

Object values are length-delimited byte strings on the wire.

### Response

A successful response begins with:

```text
function_code       1 byte = 0x2B
mei_type            1 byte = 0x0E
read_device_id_code 1 byte = echoed request code
conformity_level    1 byte = 0x01, 0x02, 0x03, 0x81, 0x82, or 0x83
more_follows        1 byte = 0x00 or 0xFF
next_object_id      1 byte
number_of_objects   1 byte
```

It is followed by exactly `number_of_objects` tuples:

```text
object_id      1 byte
object_length  1 byte
object_value   object_length bytes
```

The low seven bits of conformity identify basic, regular, or extended
conformity. Bit 7 reports individual-access capability.

For individual access, exactly one object is returned, its identifier equals
the requested identifier, individual-access capability is reported,
`more_follows` is zero, and `next_object_id` is zero. An unknown individual
object returns exception code `0x02`.

For stream access, objects are returned in identifier order. A response too
large for one PDU is segmented. `more_follows == 0xFF` supplies the next cursor;
`more_follows == 0x00` has `next_object_id == 0x00`. An illegal Read Device ID
code returns exception code `0x03`. A device asked for a higher category than
its conformity responds according to its actual conformity.

For stream access, an object identifier unknown to the server is handled as a
request for object `0x00`, restarting at the beginning. Clients therefore need
bounded progress detection when following continuation cursors.

The maximum value bytes for a single object in a legal response is 244: the
253-byte PDU maximum minus the seven-byte response header and two-byte object
tuple header.

## Modbus TCP ADU

A Modbus TCP ADU is at most 260 bytes:

```text
transaction_id  2 bytes
protocol_id     2 bytes = 0
length          2 bytes = bytes following this field
unit_id         1 byte
pdu             length - 1 bytes
```

`length` includes the unit identifier and PDU and is in `2..254`. TCP is a byte
stream: the MBAP length delimits an ADU, independently of socket-read
boundaries. The server copies the request transaction identifier into the
response. The identifier pairs concurrent transactions on one connection.

## Modbus RTU ADU

An RTU ADU is at most 256 bytes:

```text
unit_address  1 byte
pdu           at most 253 bytes
crc16         2 bytes, low-order CRC byte first
```

Individually addressable units are `1..247`. Address `0` is broadcast;
`248..255` are reserved.

CRC is CRC-16/Modbus over `unit_address || pdu`: initial register `0xFFFF`,
reflected polynomial `0xA001`, least-significant bit processed first, and no
final XOR. The low-order CRC byte is transmitted first.

An RTU frame is one continuous character stream. Frames are separated by at
least 3.5 character times. A gap greater than 1.5 character times within a
frame makes that frame incomplete. At baud rates above 19,200, the serial-line
guide recommends fixed timers of 750 microseconds for t1.5 and 1,750
microseconds for t3.5.
