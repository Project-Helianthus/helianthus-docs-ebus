"""Synthetic checks for symbol identity, debt ceilings and fail-closed tools."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "readability_gate", Path(__file__).resolve().parents[1] / "scripts/check_readability.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def baseline_text(records):
    return json.dumps(dict(schema_version=1, ruff_version=GATE.RUFF_VERSION,
                           generation="Reviewed synthetic findings", findings=records))


def record(**changes):
    result = dict(path="scripts/sample.py", symbol="inspect_values", rule="C901", count=12)
    result.update(changes)
    return result


class TestDebtCeilings(unittest.TestCase):
    def test_clean_inputs_and_existing_debt_pass(self):
        self.assertEqual(GATE.compare_findings({}, {}), [])
        key = GATE.record_key(record())
        self.assertEqual(GATE.compare_findings({key: 12}, {key: 12}), [])

    def test_new_and_grown_findings_fail(self):
        key = GATE.record_key(record())
        self.assertTrue(GATE.compare_findings({key: 12}, {}))
        self.assertTrue(GATE.compare_findings({key: 13}, {key: 12}))

    def test_reduced_findings_pass_and_deleted_debt_requires_removal(self):
        key = GATE.record_key(record())
        self.assertEqual(GATE.compare_findings({key: 11}, {key: 12}), [])
        self.assertTrue(GATE.compare_findings({}, {key: 12}))
        self.assertEqual(GATE.compare_findings({}, {}), [])

    def test_every_identity_field_distinguishes_new_debt(self):
        original = GATE.record_key(record())
        for field, value in (("path", "tests/sample.py"),
                             ("symbol", "other_values"), ("rule", "PLR0915")):
            with self.subTest(field=field):
                changed = GATE.record_key(record(**{field: value}))
                self.assertTrue(GATE.compare_findings({changed: 12}, {original: 12}))

    def test_duplicate_and_malformed_baselines_fail(self):
        invalid = ["{", "[]", baseline_text([record(), record()]),
                   baseline_text([record(count=True)]), baseline_text([record(count=0)]),
                   baseline_text([record(path="../sample.py")]),
                   baseline_text([record(path="/scripts/sample.py")]),
                   baseline_text([record(symbol="")]), baseline_text([record(rule="bad")]),
                   baseline_text([dict(record(), extra=1)]),
                   baseline_text([record()]).replace('"schema_version": 1',
                                                    '"schema_version": 1, "schema_version": 1')]
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    GATE.read_baseline(text)

    def test_wrong_tool_version_fails(self):
        text = baseline_text([]).replace(GATE.RUFF_VERSION, "0.0.0")
        with self.assertRaises(ValueError):
            GATE.read_baseline(text)


class TestFindingCollection(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "scripts").mkdir()
        (self.root / "tests").mkdir()
        self.path = self.root / "scripts/sample.py"

    def findings(self, source, rule="C901", message="complexity (12 > 10)", row=1):
        self.path.write_text(source)
        text = json.dumps([dict(filename=str(self.path), code=rule, message=message,
                                location=dict(row=row, column=5))])
        return GATE.collect_findings(text, self.root)

    def test_moved_symbols_keep_identity(self):
        source = "def inspect_values():\n    pass\n"
        before = self.findings(source)
        after = self.findings("\n\n" + source, row=3)
        self.assertEqual(before, after)

    def test_nested_symbols_and_naming_targets_remain_distinct(self):
        source = "class Sample:\n    def inspect_values(self):\n        pass\n"
        result = self.findings(source, row=2)
        self.assertEqual(next(iter(result))[1], "Sample.inspect_values")
        first = self.findings("def BadName():\n    pass\n", "N802", "invalid name")
        second = self.findings("def OtherName():\n    pass\n", "N802", "invalid name")
        self.assertNotEqual(first, second)

    def test_statement_measurement_and_naming_occurrence_counts(self):
        source = "def inspect_values():\n    pass\n"
        result = self.findings(source, "PLR0915", "Too many statements (55 > 50)")
        self.assertEqual(list(result.values()), [55])
        self.path.write_text("BadName = 1\n")
        item = dict(filename=str(self.path), code="N816", message="invalid name",
                    location=dict(row=1, column=1))
        result = GATE.collect_findings(json.dumps([item, item]), self.root)
        self.assertEqual(list(result.values()), [2])

    def test_malformed_diagnostics_fail(self):
        for text in ("{", "{}", "[{}]", "[null]"):
            with self.subTest(text=text):
                with self.assertRaises((ValueError, KeyError)):
                    GATE.collect_findings(text, self.root)
        with self.assertRaises(ValueError):
            self.findings("def inspect_values():\n    pass\n", message="no measurement")

    def test_tool_failure_and_malformed_json_fail(self):
        version = subprocess.CompletedProcess([], 0, "ruff " + GATE.RUFF_VERSION, "")
        for failure in (subprocess.CompletedProcess([], 2, "[]", "tool error"),
                        subprocess.CompletedProcess([], 0, "{", ""),
                        subprocess.CompletedProcess([], 1, "[]", "")):
            calls = iter([version, failure])
            with self.subTest(failure=failure):
                with self.assertRaises(ValueError):
                    GATE.run_ruff(self.root, runner=lambda *args, **kwargs: next(calls))
        with self.assertRaises(FileNotFoundError):
            GATE.run_ruff(self.root, runner=self.missing_tool)

    @staticmethod
    def missing_tool(*args, **kwargs):
        raise FileNotFoundError("synthetic missing cached tool")

    def test_cached_ruff_clean_naming_default_rules_and_statement_limit(self):
        config = Path(__file__).resolve().parents[1] / "ruff.toml"
        (self.root / "ruff.toml").write_text(config.read_text())
        self.path.write_text("def inspect_values():\n    return 1\n")
        self.assertEqual(GATE.run_ruff(self.root), {})
        self.path.write_text("import os\n\ndef BadName():\n    pass\n")
        rules = {key[2] for key in GATE.run_ruff(self.root)}
        self.assertTrue({"F401", "N802"}.issubset(rules))
        self.path.write_text("def inspect_values():\n" + "    value = 1\n" * 51
                             + "    return value\n")
        findings = GATE.run_ruff(self.root)
        counts = [count for key, count in findings.items() if key[2] == "PLR0915"]
        self.assertTrue(counts)
        self.assertGreater(counts[0], 50)

    def test_cached_tool_version_and_timeout_fail_closed(self):
        wrong = subprocess.CompletedProcess([], 0, "ruff 0.0.0", "")
        with self.assertRaises(ValueError):
            GATE.run_ruff(self.root, runner=lambda *args, **kwargs: wrong)
        with self.assertRaises(subprocess.TimeoutExpired):
            GATE.run_ruff(self.root, runner=self.timed_out_tool)

    @staticmethod
    def timed_out_tool(*args, **kwargs):
        raise subprocess.TimeoutExpired("ruff", 30)

    def test_cached_ruff_rejects_new_function_in_baselined_file(self):
        config = Path(__file__).resolve().parents[1] / "ruff.toml"
        (self.root / "ruff.toml").write_text(config.read_text())
        self.path.write_text("def inspect_values(value):\n" + "".join(
            f"    if value == {index}:\n        return {index}\n" for index in range(12)))
        before = GATE.run_ruff(self.root)
        self.assertTrue(before)
        self.path.write_text("\n\n" + self.path.read_text())
        self.assertEqual(GATE.compare_findings(GATE.run_ruff(self.root), before), [])
        with self.path.open("a") as stream:
            stream.write(self.path.read_text().replace("inspect_values", "compare_values"))
        self.assertTrue(GATE.compare_findings(GATE.run_ruff(self.root), before))


def test_local_gate_runs_readability_with_hash_pinned_ruff():
    root = Path(__file__).resolve().parents[1]
    gate = (root / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 scripts/check_readability.py --self-test" in gate
    assert "python3 scripts/check_readability.py --check" in gate
    requirements = (root / "requirements-ci.txt").read_text(encoding="utf-8")
    ruff_entry = requirements.split("ruff==0.15.10 \\\n", 1)[1]
    assert ruff_entry.splitlines()[0].strip().startswith("--hash=sha256:")
