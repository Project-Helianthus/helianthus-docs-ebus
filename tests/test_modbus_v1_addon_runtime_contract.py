from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-addon-runtime.md"


class ModbusV1AddonRuntimeContractTest(unittest.TestCase):
    def test_contract_freezes_configuration_recovery_and_stop_boundaries(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        for required in (
            "modbus_tcp_enabled",
            "modbus_tcp_endpoint",
            "modbus_tcp_dial_timeout",
            "disabled by default",
            "atomic validation",
            "100 ms through 30 s",
            "0600",
            "sha256:",
            "helianthus.modbus-addon-health.v1",
            "CONFIG_VALIDATED",
            "RECOVERY_RETRY",
            "FALLBACK_STARTING",
            "FALLBACK_ACTIVE",
            "FALLBACK_EXITED",
            "EXITED_AFTER_STARTUP_WINDOW",
            "STOPPED",
            "three",
            "current gateway",
            "previous gateway",
            "TERM",
            "INT",
            "TERM/KILL/wait",
            "M4-04",
            "No GraphQL, Portal, Home Assistant",
        ):
            self.assertIn(required, text)

    def test_contract_freezes_secret_and_process_ownership(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        for required in (
            "never appears in process arguments",
            "never appears in environment variables",
            "private synchronized redaction pipes",
            "validator",
            "redactor",
            "child process",
            "endpoint file is removed before fallback",
            "fail closed",
        ):
            self.assertIn(required, text)

    def test_landing_pages_link_contract(self) -> None:
        self.assertIn(
            "modbus-v1-addon-runtime.md",
            (ROOT / "api" / "mcp.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "../../api/modbus-v1-addon-runtime.md",
            (ROOT / "docs" / "platform" / "README.md").read_text(
                encoding="utf-8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
