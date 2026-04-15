# Brink 40xx Protocol Family (Heat Recovery Ventilation)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

`PB=0x40`, `SB=0xFF/0x91/0x90/0xA1/0xCB/0x22/0x50/0x80`.

## Status

**Comprehensive static extraction** from the Brink Service Tool
decompilation. Not yet live-validated on any eBUS bus.

This document covers 8 protocols, 89 sensor registers, 126 configurable
parameters, 7 device clusters, and 33 device variants. All information is
derived from service tool binary analysis.

Evidence labels:

- `PVYLETA_SENSOR`: pvyleta/ebusd-brink-hru `sensor_data.py`
- `PVYLETA_PARAM`: pvyleta/ebusd-brink-hru `param_data.py`
- `JOHN30_DEVICE`: john30/ebusd-configuration device entry for 0x3C

**Confidence:** HIGH for register names, types, ranges, defaults (service
tool data structures). MEDIUM for live eBUS wire behavior (framing, timing,
cluster-variant response differences) until bus captures validate.

---

## 1. Protocol Family Overview

The Brink 40xx family uses **Process Byte (PB) = 0x40** and a flat 1-byte
Secondary Byte (SB) space. All registers are addressed by a single 1-byte
ID with no group/instance hierarchy.

The self-describing 4050 read protocol is the defining feature of the
family: each ID returns five fields (current, min, max, step, default) in
a single response, eliminating the need for out-of-band metadata queries.

### Physical Addressing

Devices are expected on eBUS address **0x3C** (confirmed by
`JOHN30_DEVICE`). The initiator sends to 0x3C; the HRU device replies from
0x3C.

### Wire-Level Framing

All 40xx transactions follow standard eBUS framing:

```
[SYNC 0xAA] [QQ src] [ZZ dst=0x3C] [PB=0x40] [SB] [NN len] [data...] [CRC]
```

SB selects the sub-protocol (0xFF, 0x91, 0x90, 0xA1, 0xCB, 0x22, 0x50,
0x80). NN is the data length byte (excludes CRC). CRC is the standard
eBUS CRC over PB..data.

### Data Types

| Type | Wire width | Encoding | Notes |
|------|-----------|----------|-------|
| UCH | 1 byte | uint8, unsigned | |
| UIR | 2 bytes | uint16 little-endian | |
| SIR | 2 bytes | int16 little-endian | |
| ULR | 4 bytes | uint32 little-endian | |
| SIR(32) | 4 bytes | int32 little-endian | |
| STR:N | N bytes | ASCII, null-padded | |
| HEX:N | N bytes | raw opaque | |

**Dividers** are post-decode scaling factors, not part of the wire encoding.
`Div=10` means `physical_value = wire_integer / 10`. `Div=1000` is used for
flow rates in some peripherals.

---

## 2. Sub-Protocol Index

| PBSB | Short name | Direction | Purpose |
|------|-----------|-----------|---------|
| 0x40FF | factory_reset (`FactoryReset`) | Write | Destructive reset of all parameters to factory defaults |
| 0x4091 | reset_notifications (`ResetNotifications`) | Write | Clears active fault/notification queue |
| 0x4090 | error_history (`ErrorHistory`) | Read | Retrieves stored fault log from NVRAM |
| 0x40A1 | fan_mode_temporary (`FanModeTemporary`) | Write | Transient fan mode override (reverts on power cycle) |
| 0x40CB | fan_mode_persistent (`FanModePersistent`) | Write | Persistent fan mode selection (survives power cycles) |
| 0x4022 | sensor_status (`SensorStatus`) | Read | Live operational status (89 registers) |
| 0x4050 | parameter_read (`ParameterRead`) | Read | Self-describing parameter read (126 registers, 5-field response) |
| 0x4080 | parameter_write (`ParameterWrite`) | Write | Parameter write (126 registers, same IDs as 4050) |

---

## 3. Protocol Details

### 3.1 -- PBSB 0x40FF: Factory Reset

**Direction:** Initiator -> Target (write-only, no response data).

#### Wire Format

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0xFF |
| 2 | NN | 0x00 |
| 3 | CRC | computed |

#### Register Table

| ID | Name | Notes | Evidence |
|----|------|-------|----------|
| 0x00 | factory_reset (`FactoryReset`) | Triggers full parameter wipe | PVYLETA_PARAM |

#### Falsifiable Claims

- Writing 0x40FF with ID=0x00 to a Brink Renovent Excellent 300 at 0x3C
  resets flow_mode_1/2/3 to 100/150/225 m3/h respectively within one power
  cycle.

---

### 3.2 -- PBSB 0x4091: Reset Notifications

**Direction:** Initiator -> Target.

#### Wire Format

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0x91 |
| 2 | NN | 0x01 |
| 3 | ID | 0x00 |
| 4 | CRC | computed |

#### Register Table

| ID | Name | Notes | Evidence |
|----|------|-------|----------|
| 0x00 | reset_notifications (`ResetNotifications`) | Clears active notification flags; does not clear 4090 error history | PVYLETA_PARAM |

#### Falsifiable Claims

- Writing 0x4091 ID=0x00 clears all bits in the active notification
  register readable via 4022 IDs 0x1A-0x1F.
- It does NOT erase the persistent error log; a subsequent 0x4090 read
  should still return previously stored fault codes.

---

### 3.3 -- PBSB 0x4090: Error History

**Direction:** Initiator -> Target request; Target -> Initiator response.

#### Wire Format -- Request

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0x90 |
| 2 | NN | 0x01 |
| 3 | ID | 0x00 |
| 4 | CRC | computed |

#### Wire Format -- Response

The response payload structure is **not fully documented** (known gap -- see
Section 8, Gap 1). The device returns a variable-length record. Based on
partial decompilation evidence, each fault entry is expected to contain a
fault code byte and a timestamp or occurrence counter. Total response length
is device-dependent.

#### Register Table

| ID | Name | Notes | Evidence |
|----|------|-------|----------|
| 0x00 | error_history (`ErrorHistory`) | Returns fault log; exact byte structure is a known gap | PVYLETA_SENSOR |

---

### 3.4 -- PBSB 0x40A1: Fan Mode Temporary Override

**Direction:** Initiator -> Target.

#### Wire Format

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0xA1 |
| 2 | NN | 0x02 |
| 3 | ID | 0x00 |
| 4 | Value | FanMode enum (UCH) |
| 5 | CRC | computed |

#### Register Table

| ID | Name | Type | Notes | Evidence |
|----|------|------|-------|----------|
| 0x00 | fan_mode_temporary (`FanModeTemporary`) | UCH | FanMode enum; reverts on next power cycle | PVYLETA_PARAM |

#### Falsifiable Claims

- Writing 0x40A1 ID=0x00 Value=0x03 (Boost) should cause 4022 ID=0x01
  to read back 0x03 immediately.
- After a power cycle, 4022 ID=0x01 should return the persistent mode
  set by 0x40CB, not 0x03.

---

### 3.5 -- PBSB 0x40CB: Fan Mode Persistent Set

**Direction:** Initiator -> Target.

#### Wire Format

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0xCB |
| 2 | NN | 0x02 |
| 3 | ID | 0x00 |
| 4 | Value | FanMode enum (UCH) |
| 5 | CRC | computed |

#### Register Table

| ID | Name | Type | Notes | Evidence |
|----|------|------|-------|----------|
| 0x00 | fan_mode_persistent (`FanModePersistent`) | UCH | FanMode enum; persists across power cycles | PVYLETA_PARAM |

#### Falsifiable Claims

- Writing 0x40CB ID=0x00 Value=0x01 (Low) followed by a power cycle
  should result in 4022 ID=0x01 reading back 0x01.
- The value 0x40CB ID=0x00 = 0x00 (Holiday) should cause
  inlet_fan_speed (4022 ID=0x02) to drop to zero or near-zero RPM within
  30 seconds.

---

### 3.6 -- PBSB 0x4022: Sensor / Status Read

**Purpose:** Live operational status: fan speeds, temperatures, pressures,
flows, CO2 levels, filter state, frost state, bypass state.

**Direction:** Initiator -> Target request; Target -> Initiator response.

#### Wire Format -- Request

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0x22 |
| 2 | NN | 0x01 |
| 3 | ID | 0x00-0x58 |
| 4 | CRC | computed |

#### Wire Format -- Response

Response NN and payload width depend on the ID's declared type:

- UCH ID: NN=0x01, 1 data byte
- UIR/SIR ID: NN=0x02, 2 data bytes (LE)
- ULR/SIR(32) ID: NN=0x04, 4 data bytes (LE)
- STR:13 ID: NN=0x0D, 13 ASCII bytes
- STR:12 ID: NN=0x0C, 12 ASCII bytes

#### Complete 4022 Register Table (89 registers)

**Identification Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x00 | software_version (`SoftwareVersion`) | STR:13 | -- | -- | All | PVYLETA_SENSOR |
| 0x4E | firmware_date (`FirmwareDate`) | STR:13 | -- | -- | All | PVYLETA_SENSOR |
| 0x4F | hardware_version (`HardwareVersion`) | UCH | 1 | -- | All | PVYLETA_SENSOR |
| 0x50 | hardware_sub_version (`HardwareSubVersion`) | UCH | 1 | -- | All | PVYLETA_SENSOR |
| 0x51 | serial_number (`SerialNumber`) | STR:12 | -- | -- | 1,2,3 | PVYLETA_SENSOR |
| 0x52 | model_name (`ModelName`) | STR:13 | -- | -- | All | PVYLETA_SENSOR |
| 0x53 | postal_code (`PostalCode`) | STR:7 | -- | -- | 1,2,3 | PVYLETA_SENSOR |
| 0x54 | installation_date (`InstallationDate`) | STR:11 | -- | -- | 1,2,3 | PVYLETA_SENSOR |

**Fan Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x01 | fan_mode (`FanMode`) | UIR | 1 | enum | 1,2,3,4,5 | PVYLETA_SENSOR |
| 0x02 | inlet_fan_speed (`InletFanSpeed`) | UIR | 1 | rpm | 1,2,3,5 | PVYLETA_SENSOR |
| 0x03 | outlet_fan_speed (`OutletFanSpeed`) | UIR | 1 | rpm | 1,2,5 | PVYLETA_SENSOR |
| 0x04 | inlet_fan_speed_setpoint (`InletFanSpeedSetpoint`) | UIR | 1 | rpm | 1,2,3,5 | PVYLETA_SENSOR |
| 0x05 | outlet_fan_speed_setpoint (`OutletFanSpeedSetpoint`) | UIR | 1 | rpm | 1,2,5 | PVYLETA_SENSOR |

**Flow Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x06 | inlet_fan_flow (`InletFanFlow`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x0B | inlet_flow (`InletFlow`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x0C | outlet_flow (`OutletFlow`) | UIR | 1 | m3/h | 1,2,5 | PVYLETA_SENSOR |
| 0x0D | inlet_flow_setpoint (`InletFlowSetpoint`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x12 | fan_mode_0_flow (`FanMode0Flow`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x13 | fan_mode_1_flow (`FanMode1Flow`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x27 | outlet_fan_flow (`OutletFanFlow`) | UIR | 1 | m3/h | 1,2,5 | PVYLETA_SENSOR |
| 0x28 | outlet_flow_setpoint (`OutletFlowSetpoint`) | UIR | 1 | m3/h | 1,2,5 | PVYLETA_SENSOR |
| 0x40 | fan_mode_2_flow (`FanMode2Flow`) | UIR | 1 | m3/h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x41 | fan_mode_3_flow (`FanMode3Flow`) | UIR | 1 | m3/h | 1,2,5 | PVYLETA_SENSOR |

**Temperature Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x07 | inside_temperature (`InsideTemperature`) | SIR | 10 | deg C | 1,2,3,4,5 | PVYLETA_SENSOR |
| 0x08 | outside_temperature (`OutsideTemperature`) | SIR | 10 | deg C | 1,2,3,5 | PVYLETA_SENSOR |
| 0x09 | supply_temperature (`SupplyTemperature`) | SIR | 10 | deg C | 1,2,3,5 | PVYLETA_SENSOR |
| 0x0A | exhaust_temperature (`ExhaustTemperature`) | SIR | 10 | deg C | 1,2 | PVYLETA_SENSOR |
| 0x11 | preheater_temp (`PreheaterTemp`) | SIR | 10 | deg C | 1,2,3 | PVYLETA_SENSOR |
| 0x42 | supply_temp_post_bypass (`SupplyTempPostBypass`) | SIR | 10 | deg C | 1,2 | PVYLETA_SENSOR |
| 0x43 | exhaust_temp_post_he (`ExhaustTempPostHE`) | SIR | 10 | deg C | 1,2 | PVYLETA_SENSOR |

**Pressure Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x14 | pressure_inlet (`PressureInlet`) | UIR | 10 | Pa | 1,2,3,5 | PVYLETA_SENSOR |
| 0x15 | pressure_outlet (`PressureOutlet`) | UIR | 10 | Pa | 1,2,5 | PVYLETA_SENSOR |

**Bypass & Preheater Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x0E | bypass_status (`BypassStatus`) | UIR | 1 | enum | 1,2,3 | PVYLETA_SENSOR |
| 0x0F | preheater_status (`PreheaterStatus`) | UIR | 1 | enum | 1,2,3 | PVYLETA_SENSOR |
| 0x10 | preheater_duty_cycle (`PreheaterDutyCycle`) | UIR | 1 | % | 1,2,3 | PVYLETA_SENSOR |

**Frost & Filter Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x16 | frost_status (`FrostStatus`) | UIR | 1 | enum | 1,2,3,4,5 | PVYLETA_SENSOR |
| 0x17 | frost_bypass (`FrostBypass`) | UIR | 1 | enum | 1,2,3 | PVYLETA_SENSOR |
| 0x18 | filter_status (`FilterStatus`) | UIR | 1 | enum | 1,2,3,5 | PVYLETA_SENSOR |
| 0x19 | filter_hours (`FilterHours`) | ULR | 1 | h | 1,2,3,5 | PVYLETA_SENSOR |

**Notification Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x1A | notification_flags_0 (`NotificationFlags0`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x1B | notification_flags_1 (`NotificationFlags1`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x1C | notification_flags_2 (`NotificationFlags2`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x1D | notification_flags_3 (`NotificationFlags3`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x1E | notification_flags_4 (`NotificationFlags4`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x1F | notification_flags_5 (`NotificationFlags5`) | UCH | 1 | bitmask | All | PVYLETA_SENSOR |
| 0x57 | notification_count (`NotificationCount`) | UIR | 1 | count | All | PVYLETA_SENSOR |
| 0x58 | active_notification_code (`ActiveNotificationCode`) | UIR | 1 | code | All | PVYLETA_SENSOR |

**Humidity Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x20 | relative_humidity (`RelativeHumidity`) | SIR | 10 | % | 1,2,3 | PVYLETA_SENSOR |
| 0x21 | absolute_humidity (`AbsoluteHumidity`) | SIR | 10 | g/m3 | 1,2 | PVYLETA_SENSOR |

**Flair-Only Registers (Cluster 2)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x22 | fan_inlet_temp (`FanInletTemp`) | SIR | 10 | deg C | 2 | PVYLETA_SENSOR |
| 0x23 | fan_outlet_temp (`FanOutletTemp`) | SIR | 10 | deg C | 2 | PVYLETA_SENSOR |
| 0x24 | relay_output (`RelayOutput`) | UCH | 1 | bitmask | 2 | PVYLETA_SENSOR |
| 0x25 | analogue_output (`AnalogueOutput`) | UIR | 10 | V | 2 | PVYLETA_SENSOR |
| 0x26 | analogue_input (`AnalogueInput`) | UIR | 10 | V | 2 | PVYLETA_SENSOR |

**CO2 Sensor Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x29 | co2_sensor_1_value (`CO2Sensor1Value`) | UIR | 1 | ppm | 1,2 | PVYLETA_SENSOR |
| 0x2A | co2_sensor_1_status (`CO2Sensor1Status`) | UIR | 1 | enum | 1,2 | PVYLETA_SENSOR |
| 0x2B | co2_sensor_2_value (`CO2Sensor2Value`) | UIR | 1 | ppm | 1,2 | PVYLETA_SENSOR |
| 0x2C | co2_sensor_2_status (`CO2Sensor2Status`) | UIR | 1 | enum | 1,2 | PVYLETA_SENSOR |
| 0x2D | co2_sensor_3_value (`CO2Sensor3Value`) | UIR | 1 | ppm | 1 | PVYLETA_SENSOR |
| 0x2E | co2_sensor_3_status (`CO2Sensor3Status`) | UIR | 1 | enum | 1 | PVYLETA_SENSOR |
| 0x2F | co2_sensor_4_value (`CO2Sensor4Value`) | UIR | 1 | ppm | 1 | PVYLETA_SENSOR |
| 0x30 | co2_sensor_4_status (`CO2Sensor4Status`) | UIR | 1 | enum | 1 | PVYLETA_SENSOR |

**DA70-Only Registers (Cluster 3)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x31 | da70_preset (`DA70Preset`) | UCH | 1 | enum | 3 | PVYLETA_SENSOR |
| 0x32 | da70_co2_value (`DA70CO2Value`) | UIR | 1 | ppm | 3 | PVYLETA_SENSOR |
| 0x33 | da70_co2_status (`DA70CO2Status`) | UIR | 1 | enum | 3 | PVYLETA_SENSOR |

**Elan-Only Registers (Cluster 4)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x34 | elan_setpoint_temp (`ElanSetpointTemp`) | SIR | 10 | deg C | 4 | PVYLETA_SENSOR |
| 0x35 | elan_current_temp (`ElanCurrentTemp`) | SIR | 10 | deg C | 4 | PVYLETA_SENSOR |
| 0x36 | elan_heat_output (`ElanHeatOutput`) | UCH | 1 | % | 4 | PVYLETA_SENSOR |
| 0x37 | elan_fan_speed (`ElanFanSpeed`) | UIR | 1 | rpm | 4 | PVYLETA_SENSOR |

**ConstRPM-Only Registers (Cluster 5)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x38 | const_rpm_setpoint (`ConstRPMSetpoint`) | UIR | 1 | % | 5 | PVYLETA_SENSOR |
| 0x39 | const_rpm_actual (`ConstRPMActual`) | UIR | 1 | % | 5 | PVYLETA_SENSOR |

**MRC-Only Registers (Cluster 6)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x3A | mrc_zone_1_co2 (`MRCZone1CO2`) | UIR | 1 | ppm | 6 | PVYLETA_SENSOR |
| 0x3B | mrc_zone_2_co2 (`MRCZone2CO2`) | UIR | 1 | ppm | 6 | PVYLETA_SENSOR |
| 0x3C | mrc_zone_3_co2 (`MRCZone3CO2`) | UIR | 1 | ppm | 6 | PVYLETA_SENSOR |
| 0x3D | mrc_zone_4_co2 (`MRCZone4CO2`) | UIR | 1 | ppm | 6 | PVYLETA_SENSOR |

**Valve-Only Registers (Cluster 7)**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x3E | valve_position (`ValvePosition`) | UCH | 1 | % | 7 | PVYLETA_SENSOR |
| 0x3F | valve_status (`ValveStatus`) | UCH | 1 | enum | 7 | PVYLETA_SENSOR |

**Efficiency & Power Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x44 | heat_exchanger_efficiency (`HeatExchangerEfficiency`) | UIR | 10 | % | 1,2 | PVYLETA_SENSOR |
| 0x45 | power_consumption_inlet (`PowerConsumptionInlet`) | UIR | 1 | W | 1,2,5 | PVYLETA_SENSOR |
| 0x46 | power_consumption_outlet (`PowerConsumptionOutlet`) | UIR | 1 | W | 1,2,5 | PVYLETA_SENSOR |

**Operating Hours Registers**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x47 | operating_hours_total (`OperatingHoursTotal`) | ULR | 1 | h | 1,2,3,4,5 | PVYLETA_SENSOR |
| 0x48 | operating_hours_fan_mode_0 (`OperatingHoursFanMode0`) | ULR | 1 | h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x49 | operating_hours_fan_mode_1 (`OperatingHoursFanMode1`) | ULR | 1 | h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x4A | operating_hours_fan_mode_2 (`OperatingHoursFanMode2`) | ULR | 1 | h | 1,2,3,5 | PVYLETA_SENSOR |
| 0x4B | operating_hours_fan_mode_3 (`OperatingHoursFanMode3`) | ULR | 1 | h | 1,2,5 | PVYLETA_SENSOR |
| 0x4C | operating_hours_bypass_open (`OperatingHoursBypassOpen`) | ULR | 1 | h | 1,2,3 | PVYLETA_SENSOR |
| 0x4D | operating_hours_preheater (`OperatingHoursPreheater`) | ULR | 1 | h | 1,2,3 | PVYLETA_SENSOR |

**Lifetime Counters**

| ID | Name | Type | Div | Unit | Clusters | Evidence |
|----|------|------|-----|------|----------|---------|
| 0x55 | bypass_openings (`BypassOpenings`) | ULR | 1 | count | 1,2,3 | PVYLETA_SENSOR |
| 0x56 | frost_events (`FrostEvents`) | ULR | 1 | count | 1,2,3,4,5 | PVYLETA_SENSOR |

#### Falsifiable Claims for 4022

- Reading 4022 ID=0x07 on a Brink Excellent 300 at 0x3C should return
  a SIR/10 value representing indoor temperature (e.g. wire 0x00C8 = 200
  -> 20.0 deg C).
- Reading 4022 ID=0x01 on a device in Normal ventilation should return
  UIR = 0x0002.
- Reading 4022 ID=0x16 on a device where outdoor temperature > 5 deg C
  should return UIR = 0x0000 (Normal, no frost).
- Reading 4022 ID=0x18 on a device whose filter_hours (ID=0x19) exceeds
  the configured filter_dirty_hours (4050 ID=0x0A) should return UIR =
  0x0001 (Dirty).

---

### 3.7 -- PBSB 0x4050: Parameter Read (Self-Describing)

**Purpose:** Reads configurable parameters. Each response contains five
fields: current value, minimum, maximum, step, and default.

**Direction:** Initiator -> Target request; Target -> Initiator response.

This is the **defining protocol** of the Brink 40xx family. The
self-describing five-field response means a controller can discover the
full parameter space at runtime without out-of-band metadata -- a capability
absent in Vaillant B524 without a separate opcode 0x01 query.

#### Wire Format -- Request

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0x50 |
| 2 | NN | 0x01 |
| 3 | ID | 0x01-0xB9 |
| 4 | CRC | computed |

#### Wire Format -- Response (5-field structure)

For a UIR-typed parameter:

| Bytes | Field | Type | Notes |
|-------|-------|------|-------|
| 0-1 | CurrentValue | UIR | Current configured value |
| 2-3 | MinValue | UIR | Minimum allowed |
| 4-5 | MaxValue | UIR | Maximum allowed |
| 6-7 | StepSize | UIR | Increment granularity |
| 8-9 | DefaultValue | UIR | Factory default |

Total NN = 0x0A (10 bytes) for UIR parameters. For SIR parameters, fields
are 2 bytes signed LE each (same NN=0x0A). Peripheral parameters with wider
types use the same five-field structure with the appropriate per-field width.

#### Complete 4050 Parameter Table (126 parameters)

**Core Flow Parameters (IDs 0x01-0x05)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x01 | flow_mode_1 (`FlowMode1`) | UIR | 1 | m3/h | 50-300 | 100 | PVYLETA_PARAM |
| 0x02 | flow_mode_2 (`FlowMode2`) | UIR | 1 | m3/h | 50-300 | 150 | PVYLETA_PARAM |
| 0x03 | flow_mode_3 (`FlowMode3`) | UIR | 1 | m3/h | 50-300 | 225 | PVYLETA_PARAM |
| 0x04 | bypass_open_temp (`BypassOpenTemp`) | SIR | 10 | deg C | 15-35 | 24.0 | PVYLETA_PARAM |
| 0x05 | bypass_close_temp (`BypassCloseTemp`) | SIR | 10 | deg C | 10-30 | 12.0 | PVYLETA_PARAM |

**Bypass & Preheater (IDs 0x06-0x15)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x06 | bypass_temp_high (`BypassTempHigh`) | SIR | 10 | deg C | 20-40 | 27.0 | PVYLETA_PARAM |
| 0x07 | bypass_temp_low (`BypassTempLow`) | SIR | 10 | deg C | 5-20 | 12.0 | PVYLETA_PARAM |
| 0x08 | preheater_frost_temp (`PreheaterFrostTemp`) | SIR | 10 | deg C | -15-5 | 0.0 | PVYLETA_PARAM |
| 0x09 | preheater_max_temp (`PreheaterMaxTemp`) | SIR | 10 | deg C | 0-40 | 25.0 | PVYLETA_PARAM |
| 0x0A | filter_dirty_hours (`FilterDirtyHours`) | UIR | 1 | h | 500-8760 | 2160 | PVYLETA_PARAM |
| 0x0B | filter_reset_hours (`FilterResetHours`) | UIR | 1 | h | 0-8760 | 0 | PVYLETA_PARAM |
| 0x0C | bypass_min_outside_temp (`BypassMinOutsideTemp`) | SIR | 10 | deg C | 0-30 | 16.0 | PVYLETA_PARAM |
| 0x0D | bypass_min_inside_temp (`BypassMinInsideTemp`) | SIR | 10 | deg C | 15-30 | 22.0 | PVYLETA_PARAM |
| 0x0E | bypass_hysteresis (`BypassHysteresis`) | SIR | 10 | deg C | 0-5 | 2.0 | PVYLETA_PARAM |
| 0x0F | preheater_enable (`PreheaterEnable`) | UCH | 1 | bool | 0-1 | 1 | PVYLETA_PARAM |
| 0x10 | bypass_enable (`BypassEnable`) | UCH | 1 | bool | 0-1 | 1 | PVYLETA_PARAM |
| 0x11 | frost_bypass_enable (`FrostBypassEnable`) | UCH | 1 | bool | 0-1 | 1 | PVYLETA_PARAM |
| 0x12 | fan_balance_enable (`FanBalanceEnable`) | UCH | 1 | bool | 0-1 | 1 | PVYLETA_PARAM |
| 0x13 | mode_0_flow_inlet (`Mode0FlowInlet`) | UIR | 1 | m3/h | 0-50 | 50 | PVYLETA_PARAM |
| 0x14 | mode_0_flow_outlet (`Mode0FlowOutlet`) | UIR | 1 | m3/h | 0-50 | 50 | PVYLETA_PARAM |
| 0x15 | outlet_flow_mode_1 (`OutletFlowMode1`) | UIR | 1 | m3/h | 50-300 | 100 | PVYLETA_PARAM |

**Fan Flow Continuations (IDs 0x16-0x23)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x16 | outlet_flow_mode_2 (`OutletFlowMode2`) | UIR | 1 | m3/h | 50-300 | 150 | PVYLETA_PARAM |
| 0x17 | outlet_flow_mode_3 (`OutletFlowMode3`) | UIR | 1 | m3/h | 50-300 | 225 | PVYLETA_PARAM |
| 0x18 | max_flow_inlet (`MaxFlowInlet`) | UIR | 1 | m3/h | 50-400 | 300 | PVYLETA_PARAM |
| 0x19 | max_flow_outlet (`MaxFlowOutlet`) | UIR | 1 | m3/h | 50-400 | 300 | PVYLETA_PARAM |
| 0x1A | min_flow_inlet (`MinFlowInlet`) | UIR | 1 | m3/h | 10-100 | 50 | PVYLETA_PARAM |
| 0x1B | min_flow_outlet (`MinFlowOutlet`) | UIR | 1 | m3/h | 10-100 | 50 | PVYLETA_PARAM |
| 0x1C | flow_balance_offset (`FlowBalanceOffset`) | SIR | 1 | m3/h | -50-50 | 0 | PVYLETA_PARAM |
| 0x1D | speed_control_p (`SpeedControlP`) | UIR | 1 | -- | 1-100 | 20 | PVYLETA_PARAM |
| 0x1E | speed_control_i (`SpeedControlI`) | UIR | 1 | -- | 1-200 | 60 | PVYLETA_PARAM |
| 0x1F | speed_control_d (`SpeedControlD`) | UIR | 1 | -- | 0-100 | 0 | PVYLETA_PARAM |
| 0x20 | pressure_mode (`PressureMode`) | UCH | 1 | enum | 0-2 | 0 | PVYLETA_PARAM |
| 0x21 | flow_mode_0 (`FlowMode0`) | SIR | 1 | m3/h | 0-50 | 50 | PVYLETA_PARAM |
| 0x22 | frost_start_temp (`FrostStartTemp`) | SIR | 10 | deg C | -5-5 | 0.0 | PVYLETA_PARAM |
| 0x23 | frost_stop_temp (`FrostStopTemp`) | SIR | 10 | deg C | -5-5 | 2.0 | PVYLETA_PARAM |

**Frost & Filter Continuations (IDs 0x24-0x33)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x24 | frost_bypass_mode (`FrostBypassMode`) | UCH | 1 | enum | 0-3 | 0 | PVYLETA_PARAM |
| 0x25 | frost_preheater_mode (`FrostPreheaterMode`) | UCH | 1 | enum | 0-2 | 0 | PVYLETA_PARAM |
| 0x26 | frost_fan_speed_reduction (`FrostFanSpeedReduction`) | UIR | 1 | % | 0-100 | 50 | PVYLETA_PARAM |
| 0x27 | frost_recovery_temp (`FrostRecoveryTemp`) | SIR | 10 | deg C | 0-10 | 5.0 | PVYLETA_PARAM |
| 0x28 | bypass_motor_time (`BypassMotorTime`) | UIR | 1 | s | 30-300 | 150 | PVYLETA_PARAM |
| 0x29 | bypass_motor_power (`BypassMotorPower`) | UIR | 1 | % | 10-100 | 100 | PVYLETA_PARAM |
| 0x2A | preheater_hysteresis (`PreheaterHysteresis`) | SIR | 10 | deg C | 0-5 | 1.0 | PVYLETA_PARAM |
| 0x2B | preheater_over_temp (`PreheaterOverTemp`) | SIR | 10 | deg C | 20-60 | 40.0 | PVYLETA_PARAM |
| 0x2C | humidity_enable (`HumidityEnable`) | UCH | 1 | bool | 0-1 | 0 | PVYLETA_PARAM |
| 0x2D | humidity_high_threshold (`HumidityHighThreshold`) | SIR | 10 | % | 50-90 | 70.0 | PVYLETA_PARAM |
| 0x2E | humidity_low_threshold (`HumidityLowThreshold`) | SIR | 10 | % | 30-60 | 40.0 | PVYLETA_PARAM |
| 0x2F | humidity_boost_flow (`HumidityBoostFlow`) | UIR | 1 | m3/h | 50-300 | 200 | PVYLETA_PARAM |
| 0x30 | bypass_temp_hyst (`BypassTempHyst`) | SIR | 10 | deg C | 0-5 | 2.0 | PVYLETA_PARAM |
| 0x31 | bypass_night_cooling_enable (`BypassNightCoolingEnable`) | UCH | 1 | bool | 0-1 | 1 | PVYLETA_PARAM |
| 0x32 | night_cooling_start_hour (`NightCoolingStartHour`) | UCH | 1 | h | 0-23 | 22 | PVYLETA_PARAM |
| 0x33 | night_cooling_end_hour (`NightCoolingEndHour`) | UCH | 1 | h | 0-23 | 7 | PVYLETA_PARAM |

**CO2 Limits Block (IDs 0x34-0x3B)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x34 | co2_limit_sensor_1_low (`CO2LimitSensor1Low`) | UIR | 1 | ppm | 400-2000 | 400 | PVYLETA_PARAM |
| 0x35 | co2_limit_sensor_1_high (`CO2LimitSensor1High`) | UIR | 1 | ppm | 400-2000 | 1200 | PVYLETA_PARAM |
| 0x36 | co2_limit_sensor_2_low (`CO2LimitSensor2Low`) | UIR | 1 | ppm | 400-2000 | 400 | PVYLETA_PARAM |
| 0x37 | co2_limit_sensor_2_high (`CO2LimitSensor2High`) | UIR | 1 | ppm | 400-2000 | 1200 | PVYLETA_PARAM |
| 0x38 | co2_limit_sensor_3_low (`CO2LimitSensor3Low`) | UIR | 1 | ppm | 400-2000 | 400 | PVYLETA_PARAM |
| 0x39 | co2_limit_sensor_3_high (`CO2LimitSensor3High`) | UIR | 1 | ppm | 400-2000 | 1200 | PVYLETA_PARAM |
| 0x3A | co2_limit_sensor_4_low (`CO2LimitSensor4Low`) | UIR | 1 | ppm | 400-2000 | 400 | PVYLETA_PARAM |
| 0x3B | co2_limit_sensor_4_high (`CO2LimitSensor4High`) | UIR | 1 | ppm | 400-2000 | 1200 | PVYLETA_PARAM |

**CO2 / DA70 / Elan / ConstRPM / Humidity (IDs 0x3C-0x4F)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0x3C | co2_boost_flow (`CO2BoostFlow`) | UIR | 1 | m3/h | 50-300 | 225 | PVYLETA_PARAM |
| 0x3D | co2_control_enable (`CO2ControlEnable`) | UCH | 1 | bool | 0-1 | 0 | PVYLETA_PARAM |
| 0x3E | co2_sensor_count (`CO2SensorCount`) | UCH | 1 | count | 0-4 | 0 | PVYLETA_PARAM |
| 0x3F | da70_preset_count (`DA70PresetCount`) | UCH | 1 | count | 2-5 | 3 | PVYLETA_PARAM |
| 0x40 | da70_preset_1_flow (`DA70Preset1Flow`) | UIR | 1 | m3/h | 10-200 | 50 | PVYLETA_PARAM |
| 0x41 | da70_preset_2_flow (`DA70Preset2Flow`) | UIR | 1 | m3/h | 10-200 | 100 | PVYLETA_PARAM |
| 0x42 | da70_preset_3_flow (`DA70Preset3Flow`) | UIR | 1 | m3/h | 10-200 | 150 | PVYLETA_PARAM |
| 0x43 | da70_preset_4_flow (`DA70Preset4Flow`) | UIR | 1 | m3/h | 10-200 | 175 | PVYLETA_PARAM |
| 0x44 | da70_preset_5_flow (`DA70Preset5Flow`) | UIR | 1 | m3/h | 10-200 | 200 | PVYLETA_PARAM |
| 0x45 | elan_setpoint (`ElanSetpoint`) | SIR | 10 | deg C | 15-30 | 21.0 | PVYLETA_PARAM |
| 0x46 | elan_hysteresis (`ElanHysteresis`) | SIR | 10 | deg C | 0-5 | 1.5 | PVYLETA_PARAM |
| 0x47 | elan_max_power (`ElanMaxPower`) | UIR | 1 | % | 10-100 | 100 | PVYLETA_PARAM |
| 0x48 | const_rpm_setpoint_mode_1 (`ConstRPMSetpointMode1`) | UIR | 1 | % | 10-100 | 40 | PVYLETA_PARAM |
| 0x49 | const_rpm_setpoint_mode_2 (`ConstRPMSetpointMode2`) | UIR | 1 | % | 10-100 | 60 | PVYLETA_PARAM |
| 0x4A | const_rpm_setpoint_mode_3 (`ConstRPMSetpointMode3`) | UIR | 1 | % | 10-100 | 80 | PVYLETA_PARAM |
| 0x4B | const_rpm_setpoint_mode_0 (`ConstRPMSetpointMode0`) | UIR | 1 | % | 0-30 | 20 | PVYLETA_PARAM |
| 0x4C | humidity_control_enable (`HumidityControlEnable`) | UCH | 1 | bool | 0-1 | 0 | PVYLETA_PARAM |
| 0x4D | humidity_boost_enable (`HumidityBoostEnable`) | UCH | 1 | bool | 0-1 | 0 | PVYLETA_PARAM |
| 0x4E | frost_start_temp_alt (`FrostStartTemp`) | SIR | 10 | deg C | -1.5-1.5 | 0.0 | PVYLETA_PARAM |
| 0x4F | frost_stop_offset (`FrostStopOffset`) | SIR | 10 | deg C | 0-5 | 2.0 | PVYLETA_PARAM |

**Reserved Range (IDs 0x50-0x7F)**

IDs 0x50-0x7F are not assigned in the decompilation.

**eBUS Addressing Block (IDs 0xD0-0xD3)**

| ID | Name | Type | Div | Unit | Range | Default | Evidence |
|----|------|------|-----|------|-------|---------|---------|
| 0xD0 | ebus_address (`EbusAddress`) | UIR | 1 | -- | 0-254 | 0x3C | PVYLETA_PARAM |
| 0xD1 | ebus_master_address (`EbusMasterAddress`) | UIR | 1 | -- | 0-254 | 0x00 | PVYLETA_PARAM |
| 0xD2 | ebus_speed (`EbusSpeed`) | UIR | 1 | baud | varies | 2400 | PVYLETA_PARAM |
| 0xD3 | ebus_protocol_version (`EbusProtocolVersion`) | UIR | 1 | -- | 1-2 | 1 | PVYLETA_PARAM |

**ValveT01 Block (IDs 0x80-0x92)**

19 parameters for Valve T01 peripheral. Individual sub-ID assignments are
not fully resolved from decompilation (known gap -- see Section 8, Gap 3).

**MRC MultiRoomCtrl Block (IDs 0xA0-0xB9)**

26 parameters for MRC peripheral. Individual sub-ID assignments are not
fully resolved from decompilation (known gap -- see Section 8, Gap 4).

#### Falsifiable Claims for 4050

- Reading 4050 ID=0x01 on a factory-default Brink Excellent 300 should
  return a 10-byte response with CurrentValue=100, Min=50, Max=300,
  Step=1 (all UIR/LE), Default=100.
- Reading 4050 ID=0x04 on a factory-default device should return
  CurrentValue=240 (wire), Min=150, Max=350, Step=5 (all UIR/LE, Div=10
  -> 24.0 deg C, 15.0 deg C, 35.0 deg C, 0.5 deg C).
- The 5-field response for a UIR parameter always has NN=0x0A (10 bytes).

---

### 3.8 -- PBSB 0x4080: Parameter Write

**Purpose:** Writes configurable parameters. Uses identical IDs to 4050.
The write takes a single value, not the five-field structure.

**Direction:** Initiator -> Target.

#### Wire Format

| Byte | Field | Value |
|------|-------|-------|
| 0 | PB | 0x40 |
| 1 | SB | 0x80 |
| 2 | NN | 0x03 (UIR) or 0x02 (UCH) |
| 3 | ID | same as 4050 |
| 4-N | Value | type-width bytes LE |
| N+1 | CRC | computed |

No range enforcement is performed at the wire level; the device silently
clamps or rejects out-of-range values. Use 4050 to query min/max before
writing.

#### Register Table

Mirrors the 4050 table exactly (126 IDs, same names, types, and ranges).
Not duplicated here.

#### Falsifiable Claims for 4080

- Writing 4080 ID=0x0A value=4320 (UIR/LE) sets filter_dirty_hours to
  4320 h; subsequent 4050 ID=0x0A should return CurrentValue=4320.
- Writing 4080 ID=0x01 value=49 (below Min=50) should either be rejected
  with NACK or clamped to 50 on readback.
- Writing 4080 ID=0xD0 value=0x3C sets the device eBUS address to 0x3C
  (address change takes effect after power cycle per spec).

---

## 4. Device Clusters (7 total)

### Cluster Definitions

**Cluster 1 -- Renovent**

Models: Excellent 180 / 300 / 400, Sky 150+ / 200+ / 300+, CWL 180 / 300 /
400, Vitovent 200-W, Vitovent 300-C.

Signature features: 2 fans (inlet + outlet), bypass damper, preheater, up
to 4 CO2 sensors, full humidity sensors.

**Cluster 2 -- Flair**

Models: Flair 225 / 325 / 400, Vitovent 300-W HE35/HE45 variants.

Signature features: all Renovent capabilities + dedicated fan temperature
sensors (IDs 0x22-0x23), relay output (0x24), analogue I/O (0x25-0x26).

**Cluster 3 -- DA70 (DecentralAir70)**

Models: DecentralAir 70.

Signature features: single fan, 5 configurable flow presets, single CO2
sensor, compact bypass.

**Cluster 4 -- Elan**

Models: Elan4, Elan10.

Signature features: heat-only operation (no cooling/bypass),
temperature-controlled, no flow-volume feedback. FanMode enum differs --
see Section 5.

**Cluster 5 -- ConstRPM (ConstantRPM400)**

Models: ConstantRPM 400.

Signature features: RPM% control instead of volumetric m3/h setpoints.
inlet_flow/outlet_flow IDs return zero or 0xFFFF -- not meaningful for
this cluster.

**Cluster 6 -- MRC (MultiRoomCtrlT01)**

Models: MultiRoomCtrl T01.

Signature features: peripheral zone CO2 controller. Reduced register set
(software version + model name + zone CO2 values only). Controlled by the
main HRU; does not accept fan mode writes.

**Cluster 7 -- Valve (ValveT01)**

Models: Valve T01.

Signature features: motorized damper peripheral. Exposes only valve position
(%) and valve status enum. Accepts position setpoint via 4080 ID=0x3E.

### Cluster Register Availability Matrix

| Register Group | Renovent (1) | Flair (2) | DA70 (3) | Elan (4) | ConstRPM (5) | MRC (6) | Valve (7) |
|---------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| FanMode (0x01) | Y | Y | Y | Y | Y | -- | -- |
| InletFanSpeed (0x02) | Y | Y | Y | -- | Y | -- | -- |
| OutletFanSpeed (0x03) | Y | Y | -- | -- | Y | -- | -- |
| InsideTemp (0x07) | Y | Y | Y | Y | Y | -- | -- |
| OutsideTemp (0x08) | Y | Y | Y | -- | Y | -- | -- |
| SupplyTemp (0x09) | Y | Y | Y | -- | Y | -- | -- |
| ExhaustTemp (0x0A) | Y | Y | -- | -- | -- | -- | -- |
| InletFlow (0x0B) | Y | Y | Y | -- | Y | -- | -- |
| OutletFlow (0x0C) | Y | Y | -- | -- | Y | -- | -- |
| BypassStatus (0x0E) | Y | Y | Y | -- | -- | -- | -- |
| PreheaterStatus (0x0F) | Y | Y | Y | -- | -- | -- | -- |
| FrostStatus (0x16) | Y | Y | Y | Y | Y | -- | -- |
| FilterStatus (0x18) | Y | Y | Y | -- | Y | -- | -- |
| RelativeHumidity (0x20) | Y | Y | Y | -- | -- | -- | -- |
| FanInletTemp (0x22) | -- | Y | -- | -- | -- | -- | -- |
| CO2 Sensors (0x29-30) | Y | Y | -- | -- | -- | -- | -- |
| DA70 Preset (0x31-33) | -- | -- | Y | -- | -- | -- | -- |
| Elan Registers (0x34-37) | -- | -- | -- | Y | -- | -- | -- |
| ConstRPM (0x38-39) | -- | -- | -- | -- | Y | -- | -- |
| MRC CO2 Zones (0x3A-3D) | -- | -- | -- | -- | -- | Y | -- |
| ValvePosition (0x3E-3F) | -- | -- | -- | -- | -- | -- | Y |
| SoftwareVersion (0x00) | Y | Y | Y | Y | Y | Y | Y |
| ModelName (0x52) | Y | Y | Y | Y | Y | Y | Y |
| OperatingHours (0x47) | Y | Y | Y | Y | Y | -- | -- |
| PowerConsumption (0x45-46) | Y | Y | -- | -- | Y | -- | -- |
| HeatExchEfficiency (0x44) | Y | Y | -- | -- | -- | -- | -- |

---

## 5. Key Enum Tables

### FanMode (4022 ID=0x01, 40A1/40CB ID=0x00)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Holiday | Minimum ventilation, lowest RPM / no flow (standby) |
| 0x01 | Low | Reduced ventilation, Mode 1 flow setpoints |
| 0x02 | Normal | Normal ventilation, Mode 2 flow setpoints |
| 0x03 | Boost | Maximum ventilation, Mode 3 flow setpoints |

Note for DA70/ConstRPM (Cluster 3/5): same 0-3 encoding is used; "Boost"
maps to Preset 3 or maximum RPM%. Exact FanMode enum for these clusters is
a partial gap (see Section 8, Gap 2).

### BypassStatus (4022 ID=0x0E)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Closed | Damper fully closed (heat recovery active) |
| 0x01 | Open | Damper fully open (free cooling / bypass active) |
| 0x02 | Moving | Damper in transit (motor running) |
| 0x03 | Frost | Damper forced closed by frost protection |

### PreheaterStatus (4022 ID=0x0F)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Off | Preheater not active |
| 0x01 | On | Preheater active, heating inlet air |
| 0x02 | Frost | Running in frost prevention mode |
| 0x03 | Overtemp | Overtemperature trip, heater disabled |

### FrostStatus (4022 ID=0x16)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Normal | No frost risk |
| 0x01 | PreFrost | Temperature approaching frost threshold |
| 0x02 | Frost | Active frost protection engaged |
| 0x03 | DeIce | De-icing cycle active (heat exchanger defrost) |

### FilterStatus (4022 ID=0x18)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Clean | Filter within service interval |
| 0x01 | Dirty | Filter hours exceeded configured threshold |
| 0x02 | Unknown | Sensor/counter not initialized |

### CO2SensorStatus (4022 IDs 0x2A, 0x2C, 0x2E, 0x30, DA70 0x33)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | OK | Sensor operating normally |
| 0x01 | NotPresent | No sensor detected at this position |
| 0x02 | Error | Sensor failure / out of range reading |
| 0x03 | Warmup | Sensor in warm-up phase after power-on |

### ValveStatus (4022 ID=0x3F)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | Closed | Valve at 0% |
| 0x01 | Open | Valve at setpoint % |
| 0x02 | Moving | Motor in transit |
| 0x03 | Error | Motor fault / position sensor fault |

### PressureMode (4050 ID=0x20)

| Value | Label | Description |
|-------|-------|-------------|
| 0x00 | FlowControl | Default: volumetric flow m3/h |
| 0x01 | PressureControl | Constant static pressure mode |
| 0x02 | RPMControl | Direct RPM% mode (ConstRPM cluster) |

---

## 6. Architecture Comparison: Brink 40xx vs Vaillant B5xx

| Feature | Brink 40xx | Vaillant B5xx |
|---------|-----------|---------------|
| Primary Byte | 0x40 | 0xB5 |
| Sub-protocol selection | SB (1 byte) | Opcode in data payload |
| ID space width | Flat 1 byte (0x00-0xFF) | B509: flat 16-bit; B524: (opcode, GG, II, RR) tuple |
| Total addressable registers | 256 per protocol x 8 protocols | Effectively unlimited via GG/RR hierarchy |
| Self-describing parameters | YES -- 4050 returns 5-field in-band | B524 requires separate opcode 0x01 query |
| Write-read symmetry | Symmetric (4080 ID = 4050 ID) | Asymmetric on some B524 registers |
| Float encoding | None -- integer wire values + divider | IEEE-754 f32 for some B509 registers |
| Timers/schedules | None natively | B524 opcodes 0x03/0x04 or B555 |
| Broadcast protocol | None | B508 |
| Error history | Dedicated 4090 protocol | No standard protocol |
| Factory reset | Dedicated 40FF protocol | No standard protocol |
| Peripheral addressing | Same 0x3C address, cluster-selected | Unique eBUS addresses per device |
| CO2 multi-sensor | Native (up to 4 sensors) | No native multi-sensor protocol |
| Bypass control | Fully observable + configurable | Not a standard protocol feature |
| Parameter discovery | Runtime via 4050 min/max/step/default | Static documentation or B524 opcode 0x01 |

---

## 7. Device Address Table

| Device | eBUS Address | Cluster | Evidence |
|--------|-------------|---------|----------|
| Brink HRU (all models) | 0x3C | 1-5 | JOHN30_DEVICE |
| MultiRoomCtrl T01 | 0x3C (shared) | 6 | PVYLETA_SENSOR |
| Valve T01 | 0x3C (shared) | 7 | PVYLETA_SENSOR |

All Brink devices share eBUS address 0x3C. The cluster is selected by the
device model/firmware, not by address. Multi-device bus configurations
(e.g., HRU + MRC + Valve) require address reassignment via 4080 ID=0xD0.

---

## 8. Known Gaps

| # | Gap | Impact | Path to Resolution |
|---|-----|--------|-------------------|
| 1 | 4090 error history response byte structure | Cannot parse fault log programmatically | Bus capture on a device with known faults |
| 2 | Complete FanMode enum for DA70 (Cluster 3) and ConstRPM (Cluster 5) | Possible unmapped values for preset 4 and 5 | DA70 bus capture with 5-preset configuration |
| 3 | ValveT01 sub-IDs 0x80-0x92 (19 params) individual assignments | Cannot write specific valve parameters by name | Deeper decompilation of ValveT01 service tool component |
| 4 | MRC sub-IDs 0xA0-0xB9 (26 params) individual assignments | Cannot configure individual zone thresholds by name | Deeper decompilation of MRC service tool component |
| 5 | No live bus verification | All claims are from static analysis; edge cases possible | eBUS capture on each cluster type |

---

## 9. Evidence

### Primary Source

**pvyleta/ebusd-brink-hru** -- Brink Service Tool binary decompilation.

- `sensor_data.py` -- all 89 4022 sensor register definitions with types,
  dividers, and cluster assignments
- `param_data.py` -- all 126 4050/4080 parameter definitions with ranges,
  defaults, and step sizes
- Protocol framing constants for 40FF, 4091, 4090, 40A1, 40CB

Confidence: **HIGH**. This is decompiled firmware/service tool logic, not
inferred from bus captures. Register names, types, dividers, ranges, and
defaults come directly from the tool's data structures.

### Confirming Source

**john30/ebusd-configuration** -- Device entry for Brink HRU at eBUS
address 0x3C confirms physical addressing. No register-level data, but
validates the device address assumption.

### Key Falsifiable Claims Summary

| Claim | Protocol | ID | Expected Result |
|-------|----------|-----|----------------|
| Factory-default flow_mode_1 = 100 m3/h | 4050 | 0x01 | CurrentValue=100, Default=100 |
| Normal FanMode = 0x02 | 4022 | 0x01 | UIR = 0x0002 |
| SIR/10 indoor temp at 20 deg C = wire 200 | 4022 | 0x07 | SIR wire = 0x00C8 |
| Bypass closed = 0x00 | 4022 | 0x0E | UIR = 0x0000 |
| No frost at outdoor > 5 deg C = 0x00 | 4022 | 0x16 | UIR = 0x0000 |
| Dirty filter after threshold exceeded | 4022 | 0x18 | UIR = 0x0001 |
| 4050 UIR response always 10 bytes | 4050 | any UIR | NN = 0x0A |
| 40CB Boost survives power cycle | 40CB | 0x00 | 4022/0x01 = 0x03 post-cycle |
| 40A1 Boost reverts after power cycle | 40A1 | 0x00 | 4022/0x01 = persistent value post-cycle |
| Excellent 300 at eBUS addr 0x3C | -- | -- | ZZ=0x3C in all frames |
