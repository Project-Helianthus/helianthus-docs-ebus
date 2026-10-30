"""Finite document/tuple oracles; deliberately no sensor interpreter."""
import copy
import json
from pathlib import Path
import re
import unittest

ab27ao27Root = Path(__file__).resolve().parents[1]
ab27ao27Page = ab27ao27Root / "architecture/ao28_b523_sensor_views.md"
ab27ao27Fixture = ab27ao27Root / "architecture/fixtures/ao28_b523_sensor_views.json"

# Separate literal contract oracle, never derived from the page or fixture.
ab27ao27Contract = {'api': {'package': 'vaillant',
         'signature': 'Ab27Ao27Interpret(ab27ao27Input json.RawMessage) (json.RawMessage, error)',
         'dependencies': 'standard library only'},
 'selection': {'primary': 181,
               'secondary': 35,
               'direction': 'positive',
               'views': ['status-zero-valid', 'status-zero-valid-or-low'],
               'field': 'logical_object',
               'prefix': 'opaque',
               'physical': 'Unknown',
               'qualified': False},
 'layouts': [{'operation': 3,
              'extent': 18,
              'sensors': [['S1', 3], ['S2', 5], ['S3', 7], ['S4', 9], ['S5', 11], ['S6', 13]],
              'pwm': 15,
              'status': [[16, ['S1', 'S2', 'S3', 'S4']], [17, ['S5', 'S6']]],
              'reserved': [17, [4, 5, 6, 7]]},
             {'operation': 6,
              'extent': 19,
              'sensors': [['S1', 3],
                          ['S2', 5],
                          ['S3', 7],
                          ['S4', 9],
                          ['S5', 11],
                          ['S6', 13],
                          ['S7', 15]],
              'status': [[17, ['S1', 'S2', 'S3', 'S4']], [18, ['S5', 'S6', 'S7']]],
              'reserved': [18, [6, 7]]},
             {'operation': 7,
              'extent': 18,
              'sensors': [['S8', 3], ['S9', 5], ['S10', 7], ['S11', 9], ['S12', 12], ['S13', 14]],
              'opaque': 11,
              'status': [[16, ['S8', 'S9', 'S10', 'S11']], [17, ['S12', 'S13']]],
              'reserved': [17, [4, 5, 6, 7]]}],
 'words': [{'bytes': [0, 128], 'raw': 32768, 'label': 'replacement'},
           {'bytes': [16, 0], 'raw': 16, 'number': 1},
           {'bytes': [240, 255], 'raw': 65520, 'number': -1},
           {'bytes': [255, 127], 'raw': 32767, 'number': 2047.9375},
           {'bytes': [1, 128], 'raw': 32769, 'number': -2047.9375},
           {'bytes': [0, 0], 'raw': 0, 'number': 0}],
 'status_labels': {'status-zero-valid': ['valid-value',
                                         'open-circuit',
                                         'closed-circuit',
                                         'high-level'],
                   'status-zero-valid-or-low': ['valid-value-or-low-level',
                                                'open-circuit',
                                                'closed-circuit',
                                                'high-level']},
 'pwm': {'bytes': [255], 'number': 127.5, 'unit': 'percent'},
 'grades': {'semantic': 'Hypothesis',
            'calculation': 'Proven',
            'native_support': 'Unknown',
            'effects': 'Unknown',
            'persistence': 'Unknown'},
 'errors': ['malformed-json',
            'duplicate-root',
            'duplicate-context',
            'duplicate-fields',
            'duplicate-arguments',
            'root-array',
            'context-array',
            'fields-array',
            'arguments-array',
            'byte-negative',
            'byte-overflow',
            'byte-fraction',
            'byte-bool',
            'byte-string',
            'byte-null',
            'field-scalar',
            'operation-string'],
 'scope': {'wire_codec': False,
           'request_encoder': False,
           'runtime_call_site': False,
           'catalog': False,
           'qualification': False},
 'case_families': ['word',
                   'status',
                   'reserved',
                   'pwm',
                   'opaque',
                   'partial',
                   'tail',
                   'selection',
                   'context',
                   'raw-field',
                   'arguments',
                   'error']}

ab27ao27Contract["json_shapes"] = {'input_required': ['context', 'fields'],
 'input_optional': ['arguments'],
 'context_required': ['primary', 'secondary', 'operation', 'direction', 'view'],
 'output_required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
 'output_optional': ['arguments'],
 'field_required': ['raw', 'state'],
 'field_optional': ['number', 'label', 'flags', 'reserved', 'candidate_domain', 'calculation'],
 'complete_state': 'Hypothesis',
 'partial_state': 'partial',
 'unknown_state': 'Unknown',
 'replacement_number_present': False,
 'incomplete_number_present': False,
 'physical': 'Unknown',
 'qualified': False,
 'copy': 'independent deep copies',
 'unknown_selection_fields': {},
 'undefined_arguments': []}

# Each row constructs an input and its known assertion from fixed constants;
# no function here consumes an arbitrary sensor input to calculate an output.
ab27ao27Sensors = {
    3: (("S1", 3), ("S2", 5), ("S3", 7), ("S4", 9), ("S5", 11), ("S6", 13)),
    6: (("S1", 3), ("S2", 5), ("S3", 7), ("S4", 9), ("S5", 11), ("S6", 13), ("S7", 15)),
    7: (("S8", 3), ("S9", 5), ("S10", 7), ("S11", 9), ("S12", 12), ("S13", 14)),
}
ab27ao27Extents = {3: 18, 6: 19, 7: 18}
ab27ao27WordCases = (
    ([0, 128], {"raw": 32768, "state": "Hypothesis", "label": "replacement"}),
    ([16, 0], {"raw": 16, "state": "Hypothesis", "number": 1, "calculation": "Proven"}),
    ([240, 255], {"raw": 65520, "state": "Hypothesis", "number": -1, "calculation": "Proven"}),
    ([255, 127], {"raw": 32767, "state": "Hypothesis", "number": 2047.9375, "calculation": "Proven"}),
    ([1, 128], {"raw": 32769, "state": "Hypothesis", "number": -2047.9375, "calculation": "Proven"}),
    ([0, 0], {"raw": 0, "state": "Hypothesis", "number": 0, "calculation": "Proven"}),
)
ab27ao27Statuses = {
    3: ((16, ("S1", "S2", "S3", "S4")), (17, ("S5", "S6"))),
    6: ((17, ("S1", "S2", "S3", "S4")), (18, ("S5", "S6", "S7"))),
    7: ((16, ("S8", "S9", "S10", "S11")), (17, ("S12", "S13"))),
}
ab27ao27Labels = {
    "status-zero-valid": ("valid-value", "open-circuit", "closed-circuit", "high-level"),
    "status-zero-valid-or-low": ("valid-value-or-low-level", "open-circuit", "closed-circuit", "high-level"),
}
ab27ao27Reserved = {3: (17, (16, 32, 64, 128)), 6: (18, (64, 128)), 7: (17, (16, 32, 64, 128))}
# Complete word counts for every truncated extent, explicit rather than decoded.
ab27ao27PartialCounts = {
    3: (0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6),
    6: (0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7),
    7: (0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6),
}


def ab27ao27Strict(ab27ao27Text):
    def ab27ao27Pairs(ab27ao27Items):
        ab27ao27Result = {}
        for ab27ao27Key, ab27ao27Value in ab27ao27Items:
            if ab27ao27Key in ab27ao27Result:
                raise ValueError("duplicate contract key")
            ab27ao27Result[ab27ao27Key] = ab27ao27Value
        return ab27ao27Result
    return json.loads(ab27ao27Text, object_pairs_hook=ab27ao27Pairs)


class TestAb27Ao27SensorViews(unittest.TestCase):
    def setUp(self):
        self.ab27ao27Fixture = ab27ao27Strict(ab27ao27Fixture.read_text())
        self.ab27ao27Rows = {ab27ao27Row["id"]: ab27ao27Row for ab27ao27Row in self.ab27ao27Fixture["cases"]}
        self.assertEqual(len(self.ab27ao27Rows), len(self.ab27ao27Fixture["cases"]))
        self.assertEqual(len(self.ab27ao27Rows), 370)
        self.assertEqual(self.ab27ao27Fixture["id"], "ab27ao27SensorViews")
        ab27ao27Match = re.search(r"<!-- ab27ao27-contract:start -->\s*```json\s*(.*?)\s*```\s*<!-- ab27ao27-contract:end -->", ab27ao27Page.read_text(), re.S)
        self.assertIsNotNone(ab27ao27Match)
        self.ab27ao27Table = ab27ao27Strict(ab27ao27Match.group(1))

    def ab27ao27Base(self, ab27ao27Op):
        return [165, 90, 222] + [0] * (ab27ao27Extents[ab27ao27Op] - 3)

    def ab27ao27Case(self, ab27ao27Id, ab27ao27Op=3, ab27ao27Data=None,
                    ab27ao27Expect=None, ab27ao27View="status-zero-valid",
                    ab27ao27Context=None, ab27ao27Fields=None, ab27ao27Args=None):
        ab27ao27Ctx = dict(primary=181, secondary=35, operation=ab27ao27Op,
                          direction="positive", view=ab27ao27View,
                          family="synthetic-family", variant="synthetic-variant")
        ab27ao27Ctx.update(ab27ao27Context or {})
        ab27ao27Input = {"context": ab27ao27Ctx, "fields": ab27ao27Fields if ab27ao27Fields is not None else {"logical_object": ab27ao27Data}}
        if ab27ao27Args is not None:
            ab27ao27Input["arguments"] = ab27ao27Args
        ab27ao27Expected = {"id": "ab27ao27" + ab27ao27Id, "input": ab27ao27Input, "expect": ab27ao27Expect}
        with self.subTest(ab27ao27Id=ab27ao27Id):
            self.assertEqual(json.dumps(self.ab27ao27Rows[ab27ao27Expected["id"]], sort_keys=True), json.dumps(ab27ao27Expected, sort_keys=True))
            self.assertEqual(json.loads(json.dumps(ab27ao27Expected)), ab27ao27Expected)

    def test_ab27ao27_page_exact_contract(self):
        self.assertEqual(json.dumps(self.ab27ao27Table, sort_keys=True), json.dumps(ab27ao27Contract, sort_keys=True))

    def test_ab27ao27_all_nineteen_words_and_signed_boundaries(self):
        for ab27ao27Op, ab27ao27Positions in ab27ao27Sensors.items():
            for ab27ao27Name, ab27ao27Offset in ab27ao27Positions:
                for ab27ao27Index, (ab27ao27Bytes, ab27ao27Result) in enumerate(ab27ao27WordCases):
                    ab27ao27Data = self.ab27ao27Base(ab27ao27Op)
                    ab27ao27Data[ab27ao27Offset:ab27ao27Offset + 2] = ab27ao27Bytes
                    self.ab27ao27Case(f"word-{ab27ao27Op}-{ab27ao27Name}-{ab27ao27Index}", ab27ao27Op, ab27ao27Data,
                                     {"state": "Hypothesis", "field": ab27ao27Name, "result": ab27ao27Result})

    def test_ab27ao27_each_status_pair_both_views(self):
        for ab27ao27Op, ab27ao27Groups in ab27ao27Statuses.items():
            for ab27ao27Offset, ab27ao27Names in ab27ao27Groups:
                for ab27ao27Pair, ab27ao27Name in enumerate(ab27ao27Names):
                    for ab27ao27View, ab27ao27LabelsForView in ab27ao27Labels.items():
                        for ab27ao27Value, ab27ao27Label in enumerate(ab27ao27LabelsForView):
                            ab27ao27Data = self.ab27ao27Base(ab27ao27Op)
                            ab27ao27Data[ab27ao27Offset] = (ab27ao27Value * (1, 4, 16, 64)[ab27ao27Pair])
                            self.ab27ao27Case(f"status-{ab27ao27Op}-{ab27ao27Name}-{ab27ao27View}-{ab27ao27Value}", ab27ao27Op, ab27ao27Data,
                                             {"state": "Hypothesis", "field": ab27ao27Name + "_status", "result": {"raw": ab27ao27Value, "state": "Hypothesis", "label": ab27ao27Label}}, ab27ao27View)

    def test_ab27ao27_each_reserved_bit(self):
        for ab27ao27Op, (ab27ao27Offset, ab27ao27Masks) in ab27ao27Reserved.items():
            for ab27ao27Bit, ab27ao27Mask in zip((4, 5, 6, 7) if ab27ao27Op != 6 else (6, 7), ab27ao27Masks):
                ab27ao27Data = self.ab27ao27Base(ab27ao27Op)
                ab27ao27Data[ab27ao27Offset] = ab27ao27Mask
                self.ab27ao27Case(f"reserved-{ab27ao27Op}-{ab27ao27Bit}", ab27ao27Op, ab27ao27Data,
                                 {"state": "Hypothesis", "reserved": {"offset": ab27ao27Offset, "value": ab27ao27Mask}})

    def test_ab27ao27_every_partial_extent_and_tail(self):
        for ab27ao27Op, ab27ao27Counts in ab27ao27PartialCounts.items():
            for ab27ao27Length, ab27ao27Count in enumerate(ab27ao27Counts):
                ab27ao27Names = [ab27ao27Name for ab27ao27Name, _ in ab27ao27Sensors[ab27ao27Op]][:ab27ao27Count]
                self.ab27ao27Case(f"partial-{ab27ao27Op}-{ab27ao27Length}", ab27ao27Op, self.ab27ao27Base(ab27ao27Op)[:ab27ao27Length],
                                 {"state": "partial", "complete_sensors": ab27ao27Names, "numeric_zero_sensors": ab27ao27Names})
            self.ab27ao27Case(f"tail-{ab27ao27Op}", ab27ao27Op, self.ab27ao27Base(ab27ao27Op) + [1, 254, 0],
                             {"state": "Hypothesis", "tail": [1, 254, 0]})

    def test_ab27ao27_pwm_and_opaque_separation(self):
        ab27ao27Data = self.ab27ao27Base(3)
        ab27ao27Data[15] = 255
        self.ab27ao27Case("pwm", 3, ab27ao27Data, {"state": "Hypothesis", "field": "PWM", "result": {"raw": 255, "state": "Hypothesis", "number": 127.5, "calculation": "Proven"}})
        ab27ao27Data = self.ab27ao27Base(7)
        ab27ao27Data[11:14] = [231, 16, 0]
        self.ab27ao27Case("opaque", 7, ab27ao27Data, {"state": "Hypothesis", "opaque": {"offset": 11, "raw": 231}, "field": "S12", "result": {"raw": 16, "state": "Hypothesis", "number": 1, "calculation": "Proven"}})

    def test_ab27ao27_selection_and_opaque_context_axes(self):
        for ab27ao27Key, ab27ao27Value in (("operation", 0), ("operation", 255), ("direction", "negative"), ("direction", ""), ("view", "unknown"), ("view", "")):
            self.ab27ao27Case(f"selection-{ab27ao27Key}-{ab27ao27Value}", 3, self.ab27ao27Base(3), {"state": "Unknown", "fields": {}}, ab27ao27Context={ab27ao27Key: ab27ao27Value})
        for ab27ao27Key, ab27ao27Value in (("primary", 0), ("secondary", 0), ("family", "other-family"), ("variant", {"opaque": [0, False]}), ("extra", {"nested": ["opaque", 0]})):
            self.ab27ao27Case("context-" + ab27ao27Key, 3, self.ab27ao27Base(3), {"preserve_context": True, "physical": "Unknown", "qualified": False}, ab27ao27Context={ab27ao27Key: ab27ao27Value})

    def test_ab27ao27_missing_empty_zero_and_unmodelled_fields(self):
        for ab27ao27Key, ab27ao27Fields in (("missing", {}), ("empty", {"logical_object": []}), ("zero", {"logical_object": [0]}), ("extra", {"logical_object": self.ab27ao27Base(3), "unmodelled": [0, 255]}), ("only-other", {"unmodelled": [0, 255]})):
            self.ab27ao27Case("raw-field-" + ab27ao27Key, ab27ao27Fields=ab27ao27Fields,
                             ab27ao27Expect={"preserve_raw": True, "state": "Hypothesis" if ab27ao27Key == "extra" else "partial"})
        self.ab27ao27Case("arguments-empty", 3, self.ab27ao27Base(3), {"preserve_arguments": {}}, ab27ao27Args={})

    def test_ab27ao27_error_vectors(self):
        ab27ao27Errors = {
            "malformed-json": "{",
            "duplicate-root": '{"context":{},"context":{},"fields":{}}',
            "duplicate-context": '{"context":{"operation":3,"operation":6},"fields":{}}',
            "duplicate-fields": '{"context":{},"fields":{"logical_object":[],"logical_object":[]}}',
            "duplicate-arguments": '{"context":{},"fields":{},"arguments":{"x":0,"x":1}}',
            "root-array": "[]",
        }
        ab27ao27Valid = {"context": {"primary": 181, "secondary": 35, "operation": 3, "direction": "positive", "view": "status-zero-valid"}, "fields": {"logical_object": []}}
        for ab27ao27Key in ("context", "fields", "arguments"):
            ab27ao27Input = copy.deepcopy(ab27ao27Valid)
            ab27ao27Input[ab27ao27Key] = []
            ab27ao27Errors[ab27ao27Key + "-array"] = json.dumps(ab27ao27Input, separators=(",", ":"))
        for ab27ao27Key, ab27ao27Value in (("negative", -1), ("overflow", 256), ("fraction", 0.5), ("bool", True), ("string", "0"), ("null", None)):
            ab27ao27Input = copy.deepcopy(ab27ao27Valid)
            ab27ao27Input["fields"]["logical_object"] = [ab27ao27Value]
            ab27ao27Errors["byte-" + ab27ao27Key] = json.dumps(ab27ao27Input, separators=(",", ":"))
        for ab27ao27Name, ab27ao27Key, ab27ao27Value in (("field-scalar", "fields", 0), ("operation-string", "context", "3")):
            ab27ao27Input = copy.deepcopy(ab27ao27Valid)
            ab27ao27Input[ab27ao27Key]["logical_object" if ab27ao27Key == "fields" else "operation"] = ab27ao27Value
            ab27ao27Errors[ab27ao27Name] = json.dumps(ab27ao27Input, separators=(",", ":"))
        self.assertEqual(set(ab27ao27Errors), set(ab27ao27Contract["errors"]))
        for ab27ao27Name, ab27ao27Text in ab27ao27Errors.items():
            with self.subTest(ab27ao27Error=ab27ao27Name):
                self.assertEqual(self.ab27ao27Rows["ab27ao27error-" + ab27ao27Name], {"id": "ab27ao27error-" + ab27ao27Name, "input_json": ab27ao27Text, "expect": {"error": True, "successful_result": False}})

    def test_ab27ao27_case_family_counts_and_schema(self):
        self.assertEqual(set(self.ab27ao27Fixture), {"id", "cases"})
        ab27ao27Counts = {"word": 114, "status": 152, "reserved": 10,
                         "partial": 55, "tail": 3, "pwm": 1, "opaque": 1,
                         "selection": 6, "context": 5, "raw": 5,
                         "arguments": 1, "error": 17}
        for ab27ao27Family, ab27ao27Count in ab27ao27Counts.items():
            self.assertEqual(sum(ab27ao27Id.startswith("ab27ao27" + ab27ao27Family + "-") or ab27ao27Id == "ab27ao27" + ab27ao27Family for ab27ao27Id in self.ab27ao27Rows), ab27ao27Count)
        for ab27ao27Row in self.ab27ao27Rows.values():
            self.assertEqual(set(ab27ao27Row), {"id", "input_json" if "input_json" in ab27ao27Row else "input", "expect"})


if __name__ == "__main__":
    unittest.main()
