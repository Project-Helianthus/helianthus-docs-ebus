# B505 operating roles and timing candidates

## Evidence and limits

Read the public native [B505 family contract](ebus-vaillant-B505.md) first.
This finite supplement describes **Hypothesis** relationships for the B505
family (`PB=B5`, `SB=05`), rather than observed device behavior. The older
catalogue's conversions, ranges, offsets and durations do not resolve this
supplement's **Unknown** values. The supplied finite relationships and
[synthetic cases](fixtures/ak04_b505_operating_roles.json) establish no native
qualification. **Proven** applies only to the synthetic representation checks.
Qualification remains **Unknown**, independently of the Hypothesis grade.

Each table row is one independent operation, field and role association.
Field and role labels are descriptive, not wire offsets, byte layouts or
numeric instances. Distinct heating/cooling and night/holiday values remain
independent. Solar tank one, two and three are separate roles. The JSON uses
implementation-neutral identities; `alternative` denotes the role, `request`
denotes the candidate B505 direction and `none` denotes a non-applicable scope.
Absent optional numeric axes are not zero. Raw synthetic tokens are retained;
`bytes: null` means no wire encoding is supplied.

## Finite role table

| Operation | Field | Role | Candidate relationship | Grade |
| --- | --- | --- | --- | --- |
| OP5A | room_setpoint | room | explicit_replacement_before_numeric | Hypothesis |
| OP3D | day_setpoint | day | explicit_replacement_before_numeric | Hypothesis |
| OP3D | night_setpoint | night | explicit_replacement_before_numeric | Hypothesis |
| OP47 | night_heating | inverter_indoor | night_room_heating | Hypothesis |
| OP47 | night_cooling | inverter_indoor | night_room_cooling | Hypothesis |
| OP48 | holiday_heating | inverter_indoor | holiday_room_heating | Hypothesis |
| OP48 | holiday_cooling | inverter_indoor | holiday_room_cooling | Hypothesis |
| OP41 | frost_protection | solar | off_replacement_code_unknown | Hypothesis |
| OP40 | minimum_temperature | second_solar_circuit | minimum_temperature | Hypothesis |
| OP40 | minimum_temperature | solid_fuel_boiler | minimum_temperature | Hypothesis |
| OP10 | maximum_preheat | heating | advance_before_first_period | Hypothesis |
| OP3F | maximum_preheat | heating | advance_before_first_period | Hypothesis |
| OP15 | early_cutoff | heating | stop_demand_before_reduction | Hypothesis |
| OP2B | early_cutoff | heating | stop_demand_before_reduction | Hypothesis |
| OP3C | uncorrected_room | room | self_heating_without_user_correction | Hypothesis |
| OP3C | corrected_room | room | self_heating_with_user_correction | Hypothesis |
| OP1B | switch_on_difference | solar_tank_one | switch_on_difference | Hypothesis |
| OP1B | cutoff_difference | solar_tank_one | cutoff_difference | Hypothesis |
| OP1E | switch_on_difference | solar_tank_two | switch_on_difference | Hypothesis |
| OP1E | cutoff_difference | solar_tank_two | cutoff_difference | Hypothesis |
| OP38 | switch_on_difference | solar_tank_three | switch_on_difference | Hypothesis |
| OP38 | cutoff_difference | solar_tank_three | cutoff_difference | Hypothesis |
| OP1A | maximum_loading_temperature | solar_tank_one | maximum_loading_temperature | Hypothesis |
| OP1D | maximum_loading_temperature | solar_tank_two | maximum_loading_temperature | Hypothesis |
| OP37 | maximum_loading_temperature | solar_tank_three | maximum_loading_temperature | Hypothesis |
| OP31 | ordinary_enable | dhw | one_permits_ordinary_blocked_frost_only | Hypothesis |
| OP19 | charging_enable | dhw_tank | one_enables_charging | Hypothesis |
| OP27 | charging_enable | dhw_tank | one_enables_charging | Hypothesis |
| OP18 | charging_disable | circuit | one_suppresses_without_parallel | Hypothesis |
| OP27 | charging_disable | circuit | one_suppresses_without_parallel | Hypothesis |
| OP14 | parallel_charging | mixer | mixer_exception_only | Hypothesis |
| OP27 | tank_flow_temperature | dhw | flow_temperature | Hypothesis |
| OP2F | external_storage_sensor | storage | external_sensor_temperature | Hypothesis |
| OP1C | outside_correction | outside | temperature_correction | Hypothesis |
| OP26 | hydraulic_schema | solar_controller | controller_specific_schema | Hypothesis |
| OP23 | duty_control | collector_pump | pump_duty | Hypothesis |
| OP21 | flow | collector_water | water_flow | Hypothesis |
| OP22 | reset | solar_pump_hours | one_requests_clear_hours | Hypothesis |
| OP20 | reset | solar_yield | one_requests_clear_yield | Hypothesis |
| OP17 | excess | demanded_flow | add_excess_to_demand | Hypothesis |
| OP0F | maximum | flow_demand | maximum_flow_demand | Hypothesis |
| OP0E | minimum | flow_demand | zero_is_off | Hypothesis |
| OP12 | overrun | charging_pump | retain_pump_inhibit_boiler_after_charging | Hypothesis |
| OP11 | recharge_delay | solar_charging | limit_recharge_delay | Hypothesis |
| OP0D | pump_idle | heating | energy_saving_after_flow_exceeds_desired | Hypothesis |
| OP0C | outside_cutoff | heating | select_summer_operation | Hypothesis |
| OP01 | day_setpoint | heating | room_temperature | Hypothesis |
| OP01 | day_setpoint | fixed_value | flow_temperature | Hypothesis |
| OP01 | day_setpoint | dhw | tank_temperature | Hypothesis |
| OP0A | reduction | room | room_reduction | Hypothesis |
| OP0A | reduction | fixed_flow | flow_reduction | Hypothesis |
| OP09 | first_period_start | programming | ignored_outside_mode_zero | Hypothesis |
| OP07 | saving | heating | zero_is_off | Hypothesis |
| OP03 | drying_day | floor_drying | zero_disables_drying | Hypothesis |

## Replacement and numeric boundaries

For OP5A and OP3D, select an explicitly identified replacement branch before
numeric conversion. Replacement=true retains the prior room/day/night token;
replacement=false remains a numeric candidate with no newly established scale.
The raw replacement code is **Unknown**: no selector is inferred from the
branch flag. OP41 has an off replacement whose raw code is also **Unknown**.
No unchanged-branch code is borrowed from another operation.

OP47 concerns heating and cooling night-room setpoints of inverter indoor
circuits. OP48 concerns their heating and cooling holiday-room setpoints.
OP40 concerns the second solar circuit or solid-fuel-boiler role. OP3C
uncorrected room temperature includes self-heating and excludes user
correction; corrected room temperature includes both. No correction formula
is supplied.

## Timing, demand and eligibility

OP10 and OP3F advance heating before the first period. OP15 and OP2B stop demand
before the reduction period. Their durations, offsets and enforcement are
Unknown. OP12 retains pump activity after charging while inhibiting the boiler;
OP11 limits recharge delay during solar charging. OP0D denotes an energy-saving
pump-idle interval after flow exceeds desired temperature. OP0C selects summer
heating operation using outside cutoff; thresholds and hysteresis are Unknown.

OP31 enabled=1 permits ordinary DHW; blocked leaves only frost protection
eligible. Eligibility does not establish execution. OP19 and OP27 charging-enable=1
concern DHW tank charging. OP18 and OP27 charging-disable=1 suppress circuits
without parallel charging. OP14 provides a mixer exception; a non-mixer circuit
does not inherit that exception merely because a parallel flag is true.
OP27 tank-flow temperature concerns DHW flow, independently of its enable and
disable fields. OP2F supplies external storage-sensor temperature; OP1C supplies
outside correction. OP26 is solar-controller-specific. OP23 concerns collector
pumps; OP21 concerns collector water.

OP22 reset=1 requests clearing solar-pump hours. OP20 reset=1 requests clearing
yield. Neither request establishes acceptance or persistent clearing. OP17 adds
excess to demanded flow: synthetic demand 40 plus excess 5 yields candidate 45.
This semantic addition supplies no byte encoding, scale or broader formula.
OP0F sets maximum flow demand; OP0E sets minimum flow demand, with zero meaning
off rather than a positive minimum. OP07 saving zero is off; OP03 drying day
zero disables drying. OP01 day setpoint means room temperature for heating,
flow temperature for fixed-value circuits and tank temperature for DHW.
OP0A keeps room reduction separate from fixed-flow reduction. OP09 first-period
start is ignored outside programming mode 0; the mode 0/1 cases differ only in
mode and its resulting candidate interpretation.

## Unknowns and raw preservation

Unprovided encodings, offsets, widths, scales, durations, other formulas and
enforcement remain **Unknown**. Native support, physical effects, acceptance,
persistence and delivery remain **Unknown**. Synthetic correctness establishes
only the declared representation. Unknown input retains raw form and independent
partial last-known-good values; it cannot establish eligibility for an unknown
action. No actual write or read-back observation is represented here.
