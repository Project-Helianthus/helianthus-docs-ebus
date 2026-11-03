# B520 actuator and sensor API results

Status: software API companion. Native support, effects and persistence are Unknown.
Family applicability is never qualified by this page; every semantic field is a
Hypothesis, and an exact arithmetic result may additionally carry
`calculation=Proven` without replacing that grade.

## Function

```go
func Ab23Ao23Interpret(ab23ao23Input json.RawMessage) (json.RawMessage, error)
```

Package `vaillant`, standard library only. The function is a pure selected
field/state interpreter: no global cache, catalog, metadata listing,
registration or runtime call site. It adds no protocol entry and no second
family schema. Identifiers introduced by it begin with `ab23ao23` or
`Ab23Ao23`; protocol field labels keep their literal names.

## Input

A JSON object with `context`, `fields` and optional `arguments`.

- `context` holds `primary` (181), `secondary` (32), `operation` (integer),
  `direction` and an explicit `view` token. Every other supplied key (opaque
  family or variant values) is preserved unchanged and never read.
- `fields` maps names to byte arrays; each element is an integer 0..255.
  The only field consumed is `logical_object`; other fields are preserved in
  `raw` untouched.
- `arguments` holds scalar booleans or integers only. They are copied to the
  output and do not change any result. Absent, `false` and `0` stay distinct.

Duplicate object keys at any depth, malformed JSON, a byte outside 0..255 or
of a non-integer kind, a wrong JSON kind for `context`, `fields`, a field or
`arguments`, a missing required context key, or a non-integer `operation`
return an error and no result.

## Selection tokens

The only known combination is operation 0 with view `logical_object` and
direction `request` (extent 10) or `positive` (extent 18). The view token
selects a software interpretation only. The view is never chosen from a name,
payload length or family label. Any other operation, direction, view, or a
primary/secondary other than 181/32 yields `state=unknown` with raw preserved,
`fields` empty and no guessed selection. Extents are logical sizes, not
physical lengths, and imply no acceptance.

The first three positions of each logical object are opaque (`prefix`,
state `opaque`, grade Unknown): preserved, never asserted or normalized, and
no identity is decoded from them.

## Output

Keys: `context` (deep copy), `raw` (independent copy of the supplied fields),
`arguments` (independent copy, only if supplied), `state`, `fields`,
`physical` (always `Unknown`) and `qualified` (always `false`).

`state` is `complete` when the logical object reaches the extent, `partial`
when it is shorter or absent, `unknown` for an unselected combination. Bytes
beyond the extent stay in `raw` and produce no field. Each result field has
`raw` (the bytes available to it), `state` and `grade` (`Hypothesis`), and
optionally `number`, `label`, `flags`, `reserved`, `candidate_domain` and
`calculation` (`Proven`). Field states: `ok`; `unmapped` (no number, no label);
`incomplete` (object shorter than the field end; no number); `missing`
(`logical_object` absent, as distinct from an empty array, which gives
`incomplete`); `opaque`. A partial result keeps every complete independent
field. Defaults of 0 are declarations only and are never inserted for missing
data; zero is not a sentinel. Results are fresh copies: mutating an output or
the input afterwards changes no other result or later call.

## Request (operation 0, direction `request`, extent 10)

| Field | Offset | Width | Result |
| --- | --- | --- | --- |
| prefix | 0 | 3 | opaque |
| relay | 3 | 1 | u8 raw as `number` |
| pwm1, pwm2 | 4, 5 | 1 | raw/2 percent, domain 0..127.5, not clipped at 100 |
| stepper | 6 | 1 | 0..240 steps; 255 label `calibrate_go_to_zero`, no number; 241..254 unmapped |
| led | 7 | 1 | 0 `disabled`, 1 `enabled`, others unmapped |
| ed | 8 | 1 | raw/2 percent, domain 0..127.5 |
| temperature_table | 9 | 1 | 0 `standard_3k3` (-13.5..116 C), 1 `extended_1k` (-20..155), 2 `low_temperature_15k` (-39..80), 3 `standard_1k` (-13.9..130), others unmapped |

## Positive (operation 0, direction `positive`, extent 18)

| Field | Offset | Width | Result |
| --- | --- | --- | --- |
| prefix | 0 | 3 | opaque |
| adc | 3 | 2 | LE u16, formal domain 0..1023 |
| temperature_1..4 | 5, 7, 9, 11 | 2 each | signed LE 16, number = raw/16 C, formal raw 0..3200 |
| reserved | 13 | 1 | `reserved` = byte, no number |
| impeller_hz | 14 | 2 | LE u16 Hz, formal 0..1000 |
| vortex_hz | 16 | 2 | LE u16 Hz, formal 0..350, candidate operational window 5..350 |

A value outside its formal domain keeps its number with
`candidate_domain=false`; a complete object is never rejected for it. A
negative temperature is not admitted merely by its signed type: `FFFF` gives
-0.0625 with `candidate_domain=false`, and `000C` bytes `00 0C` give 192 with
`true`. Raw 0 gives number 0 (no zero-unavailable meaning). `vortex_hz`
carries `flags` `formal_domain` and `operational_window` independently.
The 5 Hz / 4 Hz hysteresis is metadata only; no time-series algorithm is
defined. Active behavior and support remain Unknown, and no permission follows
from a candidate label.

## Structured contract

The block below is the machine-readable finite case table checked by
`tests/test_ao24_b520_actuator_views.py`. `logical_object` arrays are decimal
bytes; `expect` lists asserted field results only.

```json
{
 "function": "Ab23Ao23Interpret",
 "signature": "func Ab23Ao23Interpret(ab23ao23Input json.RawMessage) (json.RawMessage, error)",
 "package": "vaillant",
 "context": {
  "primary": 181,
  "secondary": 32,
  "operations": [
   0
  ],
  "directions": [
   "request",
   "positive"
  ],
  "views": [
   "logical_object"
  ],
  "required_keys": [
   "primary",
   "secondary",
   "operation",
   "direction",
   "view"
  ]
 },
 "input_keys": [
  "context",
  "fields",
  "arguments"
 ],
 "output_keys": [
  "context",
  "raw",
  "arguments",
  "state",
  "fields",
  "physical",
  "qualified"
 ],
 "output_constants": {
  "physical": "Unknown",
  "qualified": false,
  "field_grade": "Hypothesis",
  "calculation_grade": "Proven"
 },
 "result_states": [
  "complete",
  "partial",
  "unknown"
 ],
 "field_states": [
  "ok",
  "unmapped",
  "incomplete",
  "missing",
  "opaque"
 ],
 "extents": {
  "request": 10,
  "positive": 18
 },
 "field_tables": {
  "request": [
   {
    "name": "prefix",
    "offset": 0,
    "width": 3
   },
   {
    "name": "relay",
    "offset": 3,
    "width": 1
   },
   {
    "name": "pwm1",
    "offset": 4,
    "width": 1
   },
   {
    "name": "pwm2",
    "offset": 5,
    "width": 1
   },
   {
    "name": "stepper",
    "offset": 6,
    "width": 1
   },
   {
    "name": "led",
    "offset": 7,
    "width": 1
   },
   {
    "name": "ed",
    "offset": 8,
    "width": 1
   },
   {
    "name": "temperature_table",
    "offset": 9,
    "width": 1
   }
  ],
  "positive": [
   {
    "name": "prefix",
    "offset": 0,
    "width": 3
   },
   {
    "name": "adc",
    "offset": 3,
    "width": 2
   },
   {
    "name": "temperature_1",
    "offset": 5,
    "width": 2
   },
   {
    "name": "temperature_2",
    "offset": 7,
    "width": 2
   },
   {
    "name": "temperature_3",
    "offset": 9,
    "width": 2
   },
   {
    "name": "temperature_4",
    "offset": 11,
    "width": 2
   },
   {
    "name": "reserved",
    "offset": 13,
    "width": 1
   },
   {
    "name": "impeller_hz",
    "offset": 14,
    "width": 2
   },
   {
    "name": "vortex_hz",
    "offset": 16,
    "width": 2
   }
  ]
 },
 "temperature_tables": {
  "0": {
   "label": "standard_3k3",
   "min_c": -13.5,
   "max_c": 116
  },
  "1": {
   "label": "extended_1k",
   "min_c": -20,
   "max_c": 155
  },
  "2": {
   "label": "low_temperature_15k",
   "min_c": -39,
   "max_c": 80
  },
  "3": {
   "label": "standard_1k",
   "min_c": -13.9,
   "max_c": 130
  }
 },
 "vortex_hysteresis_hz": {
  "enter": 5,
  "exit": 4,
  "role": "metadata"
 },
 "cases": [
  {
   "id": "ab23ao23_req_zero",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "relay": {
      "state": "ok",
      "number": 0
     },
     "pwm1": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     },
     "pwm2": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     },
     "stepper": {
      "state": "ok",
      "number": 0,
      "label": "steps"
     },
     "led": {
      "state": "ok",
      "label": "disabled"
     },
     "ed": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     },
     "temperature_table": {
      "state": "ok",
      "label": "standard_3k3"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_pwm_ed_ff",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    255,
    255,
    0,
    0,
    255,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "relay": {
      "state": "ok",
      "number": 1
     },
     "pwm1": {
      "state": "ok",
      "number": 127.5,
      "candidate_domain": true
     },
     "pwm2": {
      "state": "ok",
      "number": 127.5,
      "candidate_domain": true
     },
     "ed": {
      "state": "ok",
      "number": 127.5,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_pwm_distinct",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    100,
    60,
    0,
    0,
    20,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "pwm1": {
      "state": "ok",
      "number": 50,
      "candidate_domain": true
     },
     "pwm2": {
      "state": "ok",
      "number": 30,
      "candidate_domain": true
     },
     "ed": {
      "state": "ok",
      "number": 10,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_stepper_240",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    240,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "stepper": {
      "state": "ok",
      "number": 240,
      "label": "steps"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_stepper_241",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    241,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "stepper": {
      "state": "unmapped"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_stepper_254",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    254,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "stepper": {
      "state": "unmapped"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_stepper_255",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    255,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "stepper": {
      "state": "ok",
      "label": "calibrate_go_to_zero"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_led_0",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "led": {
      "state": "ok",
      "label": "disabled"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_led_1",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    1,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "led": {
      "state": "ok",
      "label": "enabled"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_led_2",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    2,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "led": {
      "state": "unmapped"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_table_0",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_table": {
      "state": "ok",
      "label": "standard_3k3"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_table_1",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    1
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_table": {
      "state": "ok",
      "label": "extended_1k"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_table_2",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    2
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_table": {
      "state": "ok",
      "label": "low_temperature_15k"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_table_3",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    3
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_table": {
      "state": "ok",
      "label": "standard_1k"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_table_4",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    4
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_table": {
      "state": "unmapped"
     }
    }
   }
  },
  {
   "id": "ab23ao23_req_relay_tail",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    7,
    0,
    0,
    0,
    0,
    0,
    0,
    238,
    1
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "relay": {
      "state": "ok",
      "number": 7
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_adc_1023",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    255,
    3,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "adc": {
      "state": "ok",
      "number": 1023,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_adc_1024",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    4,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "adc": {
      "state": "ok",
      "number": 1024,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_1_000c",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_2_000c",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_2": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_3_000c",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_3": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_4_000c",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    12,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_4": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_1_ffff",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    255,
    255,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": -0.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_2_ffff",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    255,
    255,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_2": {
      "state": "ok",
      "number": -0.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_3_ffff",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    255,
    255,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_3": {
      "state": "ok",
      "number": -0.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_4_ffff",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    255,
    255,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_4": {
      "state": "ok",
      "number": -0.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_1_zero",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_2_zero",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_2": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_3_zero",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_3": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_4_zero",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_4": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_1_max",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    128,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": 200,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_2_max",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    128,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_2": {
      "state": "ok",
      "number": 200,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_3_max",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    128,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_3": {
      "state": "ok",
      "number": 200,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_4_max",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    128,
    12,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_4": {
      "state": "ok",
      "number": 200,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_1_over",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    129,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": 200.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_2_over",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    129,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_2": {
      "state": "ok",
      "number": 200.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_3_over",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    129,
    12,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_3": {
      "state": "ok",
      "number": 200.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_4_over",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    129,
    12,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_4": {
      "state": "ok",
      "number": 200.0625,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_temperature_distinct",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "temperature_1": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     },
     "temperature_2": {
      "state": "ok",
      "number": 128,
      "candidate_domain": true
     },
     "temperature_3": {
      "state": "ok",
      "number": 64,
      "candidate_domain": true
     },
     "temperature_4": {
      "state": "ok",
      "number": 16,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_vortex_0",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": false
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_vortex_4",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    4,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 4,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": false
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_vortex_5",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    5,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 5,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": true
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_vortex_350",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    94,
    1
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 350,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": true
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_vortex_351",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    95,
    1
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 351,
      "candidate_domain": false,
      "flags": {
       "formal_domain": false,
       "operational_window": false
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_impeller_0",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "impeller_hz": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_impeller_1000",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    232,
    3,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "impeller_hz": {
      "state": "ok",
      "number": 1000,
      "candidate_domain": true
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_impeller_1001",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    233,
    3,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "impeller_hz": {
      "state": "ok",
      "number": 1001,
      "candidate_domain": false
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_reserved_0",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "reserved": {
      "state": "ok",
      "reserved": 0
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_reserved_1",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "reserved": {
      "state": "ok",
      "reserved": 1
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_reserved_255",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    255,
    0,
    0,
    0,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "reserved": {
      "state": "ok",
      "reserved": 255
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_distinct_all",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126,
    3,
    2,
    100,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "prefix": {
      "state": "opaque"
     },
     "adc": {
      "state": "ok",
      "number": 258,
      "candidate_domain": true
     },
     "temperature_1": {
      "state": "ok",
      "number": 192,
      "candidate_domain": true
     },
     "temperature_2": {
      "state": "ok",
      "number": 128,
      "candidate_domain": true
     },
     "temperature_3": {
      "state": "ok",
      "number": 64,
      "candidate_domain": true
     },
     "temperature_4": {
      "state": "ok",
      "number": 16,
      "candidate_domain": true
     },
     "reserved": {
      "state": "ok",
      "reserved": 126
     },
     "impeller_hz": {
      "state": "ok",
      "number": 515,
      "candidate_domain": true
     },
     "vortex_hz": {
      "state": "ok",
      "number": 100,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": true
      }
     }
    }
   }
  },
  {
   "id": "ab23ao23_pos_tail",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    85
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "vortex_hz": {
      "state": "ok",
      "number": 0,
      "candidate_domain": true,
      "flags": {
       "formal_domain": true,
       "operational_window": false
      }
     }
    }
   }
  }
 ],
 "truncation": [
  {
   "id": "ab23ao23_trunc_request_0",
   "direction": "request",
   "logical_object": [],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "relay": "incomplete",
     "pwm1": "incomplete",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_1",
   "direction": "request",
   "logical_object": [
    161
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "relay": "incomplete",
     "pwm1": "incomplete",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_2",
   "direction": "request",
   "logical_object": [
    161,
    178
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "relay": "incomplete",
     "pwm1": "incomplete",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_3",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "incomplete",
     "pwm1": "incomplete",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_4",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "incomplete",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_5",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "incomplete",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_6",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2,
    3
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "ok",
     "stepper": "incomplete",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_7",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2,
    3,
    4
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "ok",
     "stepper": "ok",
     "led": "incomplete",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_8",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2,
    3,
    4,
    1
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "ok",
     "stepper": "ok",
     "led": "ok",
     "ed": "incomplete",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_9",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2,
    3,
    4,
    1,
    6
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "ok",
     "stepper": "ok",
     "led": "ok",
     "ed": "ok",
     "temperature_table": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_request_10",
   "direction": "request",
   "logical_object": [
    161,
    178,
    195,
    1,
    2,
    3,
    4,
    1,
    6,
    2
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "prefix": "opaque",
     "relay": "ok",
     "pwm1": "ok",
     "pwm2": "ok",
     "stepper": "ok",
     "led": "ok",
     "ed": "ok",
     "temperature_table": "ok"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_0",
   "direction": "positive",
   "logical_object": [],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "adc": "incomplete",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_1",
   "direction": "positive",
   "logical_object": [
    161
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "adc": "incomplete",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_2",
   "direction": "positive",
   "logical_object": [
    161,
    178
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "incomplete",
     "adc": "incomplete",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_3",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "incomplete",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_4",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "incomplete",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_5",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_6",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "incomplete",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_7",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_8",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "incomplete",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_9",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_10",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "incomplete",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_11",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_12",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "incomplete",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_13",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "incomplete",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_14",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "ok",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_15",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126,
    3
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "ok",
     "impeller_hz": "incomplete",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_16",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126,
    3,
    2
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "ok",
     "impeller_hz": "ok",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_17",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126,
    3,
    2,
    100
   ],
   "expect": {
    "state": "partial",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "ok",
     "impeller_hz": "ok",
     "vortex_hz": "incomplete"
    }
   }
  },
  {
   "id": "ab23ao23_trunc_positive_18",
   "direction": "positive",
   "logical_object": [
    161,
    178,
    195,
    2,
    1,
    0,
    12,
    0,
    8,
    0,
    4,
    0,
    1,
    126,
    3,
    2,
    100,
    0
   ],
   "expect": {
    "state": "complete",
    "fields": {
     "prefix": "opaque",
     "adc": "ok",
     "temperature_1": "ok",
     "temperature_2": "ok",
     "temperature_3": "ok",
     "temperature_4": "ok",
     "reserved": "ok",
     "impeller_hz": "ok",
     "vortex_hz": "ok"
    }
   }
  }
 ],
 "unknown_cases": [
  {
   "id": "ab23ao23_unknown_operation",
   "context": {
    "family": "opaque-family-a",
    "variant": "opaque-variant-1",
    "primary": 181,
    "secondary": 32,
    "operation": 1,
    "direction": "request",
    "view": "logical_object"
   },
   "expect": {
    "state": "unknown",
    "fields": {},
    "raw_preserved": true,
    "qualified": false
   }
  },
  {
   "id": "ab23ao23_unknown_direction",
   "context": {
    "family": "opaque-family-a",
    "variant": "opaque-variant-1",
    "primary": 181,
    "secondary": 32,
    "operation": 0,
    "direction": "response",
    "view": "logical_object"
   },
   "expect": {
    "state": "unknown",
    "fields": {},
    "raw_preserved": true,
    "qualified": false
   }
  },
  {
   "id": "ab23ao23_unknown_view",
   "context": {
    "family": "opaque-family-a",
    "variant": "opaque-variant-1",
    "primary": 181,
    "secondary": 32,
    "operation": 0,
    "direction": "request",
    "view": "payload_length_10"
   },
   "expect": {
    "state": "unknown",
    "fields": {},
    "raw_preserved": true,
    "qualified": false
   }
  },
  {
   "id": "ab23ao23_unknown_primary",
   "context": {
    "family": "opaque-family-a",
    "variant": "opaque-variant-1",
    "primary": 180,
    "secondary": 32,
    "operation": 0,
    "direction": "request",
    "view": "logical_object"
   },
   "expect": {
    "state": "unknown",
    "fields": {},
    "raw_preserved": true,
    "qualified": false
   }
  },
  {
   "id": "ab23ao23_unknown_secondary",
   "context": {
    "family": "opaque-family-a",
    "variant": "opaque-variant-1",
    "primary": 181,
    "secondary": 33,
    "operation": 0,
    "direction": "request",
    "view": "logical_object"
   },
   "expect": {
    "state": "unknown",
    "fields": {},
    "raw_preserved": true,
    "qualified": false
   }
  }
 ],
 "error_cases": [
  {
   "id": "ab23ao23_err_malformed",
   "input_text": "{\"context\":"
  },
  {
   "id": "ab23ao23_err_duplicate_top_key",
   "input_text": "{\"context\":{},\"context\":{},\"fields\":{}}"
  },
  {
   "id": "ab23ao23_err_duplicate_field_key",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":[],\"logical_object\":[]}}"
  },
  {
   "id": "ab23ao23_err_byte_256",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":[256]}}"
  },
  {
   "id": "ab23ao23_err_byte_negative",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":[-1]}}"
  },
  {
   "id": "ab23ao23_err_byte_fraction",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":[1.5]}}"
  },
  {
   "id": "ab23ao23_err_byte_string",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":[\"1\"]}}"
  },
  {
   "id": "ab23ao23_err_field_not_array",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{\"logical_object\":5}}"
  },
  {
   "id": "ab23ao23_err_fields_not_object",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":[]}"
  },
  {
   "id": "ab23ao23_err_context_missing",
   "input_text": "{\"fields\":{}}"
  },
  {
   "id": "ab23ao23_err_operation_string",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":\"0\",\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{}}"
  },
  {
   "id": "ab23ao23_err_arguments_nested",
   "input_text": "{\"context\":{\"primary\":181,\"secondary\":32,\"operation\":0,\"direction\":\"request\",\"view\":\"logical_object\"},\"fields\":{},\"arguments\":{\"flag\":[true]}}"
  }
 ],
 "presence_cases": [
  {
   "id": "ab23ao23_presence_missing",
   "direction": "request",
   "fields": "absent",
   "expect": {
    "state": "partial",
    "field_state": "missing"
   }
  },
  {
   "id": "ab23ao23_presence_empty",
   "direction": "request",
   "fields": {
    "logical_object": []
   },
   "expect": {
    "state": "partial",
    "field_state": "incomplete"
   }
  },
  {
   "id": "ab23ao23_presence_zero_bytes",
   "direction": "request",
   "fields": {
    "logical_object": [
     0,
     0,
     0,
     0,
     0,
     0,
     0,
     0,
     0,
     0
    ]
   },
   "expect": {
    "state": "complete",
    "field_state": "ok"
   }
  }
 ]
}
```
