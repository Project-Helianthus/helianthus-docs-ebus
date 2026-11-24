# Config-setter mutation surface

This page lists every key and argument of the config setters that the gateway
publishes in GraphQL and in MCP. One table covers one setter. A setter and a key
are read together: a key belongs to the table under its own setter heading.

The setters are served from the ebusreg driver namespace in GraphQL and in MCP.
Every key the gateway wrote before the port keeps a driver operation. On B524 the
permission to write is the access bit the device reports; this page grants or
withholds none.

## Reading the columns

| Column | Content |
| --- | --- |
| key (argument) | The exposed key, or the argument of a time-program writer. |
| service and register selector | The service (`B509`, `B524` or `B555`) and each register as its own `RR=0x....` component. B524 rows also carry `OP`, `OT=0x01` (write), `GG` and `II` (a hex byte or the literal `index`). |
| value type | The value type the setter accepts, as the setter-key list names it. |
| unit | The unit the register page records in its decode column. `unknown` where no page states one. |
| range source | The B524 description record (`GG RRlo RRhi MIN MAX STEP`) where that query exists. The register-map row applies only where no query exists. `unknown` where the query exists and the device returns no reply or no result. No range is taken from the setter-key list. |
| grade | The grade the register page records. A provisional name carries its open question as the setter-key list records it. `Unknown (none printed)` where the page prints no grade for the row. |
| driver operation | The operation of the ebusreg write inventory entry for the row. The binding is EE04's inventory entry and is pending EE04's merge. |

Range source for a B524 row below reads: B524 description record; register-map
row only where no query exists; unknown where the query yields no reply.

## set_boiler_config

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `central_heating_pump_mode` | B509, RR=0x4904 | uch | unknown | unknown; the B509 register map row states no range | Hypothesis. Provisional name. Candidate interpretation, unconfirmed on the wire: central heating pump mode (0 post-run, 1 permanent, 2 winter). Another reading is an installer access code (the legacy API path describes one); see the Open questions of the boiler map. Which devices of the class use which meaning is unresolved. The canonical name is provisional until this is resolved. | EE04 inventory entry; binding pending EE04 merge |
| `dhw_partial_load_power` | B509, RR=0x0804 | uch | unknown; the unit (kW or %) is unresolved | unknown; the B509 register map row states no range | Unknown (none printed). Open question: one community configuration lists the unit as kW or %; the unit is unresolved. | EE04 inventory entry; binding pending EE04 merge |
| `heating_partial_load_power` | B509, RR=0x0704 | uch | unknown; the unit (kW or %) is unresolved | unknown; the B509 register map row states no range | Unknown (none printed). Open question: one community configuration lists the unit as kW or %; the unit is unresolved. | EE04 inventory entry; binding pending EE04 merge |
| `installer_phone_number` | B509, RR=0x8104 | bcd | text | unknown; the B509 register map row states no range | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maximum_dhw_flow_temperature_setpoint` | B509, RR=0x0F04 | data2c | °C | unknown; the B509 register map row states no range | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maximum_heating_flow_temperature_setpoint` | B509, RR=0x0E04, RR=0xA500 | data2c | °C | unknown; the B509 register map row states no range | Unknown (none printed). Open question: separate selector with the same community name; which devices of the class use which id is unresolved. | EE04 inventory entry; binding pending EE04 merge |

## ebus_v1_semantic_boiler_status_set_config

The MCP tool takes the keys of `set_boiler_config`.

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `central_heating_pump_mode` | B509, RR=0x4904 | uch | unknown | unknown; the B509 register map row states no range | Hypothesis. Provisional name. Candidate interpretation, unconfirmed on the wire: central heating pump mode (0 post-run, 1 permanent, 2 winter). Another reading is an installer access code (the legacy API path describes one); see the Open questions of the boiler map. Which devices of the class use which meaning is unresolved. The canonical name is provisional until this is resolved. | EE04 inventory entry; binding pending EE04 merge |
| `dhw_partial_load_power` | B509, RR=0x0804 | uch | unknown; the unit (kW or %) is unresolved | unknown; the B509 register map row states no range | Unknown (none printed). Open question: one community configuration lists the unit as kW or %; the unit is unresolved. | EE04 inventory entry; binding pending EE04 merge |
| `heating_partial_load_power` | B509, RR=0x0704 | uch | unknown; the unit (kW or %) is unresolved | unknown; the B509 register map row states no range | Unknown (none printed). Open question: one community configuration lists the unit as kW or %; the unit is unresolved. | EE04 inventory entry; binding pending EE04 merge |
| `installer_phone_number` | B509, RR=0x8104 | bcd | text | unknown; the B509 register map row states no range | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maximum_dhw_flow_temperature_setpoint` | B509, RR=0x0F04 | data2c | °C | unknown; the B509 register map row states no range | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maximum_heating_flow_temperature_setpoint` | B509, RR=0x0E04, RR=0xA500 | data2c | °C | unknown; the B509 register map row states no range | Unknown (none printed). Open question: separate selector with the same community name; which devices of the class use which id is unresolved. | EE04 inventory entry; binding pending EE04 merge |

## set_circuit_config

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `circuit_cooling_enabled` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x0006 | bool_u8 | bool | B524 description record; register-map row (0..1) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `circuit_flow_temperature_setpoint_minimum` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x0012 | float32 | °C | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `circuit_heating_curve_factor` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x000F | float32 | dimensionless | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `circuit_room_temperature_influence_mode` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x0015 | enum_u16 (modulating 1, off 0, thermostat 2) | enum | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `heating_circuit_flow_temperature_setpoint_maximum` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x0010 | float32 | °C | B524 description record; register-map row (15..80 per ebusd) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `heating_circuit_outdoor_temperature_limit_maximum` | B524, OP=0x02, OT=0x01, GG=0x02, II=index, RR=0x0014 | float32 | °C | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Hypothesis. Installer-field candidate; the summer-cutoff interpretation requires physical corroboration. | EE04 inventory entry; binding pending EE04 merge |

## set_system_config

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `adaptive_heating_curve_enabled` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0014 | bool_u8 | bool | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `dhw_flow_temperature_setpoint_maximum` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0046 | float32 | °C | B524 description record; register-map row (15..80 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `dhw_outdoor_bivalence_temperature_limit` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0001 | float32 | °C | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed). The register page records a profile-scoped decoding of the description record as Hypothesis. | EE04 inventory entry; binding pending EE04 merge |
| `heating_flow_temperature_setpoint_maximum_at_heat_pump_fault` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0026 | float32 | °C | B524 description record; register-map row (20..80 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `heating_outdoor_bivalence_temperature_limit` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0023 | float32 | °C | B524 description record; register-map row (-20..30 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_access_code` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0076 | uint16 | count | B524 description record; register-map row (0..999) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_name` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x006C, RR=0x006D | cstring_pair | text | B524 description record; register-map row (maxLength 6 per register) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_phone_number` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x006F, RR=0x0070 | cstring_pair | text | B524 description record; register-map row (maxLength 6 per register) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maintenance_date` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x002C | date_hda3 | date | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `room_humidity_limit_maximum` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x000E | uint16 | % | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## ebus_v1_semantic_system_set_config

The MCP tool takes the keys of `set_system_config`.

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `adaptive_heating_curve_enabled` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0014 | bool_u8 | bool | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `dhw_flow_temperature_setpoint_maximum` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0046 | float32 | °C | B524 description record; register-map row (15..80 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `dhw_outdoor_bivalence_temperature_limit` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0001 | float32 | °C | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed). The register page records a profile-scoped decoding of the description record as Hypothesis. | EE04 inventory entry; binding pending EE04 merge |
| `heating_flow_temperature_setpoint_maximum_at_heat_pump_fault` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0026 | float32 | °C | B524 description record; register-map row (20..80 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `heating_outdoor_bivalence_temperature_limit` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0023 | float32 | °C | B524 description record; register-map row (-20..30 per TSP) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_access_code` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x0076 | uint16 | count | B524 description record; register-map row (0..999) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_name` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x006C, RR=0x006D | cstring_pair | text | B524 description record; register-map row (maxLength 6 per register) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `installer_phone_number` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x006F, RR=0x0070 | cstring_pair | text | B524 description record; register-map row (maxLength 6 per register) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `maintenance_date` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x002C | date_hda3 | date | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `room_humidity_limit_maximum` | B524, OP=0x02, OT=0x01, GG=0x00, II=0x00, RR=0x000E | uint16 | % | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## set_zone_config

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `heating_zone_operating_mode` | B524, OP=0x02, OT=0x01, GG=0x03, II=index, RR=0x0006 | enum_u16 (auto 1, manual 2, off 0) | enum | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Hypothesis. Provisional name. Open question: representation is not established; the relation to `OP=0x02, GG=0x03, RR=0x0006` (same name) is not established. | EE04 inventory entry; binding pending EE04 merge |
| `heating_zone_room_manual_temperature_setpoint` | B524, OP=0x02, OT=0x01, GG=0x03, II=index, RR=0x0022 | float32 | °C | B524 description record; register-map row (15..30 step 0.5 per ebusd) only where no query exists; unknown where the query yields no reply | Hypothesis. Candidate, unconfirmed on the wire. This is the write route of `thermal.operation.set_temperature` stated on the [zone setpoint page](zone-setpoint-semreg-cutover.md). | EE04 inventory entry; binding pending EE04 merge |
| `zone_quick_veto_time` | B524, OP=0x02, OT=0x01, GG=0x03, II=index, RR=0x0026 | float32 | hrs; the register page notes the unit is not established | B524 description record; register-map row (0.5..12 step 0.5) only where no query exists; unknown where the query yields no reply | Hypothesis. Candidate, unconfirmed on the wire. | EE04 inventory entry; binding pending EE04 merge |
| `zone_room_temperature_setpoint_at_holiday` | B524, OP=0x02, OT=0x01, GG=0x03, II=index, RR=0x0005 | float32 | °C | B524 description record; register-map row (5..30) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `zone_room_temperature_setpoint_at_quick_veto` | B524, OP=0x02, OT=0x01, GG=0x03, II=index, RR=0x0008 | float32 | °C; the register page notes the unit is not established | B524 description record; register-map row only where no query exists; unknown where the query yields no reply | Hypothesis. Candidate, unconfirmed on the wire. | EE04 inventory entry; binding pending EE04 merge |

## set_dhw_config

The rows come from the hot-water writes of `development/ha-integration.md`
(group `0x01`, instance `0x00`). The exposed key of each row is EE04's, and is
pending EE04's merge; until then each row is keyed by its selector and the
register page's documentation name.

| key | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `dhw_temperature_setpoint` | B524, OP=0x02, OT=0x01, GG=0x01, II=0x00, RR=0x0004 | float32 | °C | B524 description record; register-map row (35..70) only where no query exists; unknown where the query yields no reply | Hypothesis. Candidate, unconfirmed on the wire. | EE04 inventory entry; binding pending EE04 merge |
| `dhw_operating_mode` | B524, OP=0x02, OT=0x01, GG=0x01, II=0x00, RR=0x0003 | enum_u16 | enum | B524 description record; register-map row (0..2) only where no query exists; unknown where the query yields no reply | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

The write route of these two rows is stated on the pages
[hot-water setpoint](dhw-setpoint-semreg-cutover.md) and
[hot-water mode](dhw-mode-semreg-cutover.md).

## set_zone_time_program

| argument | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `zone` | B555, OP=0xA6, ZONE=index, HC=0x00 | Int (required) | zone index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `weekday` | B555, OP=0xA6, ZONE=index, HC=0x00 | Int (required) | weekday index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `slots` | B555, OP=0xA6, ZONE=index, HC=0x00 | String | slot list | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## set_dhw_time_program

| argument | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `weekday` | B555, OP=0xA6, ZONE=0xFF, HC=0x02 | Int (required) | weekday index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `slots` | B555, OP=0xA6, ZONE=0xFF, HC=0x02 | String | slot list | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## ebus_v1_semantic_schedules_set_zone_time_program

The `slots` input is an array of objects with required integer `start_hour`,
`start_minute`, `end_hour`, `end_minute` and required numeric `temperature_c`.

| argument | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `zone` | B555, OP=0xA6, ZONE=index, HC=0x00 | integer (required) | zone index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `weekday` | B555, OP=0xA6, ZONE=index, HC=0x00 | integer (required) | weekday index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `slots` | B555, OP=0xA6, ZONE=index, HC=0x00 | array of slot objects with required temperature_c | hour, minute, °C | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## ebus_v1_semantic_schedules_set_dhw_time_program

The `slots` input is an array of objects with required integer `start_hour`,
`start_minute`, `end_hour`, `end_minute` and optional numeric `temperature_c`.
The omission of `temperature_c` keeps its native disposition.

| argument | service and register selector | value type | unit | range source | grade | driver operation |
| --- | --- | --- | --- | --- | --- | --- |
| `weekday` | B555, OP=0xA6, ZONE=0xFF, HC=0x02 | integer (required) | weekday index | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |
| `slots` | B555, OP=0xA6, ZONE=0xFF, HC=0x02 | array of slot objects with optional temperature_c | hour, minute, °C | unknown | Unknown (none printed) | EE04 inventory entry; binding pending EE04 merge |

## Zone holiday registers (read side)

These are the `OT=0x00` read registers of group `0x03` of
[the B524 register page](../protocols/vaillant/ebus-vaillant-b524.md)
(`OP=0x02, OT=0x00, GG=0x03`, `II` is the zone). They are read evidence. No write
selector is derived from an `OT=0x00` read selector. The write route of a zone
holiday value is shown only where the EE04 write inventory and its contract
evidence it; where the contract gives none, the route is not established.

| register | selector | meaning (candidate) | grade | write route |
| --- | --- | --- | --- | --- |
| `zone_holiday_start_date` | OP=0x02, OT=0x00, GG=0x03, II=index, RR=0x0003 | holiday start date | Unknown (none printed) | not established |
| `zone_holiday_end_date` | OP=0x02, OT=0x00, GG=0x03, II=index, RR=0x0004 | holiday end date | Unknown (none printed) | not established |
| `zone_holiday_end_clock_time` | OP=0x02, OT=0x00, GG=0x03, II=index, RR=0x0020 | holiday end time | Unknown (none printed) | not established |
| `zone_holiday_start_clock_time` | OP=0x02, OT=0x00, GG=0x03, II=index, RR=0x0021 | holiday start time | Unknown (none printed) | not established |
| `zone_room_temperature_setpoint_at_holiday` | OP=0x02, OT=0x00, GG=0x03, II=index, RR=0x0005 | holiday room temperature setpoint; its key and row are those of `set_zone_config` | Unknown (none printed) | the row of `set_zone_config` |

## System holiday naming

The register page records an open disagreement about the system holiday
sequence selectors `GG=0x00` `RR=0x00F3` and `RR=0x00F4`. The set sequence of one
controller family reads `RR=0x00F3` as the start time and `RR=0x00F4` as the end date,
while the register map rows name `RR=0x00F3` the system holiday end date and
`RR=0x00F4` the system holiday start date. The disagreement is unresolved and
concerns those two selectors only. It does not concern the zone holiday rows.

## Mutation roots

The gateway publishes these GraphQL mutation roots: `invoke`, `set_boiler_config`,
`set_circuit_config`, `set_system_config`, `set_zone_config`,
`set_zone_time_program` and `set_dhw_time_program`. Each root except `invoke` has
its table above. The generic `invoke` mutation is not a config setter and has no
setter-key entry; its documentation stays in its owning page `api/graphql.md`.

## Completion by the write inventory

The driver-operation cells, the exposed key of each `set_dhw_config` row and the
write route of each zone holiday value are completed from the EE04 write
inventory when EE04 merges. The completion is a separate documentation change
that edits only this page. A selector, range or grade that no documentation page
states is `unknown` here, and read evidence is never write authority.
