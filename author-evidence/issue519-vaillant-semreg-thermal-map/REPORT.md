# Author evidence — docs-eBUS issue #519

## Scope and base

- Repository: `Project-Helianthus/helianthus-docs-ebus`
- Issue: [#519](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/519)
- Branch: `issue/519-vaillant-semreg-thermal-map`
- Initial implementation commit: `bce5c4c6f96211b313f0c056b79d2c63b0818307`
- Follow-up review evidence: `106fcbe4f001087736d54d246a803ae56fc5700b9bdb7a12681db0a80699ea48`

This change documents and mechanically validates only the public, read-only
candidate mapping from the three bounded Vaillant B524 controller observations
to the accepted thermal pack. It does not implement a gateway surface, a
runtime qualified binding, a write route, topology, a complete Portal
descriptor, eeBUS/Matter output, hardware behavior, or a live test.

## Changed files

| File | Purpose |
| --- | --- |
| `architecture/b524-semantic-mapping.md` | Renders distinct native `degC` and SemReg `unit.celsius`, plus the retained-receipt/caller-evaluation lifecycle boundary. |
| `architecture/fixtures/vaillant-semreg-thermal-map-v1.json` | Checked-in three-row index with separate native and semantic value types/units, and a delayed `R != E` lifecycle vector. |
| `scripts/validate_vaillant_semreg_thermal_map.py` | Validates typed rows only: selectors, value type/unit pairs, facts/dimensions/dispositions/loss, lifecycle boundary, distinctions, applicability, and non-claims. |
| `tests/test_vaillant_semreg_thermal_map.py` | Rejects native or SemReg unit drift/missing semantic unit, lifecycle overwrite/freshness drift, FactKey, selector, disposition, and non-claim mutations. |
| `tests/semreg_thermal_map_contract/` | Standalone public Go module with no `replace` or sibling path; validates both exact FactKey/quantity pairs at SemReg `e1d4c70924254cf44f39304fc94856925328675d`, candidates/Times, and delayed EvaluationContext. |
| `scripts/ci_local.sh` | Registers the Python and standalone Go checks as repository CI gates. |

## Validation

Genuine RED against the current `bce5c4c` fixture before the typed rows:

```text
python3 -m pytest -q tests/test_vaillant_semreg_thermal_map.py
FAILED tests/test_vaillant_semreg_thermal_map.py::test_exact_rows_keep_native_and_semreg_units_and_delayed_evaluation_separate
KeyError: 'native_value'
1 failed, 9 passed in 0.03s
```

Focused GREEN after correction:

```text
python3 scripts/validate_vaillant_semreg_thermal_map.py
Vaillant SemReg thermal mapping index passed.

python3 -m pytest -q tests/test_vaillant_semreg_thermal_map.py
11 passed in 0.66s

(cd tests/semreg_thermal_map_contract && GOWORK=off go test -mod=readonly ./...)
ok github.com/Project-Helianthus/helianthus-docs-ebus/tests/semreg_thermal_map_contract

git diff --check
PASS (no output)
```

Complete repository CI passed with the repository-required M6.25 companion
inputs, rather than bypassing the fail-closed gate:

```text
PLATFORM_M625_DOCS_EEBUS_ROOT=.../wave12/read/docs-eebus-m625-cedf-fresh
PLATFORM_M625_EXECUTION_PLANS_ROOT=.../wave10/ci-deps/execution-plans-fb384
./scripts/ci_local.sh
exit 0
```

The supplied companion roots resolved to docs-eeBUS
`cedf238e34f879815ba773e9cd76b2b31c2822a3` and execution-plans
`fb384ab57d79f0020c54d2c66416e8a7666f0ceb`. The complete CI included the
new `11 passed` mapping suite and the pinned standalone Go contract suite,
then completed all recorded suites successfully,
including 104 qualified-identity tests, 49 adversarial-runtime tests, 20
capability-API tests, 174 GraphQL-provenance tests, 385 cross-runtime tests
(10 deselected), then 304, 265, 67, 51, 34, 6, 146, 230 and the remaining
focused contract suites. M6.25 provenance, address-table taxonomy,
runtime-state negative fixtures, deployment wording and NM service-name gates
also passed.

No credential handling, live device action, or hardware action was performed.
This report accompanies the corrected PR branch; GitHub is authoritative for
its current commit, checks, review, and merge state.
