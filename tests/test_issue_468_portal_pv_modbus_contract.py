from __future__ import annotations

import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PortalPVModbusContractTests(unittest.TestCase):
    def test_portal_routes_keep_semantic_and_raw_boundaries_separate(self) -> None:
        portal = (ROOT / "api/portal.md").read_text(encoding="utf-8")
        required = (
            "GET /portal/api/v1/semantic/pv/current",
            "POST /portal/api/v1/explorer/modbus/raw-read",
            "M2MCurrentSnapshot",
            "modbus.v1.raw.read",
            "semantic_pv",
            "modbus_raw_diagnostic",
            "disabled independently by default",
        )
        for phrase in required:
            self.assertIn(phrase, portal)
        self.assertIn("accepts no endpoint, tool name, profile, asset, credential, or write", portal)
        self.assertIn("must keep the raw route disabled", portal)

    def test_portal_bff_keeps_m2m_credentials_out_of_browser(self) -> None:
        contract = (ROOT / "docs/platform/public-graphql-m2m-v1.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Portal BFF Consumer Target", contract)
        self.assertIn("never receives its client private key", contract)
        self.assertIn("exact canonical query over TLS 1.3", contract)
        self.assertIn("generic Portal listener does not mount the M2M", contract)
        self.assertIn("cannot add fields", contract)

    def test_raw_portal_reuses_mcp_limits_and_quota(self) -> None:
        mcp = (ROOT / "api/modbus-v1-mcp.md").read_text(encoding="utf-8")
        self.assertIn("FMV3-M5-06 Portal Reuse Target", mcp)
        self.assertIn("same closed `modbus.v1.raw.read` operation core", mcp)
        self.assertIn("four-reads-per-second runtime quota", mcp)
        self.assertIn("fifth combined MCP-or-Portal request", mcp)
        self.assertIn("before wire I/O", mcp)

    def test_public_graphql_contract_has_no_raw_modbus_expansion(self) -> None:
        sdl = (ROOT / "api/public-graphql-m2m-v1.graphql").read_text(
            encoding="utf-8"
        ).lower()
        for forbidden in ("register", "wire_bytes", "raw_read", "endpoint"):
            self.assertNotIn(forbidden, sdl)

        manifest = json.loads(
            (ROOT / "docs/platform/manifests/public-graphql-m2m-v1.json").read_text(
                encoding="utf-8"
            )
        )
        serialized = json.dumps(manifest, sort_keys=True).lower()
        for forbidden in ("raw_read", "wire_bytes", "modbus_endpoint"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
