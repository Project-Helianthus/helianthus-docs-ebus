# Boiler B509 codec dictionary boundaries

This finite architecture contract follows the public native
[B509 register-access contract](../protocols/vaillant/ebus-vaillant-b509.md)
and [boiler candidate map](../protocols/vaillant/ebus-vaillant-b509-boiler-register-map.md).
Those pages own native facts. Here, **Proven** describes the local software
contract, **Hypothesis** describes every codec association, and **Unknown**
describes native support and effects. Qualification is independent of invocation.
The [synthetic package](fixtures/am12_b509_boiler_codec_dictionary.json) and
[focused tests](../tests/test_am12_b509_boiler_codec_dictionary.py) exercise only
this page's executable reference, not another repository's implementation.

## Exact metadata boundary

`entries()` returns the embedded finite metadata array in the listed order.
`lookup(key)` returns one row or `None`. Both return deep independent data.
`validate_rows(rows)` is the owned validation seam: validate the entire array
before admission, reject duplicate complete keys, return an independent array.
Validation failure raises `ValueError` and returns no result; it never replaces
an earlier valid dictionary with a partial array. Unknown codec labels are
accepted as opaque metadata by this seam; the embedded dictionary is the exact
finite set below. No codec label selects an executable converter.

Keys are objects with exactly these members. String tokens are case-sensitive;
there is no coercion, defaulting, device inference or proximity-based selection.
A well-formed unknown family, variant or complete key returns no row. A partial
key also returns no row; malformed present members and extra key members fail
validation even in a partial key. Missing differs from explicit zero; zero is
valid for numeric key members but matches none of these rows. Null and Boolean
are invalid numeric members.

| Key member | Kind | Selected value |
|---|---|---|
| family | nonempty string | boiler |
| variant | nonempty string | direct_symbolic_candidate |
| primary | integer byte | 181 |
| secondary | integer byte | 9 |
| operation | integer byte | 13 |
| direction | nonempty string | read |
| selector | four uppercase hex digits | ordered pair below |

`read` is a metadata access-direction token. Neither `request` nor `positive`
is an alias for it. B5/09 and explicit OP0D select these read candidates;
OP0E and OP29 return no row. The variant is the explicitly selected
**direct-symbolic candidate**, never a runtime inference. Each selector is the
literal ordered pair of address bytes, first byte first: `0E04` is `[14, 4]`,
not `[4, 14]`; its second byte is not a page. No integer-address endian choice
is made. `0E04` and `A500` remain separate selectors with one quantity name.
Equal selectors in another family cannot inherit a boiler row. No missing
heat-pump interface-unit row is admitted.

Each row has exactly `key`, `quantity`, `codec`, `grade`, `conflicts`, `native`.
`quantity` is a canonical name independent of codec and unit. `codec` contains
only a nonempty literal `label`. `grade` is always Hypothesis. `conflicts` is
an array of nonempty strings, possibly empty; empty means no additional conflict
recorded in this finite slice, not native certainty. `native` contains the seven
Unknown properties checked by the reference. Width, endian, unit, mapping,
sentinel, scale, converter and numeric value fields are absent. Even compound
labels preserve literal declarations rather than resolving alternatives.
DATA2c, DATA2b, on/off and percent0 supply no complete conversion here.
The UCH on/off declaration preserves its stated alternatives as text only.

## Finite associations

All rows have family `boiler`, variant `direct_symbolic_candidate`, B5/09,
operation `13` (OP0D), direction `read` and grade **Hypothesis**.

| Selector | Quantity | Codec declaration | Conflict retained |
|---|---|---|---|
| 1800 | flow_temperature | DATA2c | none stated |
| 4400 | central_heating_pump_active | on/off | none stated |
| 0200 | water_pressure | DATA2b | none stated |
| 0500 | flame_active | UCH (0x0F=on, 0xF0=off) | none stated |
| BB00 | gas_valve_active | UCH (0x0F=on, 0xF0=off) | none stated |
| 8300 | fan_speed | UIN | none stated |
| 2E00 | modulation_setpoint | SIN / 10 | setpoint versus achieved modulation unresolved |
| AB00 | boiler_state_code | UCH | none stated |
| 5400 | diverter_valve_position | UCH | position enum versus percent unresolved |
| 5800 | dhw_demand_active | on/off | none stated |
| 5500 | dhw_water_flow_rate | UIN / 100 | none stated |
| 0E04 | maximum_heating_flow_temperature_setpoint | DATA2c | separate selector; family applicability Unknown |
| A500 | maximum_heating_flow_temperature_setpoint | DATA2c | separate selector; family applicability Unknown |
| 0F04 | maximum_dhw_flow_temperature_setpoint | DATA2c | none stated |
| 0704 | heating_partial_load_power | UCH | unit Unknown |
| 0804 | dhw_partial_load_power | UCH | unit Unknown |
| 9E00 | storage_loading_pump_level | percent0 | none stated |
| 3900 | flow_temperature_setpoint | DATA2c | none stated |
| EA03 | dhw_temperature_setpoint | DATA2c | none stated |
| 7B00 | circulation_pump_active | on/off | none stated |
| 3F00 | external_pump_active | on/off | none stated |
| F203 | heating_switch_active | on/off | none stated |
| 2400 | fan_speed_setpoint | UIN | none stated |
| A400 | flame_ionization_current | SIN / 10 | current versus voltage unresolved |
| FB00 | primary_circuit_flow_rate | UIN / 100 | litres/minute versus litres/hour unresolved |

## Executable local reference

```python
from copy import deepcopy
import re

KEY_FIELDS = ("family", "variant", "primary", "secondary", "operation",
              "direction", "selector")
NATIVE_FIELDS = ("support", "presence", "freshness", "execution", "effects",
                 "persistence", "delivery")


def validate_key(key, complete=False):
    if type(key) is not dict or set(key) - set(KEY_FIELDS):
        raise ValueError("key members")
    for field, value in key.items():
        if field in ("primary", "secondary", "operation"):
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError("integer byte required")
        elif type(value) is not str or not value:
            raise ValueError("nonempty string required")
        elif field == "selector" and not re.fullmatch(r"[0-9A-F]{4}", value):
            raise ValueError("ordered selector required")
    if complete and set(key) != set(KEY_FIELDS):
        raise ValueError("incomplete row key")


def validate_rows(rows):
    if type(rows) is not list:
        raise ValueError("row array required")
    seen = set()
    for row in rows:
        if type(row) is not dict or set(row) != {
                "key", "quantity", "codec", "grade", "conflicts", "native"}:
            raise ValueError("row members")
        validate_key(row["key"], complete=True)
        identity = tuple(row["key"][field] for field in KEY_FIELDS)
        if identity in seen:
            raise ValueError("duplicate complete key")
        seen.add(identity)
        if (type(row["quantity"]) is not str or
                not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", row["quantity"])):
            raise ValueError("canonical quantity required")
        codec = row["codec"]
        if (type(codec) is not dict or set(codec) != {"label"} or
                type(codec["label"]) is not str or not codec["label"]):
            raise ValueError("literal codec label required")
        if row["grade"] != "Hypothesis":
            raise ValueError("candidate grade required")
        if (type(row["conflicts"]) is not list or any(
                type(item) is not str or not item for item in row["conflicts"])):
            raise ValueError("conflict strings required")
        if (type(row["native"]) is not dict or
                set(row["native"]) != set(NATIVE_FIELDS) or
                any(value != "Unknown" for value in row["native"].values())):
            raise ValueError("native properties remain Unknown")
    return deepcopy(rows)


# Literal finite associations; no fixture file or runtime dependency is loaded.
_DECLARATIONS = [
    ('1800', 'flow_temperature', 'DATA2c', []),
    ('4400', 'central_heating_pump_active', 'on/off', []),
    ('0200', 'water_pressure', 'DATA2b', []),
    ('0500', 'flame_active', 'UCH (0x0F=on, 0xF0=off)', []),
    ('BB00', 'gas_valve_active', 'UCH (0x0F=on, 0xF0=off)', []),
    ('8300', 'fan_speed', 'UIN', []),
    ('2E00', 'modulation_setpoint', 'SIN / 10', ['setpoint versus achieved modulation unresolved']),
    ('AB00', 'boiler_state_code', 'UCH', []),
    ('5400', 'diverter_valve_position', 'UCH', ['position enum versus percent unresolved']),
    ('5800', 'dhw_demand_active', 'on/off', []),
    ('5500', 'dhw_water_flow_rate', 'UIN / 100', []),
    ('0E04', 'maximum_heating_flow_temperature_setpoint', 'DATA2c', ['separate selector; family applicability Unknown']),
    ('A500', 'maximum_heating_flow_temperature_setpoint', 'DATA2c', ['separate selector; family applicability Unknown']),
    ('0F04', 'maximum_dhw_flow_temperature_setpoint', 'DATA2c', []),
    ('0704', 'heating_partial_load_power', 'UCH', ['unit Unknown']),
    ('0804', 'dhw_partial_load_power', 'UCH', ['unit Unknown']),
    ('9E00', 'storage_loading_pump_level', 'percent0', []),
    ('3900', 'flow_temperature_setpoint', 'DATA2c', []),
    ('EA03', 'dhw_temperature_setpoint', 'DATA2c', []),
    ('7B00', 'circulation_pump_active', 'on/off', []),
    ('3F00', 'external_pump_active', 'on/off', []),
    ('F203', 'heating_switch_active', 'on/off', []),
    ('2400', 'fan_speed_setpoint', 'UIN', []),
    ('A400', 'flame_ionization_current', 'SIN / 10', ['current versus voltage unresolved']),
    ('FB00', 'primary_circuit_flow_rate', 'UIN / 100', ['litres/minute versus litres/hour unresolved']),
 ]
_EMBEDDED = validate_rows([
    {"key": {"family": "boiler", "variant": "direct_symbolic_candidate",
             "primary": 181, "secondary": 9, "operation": 13,
             "direction": "read", "selector": selector},
     "quantity": quantity, "codec": {"label": label}, "grade": "Hypothesis",
     "conflicts": conflicts,
     "native": {field: "Unknown" for field in NATIVE_FIELDS}}
    for selector, quantity, label, conflicts in _DECLARATIONS
])


def entries():
    return deepcopy(_EMBEDDED)


def lookup(key):
    validate_key(key)
    if set(key) != set(KEY_FIELDS):
        return None
    for row in _EMBEDDED:
        if row["key"] == key:
            return deepcopy(row)
    return None


_ABSENT = object()


def example_lookup(key, raw, last_known_good=_ABSENT):
    # Synthetic caller packaging only; not an additional registry API.
    result = {"row": lookup(key), "raw": deepcopy(raw),
              "qualification": "Unknown"}
    if last_known_good is not _ABSENT:
        result["last_known_good"] = deepcopy(last_known_good)
    return result
```

## Synthetic caller examples and limits

The package has the exact finite rows and named cases below. `example_lookup`
is only a synthetic caller wrapper: input `key` follows the lookup rules, `raw`
is opaque JSON, and optional `last_known_good` is opaque JSON. Output has `row`,
an independent `raw`, qualification `Unknown`, and `last_known_good` exactly
when supplied. A missing key yields row `None` without discarding raw or prior
state. Malformed key data fails with `ValueError`, without mutating caller
storage or a previously returned successful result. No raw width or value is
validated or interpreted. An absent field, empty array and `[0]` are distinct.
Partial, malformed-looking and extra raw content remains available verbatim;
independently useful siblings and prior state are never overwritten by zero.
Prior state is caller-owned context, not evidence of freshness or support.
This accessor itself consumes no raw data and decodes no values.

| Case | Expected selector (none means no row) |
|---|---|
| valid | 1800 |
| equal-name-first | 0E04 |
| equal-name-second | A500 |
| family-heat_pump | none |
| family-heat_pump_interface_unit | none |
| variant-other_candidate | none |
| primary-180 | none |
| secondary-8 | none |
| operation-14 | none |
| operation-41 | none |
| direction-request | none |
| direction-positive | none |
| selector-0018 | none |
| selector-FFFF | none |
| absent-family | none |
| absent-variant | none |
| absent-primary | none |
| absent-secondary | none |
| absent-operation | none |
| absent-direction | none |
| absent-selector | none |
| zero-primary | none |
| zero-secondary | none |
| zero-operation | none |
| absent-raw-field | 1800 |
| zero-raw-field | 1800 |
| partial-raw | 2E00 |
| extra-raw | 5400 |

No numeric codec arithmetic is defined, so there is no decoded-number oracle.
The tests independently check selector octets with integer arithmetic and literal
expected values. They independently enumerate all associations, conflicts,
key axes, field shapes and examples; they do not derive their oracle from the
embedded rows. Unknown codec labels in a validation-seam control stay metadata.

The AM11 registry companion is a prerequisite for adopting this contract in the
registry. Its implementation and readiness are unverified here. Existing generic
name correspondence and identity shapes are separate contracts. No pending
schema/API import, provider registration, generic raw-access change, discovery
change, transmit route, scan-default change, active executor or automatic native
qualification is introduced. eBUS MCP compatibility and GraphQL parity are
unchanged: neither surface gains a schema or caller. Physical support, presence,
freshness, execution, effects, persistence and delivery remain Unknown.
Nothing is stable before Helianthus 1.0; no new major or experimental namespace
is introduced. This page establishes only the local software/page contract.

Refs #1027; partial child of #736, which remains open. Full repository CI,
Gate D, publication checks, independent committed-change review and applicable
transport classification remain later ship requirements. Focused offline tests
do not establish those outcomes.
