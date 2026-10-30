# B519 opaque-body software API companion

Refs #941; partial child of #736. Nothing is stable before Helianthus 1.0.

## Evidence and scope

Read the public [B519 candidate contract](../protocols/vaillant/ebus-vaillant.md#b519-test-and-echo-services)
first. Its candidate service descriptions are not native qualification. This
companion specifies bounded software selection from the supplied contract;
it does not establish CRC coordinates from candidate labels. In particular,
positive 01 stays raw-only despite the older candidate CRC description.
Selectors 00 through 08 and AA remain separate identities. The more conservative
unresolved-reply rule below is a software admission boundary, not a correction
of physical evidence. Family interpretation is Hypothesis; native support,
effects and persistence are Unknown. No candidate label grants permission.

This page is independent of AO21 and requires no pending implementation import.
It adds no runtime call site, catalog, registration, retry, request builder,
executor, UI behavior or scan default. Existing eBUS MCP compatibility and
GraphQL parity are unchanged; no new transport projection is specified.

## Pure library boundary

Package `vaillant`, standard library only:

```go
func Ab21Ao21Interpret(ab21ao21Input json.RawMessage) (json.RawMessage, error)
```

All new Go declarations, fields, locals and helpers use `ab21ao21` or exported
`Ab21Ao21`; Go tests use `TestAb21Ao21`. Literal JSON labels retain their names.
There is no global cache, second family schema, Entries/Lookup API or metadata
listing. This checkout supplies a documentation contract, not this Go function.
The finite Python checks below validate publication artifacts, not execution of
an unavailable production interpreter.

Input is an object with required `context` and `fields` objects and optional
`arguments` object. Context requires integer `primary`, `secondary`, `operation`
and string `direction`, `view`. B519 selection uses 181, 25, one of the ten
selectors, `request` or `positive`, and `logical-body`. No scalar arguments are
declared for this view: absent arguments are omitted in output; `{}` is
preserved; any argument key is an error. Family, variant and every other
supplied context key retain their opaque JSON values independently.

```json
{"context":{"primary":181,"secondary":25,"operation":8,"direction":"request","view":"logical-body","family":"synthetic-family","variant":0},"fields":{"logical_object":[0,0,0,127,0,255]},"arguments":{}}
```

Output has `context`, `raw`, optional `arguments`, `state`, `fields`,
`physical: "Unknown"` and `qualified: false`. `context` is an unchanged deep
copy; `raw` is an independent copy of **all** supplied named byte arrays.
Unknown field names and tails survive. `arguments` is copied independently
when present. No invocation, returned nested value or subsequent mutation of
input can change another result or a later call. Successful JSON round trips
preserve absence, explicit zero, empty arrays, empty objects and each state.

For the example, `state` is `Hypothesis` and semantic `fields` is:

```json
{"slave_address":{"raw":[127],"state":"Hypothesis"},"opaque":{"raw":[0,255],"state":"Hypothesis"}}
```

Every result field has `raw` and `state`. This view supplies only the optional
`label` on `declared_form`; it declares no `number`, `flags`, `reserved` or
`candidate_domain`. The slave address remains one raw byte, with no numeric
conversion or domain qualification. There are no numeric results or units.
A future independently exact numeric calculation may additionally have
`calculation: "Proven"`, without promoting a Hypothesis family grade. Incomplete,
unmapped, unit-conflict and unknown-order fields never gain a number;
an explicitly specified outside-domain numeric carrier would separately have
`candidate_domain: false`, but none is defined in this view.

## Selection and partial results

Logical offsets are zero-based. The first three positions are opaque and
preserved only in `raw`: no prefix assertion, decoded identity, header-byte
algorithm or physical normalization applies. Only explicit context chooses the
operation. Unknown operation, direction, view, primary or secondary produces
structured raw-only `Unknown`, with empty semantic `fields`, unchanged context
and all raw fields retained. A family label, name or plausible length never
selects a view. Wrong JSON kinds remain errors even in an Unknown branch.

The structured table below enumerates each selector independently. Request
00/02/AA have no declared argument; their supplied tails remain `unmodelled`
Unknown. Request 01/03/04/05/06/07 takes opaque bytes from position 3;
request 08 takes `slave_address` at 3 and opaque bytes from 4. Positive 03/AA
takes opaque bytes from 3. Positive 06 declares prefix-only form and retains
unexpected tails as `unmodelled` Unknown. Other positives are raw-only Unknown:
no plausible CRC byte changes that result.

For a selected form, a missing `logical_object` or fewer than three positions
returns `partial` with no semantic fields; all supplied raw bytes remain.
Request 08 with exactly three positions is also partial because its address
is missing. With an address present, its independent address field survives
even when the opaque slice is empty. Empty versus missing byte arrays remain
distinct in `raw`. Complete selected forms return `Hypothesis`, even when an
Unknown unmodelled sibling exists. Explicit unresolved branches stay `Unknown`
at every length. An empty opaque slice has `raw: []` and `state: "Hypothesis"`;
minimum zero is a software slice boundary, not evidence of accepted emptiness.
Maximum is unset, not an unlimited carrier or transport maximum.

Positive 06 with at least three positions has
`declared_form: {"raw":[],"state":"Hypothesis","label":"prefix-only"}`.
This label does not mean a physically complete or physically empty response.
Its unexpected tail is never discarded. Opaque zero and FF bytes survive
through the supplied end without ASCII, text or u32 coercion. There is no CRC
algorithm, correlation, programming effect or transport maximum established.

## Errors and admission

Malformed JSON, duplicate object keys at **any depth**, wrong object kinds,
missing required context keys, wrong scalar kinds, non-array raw fields,
non-integer bytes (including booleans and decimal forms) or values outside
0..255 return an error and no successful result. Every supplied named raw field
is validated, including unmodelled fields. JSON null does not stand in for a
missing object, byte array or context scalar. Arguments admit no undeclared
flags/integers. A missing logical object is a partial observation, not an error;
an explicitly supplied numeric zero for that object is an error. Validation
precedes selection, including for unknown context. Raw/partial preservation
must not turn invalid JSON into a successful admission.

## Machine-readable finite contract

The following JSON is normative for this software companion. `selection` rows
are `[operation, direction, policy]`. Finite cases use the declared tuple
columns. The length cross product covers all ten selectors in both directions
at lengths 0..5. Six independent byte axes enumerate every value 0..255 while
holding all other positions constant. Six explicit examples cover the supplied
longer and unresolved cases. Boundary rows are `[id, input, output]`; error
rows are `[id, JSON text, error, null]`, where null means no successful result.
They specify admission and preservation expectations for later production tests. These are synthetic software tuples, not captures.
The [fixture](fixtures/ao22_b519_opaque_views.json) expands that finite set.
The standard-library unittest checks the page and every fixture result against
independent constants; it does not implement a second production interpreter.

<!-- ab21ao21-contract -->
```json
{
  "api": {
    "package": "vaillant",
    "signature": "Ab21Ao21Interpret(ab21ao21Input json.RawMessage) (json.RawMessage, error)",
    "view": "logical-body",
    "primary": 181,
    "secondary": 25,
    "directions": [
      "request",
      "positive"
    ],
    "arguments": {}
  },
  "grades": {
    "semantic": "Hypothesis",
    "physical": "Unknown",
    "qualified": false,
    "numeric_results": [],
    "calculation": "Proven only for independently exact numeric calculations; none declared here"
  },
  "selection": [
    [
      0,
      "request",
      "none"
    ],
    [
      1,
      "request",
      "opaque"
    ],
    [
      2,
      "request",
      "none"
    ],
    [
      3,
      "request",
      "opaque"
    ],
    [
      4,
      "request",
      "opaque"
    ],
    [
      5,
      "request",
      "opaque"
    ],
    [
      6,
      "request",
      "opaque"
    ],
    [
      7,
      "request",
      "opaque"
    ],
    [
      8,
      "request",
      "address-opaque"
    ],
    [
      170,
      "request",
      "none"
    ],
    [
      0,
      "positive",
      "Unknown"
    ],
    [
      1,
      "positive",
      "Unknown"
    ],
    [
      2,
      "positive",
      "Unknown"
    ],
    [
      3,
      "positive",
      "opaque"
    ],
    [
      4,
      "positive",
      "Unknown"
    ],
    [
      5,
      "positive",
      "Unknown"
    ],
    [
      6,
      "positive",
      "prefix-only"
    ],
    [
      7,
      "positive",
      "Unknown"
    ],
    [
      8,
      "positive",
      "Unknown"
    ],
    [
      170,
      "positive",
      "opaque"
    ]
  ],
  "field_table": {
    "opaque": {
      "offset": 3,
      "request08_offset": 4,
      "encoding": "bytes",
      "minimum": 0,
      "maximum": null,
      "empty_acceptance": "Unknown"
    },
    "slave_address": {
      "offset": 3,
      "width": 1,
      "encoding": "raw byte"
    },
    "declared_form": {
      "raw": [],
      "label": "prefix-only",
      "physical_completeness": "Unknown"
    },
    "unmodelled": {
      "state": "Unknown",
      "encoding": "bytes"
    }
  },
  "states": {
    "complete_selected": "Hypothesis",
    "short_selected": "partial",
    "unresolved": "Unknown",
    "unknown_sibling": "preserve complete independent fields"
  },
  "finite_cases": {
    "tuple_columns": [
      "id",
      "operation",
      "direction",
      "logical_object",
      "state",
      "fields"
    ],
    "lengths": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
    "length_carrier": [
      0,
      0,
      0,
      127,
      0
    ],
    "byte_axes": [
      [
        "request03_data",
        3,
        "request",
        [
          0,
          0,
          0,
          0
        ],
        3
      ],
      [
        "request08_address",
        8,
        "request",
        [
          0,
          0,
          0,
          0,
          65
        ],
        3
      ],
      [
        "request08_data",
        8,
        "request",
        [
          0,
          0,
          0,
          127,
          0
        ],
        4
      ],
      [
        "positive03_data",
        3,
        "positive",
        [
          0,
          0,
          0,
          0
        ],
        3
      ],
      [
        "positiveaa_data",
        170,
        "positive",
        [
          0,
          0,
          0,
          0
        ],
        3
      ],
      [
        "positive06_tail",
        6,
        "positive",
        [
          0,
          0,
          0,
          0
        ],
        3
      ]
    ],
    "byte_values": [
      0,
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      45,
      46,
      47,
      48,
      49,
      50,
      51,
      52,
      53,
      54,
      55,
      56,
      57,
      58,
      59,
      60,
      61,
      62,
      63,
      64,
      65,
      66,
      67,
      68,
      69,
      70,
      71,
      72,
      73,
      74,
      75,
      76,
      77,
      78,
      79,
      80,
      81,
      82,
      83,
      84,
      85,
      86,
      87,
      88,
      89,
      90,
      91,
      92,
      93,
      94,
      95,
      96,
      97,
      98,
      99,
      100,
      101,
      102,
      103,
      104,
      105,
      106,
      107,
      108,
      109,
      110,
      111,
      112,
      113,
      114,
      115,
      116,
      117,
      118,
      119,
      120,
      121,
      122,
      123,
      124,
      125,
      126,
      127,
      128,
      129,
      130,
      131,
      132,
      133,
      134,
      135,
      136,
      137,
      138,
      139,
      140,
      141,
      142,
      143,
      144,
      145,
      146,
      147,
      148,
      149,
      150,
      151,
      152,
      153,
      154,
      155,
      156,
      157,
      158,
      159,
      160,
      161,
      162,
      163,
      164,
      165,
      166,
      167,
      168,
      169,
      170,
      171,
      172,
      173,
      174,
      175,
      176,
      177,
      178,
      179,
      180,
      181,
      182,
      183,
      184,
      185,
      186,
      187,
      188,
      189,
      190,
      191,
      192,
      193,
      194,
      195,
      196,
      197,
      198,
      199,
      200,
      201,
      202,
      203,
      204,
      205,
      206,
      207,
      208,
      209,
      210,
      211,
      212,
      213,
      214,
      215,
      216,
      217,
      218,
      219,
      220,
      221,
      222,
      223,
      224,
      225,
      226,
      227,
      228,
      229,
      230,
      231,
      232,
      233,
      234,
      235,
      236,
      237,
      238,
      239,
      240,
      241,
      242,
      243,
      244,
      245,
      246,
      247,
      248,
      249,
      250,
      251,
      252,
      253,
      254,
      255
    ],
    "examples": [
      [
        "ab21ao21_request03",
        3,
        "request",
        [
          0,
          0,
          0,
          0,
          255,
          65
        ],
        "Hypothesis",
        {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        }
      ],
      [
        "ab21ao21_request08",
        8,
        "request",
        [
          0,
          0,
          0,
          127,
          0,
          255
        ],
        "Hypothesis",
        {
          "slave_address": {
            "raw": [
              127
            ],
            "state": "Hypothesis"
          },
          "opaque": {
            "raw": [
              0,
              255
            ],
            "state": "Hypothesis"
          }
        }
      ],
      [
        "ab21ao21_positive03",
        3,
        "positive",
        [
          0,
          0,
          0,
          0,
          255,
          65
        ],
        "Hypothesis",
        {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        }
      ],
      [
        "ab21ao21_positiveaa",
        170,
        "positive",
        [
          0,
          0,
          0,
          0,
          255,
          65
        ],
        "Hypothesis",
        {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        }
      ],
      [
        "ab21ao21_positive06tail",
        6,
        "positive",
        [
          0,
          0,
          0,
          0,
          255
        ],
        "Hypothesis",
        {
          "declared_form": {
            "raw": [],
            "state": "Hypothesis",
            "label": "prefix-only"
          },
          "unmodelled": {
            "raw": [
              0,
              255
            ],
            "state": "Unknown"
          }
        }
      ],
      [
        "ab21ao21_positive01crc",
        1,
        "positive",
        [
          0,
          0,
          0,
          165
        ],
        "Unknown",
        {}
      ]
    ]
  },
  "identity_axes": [
    [
      "primary",
      182,
      "Unknown"
    ],
    [
      "secondary",
      26,
      "Unknown"
    ],
    [
      "operation",
      9,
      "Unknown"
    ],
    [
      "direction",
      "other",
      "Unknown"
    ],
    [
      "view",
      "other",
      "Unknown"
    ],
    [
      "family",
      {
        "opaque": [
          0,
          255
        ]
      },
      "Hypothesis"
    ],
    [
      "variant",
      {
        "opaque": false
      },
      "Hypothesis"
    ]
  ],
  "presence": {
    "missing_logical_object": "partial",
    "empty_logical_object": "partial",
    "zero_logical_object": "error",
    "unknown_raw_field": "preserve",
    "missing_arguments": "omit",
    "empty_arguments": {},
    "unknown_argument": "error"
  },
  "errors": [
    "malformed JSON",
    "duplicate object key at any depth",
    "non-object root/context/fields/arguments",
    "missing required context key",
    "non-integer primary/secondary/operation",
    "non-string direction/view",
    "non-array raw field",
    "non-integer byte",
    "byte outside 0..255",
    "undeclared argument"
  ],
  "ownership": "independent deep copies of context, raw and supplied arguments; no shared state across calls",
  "selection_rule": "explicit context only; first three logical positions opaque; no family, name or length inference",
  "unknowns": [
    "CRC coordinates except declared opaque forms",
    "CRC algorithm",
    "correlation",
    "transport maximum",
    "programming effect",
    "effects",
    "persistence",
    "native support",
    "accepted emptiness",
    "unlimited carrier"
  ],
  "boundary_cases": [
    [
      "ab21ao21_control",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_primary",
      {
        "context": {
          "primary": 182,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 182,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Unknown",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_secondary",
      {
        "context": {
          "primary": 181,
          "secondary": 26,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 26,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Unknown",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_operation",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 9,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 9,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Unknown",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_direction",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "other",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "other",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Unknown",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_view",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "other",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "other",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Unknown",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_family",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": {
            "opaque": [
              0,
              255
            ]
          },
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": {
            "opaque": [
              0,
              255
            ]
          },
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_variant",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": {
            "opaque": false
          }
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": {
            "opaque": false
          }
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_context_extension",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0,
          "extension": {
            "nested": [
              0,
              {},
              false
            ]
          }
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0,
          "extension": {
            "nested": [
              0,
              {},
              false
            ]
          }
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_leading_0",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            255,
            0,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            255,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_leading_1",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            255,
            0,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            255,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_leading_2",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            255,
            0,
            255,
            65
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            255,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_missing",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {}
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {},
        "state": "partial",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_empty",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": []
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": []
        },
        "state": "partial",
        "fields": {},
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_empty_opaque",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_unknown_sibling",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ],
          "extra": [
            255,
            0
          ]
        }
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ],
          "extra": [
            255,
            0
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    ],
    [
      "ab21ao21_empty_arguments",
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "fields": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "arguments": {}
      },
      {
        "context": {
          "primary": 181,
          "secondary": 25,
          "operation": 3,
          "direction": "request",
          "view": "logical-body",
          "family": "synthetic-family",
          "variant": 0
        },
        "raw": {
          "logical_object": [
            0,
            0,
            0,
            0,
            255,
            65
          ]
        },
        "state": "Hypothesis",
        "fields": {
          "opaque": {
            "raw": [
              0,
              255,
              65
            ],
            "state": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false,
        "arguments": {}
      }
    ]
  ],
  "error_cases": [
    [
      "ab21ao21_error_0",
      "{",
      "error",
      null
    ],
    [
      "ab21ao21_error_1",
      "{\"context\":{},\"context\":{}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_2",
      "{\"context\":{\"family\":{\"x\":0,\"x\":1}}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_3",
      "[]",
      "error",
      null
    ],
    [
      "ab21ao21_error_4",
      "null",
      "error",
      null
    ],
    [
      "ab21ao21_error_5",
      "{\"context\":null,\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_6",
      "{\"context\":[],\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_7",
      "{\"context\":0,\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_8",
      "{\"context\":\"x\",\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_9",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":null}",
      "error",
      null
    ],
    [
      "ab21ao21_error_10",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":[]}",
      "error",
      null
    ],
    [
      "ab21ao21_error_11",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":0}",
      "error",
      null
    ],
    [
      "ab21ao21_error_12",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":\"x\"}",
      "error",
      null
    ],
    [
      "ab21ao21_error_13",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]},\"arguments\":null}",
      "error",
      null
    ],
    [
      "ab21ao21_error_14",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]},\"arguments\":[]}",
      "error",
      null
    ],
    [
      "ab21ao21_error_15",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]},\"arguments\":0}",
      "error",
      null
    ],
    [
      "ab21ao21_error_16",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]},\"arguments\":\"x\"}",
      "error",
      null
    ],
    [
      "ab21ao21_error_17",
      "{\"context\":{\"primary\":true,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_18",
      "{\"context\":{\"primary\":1.0,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_19",
      "{\"context\":{\"primary\":\"3\",\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_20",
      "{\"context\":{\"primary\":null,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_21",
      "{\"context\":{\"primary\":181,\"secondary\":true,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_22",
      "{\"context\":{\"primary\":181,\"secondary\":1.0,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_23",
      "{\"context\":{\"primary\":181,\"secondary\":\"3\",\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_24",
      "{\"context\":{\"primary\":181,\"secondary\":null,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_25",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":true,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_26",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":1.0,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_27",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":\"3\",\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_28",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":null,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_29",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":0,\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_30",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":0,\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_31",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":null}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_32",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":0}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_33",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":\"00\"}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_34",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[true]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_35",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[1.0]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_36",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[-1]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_37",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[256]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_38",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[\"0\"]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_39",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[null]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_40",
      "{\"context\":{\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_41",
      "{\"context\":{\"primary\":181,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_42",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_43",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_44",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_45",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":3,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65]},\"arguments\":{\"flag\":0}}",
      "error",
      null
    ],
    [
      "ab21ao21_error_46",
      "{\"context\":{\"primary\":181,\"secondary\":25,\"operation\":9,\"direction\":\"request\",\"view\":\"logical-body\",\"family\":\"synthetic-family\",\"variant\":0},\"fields\":{\"logical_object\":[0,0,0,0,255,65],\"extra\":[256]}}",
      "error",
      null
    ]
  ]
}
```
<!-- /ab21ao21-contract -->

## Validation boundary

The focused suite is a mandatory separate ship check: Gate D uses an explicit
list and does not automatically include it. No gate registration is added here.
Production invocation, error/no-result behavior, defensive memory ownership,
and mutation isolation require companion implementation evidence; static tuples
cannot prove them. Full repository Gate D with the provisioned references,
independent committed-change review, publication checks and applicable transport
classification remain required before shipping. This page claims no native
qualification and adds no active traffic.
