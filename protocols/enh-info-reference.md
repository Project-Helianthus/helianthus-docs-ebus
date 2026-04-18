# ENH INFO ID Reference

Detailed reference for the `INFO` command IDs used by the Enhanced (ENH) adapter
protocol. For the overall ENH framing, encoding, and command structure see
[`enh.md`](enh.md).

## Wire format recap

```text
Request:   <INFO(0x3)> <info_id>
Response:  <INFO(0x3)> <length_N>          (first frame)
           <INFO(0x3)> <data_byte_1>       (subsequent frames)
           ...
           <INFO(0x3)> <data_byte_N>       (final frame)
```

`length_N` excludes itself. An empty response has `length_N = 0` with no data
frames. Overlapping INFO requests on the same session MUST be serialized or rejected (see [enh.md §INFO Concurrency](enh.md#info-concurrency)). For portable behavior, a new INFO request SHOULD NOT be sent while a previous response is still streaming.

## Capability gating

Adapters advertise INFO support via `RESETTED` / `INIT` feature bit 0. The
version response (ID 0x00) further gates access to higher IDs:

| Gate | Condition | IDs enabled |
|------|-----------|-------------|
| Base | `features & 0x01` | 0x00 -- 0x05 |
| Bootloader | `version_len == 8` | + 0x06 |
| WiFi | `version_len >= 5 && jumpers & 0x08` | + 0x07 |

`version_len` is the response length for ID 0x00 (2, 5, or 8 bytes).

> **PIC16F15356 firmware note:** The current PIC firmware only validates that
> the INFO ID is within range (`< INFO_COUNT`). It does not enforce the
> features/version/jumper gating described above -- all IDs up to `INFO_COUNT`
> are serviced regardless of the version response length or jumper flags. The
> gating table above describes the intended protocol-level behavior; host
> software should not rely on firmware-side gating.

## ID 0x00 -- Version

| Offset | Field | Notes |
|--------|-------|-------|
| 0 | version | Firmware major version byte |
| 1 | features | Bit 0: INFO support |
| 2-3 | checksum | Big-endian firmware CRC (present when `len >= 5`) |
| 4 | jumpers | Hardware config flags (present when `len >= 5`) |
| 5 | bootloader_version | Bootloader major (present when `len == 8`) |
| 6-7 | bootloader_checksum | Big-endian bootloader CRC (present when `len == 8`) |

Valid response lengths: 2, 5, or 8 bytes only.

**Jumper flags** (byte 4):

| Bit | Flag | Meaning |
|-----|------|---------|
| 0 | enhanced | Always set for INFO-capable adapters |
| 1 | high_speed | High-speed bus mode |
| 2 | ethernet | Ethernet hardware |
| 3 | wifi | WiFi hardware (gates ID 0x07) |
| 4 | v3.1 | Adapter HW revision 3.1+ |
| 5 | soft_config | Software-configurable jumpers |

## ID 0x01 -- Hardware ID

Raw binary hardware identifier. Length and format are adapter-specific.

## ID 0x02 -- Hardware Config

Raw binary hardware configuration. Length and format are adapter-specific.

## ID 0x03 -- Temperature

| Offset | Field | Unit | Encoding |
|--------|-------|------|----------|
| 0-1 | temperature | 0.01 C | Big-endian signed 16-bit |

## ID 0x04 -- Supply Voltage

| Offset | Field | Unit | Encoding |
|--------|-------|------|----------|
| 0-1 | supply_voltage | 1 mV | Big-endian unsigned 16-bit |

## ID 0x05 -- Bus Voltage

| Offset | Field | Unit | Encoding |
|--------|-------|------|----------|
| 0 | max_voltage | 0.1 V | Unsigned byte (decivolts) |
| 1 | min_voltage | 0.1 V | Unsigned byte (decivolts) |

## ID 0x06 -- Reset Info

Protocol-level recommendation: query ID 0x00 (Version) first to determine availability of IDs 0x06 and 0x07 via the `version_len` and `jumpers` fields. Some firmware may respond to 0x06/0x07 without a prior 0x00 query, but callers should not rely on firmware-side enforcement.

Requires bootloader gate (`version_len == 8`).

| Offset | Field | Encoding |
|--------|-------|----------|
| 0 | cause_code | See table below |
| 1 | restart_count | Unsigned byte |

**Reset cause codes:**

| Code | Name |
|------|------|
| 1 | power_on |
| 2 | brown_out |
| 3 | watchdog |
| 4 | clear |
| 5 | external_reset |
| 6 | stack_overflow |
| 7 | memory_failure |
| other | unknown |

## ID 0x07 -- WiFi RSSI

Protocol-level recommendation: query ID 0x00 (Version) first to determine availability via the `version_len` and `jumpers` fields. Some firmware may respond without a prior 0x00 query, but callers should not rely on firmware-side enforcement.

Requires WiFi gate (`version_len >= 5 && jumpers & 0x08`).

| Offset | Field | Unit | Encoding |
|--------|-------|------|----------|
| 0 | rssi | dBm | Signed byte |

## Implementation references

- ebusgo transport types: `transport/adapter_info.go`
- ebusgo ENH transport: `transport/enh_transport.go`
- Gateway semantic model: `cmd/gateway/semantic_vaillant_adapter_info.go`
- Proxy identity cache: `internal/adapterproxy/adapter_info_cache.go`
