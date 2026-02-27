# VR90 Room Controller — Emulation Reference

This document covers the eBUS protocol details needed to emulate a Vaillant VR90 room controller (RCC) on the bus, as implemented in `helianthus-ebus-vdev`.

## Device Identity

| Field | Value | Notes |
|-------|-------|-------|
| Manufacturer | `0xB5` | Vaillant |
| Device ID | `"RC C "` | 5 bytes, space-padded |
| Software version | `0x0508` | Big-endian on wire |
| Hardware version | `0x6201` | Big-endian on wire |
| Identify command | PB=`0x07`, SB=`0x04` | Standard eBUS identify |

## RCC Address Pairs

VR90 uses Room Controller Circuit (RCC) address pairs. Each pair has a master address (for initiating) and a slave address (for responding to polls):

| Master | Slave | Notes |
|--------|-------|-------|
| `0x17` | `0x1C` | |
| `0x30` | `0x35` | |
| `0x37` | `0x3C` | |
| `0x70` | `0x75` | Common choice |
| `0x77` | `0x7C` | |
| `0xF0` | `0xF5` | |
| `0xF7` | `0xFC` | |

All master addresses are valid eBUS initiator addresses. The slave address is the master XOR `0x05`.

## B509 Protocol

The VR90 uses Vaillant's B509 extended register protocol:

- **Primary byte (PB):** `0xB5`
- **Secondary byte (SB):** `0x09`

### Read Operation

Master sends: `[0x0D, register, sub_register]`

Slave responds with the register value. Response format depends on the register type.

### Write Operation

Master sends: `[0x0E, register, sub_register, data...]`

Slave responds with acceptance (typically `[0x00]`).

### Scan ID Discovery

Master sends single-byte selectors `0x24`–`0x27` to read the device scan ID in 8-byte chunks:

| Selector | Scan ID offset | Bytes |
|----------|---------------|-------|
| `0x24` | 0–7 | 8 |
| `0x25` | 8–15 | 8 |
| `0x26` | 16–23 | 8 |
| `0x27` | 24–31 | 8 |

Response format: `[0x00, chunk_byte_0, ..., chunk_byte_7]` (9 bytes total, leading `0x00` status byte).

## Key Registers

### RoomTemp — `@ext(0x00, 0x00)`

The primary temperature register. Response data:

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0–1 | 2 | D2C (DATA2c) | Temperature in °C, little-endian, divisor 16 |
| 2 | 1 | UCH | Sensor status: `0x00`=OK, `0x55`=circuit fault |

**D2C encoding:** `int16(temp_celsius * 16)`, stored little-endian. Resolution: 1/16°C = 0.0625°C.

Example: 21.5°C → `21.5 * 16 = 344` → `0x0158` → wire bytes `[0x58, 0x01]`.

### Other Registers

| Register | Sub | Name | Notes |
|----------|-----|------|-------|
| `0x1F` | `0x00` | RoomTempOffset | Temperature correction offset |
| `0x20` | `0x00` | SelfWarming | Self-warming compensation |
| `0x22` | `0x00` | RoomTempHoliday | Holiday mode temperature |
| `0x36` | `0x00` | LcdContrast | Display contrast setting |
| `0x43` | `0x00` | HolidayPeriod | Holiday period configuration |

## Slave Wire Protocol

When a master polls the VR90's slave address, the response sequence is:

1. Master sends frame: `[SRC, DST, PB, SB, NN, DATA..., CRC]`
2. Slave validates CRC; if invalid → silence (no response)
3. Slave checks if `DST` matches its slave address; if not → silence
4. If addressed but cannot service → send `NACK` (`0xFF`)
5. If match → send `ACK` (`0x00`)
6. Build response: `[NN, DATA..., CRC]` where:
   - `NN` = response data length (1 byte, 0–255)
   - `DATA` = response payload
   - `CRC` = CRC8 over `[NN, DATA...]` (unescaped)
7. Escape response bytes for wire: `0xA9` → `[0xA9, 0x00]`, `0xAA` → `[0xA9, 0x01]`
8. Send escaped response bytes
9. Read master's ACK (best-effort)

## Emulation Jitter

To avoid the VRC700 detecting a perfectly stable synthetic temperature, the emulator applies slow-drift jitter:

- **Random walk:** ±1 D2C tick (0.0625°C) per poll cycle
- **Bounded:** total drift clamped to ±0.5°C from source temperature
- **D2C-quantized:** final value is always an exact D2C tick (`math.Round(temp * 16) / 16`)

This produces naturalistic temperature fluctuation that matches real sensor noise characteristics.
