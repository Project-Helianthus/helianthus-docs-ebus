"""Finite documentation oracles; these do not execute the Go implementation."""

import copy
import json
from pathlib import Path
import re
import unittest


ab07ao07Root = Path(__file__).resolve().parents[1]
ab07ao07Signature = "Ab07Ao07Interpret(ab07ao07Input json.RawMessage) (json.RawMessage, error)"
# Independent row constants: key, kind, width, companion, offset, width.
ab07ao07Rows = [
    [0, "opaque", None, None, None, None],
    [1, "boolean-carrier", 1, None, None, None],
    [2, "u8", 1, None, None, None],
    [3, "i8", 1, None, None, None],
    [4, "u16", 2, None, None, None],
    [5, "i16", 2, None, None, None],
    [6, "u32", 4, None, None, None],
    [7, "i32", 4, None, None, None],
    [8, "secure-boolean", 1, None, None, None],
    [9, "u8", 1, "inverse", 1, 1],
    [10, "i8", 1, "inverse", 1, 1],
    [11, "u16", 2, "inverse", 2, 2],
    [12, "i16", 2, "inverse", 2, 2],
    [13, "u32", 4, "inverse", 4, 4],
    [14, "i32", 4, "inverse", 4, 4],
    [15, "opaque", None, None, None, None],
    [16, "opaque", None, None, None, None],
    [17, "signed-temperature-candidate", 2, "status", 2, 1],
    [18, "signed-temperature-candidate", 2, "inverse", 2, 2],
]


def ab07ao07Field(ab07ao07Raw, ab07ao07State="Hypothesis", **ab07ao07Extra):
    return {"raw": ab07ao07Raw, "state": ab07ao07State, **ab07ao07Extra}


def ab07ao07Golden():
    """Build fixed expected vectors, never interpret an arbitrary input object."""
    ab07ao07Cases = []
    ab07ao07Context = {"primary": 181, "secondary": 14, "operation": 2,
                       "direction": "positive", "view": "row-spans",
                       "family": {"opaque": "synthetic-family"},
                       "variant": ["synthetic-variant", 0]}

    def ab07ao07Add(ab07ao07Id, ab07ao07Key, ab07ao07Value,
                   ab07ao07Fields, ab07ao07State="complete"):
        ab07ao07Input = {"context": copy.deepcopy(ab07ao07Context),
                         "fields": {"key": [ab07ao07Key], "value": ab07ao07Value}}
        ab07ao07Output = {"context": copy.deepcopy(ab07ao07Context),
                          "raw": copy.deepcopy(ab07ao07Input["fields"]),
                          "state": ab07ao07State, "fields": ab07ao07Fields,
                          "physical": "Unknown", "qualified": False}
        ab07ao07Cases.append({"id": "ab07ao07_" + ab07ao07Id,
                              "input": ab07ao07Input, "expected": ab07ao07Output})

    # Fixed asymmetric bytes expose any guessed byte order or complement rule.
    # Each tuple states complete raw bytes, independent expected fields, short
    # raw bytes, independent short fields. No production decoding algorithm.
    ab07ao07Vectors = [
        (1, [2], {"value": ab07ao07Field([2], label="truth-unqualified")}, [], {"value": ab07ao07Field([], "Unknown")}),
        (2, [254], {"value": ab07ao07Field([254], number=254, calculation="Proven")}, [], {"value": ab07ao07Field([], "Unknown")}),
        (3, [255], {"value": ab07ao07Field([255], number=-1, calculation="Proven")}, [], {"value": ab07ao07Field([], "Unknown")}),
        (4, [16, 0], {"value": ab07ao07Field([16, 0])}, [16], {"value": ab07ao07Field([16], "Unknown")}),
        (5, [254, 128], {"value": ab07ao07Field([254, 128])}, [254], {"value": ab07ao07Field([254], "Unknown")}),
        (6, [16, 32, 48, 64], {"value": ab07ao07Field([16, 32, 48, 64])}, [16, 32, 48], {"value": ab07ao07Field([16, 32, 48], "Unknown")}),
        (7, [254, 128, 32, 16], {"value": ab07ao07Field([254, 128, 32, 16])}, [254, 128, 32], {"value": ab07ao07Field([254, 128, 32], "Unknown")}),
        (8, [15], {"value": ab07ao07Field([15], label="true")}, [], {"value": ab07ao07Field([], "Unknown")}),
        (9, [254, 18], {"value": ab07ao07Field([254], number=254, calculation="Proven"), "inverse": ab07ao07Field([18])}, [254], {"value": ab07ao07Field([254], number=254, calculation="Proven"), "inverse": ab07ao07Field([], "Unknown")}),
        (10, [255, 18], {"value": ab07ao07Field([255], number=-1, calculation="Proven"), "inverse": ab07ao07Field([18])}, [255], {"value": ab07ao07Field([255], number=-1, calculation="Proven"), "inverse": ab07ao07Field([], "Unknown")}),
        (11, [16, 0, 18, 52], {"value": ab07ao07Field([16, 0]), "inverse": ab07ao07Field([18, 52])}, [16, 0, 18], {"value": ab07ao07Field([16, 0]), "inverse": ab07ao07Field([18], "Unknown")}),
        (12, [254, 128, 18, 52], {"value": ab07ao07Field([254, 128]), "inverse": ab07ao07Field([18, 52])}, [254, 128, 18], {"value": ab07ao07Field([254, 128]), "inverse": ab07ao07Field([18], "Unknown")}),
        (13, [16, 32, 48, 64, 18, 52, 86, 120], {"value": ab07ao07Field([16, 32, 48, 64]), "inverse": ab07ao07Field([18, 52, 86, 120])}, [16, 32, 48, 64, 18, 52, 86], {"value": ab07ao07Field([16, 32, 48, 64]), "inverse": ab07ao07Field([18, 52, 86], "Unknown")}),
        (14, [254, 128, 32, 16, 18, 52, 86, 120], {"value": ab07ao07Field([254, 128, 32, 16]), "inverse": ab07ao07Field([18, 52, 86, 120])}, [254, 128, 32, 16, 18, 52, 86], {"value": ab07ao07Field([254, 128, 32, 16]), "inverse": ab07ao07Field([18, 52, 86], "Unknown")}),
        (17, [16, 0, 85], {"value": ab07ao07Field([16, 0]), "status": ab07ao07Field([85], label="short-circuit")}, [16, 0], {"value": ab07ao07Field([16, 0]), "status": ab07ao07Field([], "Unknown")}),
        (18, [16, 0, 18, 52], {"value": ab07ao07Field([16, 0]), "inverse": ab07ao07Field([18, 52])}, [16, 0, 18], {"value": ab07ao07Field([16, 0]), "inverse": ab07ao07Field([18], "Unknown")}),
    ]
    for ab07ao07Key, ab07ao07Raw, ab07ao07Full, ab07ao07Short, ab07ao07Partial in ab07ao07Vectors:
        ab07ao07Add(f"key{ab07ao07Key}_full", ab07ao07Key, ab07ao07Raw, ab07ao07Full)
        ab07ao07Add(f"key{ab07ao07Key}_short", ab07ao07Key, ab07ao07Short, ab07ao07Partial, "partial")
        ab07ao07Add(f"key{ab07ao07Key}_tail", ab07ao07Key, ab07ao07Raw + [222, 173], copy.deepcopy(ab07ao07Full))
    for ab07ao07Key in (0, 15, 16):
        for ab07ao07Suffix, ab07ao07Raw in (("empty", []), ("raw", [16]), ("tail", [16, 0, 222, 173])):
            ab07ao07Add(f"key{ab07ao07Key}_{ab07ao07Suffix}", ab07ao07Key, ab07ao07Raw,
                         {"value": ab07ao07Field(ab07ao07Raw, "Unknown")}, "Unknown")
    for ab07ao07Id, ab07ao07Key, ab07ao07Raw, ab07ao07Fields, ab07ao07State in (
        ("boolean_false", 8, [240], {"value": ab07ao07Field([240], label="false")}, "complete"),
        ("boolean_unmapped", 8, [0], {"value": ab07ao07Field([0], "Unknown")}, "Unknown"),
        ("status_okay", 17, [16, 0, 0], {"value": ab07ao07Field([16, 0]), "status": ab07ao07Field([0], label="okay")}, "complete"),
        ("status_interrupted", 17, [16, 0, 170], {"value": ab07ao07Field([16, 0]), "status": ab07ao07Field([170], label="interrupted")}, "complete"),
        ("status_unmapped", 17, [16, 0, 1], {"value": ab07ao07Field([16, 0]), "status": ab07ao07Field([1], "Unknown")}, "partial"),
        ("zero_u8", 2, [0], {"value": ab07ao07Field([0], number=0, calculation="Proven")}, "complete"),
        ("signed_positive", 3, [127], {"value": ab07ao07Field([127], number=127, calculation="Proven")}, "complete"),
        ("signed_minimum", 3, [128], {"value": ab07ao07Field([128], number=-128, calculation="Proven")}, "complete"),
        ("unknown_key", 19, [16, 0], {}, "Unknown"),
    ):
        ab07ao07Add(ab07ao07Id, ab07ao07Key, ab07ao07Raw, ab07ao07Fields, ab07ao07State)
    ab07ao07Control = copy.deepcopy(ab07ao07Cases[3])  # key2_full
    for ab07ao07Axis, ab07ao07Value in (("primary", 180), ("secondary", 15), ("operation", 3), ("direction", "request"), ("view", "unknown")):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_selector_" + ab07ao07Axis
        for ab07ao07Side in ("input", "expected"):
            ab07ao07Case[ab07ao07Side]["context"][ab07ao07Axis] = ab07ao07Value
        ab07ao07Case["expected"].update(state="Unknown", fields={})
        ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Axis, ab07ao07Value in (("family", {"opaque": "other-family"}), ("variant", ["other-variant", 1]), ("extra", {"nested": [0, None]})):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_context_" + ab07ao07Axis
        for ab07ao07Side in ("input", "expected"):
            ab07ao07Case[ab07ao07Side]["context"][ab07ao07Axis] = ab07ao07Value
        ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Axis in ("primary", "secondary", "operation", "direction", "view", "family", "variant"):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_absent_" + ab07ao07Axis
        for ab07ao07Side in ("input", "expected"):
            ab07ao07Case[ab07ao07Side]["context"].pop(ab07ao07Axis)
        if ab07ao07Axis not in ("family", "variant"):
            ab07ao07Case["expected"].update(state="Unknown", fields={})
        ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Axis, ab07ao07Value in (("primary", 0), ("secondary", 0), ("operation", 0), ("direction", ""), ("view", ""), ("family", {}), ("variant", [])):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_zero_empty_" + ab07ao07Axis
        for ab07ao07Side in ("input", "expected"):
            ab07ao07Case[ab07ao07Side]["context"][ab07ao07Axis] = ab07ao07Value
        if ab07ao07Axis not in ("family", "variant"):
            ab07ao07Case["expected"].update(state="Unknown", fields={})
        ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Id, ab07ao07Fields in (("missing_key", {"value": [254]}), ("empty_key", {"key": [], "value": [254]}), ("wide_key", {"key": [2, 0], "value": [254]}), ("missing_value", {"key": [2]})):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_" + ab07ao07Id
        ab07ao07Case["input"]["fields"] = ab07ao07Fields
        ab07ao07Case["expected"].update(raw=copy.deepcopy(ab07ao07Fields), state="Unknown", fields={})
        ab07ao07Cases.append(ab07ao07Case)
    ab07ao07Case = copy.deepcopy(ab07ao07Control)
    ab07ao07Case["id"] = "ab07ao07_extra_field"
    ab07ao07Case["input"]["fields"]["unmodelled"] = [0, 255, 18]
    ab07ao07Case["expected"]["raw"]["unmodelled"] = [0, 255, 18]
    ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Id, ab07ao07Raw in (("extra_empty", []), ("extra_zero", [0])):
        ab07ao07Case = copy.deepcopy(ab07ao07Control)
        ab07ao07Case["id"] = "ab07ao07_" + ab07ao07Id
        ab07ao07Case["input"]["fields"]["unmodelled"] = ab07ao07Raw
        ab07ao07Case["expected"]["raw"]["unmodelled"] = copy.deepcopy(ab07ao07Raw)
        ab07ao07Cases.append(ab07ao07Case)
    ab07ao07Case = copy.deepcopy(ab07ao07Control)
    ab07ao07Case["id"] = "ab07ao07_empty_arguments"
    ab07ao07Case["input"]["arguments"] = {}
    ab07ao07Case["expected"]["arguments"] = {}
    ab07ao07Cases.append(ab07ao07Case)
    for ab07ao07Key, ab07ao07Raw, ab07ao07Full, ab07ao07Short, ab07ao07Partial in ab07ao07Vectors:
        if ab07ao07Key < 9:
            continue
        ab07ao07Width = {9: 1, 10: 1, 11: 2, 12: 2, 13: 4, 14: 4, 17: 2, 18: 2}[ab07ao07Key]
        ab07ao07Companion = "status" if ab07ao07Key == 17 else "inverse"
        ab07ao07Add(f"key{ab07ao07Key}_value_short", ab07ao07Key,
                     ab07ao07Raw[:ab07ao07Width - 1],
                     {"value": ab07ao07Field(ab07ao07Raw[:ab07ao07Width - 1], "Unknown"),
                      ab07ao07Companion: ab07ao07Field([], "Unknown")}, "partial")
    return ab07ao07Cases


ab07ao07Errors = [
    ["ab07ao07_malformed", '{'],
    ["ab07ao07_trailing_json", '{} {}'],
    ["ab07ao07_missing_context", '{"fields":{}}'],
    ["ab07ao07_missing_fields", '{"context":{}}'],
    ["ab07ao07_duplicate_root", '{"context":{},"context":{},"fields":{}}'],
    ["ab07ao07_duplicate_context", '{"context":{"primary":181,"primary":181},"fields":{}}'],
    ["ab07ao07_duplicate_fields", '{"context":{},"fields":{"key":[2],"key":[2]}}'],
    ["ab07ao07_duplicate_opaque", '{"context":{"family":{"a":0,"a":1}},"fields":{}}'],
    ["ab07ao07_duplicate_arguments", '{"context":{},"fields":{},"arguments":{"flag":0,"flag":1}}'],
    ["ab07ao07_root_kind", '[]'],
    ["ab07ao07_null", 'null'],
]
for ab07ao07Axis in ("key", "value", "unmodelled"):
    for ab07ao07Id, ab07ao07Value in (("negative", -1), ("overflow", 256), ("fraction", 1.5), ("bool", True), ("null", None), ("string", "0"), ("object", {}), ("array", [])):
        ab07ao07Input = copy.deepcopy(ab07ao07Golden()[3]["input"])
        ab07ao07Input["fields"][ab07ao07Axis] = [ab07ao07Value]
        ab07ao07Errors.append(["ab07ao07_byte_" + ab07ao07Axis + "_" + ab07ao07Id, json.dumps(ab07ao07Input, separators=(",", ":"))])
for ab07ao07Id, ab07ao07Path, ab07ao07Value in (
    ("context_kind", "context", []), ("fields_kind", "fields", []),
    ("arguments_kind", "arguments", None), ("unknown_argument", "arguments", {"flag": True}),
):
    ab07ao07Input = copy.deepcopy(ab07ao07Golden()[3]["input"])
    ab07ao07Input[ab07ao07Path] = ab07ao07Value
    ab07ao07Errors.append(["ab07ao07_" + ab07ao07Id, json.dumps(ab07ao07Input, separators=(",", ":"))])
for ab07ao07Axis, ab07ao07Bad in (("primary", True), ("secondary", "14"), ("operation", 2.5), ("direction", 2), ("view", None)):
    ab07ao07Input = copy.deepcopy(ab07ao07Golden()[3]["input"])
    ab07ao07Input["context"][ab07ao07Axis] = ab07ao07Bad
    ab07ao07Errors.append(["ab07ao07_kind_" + ab07ao07Axis, json.dumps(ab07ao07Input, separators=(",", ":"))])
for ab07ao07Axis in ("key", "value", "unmodelled"):
    ab07ao07Input = copy.deepcopy(ab07ao07Golden()[3]["input"])
    ab07ao07Input["fields"][ab07ao07Axis] = None
    ab07ao07Errors.append(["ab07ao07_array_kind_" + ab07ao07Axis, json.dumps(ab07ao07Input, separators=(",", ":"))])


def ab07ao07Read(ab07ao07RootPath):
    ab07ao07Page = (ab07ao07RootPath / "architecture/ao08_b50e_row_spans.md").read_text()
    ab07ao07Blocks = re.findall(r"```json ab07ao07-contract\n(.*?)\n```", ab07ao07Page, re.S)
    if len(ab07ao07Blocks) != 1:
        raise AssertionError("exactly one finite contract block required")
    return json.loads(ab07ao07Blocks[0], object_pairs_hook=ab07ao07Unique), json.loads((ab07ao07RootPath / "architecture/fixtures/ao08_b50e_row_spans.json").read_text(), object_pairs_hook=ab07ao07Unique)


def ab07ao07Unique(ab07ao07Pairs):
    ab07ao07Object = {}
    for ab07ao07Key, ab07ao07Value in ab07ao07Pairs:
        if ab07ao07Key in ab07ao07Object:
            raise ValueError("duplicate contract key")
        ab07ao07Object[ab07ao07Key] = ab07ao07Value
    return ab07ao07Object


class Ab07Ao07ContractTests(unittest.TestCase):
    def TestAb07Ao07ExactPageAndFixture(self):
        ab07ao07Page, ab07ao07Fixture = ab07ao07Read(ab07ao07Root)
        for ab07ao07Artifact in (ab07ao07Page, ab07ao07Fixture):
            ab07ao07Expected = {
                "signature": ab07ao07Signature, "package": "vaillant",
                "row_columns": ["key", "kind", "width", "companion", "offset", "companion_width"],
                "rows": ab07ao07Rows, "cases": ab07ao07Golden(),
                "errors": [{"id": ab07ao07Id, "input_json": ab07ao07Raw, "error": True, "result": None} for ab07ao07Id, ab07ao07Raw in ab07ao07Errors],
            }
            # JSON spelling distinguishes true/1 and 1/1.0, unlike Python ==.
            self.assertEqual(json.dumps(ab07ao07Artifact, sort_keys=True),
                             json.dumps(ab07ao07Expected, sort_keys=True))

    def TestAb07Ao07FiniteCoverage(self):
        for ab07ao07Artifact in ab07ao07Read(ab07ao07Root):
            ab07ao07Cases = ab07ao07Artifact["cases"]
            self.assertEqual(len({ab07ao07Case["id"] for ab07ao07Case in ab07ao07Cases}), len(ab07ao07Cases))
            self.assertEqual({ab07ao07Case["input"]["fields"]["key"][0] for ab07ao07Case in ab07ao07Cases if ab07ao07Case["id"].endswith("_full")}, set(range(19)) - {0, 15, 16})
            for ab07ao07Case in ab07ao07Cases:
                with self.subTest(case=ab07ao07Case["id"]):
                    self.assertEqual(ab07ao07Case, json.loads(json.dumps(ab07ao07Case)))
                    self.assertEqual(ab07ao07Case["expected"]["raw"], ab07ao07Case["input"]["fields"])
                    self.assertEqual(ab07ao07Case["expected"]["context"], ab07ao07Case["input"]["context"])
                    self.assertIs(ab07ao07Case["expected"]["qualified"], False)
                    self.assertEqual(ab07ao07Case["expected"]["physical"], "Unknown")


def load_tests(ab07ao07Loader, ab07ao07Tests, ab07ao07Pattern):
    """Standard unittest discovery hook preserves the required test prefix."""
    ab07ao07Loader = unittest.TestLoader()
    ab07ao07Loader.testMethodPrefix = "TestAb07Ao07"
    return ab07ao07Loader.loadTestsFromTestCase(Ab07Ao07ContractTests)
