"""The zone setpoint page states the write route of thermal.operation.set_temperature."""
from pathlib import Path


PAGE = Path("architecture/zone-setpoint-semreg-cutover.md")

SECTION = "## Write route of the zone temperature operation"

STATEMENTS = (
    "thermal.operation.set_temperature",
    "RR=0x0022",
    "group `0x03`",
    "PB=0xB5 SB=0x24 OP=0x02",
    "kelvin",
    "273.15",
    "B524 description record",
    "no query exists",
    "limits stay unknown",
    "nothing is sent on the bus",
    "One write per operation",
    "no retry of its own",
    "eBUS data link layer V1.3.1",
    "same lifecycle generation",
    "thermal.setpoint.temperature_setpoint",
    "thermal.capability.set_temperature",
    "B524 access flag",
    "heating-manual selector",
    "zone resource",
    "RR=0x0014",
    "development/ha-integration.md",
    "This section is the contract of the write route",
)

INVENTORY = (
    "thermal.setpoint.temperature_setpoint",
    "thermal.operation.set_temperature",
    "`member`",
    "thermal.dimension.zone",
    "resource.zone",
    "thermal.service.zone",
)

DENIALS = (
    "read-only effective value",
    "qualifies neither selector for writes",
    "no writable support",
    "write-authority",
    "stable RO computed output",
)


def test_zone_setpoint_page_states_the_write_route():
    text = PAGE.read_text(encoding="utf-8")
    start = text.index(SECTION)
    section = text[start:].split("\n## ", 1)[0]
    for statement in STATEMENTS:
        assert statement in section
    inventory = text.split("**Element inventory.**", 1)[1].split("\n- ", 1)[0]
    for statement in INVENTORY:
        assert statement in inventory
    for denial in DENIALS:
        assert denial not in text
    boundary = text.split("## Acceptance boundary", 1)[1].split("\n## ", 1)[0]
    effective = next(line for line in text.splitlines() if line.startswith("| Heating computed effective |"))
    for passage in (boundary, effective):
        assert "read-only" not in passage.lower()
        assert "never takes a write" not in passage
        assert "RR=0x0014" in passage
