# B505 replacement-pair software API

This software companion defines a bounded pure library contract for the Vaillant
family. Its native evidence boundary is the public [B505 bounded sentinel
contract](../protocols/vaillant/ebus-vaillant-b505.md#bounded-sentinel-and-override-candidates).
That contract labels the two independent OP32 words **Hypothesis** and leaves
native direction, absolute positions, conversion and acceptance **Unknown**.
The `request` direction below selects a software view; it is not native direction
qualification. No code merge or AO01 dependency is needed to check this page.
Refs [#926](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/926)
and partial parent [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).

## Function and JSON boundary

```go
package vaillant

func Ab01Ao01Interpret(ab01ao01Input json.RawMessage) (json.RawMessage, error)
```

The standard-library-only function interprets selected fields and states. It has
no global cache, generic catalog, metadata listing, registration, pending API
import, runtime call site, Entries/Lookup API or second family schema. All new
Go identifiers use `ab01ao01` or `Ab01Ao01`; Go tests use `TestAb01Ao01`.
There is no write construction, execution, scan, UI or transport behavior here.
eBUS MCP compatibility and GraphQL parity receive no new surface.

Input is an object with required object members `context` and `fields` and
optional object member `arguments`. Context contains integer `primary`,
`secondary`, `operation` and string `direction`, `view`; preserve all other keys
and opaque family/variant values without interpreting them. Missing required
selection keys or wrong kinds are errors. Fields maps names to byte arrays:
only integer JSON values 0 through 255 are admitted, including in unmodelled
fields. Booleans, floating-point tokens, null, scalars and objects are not bytes.
Duplicate keys at every nesting depth, malformed JSON, trailing input, wrong
JSON kinds and unsupported arguments return an error and no successful result.
No scalar argument is defined for this view, so only absent arguments or `{}`
are valid. A present empty arguments object remains present in the output.

Only `(181, 5, 50, "request", "replacement-pair")` selects interpretation.
Well-typed different primary, secondary, operation, direction or view values
produce raw-only `Unknown`. Neither family label, field name alone nor payload
length selects a view. Unknown context never confers native qualification.

## Results and partial state

The output has `context`, `raw`, `state`, `fields`, `physical: "Unknown"` and
`qualified: false`; it also has `arguments` exactly when supplied. Context is an
unchanged deep copy, raw is an independent copy of every supplied field, and
arguments is an independent copy. No returned memory may alias input, another
result or a later call. All presence distinctions survive JSON round trips.
A zero byte or zero word is present data; empty arrays and missing fields differ.

The two already isolated fields are `temperature_one` and `temperature_two`.
The little-endian order identifies tokens only, not a numeric temperature codec.
Each selected semantic field has `grade: "Hypothesis"`, `state` and its exact
`raw` array when present. Missing fields omit `raw` and have state `missing`;
empty, short and overlong fields have state `incomplete`, retaining every byte.
Overlong words are not truncated or interpreted by prefix. Unmodelled fields
have their raw arrays, state `Unknown` and grade `Unknown`.

| Raw word (LE bytes) | Field state | Numeric result | Grade |
| --- | --- | --- | --- |
| 8000 (`[0,128]`) | preserve-existing | absent | Hypothesis |
| 0000 (`[0,0]`) | circuit-default | absent | Hypothesis |
| 0001 (`[1,0]`) | numeric-unqualified | absent | Hypothesis |
| FFFF (`[255,255]`) | numeric-unqualified | absent | Hypothesis |
| Any other exact two-byte word | numeric-unqualified | absent | Hypothesis |

Select sentinel branches before any conversion, independently for each word.
No branch supplies `number`, `label`, `flags`, `reserved`, `candidate_domain` or
`calculation`. There are no numeric cases, scale, signedness or physical bounds.
Exact software results may be checked as **Proven**, but semantic family grades
stay **Hypothesis**; no arithmetic `calculation: Proven` applies to this view.
The general API may carry a number with `candidate_domain: false` for an
explicitly specified outside-domain carrier; none is specified in this slice.
Incomplete, unmapped, unit-conflict and unknown-order fields never gain numbers.

Both resolved sentinel fields yield overall `complete`. Any unresolved field
(including numeric-unqualified, missing, incomplete or unmodelled) yields
`partial`, preserving every independent complete field. An unselected branch
has overall `Unknown` and only supplied raw fields with `Unknown` state and
grade. Unknown siblings cannot erase a valid field. A call is stateless; callers
retain any earlier last-known-good value separately rather than replacing it
with an unknown sibling or inferring persistence from a partial result.

Physical effects, acceptance, persistence, complete write body and absolute
positions remain **Unknown**. Successful interpretation grants no permission,
family applicability, native support or write qualification.

## Machine-readable finite contract table

The following JSON table and the [synthetic tuples](fixtures/ao02_b505_sentinel_views.json)
are declarations checked against independent constants by the focused unittest.
Each row contains input and the entire expected successful output, or raw JSON
and the required error/no-success outcome. This documentation test does not call
a production interpreter. Production invocation, memory-isolation and executed
production mutation evidence require the separately owned library implementation.

<!-- ab01ao01-contract:start -->
```json
{
  "contract": {
    "id": "ab01ao01_replacement_pair",
    "api": "Ab01Ao01Interpret(ab01ao01Input json.RawMessage) (json.RawMessage, error)",
    "package": "vaillant",
    "selector": {
      "primary": 181,
      "secondary": 5,
      "operation": 50,
      "direction": "request",
      "view": "replacement-pair"
    },
    "field_names": [
      "temperature_one",
      "temperature_two"
    ],
    "word_bytes": 2,
    "byte_order": "little-endian-token-only",
    "branches": [
      {
        "raw": [
          0,
          128
        ],
        "state": "preserve-existing",
        "grade": "Hypothesis"
      },
      {
        "raw": [
          0,
          0
        ],
        "state": "circuit-default",
        "grade": "Hypothesis"
      },
      {
        "raw": [
          1,
          0
        ],
        "state": "numeric-unqualified",
        "grade": "Hypothesis"
      },
      {
        "raw": [
          255,
          255
        ],
        "state": "numeric-unqualified",
        "grade": "Hypothesis"
      }
    ],
    "numeric_results": [],
    "physical": "Unknown",
    "qualified": false,
    "unknowns": [
      "absolute_positions",
      "complete_write_body",
      "ordinary_numeric_scale",
      "conflicting_bounds",
      "persistence",
      "physical_effects",
      "acceptance",
      "family_applicability"
    ],
    "arguments": {
      "allowed_keys": [],
      "optional": true
    },
    "output_keys": [
      "context",
      "raw",
      "state",
      "fields",
      "physical",
      "qualified"
    ],
    "optional_output_keys": [
      "arguments"
    ],
    "field_keys": [
      "raw",
      "state",
      "grade"
    ],
    "absent_field_keys": [
      "state",
      "grade"
    ],
    "forbidden_field_keys": [
      "number",
      "label",
      "flags",
      "reserved",
      "candidate_domain",
      "calculation"
    ],
    "states": {
      "selected": "complete",
      "unresolved": "partial",
      "unselected": "Unknown",
      "short": "incomplete",
      "overlong": "incomplete",
      "empty": "incomplete",
      "absent": "missing",
      "unmodelled": "Unknown"
    },
    "errors": [
      "malformed_json",
      "duplicate_key",
      "wrong_kind",
      "invalid_byte",
      "unsupported_argument"
    ],
    "copy_contract": [
      "context_deep_copy",
      "raw_independent_copy",
      "arguments_independent_copy",
      "no_cross_result_alias",
      "no_cross_call_alias"
    ],
    "round_trip": "preserve_presence_states_and_errors",
    "implementation_scope": "pure_library_no_cache_catalog_registration_or_call_site"
  },
  "cases": [
    {
      "id": "ab01ao01_pair",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_reverse",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            0
          ],
          "temperature_two": [
            0,
            128
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            0
          ],
          "temperature_two": [
            0,
            128
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          },
          "temperature_two": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_8000",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_0000",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_0001",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            1,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            1,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "numeric-unqualified",
            "grade": "Hypothesis",
            "raw": [
              1,
              0
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_ffff",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            255,
            255
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            255,
            255
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "numeric-unqualified",
            "grade": "Hypothesis",
            "raw": [
              255,
              255
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_short",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": [
              0
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_empty",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": []
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_absent",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "missing",
            "grade": "Hypothesis"
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_one_overlong",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128,
            0
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": [
              0,
              128,
              0
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_8000",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            128
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            128
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_0000",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_0001",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            1,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            1,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "numeric-unqualified",
            "grade": "Hypothesis",
            "raw": [
              1,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_ffff",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            255,
            255
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            255,
            255
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "numeric-unqualified",
            "grade": "Hypothesis",
            "raw": [
              255,
              255
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_short",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": [
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_empty",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": []
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": []
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": []
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_absent",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "missing",
            "grade": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_temperature_two_overlong",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            128,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            128,
            0
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "incomplete",
            "grade": "Hypothesis",
            "raw": [
              0,
              128,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_context_primary",
      "input": {
        "context": {
          "primary": 180,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 180,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "Unknown",
        "fields": {
          "temperature_one": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_context_secondary",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 4,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 4,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "Unknown",
        "fields": {
          "temperature_one": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_context_operation",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 49,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 49,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "Unknown",
        "fields": {
          "temperature_one": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_context_direction",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "response",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "response",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "Unknown",
        "fields": {
          "temperature_one": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_context_view",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "other",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "other",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "Unknown",
        "fields": {
          "temperature_one": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_opaque_family",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": {
            "opaque": [
              1
            ]
          },
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": {
            "opaque": [
              1
            ]
          },
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_opaque_variant",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": null,
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": null,
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_opaque_opaque",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              1
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              1
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_arguments_empty",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "arguments": {}
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ]
        },
        "state": "complete",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false,
        "arguments": {}
      }
    },
    {
      "id": "ab01ao01_unmodelled",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ],
          "unmodelled": [
            0,
            255,
            128
          ]
        }
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {
          "temperature_one": [
            0,
            128
          ],
          "temperature_two": [
            0,
            0
          ],
          "unmodelled": [
            0,
            255,
            128
          ]
        },
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "preserve-existing",
            "grade": "Hypothesis",
            "raw": [
              0,
              128
            ]
          },
          "temperature_two": {
            "state": "circuit-default",
            "grade": "Hypothesis",
            "raw": [
              0,
              0
            ]
          },
          "unmodelled": {
            "state": "Unknown",
            "grade": "Unknown",
            "raw": [
              0,
              255,
              128
            ]
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    },
    {
      "id": "ab01ao01_both_missing",
      "input": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "fields": {}
      },
      "expected": {
        "context": {
          "primary": 181,
          "secondary": 5,
          "operation": 50,
          "direction": "request",
          "view": "replacement-pair",
          "family": "synthetic-family",
          "variant": "synthetic-variant",
          "opaque": {
            "value": [
              0
            ]
          }
        },
        "raw": {},
        "state": "partial",
        "fields": {
          "temperature_one": {
            "state": "missing",
            "grade": "Hypothesis"
          },
          "temperature_two": {
            "state": "missing",
            "grade": "Hypothesis"
          }
        },
        "physical": "Unknown",
        "qualified": false
      }
    }
  ],
  "errors": [
    {
      "id": "ab01ao01_malformed",
      "input_json": "{",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_duplicate_top",
      "input_json": "{\"context\":{},\"context\":{},\"fields\":{}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_duplicate_nested",
      "input_json": "{\"context\":{\"primary\":181,\"primary\":181},\"fields\":{}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_duplicate_field",
      "input_json": "{\"context\":{},\"fields\":{\"temperature_one\":[],\"temperature_one\":[]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_root_array",
      "input_json": "[]",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_root_null",
      "input_json": "null",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_fields_null",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": null}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_fields_array",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": []}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_fields_string",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": \"\"}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_negative",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [-1], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_overflow",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [256], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_float",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0.0], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_boolean",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [true], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_null",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [null], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_string",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [\"0\"], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_word_null",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": null, \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_word_scalar",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": 0, \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_word_object",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": {}, \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_arguments_null",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}, \"arguments\": null}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_arguments_array",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}, \"arguments\": []}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_arguments_flag",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}, \"arguments\": {\"flag\": false}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_arguments_zero",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}, \"arguments\": {\"value\": 0}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_kind_primary",
      "input_json": "{\"context\": {\"primary\": true, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_kind_secondary",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": true, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_kind_operation",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": true, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_kind_direction",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": 0, \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_kind_view",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": 0, \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_missing_fields",
      "input_json": "{\"context\": {\"primary\": 181, \"secondary\": 5, \"operation\": 50, \"direction\": \"request\", \"view\": \"replacement-pair\", \"family\": \"synthetic-family\", \"variant\": \"synthetic-variant\", \"opaque\": {\"value\": [0]}}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_missing_context",
      "input_json": "{\"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    },
    {
      "id": "ab01ao01_context_null",
      "input_json": "{\"context\": null, \"fields\": {\"temperature_one\": [0, 128], \"temperature_two\": [0, 0]}}",
      "expected_error": true,
      "successful_result": false
    }
  ]
}
```
<!-- ab01ao01-contract:end -->
