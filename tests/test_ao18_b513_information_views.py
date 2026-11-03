"""Finite documentation oracle; this suite does not execute a Go implementation."""

import copy
import json
from pathlib import Path
import unittest


ab17ao17Root = Path(__file__).resolve().parents[1]
ab17ao17Signature = (
    "Ab17Ao17Interpret(ab17ao17Input json.RawMessage) (json.RawMessage, error)"
)
ab17ao17Rows = [
    ["type", 3, ["modulating", "single-step", "two-step"]],
    ["capabilities", 4, ["floor-standing", "condensing", "fan-assisted",
                         "open-vented", "high-modulation-range", "water-heater",
                         "step-modulation", "ECS"]],
    ["fuel", 5, ["gas", "oil", "ABC"]],
    ["storage", 6, ["layer-tank", "warm-start", "external-tank", "combination"]],
    ["features", 7, ["solar-compact", "basic-solar", "AAPS", "advanced-power",
                     "partial-load", "parameter-master"]],
    ["pump_mode", 8, [0, 1]],
    ["opaque", [0, 1, 2, 9, 10, 11], []],
]


def ab17ao17Field(ab17ao17Raw, **ab17ao17Values):
    return {"raw": ab17ao17Raw, "state": "Hypothesis", **ab17ao17Values}


def ab17ao17Expected():
    """Construct named test vectors from constants, never decode supplied bytes."""
    ab17ao17Context = {"primary": 181, "secondary": 19, "operation": 7,
                      "direction": "positive", "view": "information",
                      "family": {"opaque": ["synthetic-family", 0]},
                      "variant": ["synthetic-variant", {"value": False}]}
    ab17ao17Raw = [41, 93, 207, 0, 0, 0, 0, 0, 0, 7, 8, 9]
    ab17ao17Fields = {
        "type": ab17ao17Field([0], number=0, label="modulating"),
        "capabilities": ab17ao17Field([0], flags=dict.fromkeys(ab17ao17Rows[1][2], False)),
        "fuel": ab17ao17Field([0], flags=dict.fromkeys(ab17ao17Rows[2][2], False), reserved=0),
        "storage": ab17ao17Field([0], flags=dict.fromkeys(ab17ao17Rows[3][2], False), reserved=0),
        "features": ab17ao17Field([0], flags=dict.fromkeys(ab17ao17Rows[4][2], False), reserved=0),
        "pump_mode": ab17ao17Field([0], number=0),
    }
    ab17ao17Cases = []

    def ab17ao17Add(ab17ao17Name, ab17ao17Input=None, ab17ao17Semantic=None,
                   ab17ao17State="Hypothesis"):
        if ab17ao17Input is None:
            ab17ao17Input = {"context": copy.deepcopy(ab17ao17Context),
                            "fields": {"logical_object": ab17ao17Raw[:]}}
        ab17ao17Output = {
            "context": copy.deepcopy(ab17ao17Input["context"]),
            "raw": copy.deepcopy(ab17ao17Input["fields"]),
            "state": ab17ao17State,
            "fields": copy.deepcopy(ab17ao17Fields if ab17ao17Semantic is None
                                    else ab17ao17Semantic),
            "physical": "Unknown", "qualified": False,
        }
        if "arguments" in ab17ao17Input:
            ab17ao17Output["arguments"] = copy.deepcopy(ab17ao17Input["arguments"])
        ab17ao17Cases.append({"id": "ab17ao17" + ab17ao17Name,
                              "input": ab17ao17Input, "output": ab17ao17Output})

    ab17ao17Add("Control")
    for ab17ao17Value, ab17ao17Label in [(0, "modulating"), (1, "single-step"),
                                        (2, "two-step"), (3, None), (255, None)]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["fields"]["logical_object"][3] = ab17ao17Value
        ab17ao17Semantic = copy.deepcopy(ab17ao17Fields)
        ab17ao17Semantic["type"] = (
            ab17ao17Field([ab17ao17Value], number=ab17ao17Value, label=ab17ao17Label)
            if ab17ao17Label else {"raw": [ab17ao17Value], "state": "Unknown"})
        ab17ao17Add("Type" + str(ab17ao17Value), ab17ao17Input, ab17ao17Semantic,
                   "Hypothesis" if ab17ao17Label else "partial")
    for ab17ao17Name, ab17ao17Position, ab17ao17Labels in ab17ao17Rows[1:5]:
        for ab17ao17Bit, ab17ao17Value in enumerate([1, 2, 4, 8, 16, 32, 64, 128]):
            ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
            ab17ao17Input["fields"]["logical_object"][ab17ao17Position] = ab17ao17Value
            ab17ao17Semantic = copy.deepcopy(ab17ao17Fields)
            ab17ao17Semantic[ab17ao17Name]["raw"] = [ab17ao17Value]
            if ab17ao17Bit < len(ab17ao17Labels):
                ab17ao17Semantic[ab17ao17Name]["flags"][ab17ao17Labels[ab17ao17Bit]] = True
            else:
                ab17ao17Semantic[ab17ao17Name]["reserved"] = ab17ao17Value
            ab17ao17Add(ab17ao17Name + "Bit" + str(ab17ao17Bit),
                       ab17ao17Input, ab17ao17Semantic)
    for ab17ao17Value in [0, 1, 2]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["fields"]["logical_object"][8] = ab17ao17Value
        ab17ao17Semantic = copy.deepcopy(ab17ao17Fields)
        ab17ao17Semantic["pump_mode"] = (
            ab17ao17Field([ab17ao17Value], number=ab17ao17Value)
            if ab17ao17Value < 2 else {"raw": [2], "state": "Unknown"})
        ab17ao17Add("Pump" + str(ab17ao17Value), ab17ao17Input, ab17ao17Semantic,
                   "Hypothesis" if ab17ao17Value < 2 else "partial")
    for ab17ao17Length in range(12):
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["fields"]["logical_object"] = ab17ao17Raw[:ab17ao17Length]
        # Extent thresholds select predeclared expectations; no byte is decoded.
        ab17ao17Semantic = {
            ab17ao17Name: (copy.deepcopy(ab17ao17Fields[ab17ao17Name])
                          if ab17ao17Length > ab17ao17Position
                          else {"raw": [], "state": "Unknown"})
            for ab17ao17Name, ab17ao17Position, _ in ab17ao17Rows[:6]
        }
        ab17ao17Add("Length" + str(ab17ao17Length), ab17ao17Input,
                   ab17ao17Semantic, "partial")
    for ab17ao17Name, ab17ao17FieldName, ab17ao17Value in [
        ("Tail", "logical_object", ab17ao17Raw + [233, 17]),
        ("ExtraEmpty", "extension", []), ("ExtraZero", "extension", [0]),
        ("ExtraBytes", "extension", [7, 8, 9]),
    ]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["fields"][ab17ao17FieldName] = ab17ao17Value
        ab17ao17Add(ab17ao17Name, ab17ao17Input)
    for ab17ao17Position in [0, 1, 2, 9, 10, 11]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["fields"]["logical_object"][ab17ao17Position] = 255
        ab17ao17Add("Opaque" + str(ab17ao17Position), ab17ao17Input)
    for ab17ao17Name, ab17ao17Key, ab17ao17Value in [
        ("Primary", "primary", 180), ("Secondary", "secondary", 18),
        ("Operation", "operation", 8), ("Op00", "operation", 0),
        ("Op04", "operation", 4), ("Direction", "direction", "request"),
        ("View", "view", "feedback"), ("UnknownView", "view", "other"),
        ("UnknownDirection", "direction", "other"),
    ]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["context"][ab17ao17Key] = ab17ao17Value
        ab17ao17Add(ab17ao17Name, ab17ao17Input, {}, "Unknown")
    for ab17ao17Name, ab17ao17Key, ab17ao17Value in [
        ("Family", "family", {"opaque": ["another-family", 1]}),
        ("Variant", "variant", ["another-variant", {"value": True}]),
        ("ContextExtension", "extension", {"nested": [None, 0, False]}),
    ]:
        ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
        ab17ao17Input["context"][ab17ao17Key] = ab17ao17Value
        ab17ao17Add(ab17ao17Name, ab17ao17Input)
    ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
    ab17ao17Input["arguments"] = {}
    ab17ao17Add("EmptyArguments", ab17ao17Input)
    ab17ao17Input = copy.deepcopy(ab17ao17Cases[0]["input"])
    ab17ao17Input["fields"] = {}
    ab17ao17Add("MissingLogical", ab17ao17Input,
               {ab17ao17Name: {"raw": [], "state": "Unknown"}
                for ab17ao17Name in ab17ao17Fields}, "partial")
    for ab17ao17Operation, ab17ao17Negative in [(5, "not-accepted-or-not-supported"),
                                             (6, "rejected")]:
        for ab17ao17Byte in [0, 1, 2, 255]:
            ab17ao17Input = {"context": {**copy.deepcopy(ab17ao17Context),
                                         "operation": ab17ao17Operation,
                                         "view": "feedback"},
                            "fields": {"feedback": [ab17ao17Byte]}}
            ab17ao17Add("Feedback" + str(ab17ao17Operation) + "Byte" + str(ab17ao17Byte),
                       ab17ao17Input, {"feedback": ab17ao17Field(
                           [ab17ao17Byte], number=ab17ao17Byte,
                           label="accepted" if ab17ao17Byte == 1 else ab17ao17Negative)})
        for ab17ao17Suffix, ab17ao17RawFields in [
            ("Missing", {}), ("Empty", {"feedback": []}),
            ("Wide", {"feedback": [1, 0]}),
            ("LogicalOnly", {"logical_object": ab17ao17Raw}),
        ]:
            ab17ao17Input = {"context": {**copy.deepcopy(ab17ao17Context),
                                         "operation": ab17ao17Operation,
                                         "view": "feedback"},
                            "fields": ab17ao17RawFields}
            ab17ao17Add("Feedback" + str(ab17ao17Operation) + ab17ao17Suffix,
                       ab17ao17Input,
                       {"feedback": {"raw": ab17ao17RawFields.get("feedback", [])[:],
                                     "state": "Unknown"}}, "partial")
        for ab17ao17Key, ab17ao17Value in [("direction", "request"),
                                          ("view", "information")]:
            ab17ao17Input = {"context": {**copy.deepcopy(ab17ao17Context),
                                         "operation": ab17ao17Operation,
                                         "view": "feedback", ab17ao17Key: ab17ao17Value},
                            "fields": {"feedback": [1]}}
            ab17ao17Add("Feedback" + str(ab17ao17Operation) + ab17ao17Key,
                       ab17ao17Input, {}, "Unknown")
    return ab17ao17Cases


def ab17ao17Errors():
    ab17ao17Base = ab17ao17Expected()[0]["input"]
    ab17ao17Cases = [("Malformed", "{"), ("TopArray", "[]"),
                     ("Trailing", '{} {}'),
                     ("DuplicateRoot", '{"fields":{},"fields":{}}'),
                     ("DuplicateContext", '{"context":{"primary":181,"primary":181}}'),
                     ("DuplicateField", '{"fields":{"x":[],"x":[]}}'),
                     ("DuplicateArguments", '{"arguments":{"x":0,"x":0}}'),
                     ("DuplicateEscaped", '{"fields":{"x":[],"\\u0078":[]}}'),
                     ("DuplicateNested", '{"context":{"family":{"x":0,"x":1}}}')]
    for ab17ao17Key in ["context", "fields", "arguments"]:
        for ab17ao17Value in [None, [], 0, "bad", True]:
            ab17ao17Input = copy.deepcopy(ab17ao17Base)
            ab17ao17Input[ab17ao17Key] = ab17ao17Value
            ab17ao17Cases.append((ab17ao17Key + repr(ab17ao17Value), json.dumps(ab17ao17Input)))
    for ab17ao17Value in [-1, 256, 1.5, True, None, "1", [], {}]:
        ab17ao17Input = copy.deepcopy(ab17ao17Base)
        ab17ao17Input["fields"]["extension"] = [ab17ao17Value]
        ab17ao17Cases.append(("Byte" + repr(ab17ao17Value), json.dumps(ab17ao17Input)))
    for ab17ao17Value in [None, 0, "bytes", {}]:
        ab17ao17Input = copy.deepcopy(ab17ao17Base)
        ab17ao17Input["fields"]["logical_object"] = ab17ao17Value
        ab17ao17Cases.append(("Array" + repr(ab17ao17Value), json.dumps(ab17ao17Input)))
    for ab17ao17Key in ["context", "fields"]:
        ab17ao17Input = copy.deepcopy(ab17ao17Base)
        del ab17ao17Input[ab17ao17Key]
        ab17ao17Cases.append(("Missing" + ab17ao17Key, json.dumps(ab17ao17Input)))
    for ab17ao17Key in ["primary", "secondary", "operation", "direction", "view"]:
        ab17ao17Input = copy.deepcopy(ab17ao17Base)
        del ab17ao17Input["context"][ab17ao17Key]
        ab17ao17Cases.append(("Missing" + ab17ao17Key, json.dumps(ab17ao17Input)))
        ab17ao17Input["context"][ab17ao17Key] = (True if ab17ao17Key in
                                               ["primary", "secondary", "operation"] else 0)
        ab17ao17Cases.append(("Kind" + ab17ao17Key, json.dumps(ab17ao17Input)))
    ab17ao17Input = copy.deepcopy(ab17ao17Base)
    ab17ao17Input["arguments"] = {"enabled": True}
    ab17ao17Cases.append(("UndeclaredArgument", json.dumps(ab17ao17Input)))
    ab17ao17Input["arguments"] = {"mode": 0}
    ab17ao17Cases.append(("UndeclaredInteger", json.dumps(ab17ao17Input)))
    ab17ao17Input = copy.deepcopy(ab17ao17Base)
    ab17ao17Input["unexpected"] = 0
    ab17ao17Cases.append(("TopExtension", json.dumps(ab17ao17Input)))
    ab17ao17Cases.append(("ExponentByte", json.dumps(ab17ao17Base).replace(
        '41, 93', '4.1e1, 93')))
    ab17ao17Input = copy.deepcopy(ab17ao17Base)
    ab17ao17Input["context"]["operation"] = 99
    ab17ao17Input["fields"]["extension"] = [256]
    ab17ao17Cases.append(("UnknownInvalidByte", json.dumps(ab17ao17Input)))
    return [{"id": "ab17ao17" + ab17ao17Name, "input_json": ab17ao17Text,
             "error": True, "successful_result": False}
            for ab17ao17Name, ab17ao17Text in ab17ao17Cases]


def ab17ao17Contract():
    return {"api": ab17ao17Signature, "package": "vaillant", "physical": "Unknown",
            "qualified": False, "semantic_grade": "Hypothesis",
            "calculation_grade": "Proven", "field_table": ab17ao17Rows,
            "selection": [[181, 19, 7, "positive", "information"],
                          [181, 19, 5, "positive", "feedback"],
                          [181, 19, 6, "positive", "feedback"]],
            "cases": ab17ao17Expected(), "errors": ab17ao17Errors()}


def ab17ao17UniqueObject(ab17ao17Pairs):
    ab17ao17Object = {}
    for ab17ao17Key, ab17ao17Value in ab17ao17Pairs:
        if ab17ao17Key in ab17ao17Object:
            raise ValueError("duplicate contract-table key: " + ab17ao17Key)
        ab17ao17Object[ab17ao17Key] = ab17ao17Value
    return ab17ao17Object


class Ab17Ao17DocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab17ao17Fixture = json.loads((ab17ao17Root / "architecture/fixtures/ao18_b513_information_views.json").read_text(), object_pairs_hook=ab17ao17UniqueObject)
        cls.ab17ao17Text = (ab17ao17Root / "architecture/ao18_b513_information_views.md").read_text()
        cls.ab17ao17Page = json.loads(cls.ab17ao17Text.split("<!-- ab17ao17-finite-table -->\n```json\n", 1)[1].split("\n```", 1)[0], object_pairs_hook=ab17ao17UniqueObject)

    def ab17ao17AssertExact(self, ab17ao17Actual, ab17ao17ExpectedValue):
        # JSON spellings distinguish booleans from integer carriers.
        self.assertEqual(json.dumps(ab17ao17Actual, sort_keys=True),
                         json.dumps(ab17ao17ExpectedValue, sort_keys=True))

    def TestAb17Ao17PageExactContract(self):
        self.ab17ao17AssertExact(self.ab17ao17Page, ab17ao17Contract())

    def TestAb17Ao17FixtureExactContract(self):
        self.ab17ao17AssertExact(self.ab17ao17Fixture, ab17ao17Contract())

    def TestAb17Ao17ReadableTables(self):
        ab17ao17Tables = []
        ab17ao17Current = []
        for ab17ao17Line in self.ab17ao17Text.splitlines():
            if ab17ao17Line.startswith("|"):
                ab17ao17Current.append([ab17ao17Cell.strip()
                                       for ab17ao17Cell in ab17ao17Line.strip("|").split("|")])
            elif ab17ao17Current:
                ab17ao17Tables.append(ab17ao17Current)
                ab17ao17Current = []
        self.assertEqual(len(ab17ao17Tables), 3)
        self.assertEqual(ab17ao17Tables[0][2:], [
            ["181", "19", "7", "positive", "information", "logical_object"],
            ["181", "19", "5", "positive", "feedback", "feedback"],
            ["181", "19", "6", "positive", "feedback", "feedback"]])
        self.assertEqual(ab17ao17Tables[1][2:], [
            ["type", "3", "number 0 / modulating; 1 / single-step; 2 / two-step; 3..255 Unknown, no number or label"],
            ["capabilities", "4", "bits 0..7: floor-standing, condensing, fan-assisted, open-vented, high-modulation-range, water-heater, step-modulation, ECS; no reserved bits"],
            ["fuel", "5", "bits 0..2: gas, oil, ABC; reserved bits 3..7"],
            ["storage", "6", "bits 0..3: layer-tank, warm-start, external-tank, combination; reserved bits 4..7"],
            ["features", "7", "bits 0..5: solar-compact, basic-solar, AAPS, advanced-power, partial-load, parameter-master; reserved bits 6..7"],
            ["pump_mode", "8", "number 0 or 1, no invented label; 2..255 Unknown, no number or label"],
            ["no semantic field", "0..2, 9..11", "opaque; preserve in raw.logical_object only"]])
        self.assertEqual(ab17ao17Tables[2][2:], [
            ["5", "accepted", "not-accepted-or-not-supported"],
            ["6", "accepted", "rejected"]])

    def TestAb17Ao17Signature(self):
        self.assertEqual(self.ab17ao17Text.split("```go\n", 1)[1].split("\n```", 1)[0],
                         "func " + ab17ao17Signature)

    def TestAb17Ao17EveryCaseAndRoundTrip(self):
        for ab17ao17Source in [self.ab17ao17Page, self.ab17ao17Fixture]:
            for ab17ao17Actual, ab17ao17ExpectedCase in zip(ab17ao17Source["cases"], ab17ao17Expected()):
                with self.subTest(ab17ao17Case=ab17ao17ExpectedCase["id"]):
                    self.ab17ao17AssertExact(ab17ao17Actual, ab17ao17ExpectedCase)
                    self.ab17ao17AssertExact(json.loads(json.dumps(ab17ao17Actual)), ab17ao17ExpectedCase)

    def TestAb17Ao17StoredValuesIndependent(self):
        # JSON documents have value semantics; Go buffer aliasing remains untested.
        ab17ao17Case = copy.deepcopy(self.ab17ao17Fixture["cases"][0])
        ab17ao17Before = copy.deepcopy(ab17ao17Case["output"])
        ab17ao17Case["input"]["fields"]["logical_object"][0] = 0
        ab17ao17Case["input"]["context"]["family"]["opaque"][0] = "changed"
        self.assertEqual(ab17ao17Case["output"], ab17ao17Before)
        ab17ao17Case["output"]["raw"]["logical_object"][3] = 255
        self.assertEqual(ab17ao17Case["output"]["fields"]["type"]["raw"], [0])
        self.assertEqual(self.ab17ao17Fixture["cases"][0]["output"], ab17ao17Before)


def load_tests(ab17ao17Loader, ab17ao17Tests, ab17ao17Pattern):
    ab17ao17Loader.testMethodPrefix = "TestAb17Ao17"
    return ab17ao17Loader.loadTestsFromTestCase(Ab17Ao17DocumentationTests)


if __name__ == "__main__":
    unittest.main()
