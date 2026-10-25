import hashlib
import inspect
import ipaddress
import json
from pathlib import Path
import re
import unicodedata
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-addon-runtime.md"
MULTI = ROOT / "api" / "modbus-multi-endpoint-runtime.md"


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


DOCUMENT_CONTRACT = "helianthus.modbus-tcp-endpoints.v2"
DRIVER_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
GRADES = ("Proven", "Hypothesis", "Unknown")
MAX_DOCUMENT_BYTES = 16384
MAX_ENTRIES = 8
MAX_ENDPOINT_BYTES = 288


def sections(text: str) -> dict[str, str]:
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def tables(body: str) -> list[tuple[list[str], list[list[str]]]]:
    found = []
    block: list[str] = []
    for line in body.split("\n") + [""]:
        if line.startswith("|"):
            block.append(line)
            continue
        if block:
            rows = [[cell.strip() for cell in row.strip().strip("|").split(" | ")] for row in block]
            found.append((rows[0], rows[2:]))
            block = []
    return found


def table_with(body: str, first_header: str) -> list[list[str]]:
    for header, rows in tables(body):
        if header[0] == first_header:
            for row in rows:
                assert len(row) == len(header), row
            return rows
    raise AssertionError(f"table {first_header!r} not found")


def first_int(cell: str) -> int:
    return int(re.search(r"\d+", cell).group(0))


class ReferenceValidator:
    """Executable reading of the stated validation order and bounds."""

    def __init__(self, text: str) -> None:
        by_title = sections(text)
        members = {
            row[0].strip("`"): row for row in table_with(by_title["Endpoints document"], "Member")
            if row[0].startswith("`")
        }
        self.label = re.compile(re.search(r"`(\^\[a-z\].*?\$)`", members["label"][2]).group(0).strip("`"))
        self.families = {
            row[0].strip("`"): row[1].strip("`")
            for row in table_with(by_title["Endpoints document"], "`family`")
        }
        self.pacing = {}
        for row in table_with(by_title["Pacing profile"], "Member"):
            low, high = map(int, re.findall(r"\d+", row[2]))
            self.pacing[row[0].strip("`")] = (low, high, first_int(row[3]))

    @staticmethod
    def utf8_size(value: str):
        """UTF-8 length of a string of Unicode scalar values; None when it holds a lone surrogate."""
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            return None
        return len(value.encode("utf-8"))

    def endpoint(self, value: object):
        if not isinstance(value, str):
            return None
        size = self.utf8_size(value)
        if size is None or size > MAX_ENDPOINT_BYTES:
            return None
        if value != value.strip() or any(ord(char) < 32 for char in value):
            return None
        match = re.fullmatch(r"tcp://(\[[0-9A-Fa-f:.]+\]|[^/:?#@\[\]\s]+):([0-9]{1,5})", value)
        if match is None or not 1 <= int(match.group(2)) <= 65535:
            return None
        host = match.group(1)
        if host.startswith("["):
            try:
                host = f"[{ipaddress.IPv6Address(host[1:-1]).compressed}]"
            except ValueError:
                return None
        else:
            try:
                host = str(ipaddress.IPv4Address(host))
            except ValueError:
                host = host.lower().removesuffix(".")
                labels = host.split(".")
                if len(host) > 253 or not all(
                    re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", item) for item in labels
                ):
                    return None
        return host, int(match.group(2))

    def driver_id(self, family: str, label: str) -> str:
        base = self.families[family]
        return base if label == "default" else f"{base}.{label}"

    @staticmethod
    def _int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def validate(self, raw: bytes):
        """Return None for an accepted document, else (category, entry position)."""
        invalid = ("INVALID_DOCUMENT", None)
        if not 1 <= len(raw) <= MAX_DOCUMENT_BYTES:
            return invalid

        def pairs(items):
            keys = [key for key, _ in items]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate key")
            return dict(items)

        def reject(_value):
            raise ValueError("rejected number")

        try:
            text = raw.decode("utf-8")
            if text.startswith("﻿"):
                return invalid
            document = json.loads(text, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
        except (ValueError, RecursionError):
            return invalid
        if "null" in re.findall(r'"(?:[^"\\]|\\.)*"|\bnull\b', text):
            return invalid
        try:
            if self._has_control_character(document):
                return invalid
        except RecursionError:
            return invalid
        if not isinstance(document, dict):
            return invalid
        for member in ("contract", "endpoints"):
            if member not in document:
                return "MISSING_FIELD", None
        if set(document) - {"contract", "endpoints"}:
            return "UNKNOWN_MEMBER", None
        if document["contract"] != DOCUMENT_CONTRACT or not isinstance(document["endpoints"], list):
            return invalid
        entries = document["endpoints"]
        if not entries:
            return "EMPTY_LIST", None
        if len(entries) > MAX_ENTRIES:
            return "TOO_MANY_ENTRIES", None
        for position, entry in enumerate(entries):
            category = self._entry(entry)
            if category:
                return category, position
        labels = [entry["label"] for entry in entries]
        if len(set(labels)) != len(labels):
            return "DUPLICATE_LABEL", None
        endpoints = [self.endpoint(entry["endpoint"]) for entry in entries]
        if len(set(endpoints)) != len(endpoints):
            return "DUPLICATE_ENDPOINT", None
        return None

    @classmethod
    def _has_control_character(cls, value: object) -> bool:
        if isinstance(value, str):
            return any(unicodedata.category(char) == "Cc" for char in value)
        if isinstance(value, dict):
            return any(cls._has_control_character(item) for pair in value.items() for item in pair)
        if isinstance(value, list):
            return any(cls._has_control_character(item) for item in value)
        return False

    def _entry(self, entry: object):
        if not isinstance(entry, dict):
            return "INVALID_DOCUMENT"
        for member in ("label", "family", "endpoint"):
            if member not in entry:
                return "MISSING_FIELD"
        known = {"label", "family", "endpoint", "dial_timeout", "units", "pacing"}
        pacing = entry.get("pacing")
        if set(entry) - known or (isinstance(pacing, dict) and set(pacing) - set(self.pacing)):
            return "UNKNOWN_MEMBER"
        label = entry["label"]
        label_size = self.utf8_size(label) if isinstance(label, str) else None
        if label_size is None or label_size > 32 or not self.label.fullmatch(label):
            return "INVALID_LABEL"
        if not isinstance(entry["family"], str) or entry["family"] not in self.families:
            return "UNKNOWN_FAMILY"
        if self.endpoint(entry["endpoint"]) is None:
            return "INVALID_ENDPOINT"
        if "dial_timeout" in entry:
            match = re.fullmatch(r"([1-9][0-9]{0,5})(ms|s)", entry["dial_timeout"]) if isinstance(
                entry["dial_timeout"], str
            ) else None
            if match is None or not 100 <= int(match.group(1)) * (1 if match.group(2) == "ms" else 1000) <= 30000:
                return "INVALID_TIMEOUT"
        if "units" in entry:
            units = entry["units"]
            if (
                not isinstance(units, list)
                or not 1 <= len(units) <= 32
                or not all(self._int(unit) and 1 <= unit <= 247 for unit in units)
                or len(set(units)) != len(units)
                or (entry["family"] == "sunspec" and units != [1])
            ):
                return "INVALID_UNITS"
        if "pacing" in entry:
            if not isinstance(pacing, dict):
                return "INVALID_PACING"
            effective = {name: bounds[2] for name, bounds in self.pacing.items()}
            for name, value in pacing.items():
                low, high, _default = self.pacing[name]
                if not self._int(value) or not low <= value <= high:
                    return "INVALID_PACING"
                effective[name] = value
            if effective["backoff_floor_s"] > effective["backoff_ceiling_s"]:
                return "INVALID_PACING"
        return None


def select_configuration(*, enabled, endpoints, scalar_endpoint="", scalar_timeout="5s"):
    """Executable reading of the add-on selection table."""
    if not enabled:
        return "inert"
    if not endpoints:
        return "v1"
    if scalar_endpoint or scalar_timeout != "5s":
        return "MIXED_CONFIGURATION"
    return "v2"


V1_GATEWAY_FLAGS = (
    "-modbus-tcp-enabled",
    "-modbus-tcp-endpoint",
    "-modbus-tcp-endpoint-file",
    "-modbus-tcp-dial-timeout",
)


def select_gateway_flags(flags):
    if "-modbus-tcp-endpoints-file" not in flags:
        return "v1"
    return "MIXED_CONFIGURATION" if any(flag in flags for flag in V1_GATEWAY_FLAGS) else "v2"


def asset_id(domain: str, label: str, asset_class: str, unit: int) -> str:
    """The stated rule for assets of a multi-asset instance: three inputs only."""
    digest = hashlib.sha256(
        b"".join(field.encode() + b"\x00" for field in (domain, label, asset_class, str(unit)))
    ).hexdigest()
    return f"{asset_class}-asset-{digest[:32]}"


class ModbusMultiEndpointRuntimeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = MULTI.read_text(encoding="utf-8")
        cls.sections = sections(cls.text)
        cls.validator = ReferenceValidator(cls.text)
        block = cls.text.split("```json\n", 1)[1].split("\n```", 1)[0]
        cls.example = json.loads(block)
        cls.example_bytes = block.encode()

    def document(self, **overrides) -> dict:
        document = json.loads(json.dumps(self.example))
        document.update(overrides)
        return document

    def check(self, document) -> object:
        return self.validator.validate(json.dumps(document).encode())

    def test_example_document_is_accepted_and_keeps_the_v1_driver_identity(self) -> None:
        self.assertIsNone(self.validator.validate(self.example_bytes))
        ids = [
            self.validator.driver_id(entry["family"], entry["label"])
            for entry in self.example["endpoints"]
        ]
        self.assertEqual(ids, ["modbus.sunspec", "modbus.sunspec.roof"])

    def test_rejection_table_categories_are_each_produced_by_their_case(self) -> None:
        rows = table_with(self.sections["Endpoints document"], "Case")
        documented = {row[1].strip("`") for row in rows}
        entry = self.example["endpoints"][1]

        def entries(*items):
            return self.document(endpoints=[json.loads(json.dumps(item)) for item in items])

        def with_entry(**changes):
            return entries({**entry, **changes})

        cases = {
            "DUPLICATE_LABEL": entries(entry, {**entry, "endpoint": "tcp://other.example.invalid:502"}),
            "DUPLICATE_ENDPOINT": entries(
                entry, {**entry, "label": "attic", "endpoint": "TCP://".lower() + "SUNSPEC-B.example.invalid.:1502"}
            ),
            "UNKNOWN_FAMILY": with_entry(family="Sunspec"),
            "TOO_MANY_ENTRIES": entries(
                *[{**entry, "label": f"unit{n}", "endpoint": f"tcp://h{n}.example.invalid:502"} for n in range(9)]
            ),
            "MISSING_FIELD": None,
            "INVALID_LABEL": with_entry(label="Roof_1"),
            "EMPTY_LIST": self.document(endpoints=[]),
            "UNKNOWN_MEMBER": with_entry(enabled=True),
            "INVALID_ENDPOINT": with_entry(endpoint="tcp://sunspec-b.example.invalid/path"),
            "INVALID_TIMEOUT": with_entry(dial_timeout="50ms"),
            "INVALID_TIMEOUT_HUGE": with_entry(dial_timeout="9" * 5000 + "s"),
            "INVALID_UNITS": with_entry(units=[2]),
            "INVALID_PACING": with_entry(pacing={"backoff_floor_s": 400}),
        }
        cases["MISSING_FIELD"] = self.document(endpoints=[{k: v for k, v in entry.items() if k != "endpoint"}])
        produced = set()
        for category, document in cases.items():
            with self.subTest(category=category):
                self.assertEqual(self.check(document)[0], category.removesuffix("_HUGE"))
                produced.add(self.check(document)[0])
        invalid_documents = (
            b"",
            b"\xef\xbb\xbf{}",
            b'{"contract": "wrong", "endpoints": [{"label": "a"}]}',
            self.example_bytes + b" {}",
            self.example_bytes.replace(b'"gap_ms": 200', b'"gap_ms": 200.0'),
            self.example_bytes.replace(b'"gap_ms": 200', b'"gap_ms": null'),
            self.example_bytes.replace(b'"label": "roof"', b'"label": "default", "label": "roof"'),
            b"x" * (MAX_DOCUMENT_BYTES + 1),
            self.example_bytes.replace(b'"label": "roof"', b'"label": "ro\\u0001of"'),
            b'{"contract": "' + DOCUMENT_CONTRACT.encode() + b'", "endpoints": [], "a\\u0001": 1}',
            b'{"contract": "' + DOCUMENT_CONTRACT.encode() + b'", "endpoints": [], "a\\u0000": 1}',
            b'{"contract": "' + DOCUMENT_CONTRACT.encode() + b'", "endpoints": [], "a\\u0080": 1}',
            self.example_bytes.replace(b'"label": "roof"', b'"label": "ro\\u009fof"'),
            b'{"contract": "' + DOCUMENT_CONTRACT.encode() + b'", "endpoints": ' + b"[" * 3000 + b"]" * 3000 + b"}",
        )
        for raw in invalid_documents:
            with self.subTest(raw=raw[:40]):
                result = self.validator.validate(raw)
                self.assertEqual(result, ("INVALID_DOCUMENT", None))
                produced.add(result[0])
        self.assertEqual(self.check(self.document(extra=1))[0], "UNKNOWN_MEMBER")
        produced.add(
            select_configuration(
                enabled=True, endpoints=[{"label": "default"}], scalar_endpoint="tcp://x:1"
            )
        )
        # Every category that remains in the table is produced by a case above;
        # none is exempt, and the table lists no category that no case can reach.
        self.assertEqual(documented, produced)
        self.assertNotIn("DUPLICATE_DRIVER_ID", self.text)
        obligation = " ".join(self.sections["Acceptance obligations"].split())
        self.assertIn("Every category of the rejection table is produced by a test case", obligation)
        check_order = " ".join(self.sections["Endpoints document"].split())
        self.assertIn("duplicate label, then duplicate endpoint.", check_order)
        self.assertIn("a duplicate label is the rejection", check_order)

    def test_lone_surrogates_in_byte_limited_strings_yield_the_member_category(self) -> None:
        # Fields covered: the two strings with a byte limit.
        #   label    - a validator that measures len(label.encode()) before it checks
        #              for scalar values raises UnicodeEncodeError; one that swallows
        #              the error and reports INVALID_DOCUMENT gives another category.
        #   endpoint - the same two mutations on the endpoint length check.
        # Each form below (high alone, low alone, high before an ordinary
        # character, reversed pair, inside a valid value) is a separate case.
        entry = self.example["endpoints"][1]
        surrogates = {
            "high alone": "\\ud800",
            "low alone": "\\udfff",
            "high before an ordinary character": "\\ud83dx",
            "low before high": "\\ude00\\ud83d",
            "inside an otherwise valid value": "ro\\ud800of",
        }
        template = {
            "label": ("label", "INVALID_LABEL", lambda escaped: escaped),
            "endpoint": (
                "endpoint",
                "INVALID_ENDPOINT",
                lambda escaped: f"tcp://{escaped}.example.invalid:1502",
            ),
        }
        base = json.dumps(self.document(endpoints=[entry]))
        for field, (member, category, build) in template.items():
            current = json.dumps(entry[member])
            self.assertIn(current, base)
            for name, escaped in surrogates.items():
                with self.subTest(field=field, surrogate=name):
                    raw = base.replace(current, '"' + build(escaped) + '"').encode()
                    self.assertEqual(self.validator.validate(raw), (category, 0))
        # A valid escaped pair is one scalar value; it must not raise either and
        # is refused by the member grammar, which is ASCII only.
        pair = base.replace(json.dumps(entry["label"]), '"\\ud83d\\ude00"').encode()
        self.assertEqual(self.validator.validate(pair), ("INVALID_LABEL", 0))
        self.assertEqual(ReferenceValidator.utf8_size("\U0001f600"), 4)
        self.assertIsNone(ReferenceValidator.utf8_size("\ud800"))

    def test_mandatory_rejection_cases_are_listed(self) -> None:
        rows = table_with(self.sections["Endpoints document"], "Case")
        listed = {row[0] for row in rows}
        for case in (
            "Duplicate label",
            "Duplicate endpoint",
            "Unknown family",
            "List too long",
            "Missing field",
            "v1 and v2 mixed",
            "Label not matching the driver ID pattern",
        ):
            self.assertIn(case, listed)

    def test_selection_rules_reject_mixed_v1_and_v2_inputs(self) -> None:
        listed = [{"label": "default"}]
        self.assertEqual(select_configuration(enabled=False, endpoints=listed, scalar_endpoint="x"), "inert")
        self.assertEqual(select_configuration(enabled=True, endpoints=[]), "v1")
        self.assertEqual(select_configuration(enabled=True, endpoints=listed), "v2")
        self.assertEqual(
            select_configuration(enabled=True, endpoints=listed, scalar_endpoint="tcp://x:1"),
            "MIXED_CONFIGURATION",
        )
        self.assertEqual(
            select_configuration(enabled=True, endpoints=listed, scalar_timeout="7s"),
            "MIXED_CONFIGURATION",
        )
        self.assertEqual(select_gateway_flags(["-modbus-tcp-endpoints-file"]), "v2")
        self.assertEqual(select_gateway_flags(["-modbus-tcp-endpoint-file"]), "v1")
        self.assertEqual(select_gateway_flags([]), "v1")
        self.assertIn(
            "never inspects support for the v2 flag",
            " ".join(self.sections["Selecting configuration v1 or v2"].split()),
        )
        for flag in V1_GATEWAY_FLAGS:
            self.assertEqual(
                select_gateway_flags(["-modbus-tcp-endpoints-file", flag]), "MIXED_CONFIGURATION"
            )
        selection = self.sections["Selecting configuration v1 or v2"]
        for flag in ("-modbus-tcp-endpoints-file", *V1_GATEWAY_FLAGS):
            self.assertIn(f"`{flag}`", selection)

    def test_first_failing_check_decides_the_category(self) -> None:
        entry = self.example["endpoints"][1]
        bad_endpoint = {**entry, "endpoint": "tcp://sunspec-b.example.invalid"}
        many = [{**entry, "label": f"unit{n}", "endpoint": bad_endpoint["endpoint"]} for n in range(9)]
        self.assertEqual(self.check(self.document(endpoints=many)), ("TOO_MANY_ENTRIES", None))
        later = {**entry, "label": "attic", "endpoint": "tcp://sunspec-c.example.invalid:502"}
        duplicate = [entry, {**later, "label": entry["label"]}, {**later, "label": "x1", "endpoint": "bad"}]
        self.assertEqual(self.check(self.document(endpoints=duplicate)), ("INVALID_ENDPOINT", 2))
        missing_and_unknown = {k: v for k, v in entry.items() if k != "endpoint"} | {"extra": 1}
        self.assertEqual(self.check(self.document(endpoints=[missing_and_unknown])), ("MISSING_FIELD", 0))
        self.assertEqual(
            self.check(self.document(endpoints=[{**entry, "extra": 1, "label": "Bad"}])), ("UNKNOWN_MEMBER", 0)
        )

    def test_driver_id_derivation_is_canonical_injective_and_keeps_the_v1_id(self) -> None:
        rows = table_with(self.sections["Driver instances"], "Family")
        self.assertGreaterEqual(len(rows), 5)
        for family, label, expected, grade in rows:
            self.assertEqual(
                self.validator.driver_id(family.strip("`"), label.strip("`")), expected.strip("`")
            )
            self.assertTrue(any(name in grade for name in GRADES))
        self.assertEqual(self.validator.driver_id("sunspec", "default"), "modbus.sunspec")
        labels = ["default", "a", "a-b", "roof", "site-a", "x9", "default2"]
        ids = {}
        for family in self.validator.families:
            for label in labels:
                self.assertTrue(self.validator.label.fullmatch(label))
                identifier = self.validator.driver_id(family, label)
                self.assertRegex(identifier, DRIVER_ID_PATTERN)
                self.assertLessEqual(len(identifier.encode()), 128)
                self.assertNotIn(identifier, ids)
                ids[identifier] = (family, label)
        for invalid in ("Roof_1", "1roof", "roof-", "-roof", "a.b", "a--b", "", "a" * 33):
            self.assertIsNone(self.validator.label.fullmatch(invalid) if len(invalid) <= 32 else None)

    def test_asset_id_rule_uses_exactly_label_class_and_unit(self) -> None:
        domain = re.search(r"domain tag `([^`]+)`", self.text).group(1)
        self.assertEqual(domain, "helianthus.modbus.asset.v1")
        self.assertEqual(list(inspect.signature(asset_id).parameters), ["domain", "label", "asset_class", "unit"])
        base = asset_id(domain, "site-a", "pv", 11)
        self.assertRegex(base, r"^pv-asset-[0-9a-f]{32}$")
        self.assertEqual(base, asset_id(domain, "site-a", "pv", 11))
        # Each field changes the identity; a production mutation that ignores
        # the field (or merges fields without a separator) would collapse these.
        variants = {
            "domain tag": asset_id("helianthus.modbus.asset.v2", "site-a", "pv", 11),
            "label": asset_id(domain, "site-b", "pv", 11),
            "class": asset_id(domain, "site-a", "storage", 11),
            "routed unit": asset_id(domain, "site-a", "pv", 12),
        }
        for field, identifier in variants.items():
            with self.subTest(field=field):
                self.assertNotEqual(identifier.split("-")[-1], base.split("-")[-1])
        self.assertTrue(variants["class"].startswith("storage-asset-"))
        self.assertNotEqual(
            asset_id(domain, "ab", "c", 1).split("-")[-1], asset_id(domain, "a", "bc", 1).split("-")[-1]
        )
        self.assertNotEqual(
            asset_id(domain, "a", "pv", 11).split("-")[-1], asset_id(domain, "a", "pv", 1).split("-")[-1]
        )
        rule = " ".join(self.sections["Asset and publication keying"].split())
        for excluded in ("serial number", "ESN", "Endpoint, host, port, address, model, firmware"):
            self.assertIn(excluded, rule)

    def test_pacing_defaults_are_bounded_proposals(self) -> None:
        pacing = self.validator.pacing
        self.assertEqual(set(pacing), {"gap_ms", "settle_ms", "cycle_s", "backoff_floor_s", "backoff_ceiling_s"})
        for name, (low, high, default) in pacing.items():
            with self.subTest(name=name):
                self.assertLessEqual(low, default)
                self.assertLessEqual(default, high)
        self.assertLessEqual(pacing["backoff_floor_s"][2], pacing["backoff_ceiling_s"][2])
        self.assertEqual(pacing["gap_ms"][2:], (200,))
        body = " ".join(self.sections["Pacing profile"].split())
        for required in (
            "Exactly one connection per endpoint",
            "Exactly one request in flight per instance",
            "recommendation for production sites",
            "not measured guarantees",
        ):
            self.assertIn(required, body)
        for entry in self.example["endpoints"]:
            for name, value in entry.get("pacing", {}).items():
                self.assertTrue(pacing[name][0] <= value <= pacing[name][1])

    def test_every_table_after_the_baseline_grades_each_row(self) -> None:
        titles = list(self.sections)
        graded = titles[titles.index("Baseline: configuration v1") :]
        count = 0
        for title in graded:
            for header, rows in tables(self.sections[title]):
                count += 1
                self.assertIn("Grade", header, title)
                for row in rows:
                    self.assertEqual(len(row), len(header), row)
                    self.assertTrue(any(grade in row[header.index("Grade")] for grade in GRADES), row)
        self.assertGreater(count, 15)
        evidence = " ".join(self.sections["Evidence labels"].split())
        self.assertIn("separate from native qualification decisions", evidence)
        self.assertIn("support_claim", evidence)

    def test_failure_isolation_and_migration_tables_cover_the_required_rows(self) -> None:
        isolation = table_with(self.sections["Driver instances"], "Event on instance A")
        events = " ".join(row[0] for row in isolation)
        for required in (
            "Dial failure",
            "Withheld by qualification",
            "START, STOP or RESTART",
            "Unproven close",
            "Restore failure",
            "Two instances reach the same asset",
            "Disabled by the Portal driver selection",
            "Rejected document",
        ):
            self.assertIn(required, events)
        for row in isolation:
            if row[0] not in ("Rejected document",):
                self.assertTrue(row[2].startswith(("None", "Desired state", "Keep", "The first")), row)
        migration = " ".join(
            " ".join(row) for row in table_with(self.sections["Endpoints document"], "v1 input")
        )
        for required in (
            "`modbus.sunspec`",
            "A single-line file behaves exactly as today",
            "same durable desired state and revision",
            "`default`",
        ):
            self.assertIn(required, migration)

    def test_reverse_move_is_equivalent_in_identity_state_and_tools_but_not_pacing(self) -> None:
        rows = table_with(self.sections["Endpoints document"], "v1 input")
        reverse = [row for row in rows if row[0] == "Reverse move"]
        self.assertEqual(len(reverse), 1)
        self.assertNotIn("default pacing", reverse[0][2])
        outcome = " ".join(reverse[0][3].split())
        for required in (
            "Equivalent to v1 in identity",
            "in state",
            "in tool behavior",
            "Not equivalent in pacing",
            "up to four requests in flight",
            "one request in flight plus a gap",
            "endpoint load and timing change on the move",
            "no pacing value is translated",
            "never pacing",
        ):
            self.assertIn(required, outcome)
        forward = [row for row in rows if row[0].startswith("Transport limits")]
        self.assertEqual(len(forward), 1)
        self.assertIn("Pacing is not equivalent across the move", forward[0][3])
        self.assertNotIn("The one intended behavior difference", forward[0][3])
        obligations = " ".join(self.sections["Acceptance obligations"].split())
        self.assertIn("their pacing is asserted to differ as the migration table states", obligations)

    def test_qualification_never_falls_back_across_families(self) -> None:
        qualification = " ".join(self.text.split())
        for required in (
            "There is no auto-detection across families",
            "never switches an instance to another family on its own",
            "Anything not positively admitted is withheld",
            "A withheld instance of this kind sends no request",
            "`FAMILY_NOT_ADMITTED`",
            "`FOREIGN_FAMILY_IDENTITY`",
            "`AMBIGUOUS_RESULT`",
            "`INSUFFICIENT_EVIDENCE`",
            "`TUPLE_NOT_ADMITTED`",
            "`ASSET_CONFLICT`",
        ):
            self.assertIn(required, qualification)

    def test_sunspec_instances_have_a_selectable_cached_status_surface(self) -> None:
        rows = table_with(self.sections["Observability"], "Surface")
        sunspec = [row for row in rows if "modbus.v1.fronius.sunspec.status.get" in row[0]]
        self.assertEqual(len(sunspec), 1)
        self.assertIn("existing SunSpec status tool", sunspec[0][0])
        for required in (
            "`instance`",
            "qualification posture",
            "closed reason",
            "asset IDs",
            "cached",
            "withheld ones included",
            "`helianthus.runtime.list`",
            "The lifecycle projection stays unchanged",
        ):
            self.assertIn(required, sunspec[0][1])
        self.assertNotIn("modbus.v1.sunspec.status.get", self.text)
        baseline = table_with(self.sections["Baseline: configuration v1"], "Statement")
        existing = [row for row in baseline if "modbus.v1.fronius.sunspec.status.get" in row[0]]
        self.assertEqual(len(existing), 1)
        self.assertTrue(existing[0][1].startswith("Proven"))
        observability = " ".join(self.sections["Observability"].split())
        self.assertIn(
            "applies to the three vendor status tools and to `modbus.v1.fronius.sunspec.status.get`",
            observability,
        )
        self.assertIn("in the second phase of [gateway issue #1362]", observability)
        self.assertIn("helianthus-ebusgateway/issues/1362", observability)
        self.assertIn("[gateway issue #1364]", observability)
        self.assertIn("helianthus-ebusgateway/issues/1364", observability)
        posture = table_with(self.sections["Driver instances"], "Posture")
        reasons = {row[1].strip("`") for row in posture}
        for reason in ("TUPLE_NOT_ADMITTED", "AMBIGUOUS_RESULT", "INSUFFICIENT_EVIDENCE", "ASSET_CONFLICT"):
            self.assertIn(reason, reasons)
            self.assertIn(f"`{reason}`", observability)

    def test_examples_hold_no_endpoint_address_serial_or_pin(self) -> None:
        for uri in re.findall(r"tcp://[^\s\"`]+", self.text):
            if uri != "tcp://host:port":
                self.assertRegex(uri, r"^tcp://[a-z0-9.-]+\.example\.invalid:[0-9]{3,5}$")
        for candidate in re.findall(r"[0-9A-Fa-f:.]{7,}", self.text):
            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                continue
            self.fail(f"address literal {candidate!r}")
        self.assertIsNone(re.search(r"\b[0-9a-f]{40}\b|\b[0-9a-f]{64}\b", self.text))
        legacy = "|".join(("ma" + "ster", "sl" + "ave"))
        self.assertIsNone(re.search(rf"\b({legacy})\b", self.text, re.I))

    def test_pages_link_the_multi_endpoint_contract(self) -> None:
        successor = CONTRACT.read_text(encoding="utf-8").split("## Multi-Endpoint Successor\n", 1)[1]
        self.assertIn("modbus-multi-endpoint-runtime.md", successor)
        self.assertIn("exactly as this page states", successor)
        mcp = (ROOT / "api" / "mcp.md").read_text(encoding="utf-8")
        platform = (ROOT / "docs" / "platform" / "README.md").read_text(encoding="utf-8")
        self.assertIn("modbus-multi-endpoint-runtime.md", mcp)
        self.assertIn("the existing SunSpec status tool", " ".join(mcp.split()))
        self.assertIn("../../api/modbus-multi-endpoint-runtime.md", platform)
        self.assertIn("modbus-v1-addon-runtime.md", self.text)


if __name__ == "__main__":
    unittest.main()
