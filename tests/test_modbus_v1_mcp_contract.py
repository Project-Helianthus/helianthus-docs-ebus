from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-mcp.md"


class ModbusV1MCPContractTest(unittest.TestCase):
    def test_contract_freezes_read_only_bounds_and_ownership(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for required in (
            "modbus.v1.raw.read",
            "modbus.v1.profile.observation.get",
            "FC03",
            "FC04",
            "1..125",
            "four raw MCP reads",
            "RESOURCE_EXHAUSTED",
            "RETAINED_SOURCE_OBSERVATION",
            "endpoint_identity",
            "observation_json_base64",
            "No other raw-result field is part of V1",
            "error` is a closed object containing",
            "helianthus-modbusreg",
            "M4-04",
            "caller-triggered",
            "exactly one bounded reconnect followed by exactly one retry",
            "exactly one raw MCP quota admission",
            "failed connection generation",
            "must not be mixed into the result",
            "does not reconnect to the Modbus endpoint or perform wire I/O",
            "Every emitted error message is endpoint-free",
            "static bounded message",
            "wrapped operating-system or network error",
            "does not run a detector, activate a profile, start a background",
            "does not derive canonical availability, freshness",
            "No GraphQL, Portal, Home Assistant",
        ):
            self.assertIn(required, normalized)

    def test_landing_pages_link_contract(self) -> None:
        self.assertIn(
            "modbus-v1-mcp.md",
            (ROOT / "api" / "mcp.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "../../api/modbus-v1-mcp.md",
            (ROOT / "docs" / "platform" / "README.md").read_text(
                encoding="utf-8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
