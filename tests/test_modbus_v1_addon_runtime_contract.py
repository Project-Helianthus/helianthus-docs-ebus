from pathlib import Path
import re
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
            "current gateway",
            "previous gateway",
            "TERM",
            "INT",
            "TERM/KILL/wait",
            "M4-04",
            "No GraphQL, Portal, Home Assistant",
        ):
            self.assertIn(required, text)

    def test_health_and_recovery_sets_are_closed(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        health = text.split("## Health Contract\n", 1)[1].split(
            "## Bounded Recovery\n", 1
        )[0]
        fields = re.search(
            r"It contains only (.*?)\.\n", health, flags=re.DOTALL
        )
        self.assertIsNotNone(fields)
        self.assertEqual(
            re.findall(r"`([^`]+)`", fields.group(1)),
            [
                "contract",
                "enabled",
                "endpoint_ref",
                "state",
                "attempt",
                "max_attempts",
                "binary",
                "reason",
            ],
        )
        self.assertEqual(
            re.findall(r"^\| `([A-Z_]+)` \|", health, flags=re.MULTILINE),
            [
                "DISABLED",
                "CONFIG_VALIDATED",
                "RUNNING",
                "RECOVERY_RETRY",
                "FALLBACK_STARTING",
                "FALLBACK_ACTIVE",
                "FALLBACK_EXITED",
                "EXITED_AFTER_STARTUP_WINDOW",
                "STOPPED",
            ],
        )

        recovery = text.split("## Bounded Recovery\n", 1)[1].split(
            "## Stop And Cleanup\n", 1
        )[0]
        self.assertEqual(
            re.findall(
                r"^\| `([a-z_]+)` \| `([0-9,]+)` \|$",
                recovery,
                flags=re.MULTILINE,
            ),
            [
                ("current_startup_attempts", "3"),
                ("retry_delays_seconds", "1,2"),
                ("startup_window_min_seconds", "5"),
                ("startup_window_max_seconds", "40"),
            ],
        )
        normalized_recovery = " ".join(recovery.split())
        self.assertIn("exactly three attempts", normalized_recovery)
        self.assertIn(
            "bounded from five through forty seconds", normalized_recovery
        )

    def test_contract_freezes_secret_and_process_ownership(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for required in (
            "never appears in process arguments",
            "never appears in environment variables",
            "private synchronized redaction pipes",
            "validator",
            "redactor",
            "child process",
            "endpoint file is removed before fallback",
            "fail closed",
            "enable-static-seed-table",
            "semantic-cache-path",
            "instance-guid-source",
            "best-effort rollback options",
            "FALLBACK_ACTIVE` therefore proves fallback liveness, not parity",
        ):
            self.assertIn(required, normalized)

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
