from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-addon-runtime.md"


class ModbusV1AddonRuntimeContractTest(unittest.TestCase):
    def test_contract_freezes_configuration_and_single_process_ownership(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        for required in (
            "modbus_tcp_enabled",
            "modbus_tcp_endpoint",
            "modbus_tcp_dial_timeout",
            "disabled by default",
            "atomic validation",
            "100 ms through 30 s",
            "0600",
            "one direct launch",
            "protocol-local",
            "s6 -> exec helianthus-gateway",
            "does not retain a parent shell",
            "does not post-process stdout or stderr",
            "TERM",
            "INT",
            "M4-04",
            "No GraphQL, Portal, Home Assistant",
        ):
            self.assertIn(required, text)

    def test_removed_supervisor_machinery_stays_removed(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        lifecycle = text.split("## Single Process Lifecycle\n", 1)[1].split(
            "## M4-03 Phase Boundary\n", 1
        )[0]
        normalized_lifecycle = " ".join(lifecycle.split())
        self.assertIn("s6 -> exec helianthus-gateway", normalized_lifecycle)
        self.assertIn(
            "It does not retain a parent shell, launch log redactors, probe local "
            "listeners, retry the complete gateway, or start a previous binary.",
            normalized_lifecycle,
        )
        for forbidden in (
            "FALLBACK_ACTIVE",
            "RECOVERY_RETRY",
            "modbus-addon-health",
            "previous gateway",
            "startup fallback",
            "startup_fallback",
            "startup window",
            "readiness probe",
            "gateway child",
        ):
            self.assertNotIn(forbidden, text)

    def test_contract_freezes_endpoint_and_library_ownership(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for required in (
            "never appears in process arguments",
            "never appears in environment variables",
            "sanitized by the component that owns the error",
            "does not create redaction FIFOs",
            "Generic reconnect behavior belongs to `helianthus-modbus`",
            "belong to `helianthus-modbusreg`",
            "For enabled startup only",
            "Partial support fails closed before `exec`",
            "Disabled startup does not inspect Modbus flag support",
        ):
            self.assertIn(required, normalized)

    def test_landing_pages_link_contract(self) -> None:
        mcp = (ROOT / "api" / "mcp.md").read_text(encoding="utf-8")
        platform = (ROOT / "docs" / "platform" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("modbus-v1-addon-runtime.md", mcp)
        self.assertIn("single direct gateway process lifecycle", mcp)
        self.assertIn("../../api/modbus-v1-addon-runtime.md", platform)
        self.assertIn("one direct gateway launch", platform)
        for obsolete in (
            "bounded recovery contract",
            "previous-gateway fallback contract",
        ):
            self.assertNotIn(obsolete, mcp)
            self.assertNotIn(obsolete, platform)


if __name__ == "__main__":
    unittest.main()
