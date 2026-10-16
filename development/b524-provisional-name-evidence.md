# Evidence missing from provisional B524 names

Refs [#573](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/573);
partial child [#590](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/590).

This is an evidence-gap view of the existing catalog, not another naming source.
The [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
establishes the selector fields and the separation of local OP02 and mediated
OP06. Read it before interpreting this index. The
[register catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md)
and its [naming policy](../architecture/naming.md#unknown-meaning) retain
maker-derived terms while their open points await evidence. Canonical names and
`previous_name` remain owned by those sources.

## Scope and computed inventory

The inclusion rule is every nonempty `open_question` in the
[canonical OP02 CSV](../protocols/vaillant/fixtures/b524-op02-register-names.csv).
It currently selects **142 of 368 rows**, each listed exactly once below:
131 retain documented terms and 11 use pre-existing `unknown` placeholders.
Both subsets have explicit open questions; neither is silently excluded.
The supplied parent snapshot has a historical title count of 96, a body count
of 99 and a truncated table. Relative to those counts the current inventory is
46 and 43 rows larger respectively; these are count differences, not verified
selector additions. All five complete selectors visible in the supplied excerpt
remain present; its sixth selector line is truncated. A complete parent-list
snapshot is required to identify actual additions and removals. This index does
not claim to reconcile the unseen parent rows.

| Opcode | Group | Open rows |
| --- | --- | ---: |
| 0x02 | 0x00 | 108 |
| 0x02 | 0x01 | 5 |
| 0x02 | 0x02 | 11 |
| 0x02 | 0x03 | 10 |
| 0x02 | 0x04 | 2 |
| 0x02 | 0x08 | 1 |
| 0x02 | 0x09 | 5 |

This is not a census of all unknown B524 semantics: unnamed catalog entries,
OP00 questions and section-level provisional OP02/GG0A or OP06 claims are not
silently added to the parent naming-row inventory. The correspondence CSV has
368 OP02 entries and 2 OP06 entries, but no `open_question` column. These
OP06 entries do not add unresolved naming rows under this inclusion rule.
OP02/GG0A and OP06/GG0A remain independent namespaces; neither is inferred from
the other. Their existing catalog caveats remain authoritative.

## Evidence and missing-evidence key

Every row below cites its existing public evidence by its exact opcode, group
and register key in [C: canonical CSV](../protocols/vaillant/fixtures/b524-op02-register-names.csv).
Its text is the existing `open_question`, retaining candidate interpretations
and conflicts. The one module designation is generalized to a functional-module
family. These are references to checked-in evidence text, not new observations.
Repository-relative references identify the source files; review the index and
sources together in the same repository revision. Issue links provide tracking,
not wire evidence.

The [A: correspondence CSV](../protocols/vaillant/fixtures/b524-register-name-correspondence.csv)
is a separate annotation source for the same keys: observed vendor, application
and community names establish neither native meaning nor codec, unit, enum or
writability. An application projection mentioned in an open question is likewise
implementation behavior, not native evidence. An empty annotation is not proof
of absence. Existing raw evidence stays beside its interpretation in the catalog;
this index adds no captures or physical-device claims.

The **gap** column classifies missing evidence, not the register:

- **M**: meaning, purpose, relation, applicability or family association needs
  a public native description or correlated selector/value evidence that
  distinguishes the competing readings.
- **P**: polarity needs a public value table or correlated state evidence that
  establishes which native value denotes each state.
- **V**: value class, representation, unit or value table needs a public native
  description or correlated raw-value evidence with an independently known
  quantity; a label or observed zero alone cannot settle it.
- **W**: writability or write path is explicitly open and needs independently
  publishable native qualification. A readable value, command-shaped name or
  FLAGS bit does not establish it. This index requests no live writes.

**Unknown** describes each listed unresolved point. Candidate interpretations
inside the quoted source text remain **Hypothesis**; none becomes **Proven**
through inclusion. These evidence labels are separate from qualification of a
family, selector, instance, codec or write. Absence of W does not assert writable
or read-only behavior. No existing evidence grade is changed.

The **II context** column reproduces only the candidate instance context in the
[I: requester matrix](../protocols/vaillant/fixtures/b524-op02-requester-register-matrix.csv).
`00` is its candidate II=0x00; `dynamic` is a parameterized selector, not a
concrete observed instance or admitted range. `Unknown` means the matrix has no
matching key. The canonical naming CSV itself omits II; these are naming-row
counts, not counts of qualified concrete instances. No II bounds, family aliases,
units, enums or write capability are inferred. The profile limits maintained
under #584 remain separate. Explorer name bridging remains with #301/#306.

## Selector coverage

All rows have OP=0x02. C/A/I references resolve by the full OP/GG/RR key;
II context stays separate rather than merging instances or inventing them.

### OP=0x02, GG=0x00

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0007 | `unknown_11` | VRC700 family: 00; VRC720 family: 00 | P | Polarity unresolved, so no Boolean name is given: the catalog row gives `0=off 1=on` (1 = switched on), while the candidate write sets the switch-off with 01 and cancels it with 00 (1 = switched off), unconfirmed on the wire. |
| 0x0008 | `cooling_enabled_at_holiday` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that cooling is permitted during a holiday; the polarity is not established and no value table is documented. |
| 0x000B | `solar_circuit_bleeding_time` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a duration of the solar circuit bleeding; the value class and unit are not established. |
| 0x000D | `solar_frost_protection_limit` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a limit of the solar frost protection; the limited quantity and the representation are not established. |
| 0x0010 | `backup_heater_tariff` | Unknown | M, V | Value class is not established: a price, a ratio or a selection are candidate readings, unconfirmed on the wire; the association with a tariff is not established. |
| 0x0011 | `electricity_price_at_low_tariff` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: an electricity price at the low tariff; value class and unit are not established. |
| 0x0012 | `electricity_price_at_high_tariff` | Unknown | M | Candidate interpretation, unconfirmed on the wire: an electricity price at the high tariff; the register map decodes a u16 in °C, which does not fit a price; unresolved. |
| 0x0013 | `backup_heater_type` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the backup heater kind (0 condensing, 1 non-condensing, 2 electrical); the representation and the applicability are not established. |
| 0x0015 | `automatic_daylight_saving_time` | Unknown | V | Value class and encoding are not established. |
| 0x001E | `automatic_sequence_reversal` | Unknown | M, V | Value class, encoding and meaning are not established; candidate reading, unconfirmed on the wire: a pump or flag value related to the reversal of the generator sequence. |
| 0x0024 | `backup_heater_mode` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the backup heater use (0 disabled, 1 heating, 2 DHW, 3 DHW and heating); the value table is not established. |
| 0x0025 | `temporary_backup_heater_mode` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration for a temporary permission of the backup heater; how it differs from the backup heater enumeration at RR=0x0024 is not established, and neither is the value table. |
| 0x002F | `functional_module_configuration_code` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: a configuration code of a functional module kind (functional-module family); the code list is not established. |
| 0x0031 | `language` | Unknown | V | Value class and encoding are not established. |
| 0x003A | `hybrid_unknown_2` | Unknown | M | A kelvin value of the hybrid control; the meaning is not established. |
| 0x003F | `environmental_yield_total_reset_command` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a command that resets the environmental yield total; representation and applicability are not established. |
| 0x0040 | `ventilation_volatile_organic_compound_sensor_1` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x09, RR=0x0005` (same name) is not established. |
| 0x0041 | `ventilation_volatile_organic_compound_sensor_2` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x09, RR=0x0006` (same name) is not established. |
| 0x0044 | `ventilation_heat_recovery` | Unknown | M, V | Value class is not established; the relation to `OP=0x02, GG=0x09, RR=0x000B` (same name) is not established. |
| 0x0045 | `utility_lockout_mode` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of utility lockouts (0 disable heat pump, 1 disable backup heater, 2 disable heat pump and backup heater, 3 disable heating, 4 disable cooling, 5 disable heating and cooling); the value table is not established. |
| 0x0047 | `emergency_operation_active` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: 1 means that the device runs in an emergency (failure) mode; no value table is documented. |
| 0x0049 | `electricity_consumption_total_reset_command` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a command that resets an electricity consumption total; representation is not established, and which accumulated value is reset is not established. |
| 0x004A | `settings_reset_command` | Unknown | M, V, W | Candidate interpretation, unconfirmed on the wire: a command that resets settings to their defaults; which settings are reset, the representation and the writability are not established. |
| 0x004C | `backup_heater_power_limit_maximum` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: the maximum power of the backup heater of the heat-pump interface unit; representation is not established. |
| 0x005C | `electricity_consumption_1_total` | Unknown | M | Coexists with `RR=0x00C6` (`electricity_consumption_total`); the documented terms differ (a consumption sum, and the consumption for the system history), so the index only keeps the two apart; whether the two registers carry the same total is not established. Candidate reading, unconfirmed on the wire: a total electricity consumption in kWh. |
| 0x005D | `fuel_consumption_1_total` | Unknown | M | Coexists with `RR=0x00CD` (`fuel_consumption_total`); the documented terms differ (a consumption sum, and the consumption for the system history), so the index only keeps the two apart; whether the two registers carry the same total is not established. Candidate reading, unconfirmed on the wire: a total fuel consumption in kWh. |
| 0x005F | `actuator_sensor_test_device_code` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a code that selects the device of an actuator and sensor test; the value class and the code list are not established. |
| 0x0060 | `actuator_sensor_test_sensor_code` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a code that selects the sensor of an actuator and sensor test; the value class and the code list are not established. |
| 0x0061 | `actuator_sensor_test_actuator_code` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a code that selects the actuator of an actuator and sensor test; the value class and the code list are not established. |
| 0x0062 | `ventilation_volatile_organic_compound_sensor_3` | Unknown | V | Representation is not established. |
| 0x0063 | `ventilation_volatile_organic_compound_limit_maximum` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x09, RR=0x000C` (same name) is not established. |
| 0x0066 | `home_screen_unknown_6` | Unknown | M, V | Value class and meaning are not established. |
| 0x0069 | `unknown_1` | VRC700 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration whose candidate labels are the controller and zones 1 to 3; the meaning is not established. |
| 0x006A | `multifunction_input_mode` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the multifunction input configuration; the value table is not established. |
| 0x0071 | `holiday_start_date` | VRC700 family: 00 | M | Family split: `RR=0x0071` is attested on the VRC700 family and `RR=0x00F2` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. |
| 0x0072 | `holiday_end_date` | VRC700 family: 00 | M | Family split: `RR=0x0072` is attested on the VRC700 family and `RR=0x00F3` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. |
| 0x0074 | `special_function_mode` | Unknown | M, V, W | Candidate interpretation, unconfirmed on the wire: an enumeration of the system special function, dormant when none is active; the mode enumeration and its write path remain hypotheses. |
| 0x0077 | `installation_assistant_ready` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: 1 means that the installation assistant has completed; no value table is documented. |
| 0x0078 | `home_screen_special_function` | Unknown | V | Representation and value class are not established. |
| 0x0079 | `heating_zone_time_program_active` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x03, RR=0x0019` (same name) is not established. |
| 0x007A | `cooling_zone_time_program_active` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x03, RR=0x001A` (same name) is not established. |
| 0x007B | `heating_zone_operating_mode` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x03, RR=0x0006` (same name) is not established. |
| 0x007C | `cooling_zone_operating_mode` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x03, RR=0x0001` (same name) is not established. |
| 0x007D | `home_screen_operating_mode` | Unknown | V | Representation is not established. |
| 0x007E | `unknown_3` | Unknown | M | A float32 value; the meaning is not established. |
| 0x007F | `screed_drying_time` | Unknown | M, V | Two readings, unresolved (candidate interpretations, unconfirmed on the wire): the elapsed duration of the screed drying in days, or the index of the current day in the screed drying programme; representation is not established. |
| 0x0082 | `room_temperature_setpoint_at_holiday` | Unknown | M, V | Family split: `RR=0x0082` is attested on the VRC700 family and `RR=0x00F6` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. Representation of `RR=0x0082` is not established. |
| 0x0083 | `bank_holiday_start_date` | Unknown | V | Representation is not established. |
| 0x0084 | `bank_holiday_end_date` | Unknown | V | Representation is not established. |
| 0x0085 | `actuator_sensor_test_sensor_reading` | Unknown | V | Representation is not established. |
| 0x0086 | `backlight_on_time` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: the time until the backlight switches off; the unit is not established. |
| 0x0087 | `drainback_start_time` | Unknown | M | Candidate interpretation, unconfirmed on the wire: a duration, an interval or a clock time of the drainback start; which of the three is not established. |
| 0x0088 | `drainback_station` | Unknown | V | Representation and value class are not established. |
| 0x008A | `solar_pump_kick_gradient_limit_minimum` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a minimum gradient limit of the solar pump kick; the quantity of the gradient and its unit are not established. |
| 0x008C | `boiler_remote_reset_available` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that a remote reset of the boiler is available; no value table is documented and the polarity is not established. |
| 0x008D | `display_test_pattern` | Unknown | V | Value class is not established. |
| 0x008F | `cylinder_type` | VRC700 family: 00; VRC720 family: 00 | M, V | Two readings, unresolved: an enumeration (0 disabled, 1 heating, 2 DHW, 3 DHW and heating) or an availability flag (candidate interpretations, unconfirmed on the wire). |
| 0x0090 | `unknown_4` | Unknown | M, V | Representation and meaning are not established. |
| 0x0091 | `left_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x0092 | `right_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x0093 | `encoder_active` | Unknown | M, V | Representation is not established: whether the value is a flag or a rotation count is open. Candidate reading, unconfirmed on the wire: a flag that the encoder was rotated. |
| 0x0094 | `external_crystal_status` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a status of the external crystal; the representation and the value table are not established. |
| 0x0096 | `maintenance_active` | Unknown | M | Two readings, unresolved (candidate interpretations, unconfirmed on the wire): 1 means that the device is in maintenance mode, or 1 means that maintenance is due; the semantic plane projects this selector as `state.maintenance_due`. |
| 0x0097 | `eeprom_update_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that an EEPROM update is in progress; no value table is documented and the polarity is not established. |
| 0x0099 | `rtc_crystal_ok` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the real-time clock crystal is OK; the polarity and the representation are not established. |
| 0x009A | `unknown_5` | Unknown | M | A boolean value; the meaning is not established. |
| 0x009C | `home_screen_headline` | Unknown | V | Representation is not established. |
| 0x00A1 | `pv_surplus_enabled` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the use of a photovoltaic surplus is enabled; no value table is documented and the polarity is not established. |
| 0x00A3 | `ventilation_time_program_active` | Unknown | M, V | Representation is not established; the relation to `OP=0x02, GG=0x09, RR=0x0003` (same name) is not established. |
| 0x00A4 | `ventilation_special_function_state` | VRC700 family: dynamic | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the ventilation special function; the representation and the applicability are not established. |
| 0x00A5 | `cascade_client_sequence` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a position in the cascade client sequence; the value class and the meaning are not established. |
| 0x00A6 | `menu_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x00A7 | `confirm_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x00A8 | `back_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x00A9 | `up_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x00AA | `down_button_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the button is pressed; the value class, the representation and the polarity are not established. |
| 0x00AB | `isolation_switch_active` | VRC700 family: 00; VRC720 family: 00 | M, P | Candidate interpretation, unconfirmed on the wire: 1 means that the isolation switch is active; which switch position 1 denotes is not established. |
| 0x00B2 | `network_identifier` | Unknown | M | Semantics are unknown; candidate reading, unconfirmed on the wire: an identifier of the network. |
| 0x00B3 | `multifunction_output_1_mode` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the first multifunction output configuration; the value table is not established. |
| 0x00B6 | `external_energy_management_enabled` | VRC700 family: 00; VRC720 family: 00 | M, P | Candidate interpretation, unconfirmed on the wire: a one-byte switch for an external energy management, 1 = enabled and 0 = disabled; the meanings of 0 and 1 and the controller reaction are not established. |
| 0x00B8 | `solar_diverter_valve` | Unknown | V | Value class is not established. |
| 0x00C6 | `electricity_consumption_total` | Unknown | M | Coexists with `RR=0x005C` (`electricity_consumption_1_total`); the documented terms differ, and whether the two registers carry the same total is not established. Candidate reading, unconfirmed on the wire: a total electricity consumption in kWh for the system history. |
| 0x00CD | `fuel_consumption_total` | Unknown | M | Coexists with `RR=0x005D` (`fuel_consumption_1_total`); the documented terms differ, and whether the two registers carry the same total is not established. Candidate reading, unconfirmed on the wire: a total fuel consumption in kWh for the system history. |
| 0x00DA | `manual_cooling_start_date` | VRC720 family: 00 | M, W | Candidate interpretation, unconfirmed on the wire: the start date of a manual cooling period on the VRC700 family; the interpretation, the writability and the family scope are not established. |
| 0x00DB | `manual_cooling_end_date` | VRC720 family: 00 | M, W | Candidate interpretation, unconfirmed on the wire: the end date of a manual cooling period on the VRC700 family; the interpretation, the writability and the family scope are not established. |
| 0x00DC | `room_temperature_control_mode` | VRC720 family: 00 | V | Representation is not established. |
| 0x00E1 | `circuit_control_mode` | Unknown | V | Representation is not established. |
| 0x00E2 | `automatic_control_active` | Unknown | V | Representation is not established. |
| 0x00E3 | `up_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E4 | `down_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E5 | `help_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E6 | `confirm_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E7 | `menu_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E8 | `back_button_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00E9 | `slider_button_1_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00EA | `slider_button_2_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00EB | `slider_button_3_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00EC | `slider_button_4_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00ED | `slider_button_5_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00EE | `slider_button_6_level` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: a raw value of the button input as a float32; only a zero has been observed, so whether it is a graded amount, a raw reading or a flag is not established. |
| 0x00F0 | `priority_error_code` | Unknown | M | Candidate interpretation, unconfirmed on the wire: the error number of highest priority; whether the value ranks errors by priority is not established. |
| 0x00F1 | `priority_maintenance_code` | Unknown | M | Candidate interpretation, unconfirmed on the wire: the maintenance number of highest priority; whether the value ranks maintenance entries by priority is not established. |
| 0x00F2 | `holiday_start_date` | Unknown | M | Family split: `RR=0x0071` is attested on the VRC700 family and `RR=0x00F2` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. |
| 0x00F3 | `holiday_end_date` | Unknown | M | Family split: `RR=0x0072` is attested on the VRC700 family and `RR=0x00F3` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. |
| 0x00F4 | `holiday_start_clock_time` | Unknown | M | Candidate interpretation, unconfirmed on the wire: the start time of the system holiday; the VRC720-family set sequence writes an end date here, and the disagreement is unresolved. |
| 0x00F6 | `room_temperature_setpoint_at_holiday` | Unknown | M | Family split: `RR=0x0082` is attested on the VRC700 family and `RR=0x00F6` on the VRC720 family (candidate, unconfirmed on the wire); whether the two selectors carry the same quantity is not established. |
| 0x00FB | `heat_pump_temperature_difference_limit_minimum` | Unknown | M | Candidate interpretation, unconfirmed on the wire: a minimum limit of a temperature difference; between which temperatures the difference is taken is not established. |
| 0x00FD | `boiler_flow_temperature_setpoint_maximum` | Unknown | V | Representation is not established. |

### OP=0x02, GG=0x01

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0001 | `dhw_circuit_type` | VRC700 family: 00; VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the DHW circuit (0 deactivated, 1 DHW circuit); the availability test and a circuit-type reading remain distinct and the value table is not established. |
| 0x000E | `dhw_central_control_active` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: 1 means that the DHW circuit is controlled by the system controller; no value table is documented. |
| 0x0014 | `dhw_preference` | VRC720 family: 00 | M, V | Representation and meaning are not established; candidate reading, unconfirmed on the wire: a preference of the DHW. |
| 0x0015 | `dhw_recharge_setpoint` | VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: a setpoint of the DHW recharge; the regulated quantity and the representation are not established. |
| 0x0019 | `dhw_loading_efficiency_state` | VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the DHW loading efficiency; the representation and the value table are not established. |

### OP=0x02, GG=0x02

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0001 | `hydraulic_circuit_type` | VRC700 family: dynamic; VRC720 family: dynamic | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the circuit kind (1 direct heating circuit, 2 external mixer circuit); the purpose is unverified. |
| 0x000A | `circuit_unknown_7` | VRC700 family: dynamic; VRC720 family: dynamic | M | A kelvin value, present with cooling; the meaning is not established. |
| 0x000E | `circuit_frost_protection_mode` | VRC700 family: dynamic; VRC720 family: dynamic | M, V | Two readings, unresolved (candidate interpretations, unconfirmed on the wire): a frost protection mode, or a setback behaviour matching the value table (eco, night). |
| 0x0013 | `dhw_circuit_operating_mode` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the DHW circuit operation; the value table is not established. |
| 0x0016 | `circuit_screed_drying_time` | Unknown | M | Two readings, unresolved (candidate interpretations, unconfirmed on the wire): the elapsed duration of the screed drying in days, or the index of the current day in the screed drying programme. |
| 0x0018 | `dhw_circuit_circulation_pump_active` | Unknown | M | Two readings, unresolved (candidate interpretations, unconfirmed on the wire): the state of a DHW circulation pump, or that external DHW is active. |
| 0x0019 | `circuit_external_demand_input` | Unknown | M, V | Candidate interpretation, unconfirmed on the wire: an external heat demand input of the circuit; the value class and the value table are not established. |
| 0x001B | `circuit_pump_unknown_8` | Unknown | M, V | A raw two-byte value related to the circuit pump; value class and meaning are not established. |
| 0x001D | `circuit_unknown_9` | Unknown | M | Candidate interpretations, unconfirmed on the wire: a DHW quick mode, or a frost protection threshold; the catalog decodes a float32 in °C; unresolved. |
| 0x001E | `circuit_state` | VRC700 family: dynamic; VRC720 family: dynamic | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the circuit state (0 standby, 1 heating, 2 cooling, 3 DHW); the assignment rests on observed naming and the hardware confirmation is pending. |
| 0x0020 | `circuit_unknown_10` | Unknown | M | An observed one-byte raw value related to automatic heating and cooling; the meaning is not established. |

### OP=0x02, GG=0x03

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0007 | `heating_zone_room_comfort_temperature_setpoint` | VRC700 family: dynamic | V | Representation is not established. |
| 0x000A | `heating_zone_operating_mode_at_teleswitch` | Unknown | V | Representation is not established. |
| 0x000B | `cooling_zone_operating_mode_at_teleswitch` | Unknown | V | Representation is not established. |
| 0x001D | `heating_zone_event_end_clock_time` | Unknown | V | Representation is not established. |
| 0x0025 | `zone_holiday_abort_command` | Unknown | M, V, W | Candidate interpretation, unconfirmed on the wire: a command that aborts the zone holiday; the representation, the applicability and the writability are not established. |
| 0x0029 | `zone_cooling_enabled` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that cooling of the zone is enabled; no value table is documented and the polarity is not established. |
| 0x002A | `zone_summer_cutoff_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the summer cutoff of the zone is active; no value table is documented and the polarity is not established. |
| 0x002B | `zone_continuous_heating_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that continuous heating of the zone is active; no value table is documented and the polarity is not established. |
| 0x002D | `heating_zone_thermostat_cutoff_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the room thermostat function has switched heating off; the polarity is not established and no value table is documented. |
| 0x002E | `cooling_zone_thermostat_cutoff_active` | Unknown | M, P, V | Candidate interpretation, unconfirmed on the wire: 1 means that the room thermostat function has switched cooling off; the polarity is not established and no value table is documented. |

### OP=0x02, GG=0x04

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x000A | `solar_circuit_flow_rate_setpoint` | Unknown | V | Representation is not established. |
| 0x000C | `solar_pump_power_limit_minimum` | Unknown | V | Representation is not established. |

### OP=0x02, GG=0x08

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0007 | `differential_control_output` | Unknown | V | Value class is not established. |

### OP=0x02, GG=0x09

| RR | Retained canonical name | II context (I) | Gap | Existing unresolved evidence (C; Unknown) |
| --- | --- | --- | --- | --- |
| 0x0004 | `ventilation_special_function_state` | VRC720 family: 00 | M, V | Candidate interpretation, unconfirmed on the wire: an enumeration of the ventilation special function (0 regular, 1 boost, 7 holiday, 10 system off); the presentation values are not independently verified and the relation to `OP=0x02, GG=0x00, RR=0x00A4` is not established. |
| 0x0005 | `ventilation_volatile_organic_compound_sensor_1` | Unknown | V | Value class and unit are not established. |
| 0x0006 | `ventilation_volatile_organic_compound_sensor_2` | Unknown | V | Value class and unit are not established. |
| 0x000B | `ventilation_heat_recovery` | Unknown | V | Value class is not established. |
| 0x000C | `ventilation_volatile_organic_compound_limit_maximum` | Unknown | V | Unit is not established. |

## Maintenance check

When a source CSV changes, recompute rather than carrying forward a count.
Run this read-only check from the repository root to compare selector/name
coverage, gap classifications, unresolved evidence text, candidate family/instance
context and published inventory totals (selected, total, retained terms,
placeholders and each group), plus correspondence counts by opcode.
It normalizes whitespace and inline-code markup, and applies only the
documented module-family generalization to the source evidence text. The
reviewed question-to-gap mappings in
[b524-provisional-name-gap-classifications.json](b524-provisional-name-gap-classifications.json)
are maintenance expectations, not native evidence. Review these mappings when
an unresolved question changes; unknown questions fail the check until reviewed.
Every classification must be a nonempty subset of M, P, V and W.
The correspondence tests separately protect the
annotation/name boundary. Parent issue additions/removals still need the full
parent list, not a comparison of headline counts.

```python
import collections
import csv
import json
import pathlib
import re

root = pathlib.Path(".")
fixture = root / "protocols/vaillant/fixtures/b524-op02-register-names.csv"
with fixture.open(encoding="utf-8") as handle:
    catalog = list(csv.DictReader(handle))
rows = [r for r in catalog if r["open_question"].strip()]

def normalized(text):
    return " ".join(text.replace("`", "").split())


def context(text):
    return tuple(sorted(normalized(part) for part in text.split(";")))


def gaps(text):
    codes = tuple(sorted(normalized(part) for part in text.split(",")))
    assert set(codes) <= {"M", "P", "V", "W"}, "invalid gap classification"
    return codes


classification_file = root / "development/b524-provisional-name-gap-classifications.json"
classifications = {}
for gap, questions in json.loads(classification_file.read_text(encoding="utf-8")).items():
    for question in questions:
        question = normalized(question)
        assert question not in classifications, "duplicate classified question"
        classifications[question] = gaps(gap)

instances = collections.defaultdict(set)
matrix = root / "protocols/vaillant/fixtures/b524-op02-requester-register-matrix.csv"
with matrix.open(encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        key = (row["opcode"], row["group"], row["register"])
        instances[key].add(normalized(f'{row["family"]}: {row["instance"]}'))
expected = []
for row in rows:
    key = (row["opcode"], row["group"], row["register"])
    evidence = row["open_question"].replace(
        "(the VR71 module)", "(functional-module family)"
    )
    ii = tuple(sorted(instances[key])) or ("Unknown",)
    evidence = normalized(evidence)
    assert evidence in classifications, "unreviewed gap classification for question"
    expected.append((*key, row["name"], ii, classifications[evidence], evidence))
index = root / "development/b524-provisional-name-evidence.md"
text = index.read_text(encoding="utf-8")
summary = text.split("## Scope and computed inventory\n", 1)[1].split("\n## ", 1)[0]
headline = re.findall(r"\*\*(\d+) of (\d+) rows\*\*", summary)
assert headline == [(str(len(rows)), str(len(catalog)))], "published inventory totals differ"
placeholders = sum(bool(re.search(r"(?:^|_)unknown_\d+$", r["name"])) for r in rows)
subsets = re.findall(
    r"(\d+) retain documented terms and (\d+) use pre-existing `unknown` placeholders\.",
    summary,
)
assert subsets == [(str(len(rows) - placeholders), str(placeholders))], "published subsets differ"
group_rows = re.findall(r"^\| (0x[0-9A-F]+) \| (0x[0-9A-F]+) \| (\d+) \|$", summary, re.M)
group_totals = collections.Counter((r["opcode"], r["group"]) for r in rows)
assert collections.Counter((op, gg, int(n)) for op, gg, n in group_rows) == collections.Counter(
    (op, gg, n) for (op, gg), n in group_totals.items()
), "published group totals differ"
correspondence = root / "protocols/vaillant/fixtures/b524-register-name-correspondence.csv"
with correspondence.open(encoding="utf-8") as handle:
    correspondence_totals = collections.Counter(r["opcode"] for r in csv.DictReader(handle))
published_correspondence = re.findall(r"(\d+) OP02 entries and (\d+) OP06 entries", summary)
assert published_correspondence == [
    (str(correspondence_totals["0x02"]), str(correspondence_totals["0x06"]))
], "published correspondence totals differ"
actual = []
opcode = group = None
for line in text.splitlines():
    heading = re.fullmatch(r"### OP=(0x[0-9A-F]+), GG=(0x[0-9A-F]+)", line)
    if heading:
        opcode, group = heading.groups()
    row = re.fullmatch(
        r"\| (0x[0-9A-F]+) \| `([^`]+)` \| ([^|]+) \| ([^|]*) \| ([^|]+) \|",
        line,
    )
    if row:
        register, name, ii, gap, evidence = row.groups()
        actual.append((opcode, group, register, name, context(ii), gaps(gap), normalized(evidence)))
keys = [row[:3] for row in actual]
assert len(keys) == len(set(keys)), "duplicate selector row"
assert collections.Counter(actual) == collections.Counter(expected)
print("Open rows:", len(rows))
print("By opcode/group:", sorted(collections.Counter(k[:2] for k in expected).items()))
print("Missing:", sorted(set(expected) - set(actual)))
print("Extra:", sorted(set(actual) - set(expected)))
```
