#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

platform_toolchain_mode="${PLATFORM_TOOLCHAIN_MODE:-supported}"
platform_docs_ebus_repository="${PLATFORM_DOCS_EBUS_REPOSITORY:-Project-Helianthus/helianthus-docs-ebus}"
case "${platform_toolchain_mode}" in
  exact|supported) ;;
  *)
    echo "PLATFORM_TOOLCHAIN_MODE must be exact or supported." >&2
    exit 2
    ;;
esac

echo "==> verify pinned workflow/schema gate tools"
if ! command -v actionlint >/dev/null 2>&1; then
  echo "actionlint v1.7.7 is required: go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.7" >&2
  exit 2
fi
actionlint_version="$(python3 scripts/check_workflow_shells.py actionlint-version)"
if [ "$(printf '%s\n' "$actionlint_version" | sed -n '1p')" != "v1.7.7" ]; then
  echo "actionlint must report v1.7.7." >&2
  exit 2
fi
if ! command -v jv >/dev/null 2>&1; then
  echo "jv v0.7.0 is required: go install github.com/santhosh-tekuri/jsonschema/cmd/jv@v0.7.0" >&2
  exit 2
fi
if [ "$(jv --version | sed -n '1p')" != "github.com/santhosh-tekuri/jsonschema/cmd/jv v0.7.0" ]; then
  echo "jv must report v0.7.0." >&2
  exit 2
fi
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "ShellCheck is required for the separate workflow run-step check." >&2
  exit 2
fi
gate_temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/docs-ebus-ci.XXXXXXXX")"
cleanup_workflow_lint() {
  local status=$?
  rm -rf -- "$gate_temp_dir" || :
  return "$status"
}
install_workflow_cleanup_trap() {
  local signal="$1" handler="$2" previous
  previous="$(trap -p "$signal")"
  if [ -n "$previous" ]; then
    # Decode Bash's quoted trap declaration without changing the caller's arguments.
    eval "set -- ${previous#trap -- }"
    previous="$1"
  else
    previous=:
  fi
  if [ "$signal" = EXIT ]; then
    # Both branches preserve the incoming status for the previous handler.
    printf -v handler 'if cleanup_workflow_lint; then\n%s\nelse\n%s\nfi' "$previous" "$previous"
  else
    printf -v handler '%s\n%s' "$previous" "$handler"
  fi
  # Quote the composed handler as data before installing it.
  printf -v handler 'trap -- %q %q' "$handler" "$signal"
  eval "$handler"
}
install_workflow_cleanup_trap EXIT ''
install_workflow_cleanup_trap INT 'exit 130'
install_workflow_cleanup_trap TERM 'exit 143'
echo "Workflow lint artifacts: ${gate_temp_dir} (removed on exit)"
workflow_lint_status=0
echo "==> actionlint (60-second limit; embedded ShellCheck disabled)"
python3 scripts/check_workflow_shells.py actionlint || workflow_lint_status=$?
echo "==> separate ShellCheck (60-second pass limit; all severities)"
python3 scripts/check_workflow_shells.py shellcheck --temp-dir "$gate_temp_dir" || {
  workflow_lint_status=$?
  # Preserve numbered source while the extracted files still exist. The pass
  # returns one status, so include every extracted script for diagnostic context.
  for workflow_script in "$gate_temp_dir"/*.bash "$gate_temp_dir"/*.sh; do
    [ -f "$workflow_script" ] || continue
    printf '\nExtracted workflow source: %s\n' "$workflow_script" >&2
    nl -ba "$workflow_script" >&2 || :
  done
}
if [ "$workflow_lint_status" -ne 0 ]; then
  exit "$workflow_lint_status"
fi
python3 -m pytest -q tests/test_workflow_shells.py
python3 -m pytest -q tests/test_workflow_lint_cleanup.py
echo "Pinned workflow/schema gate tools passed."

echo "==> verify markdown files are present"
count="$(git ls-files '*.md' | wc -l | tr -d ' ')"
if [ "${count}" -eq 0 ]; then
  echo "No markdown files found."
  exit 1
fi
echo "Found ${count} markdown files."

echo "==> check markdown for tabs and trailing spaces"
failed=0
if git grep -nI $'\t' -- '*.md'; then
  echo "Tab characters are not allowed in markdown files."
  failed=1
fi
if git grep -nI -E ' +$' -- '*.md'; then
  echo "Trailing spaces are not allowed in markdown files."
  failed=1
fi
if [ "${failed}" -ne 0 ]; then
  exit 1
fi

echo "==> enforce initiator/target terminology"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

begin_marker = "<!-- legacy-role-mapping:begin -->"
end_marker = "<!-- legacy-role-mapping:end -->"

# Construct legacy terms without spelling them out literally in-repo.
terms = ["m" + "aster", "sl" + "ave"]
pattern = re.compile(r"\b(" + "|".join(map(re.escape, terms)) + r")\b", re.IGNORECASE)

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()

def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1

def print_match(file_path: str, text: str, index: int, match_text: str) -> None:
    print(f"{file_path}:{line_number(text, index)}:{match_text}", file=sys.stderr)

failed = False

for file_path in md_files:
    path = pathlib.Path(file_path)
    text = path.read_text(encoding="utf-8")

    # Build allowed regions from legacy-role-mapping markers in this file.
    allowed_ranges: list[tuple[int, int]] = []
    search_start = 0
    while True:
        b = text.find(begin_marker, search_start)
        if b == -1:
            break
        e = text.find(end_marker, b)
        if e == -1:
            break
        allowed_ranges.append((b, e + len(end_marker)))
        search_start = e + len(end_marker)

    for match in pattern.finditer(text):
        in_allowed = any(s <= match.start() < e for s, e in allowed_ranges)
        if not in_allowed:
            if not failed:
                print(
                    "Legacy role terms found outside legacy-role-mapping regions.",
                    file=sys.stderr,
                )
            failed = True
            print_match(file_path, text, match.start(), match.group(0))

if failed:
    sys.exit(1)

print("Terminology gate passed.")
PY

echo "==> private network address gate (docs must use placeholders)"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path("scripts").resolve()))
from validate_platform_contracts import _private_network_literals

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()
failed = False

for file_path in md_files:
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for _, offset in _private_network_literals(text):
        line = text.count("\n", 0, offset) + 1
        print(f"{file_path}:{line}: private network address found (redact and use a placeholder)", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Private network gate passed.")
PY

echo "==> check eBUS source-address table"
python3 scripts/check_source_address_table_against_official_specs.py --run-canary
python3 -m pytest -q tests/test_source_address_table_checker.py

echo "==> check qualified identity documentation contract"
python3 scripts/check_regulator_identity_contract.py
python3 -m pytest -q tests/test_regulator_identity_contract_checker.py

echo "==> check bounded Prometheus semantic coverage contract"
python3 scripts/validate_prometheus_semantic_coverage.py
python3 -m pytest -q tests/test_prometheus_semantic_coverage.py

echo "==> check Vaillant SemReg thermal mapping contract"
python3 scripts/validate_vaillant_semreg_thermal_map.py
python3 -m pytest -q tests/test_vaillant_semreg_thermal_map.py
python3 -m pytest -q tests/test_dhw_setpoint_semreg_cutover.py
(
  cd tests/semreg_thermal_map_contract
  GOWORK=off go test -mod=readonly ./...
)

echo "==> check Vaillant controller qualification contract"
python3 scripts/validate_vaillant_controller_qualification.py
python3 -m pytest -q tests/test_vaillant_controller_qualification.py

echo "==> check adversarial runtime report v1 contract"
for report in docs/platform/fixtures/adversarial-runtime/v1/positive/*.json; do
  python3 scripts/validate_adversarial_runtime_report_v1.py "$report"
done
for driver in docs/platform/fixtures/adversarial-runtime/v1/inputs/*.json; do
  jv docs/platform/schemas/adversarial-runtime-offline-fixture-v1.schema.json "$driver"
done
python3 -m pytest -q tests/test_adversarial_runtime_report_v1.py

echo "==> check Vaillant regulator capability API contract"
python3 scripts/validate_vaillant_regulator_capability_api_v1.py
python3 -m pytest -q tests/test_vaillant_regulator_capability_api_v1.py

echo "==> check GraphQL device-face provenance contract"
python3 scripts/check_graphql_face_provenance.py
python3 -m pytest -q tests/test_graphql_face_provenance_checker.py
python3 -m pytest -q -p no:cacheprovider tests/test_system_config_bound_contract.py
python3 -m pytest -q tests/test_semantic_snapshot_read_contract.py
python3 -m pytest -q tests/test_semantic_operation_route_contract.py

echo "==> check contribution-driven Portal UX contract"
python3 scripts/check_portal_ux_contract.py
python3 -m pytest -q tests/test_portal_ux_contract_checker.py

echo "==> check CC0 and AGPL documentation boundary"
python3 scripts/check_public_domain_boundary.py
python3 -m pytest -q tests/test_public_domain_boundary.py

echo "==> check Vaillant B503 milestone contract"
python3 scripts/check_vaillant_b503_milestones.py
python3 -m pytest -q tests/test_vaillant_b503_milestone_checker.py

echo "==> check Vaillant B505 sentinel and override candidates"
python3 -m pytest -q tests/test_ae04_b505_candidates.py

echo "==> check B520 simulator actuator and ADC declarations"
python3 -m pytest -q tests/test_ac20_simulator_adc.py
python3 -m pytest -q tests/test_al20_b555_extent_views.py

echo "==> check B509/B524 passive watch-policy documentation contract"
python3 -m pytest -q tests/test_watch_policy_contract.py
python3 -m pytest -q tests/test_b524_operation_docs.py
python3 -m pytest -q tests/test_b524_register_name_correspondence.py
python3 -m pytest -q tests/test_b524_name_bridge_contract.py
python3 -m pytest -q tests/test_b524_provisional_name_evidence.py
echo "==> check canonical register names against the register naming rules"
python3 scripts/check_register_names.py
python3 -m pytest -q tests/test_register_names.py
echo "==> check B509 register name correspondence fixture"
python3 -m pytest -q tests/test_b509_register_name_correspondence.py
python3 scripts/validate_b524_op06_observed_windows.py \
  protocols/vaillant/fixtures/b524-op06-observed-windows-v1.json
echo "==> check BASV0 parameter-description profile"
jv protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json \
  protocols/vaillant/fixtures/b524-basv0-description-profile-v1.json
python3 scripts/validate_b524_basv0_description_profile.py \
  protocols/vaillant/fixtures/b524-basv0-description-profile-v1.json \
  --observations protocols/vaillant/fixtures/b524-basv0-register-observations-v1.json
jv protocols/vaillant/fixtures/b524-basv0-register-observations-schema-v1.json \
  protocols/vaillant/fixtures/b524-basv0-register-observations-v1.json
python3 -m pytest -q tests/test_b524_basv0_description_profile.py
python3 -m pytest -q tests/test_b524_calendar_edge_vectors.py
python3 -m pytest -q tests/test_b524_description_schema_privacy.py
python3 -m pytest -q tests/test_b524_exp_nonfinite_limits.py
python3 -m pytest -q tests/test_b524_evidence_join_permutations.py
python3 -m pytest -q tests/test_b524_external_bundle_cli.py
python3 -m pytest -q tests/test_b524_cli_input_errors.py
python3 -m pytest -q tests/test_b524_overlay_cli_rejection.py
python3 -m pytest -q tests/test_b524_bounded_survey_profile.py
for profile in protocols/vaillant/fixtures/b524-bounded-survey-*-v1.json; do
  case "$profile" in
    *-profile-schema-v1.json|*-profile-template-v1.json) continue ;;
  esac
  jv protocols/vaillant/fixtures/b524-bounded-survey-profile-schema-v1.json "$profile"
  python3 scripts/validate_b524_bounded_survey_profile.py "$profile"
done
for plan in development/fixtures/b524-operation-read-plan-*-v1.json; do
  case "$plan" in *-schema-v1.json) continue ;; esac
  jv development/fixtures/b524-operation-read-plan-schema-v1.json "$plan"
done
for artifact in development/fixtures/b524-operation-reads-artifact-*-v1.json; do
  case "$artifact" in *-schema-v1.json) continue ;; esac
  jv development/fixtures/b524-operation-reads-artifact-schema-v1.json "$artifact"
  python3 scripts/validate_b524_operation_reads_artifact.py "$artifact"
done
jv development/fixtures/b524-operation-edit-plan-schema-v1.json development/fixtures/b524-operation-edit-plan-synthetic-v1.json
jv development/fixtures/b524-native-write-qualification-schema-v1.json development/fixtures/b524-native-write-qualification-synthetic-v1.json
python3 -m pytest -q tests/test_b524_operation_reads.py

echo "==> check cross-runtime platform contracts (MSP-DOCS-CLEAN)"
python3 -m pytest -q tests/test_m625_cross_seed_contract.py
python3 -m pytest -q tests/test_platform_contracts.py -k trusted_prior_workflow
python3 -m pytest -q tests/test_platform_contracts.py -k 'not trusted_prior_workflow'
python3 -m pytest -q tests/test_synchronized_evidence_contract.py
python3 -m pytest -q tests/test_synchronized_evidence_executable_contract.py
python3 -m pytest -q tests/test_synchronized_evidence_m625_contract.py
python3 -m pytest -q tests/test_synchronized_evidence_one_shot_contract.py
python3 -m pytest -q tests/test_candidate_fact_graph_contract.py
python3 -m pytest -q tests/test_candidate_fact_graph_executable_contract.py
python3 -m pytest -q tests/test_multi_runtime_live_coexistence_contract.py
python3 -m pytest -q tests/test_leaf_promotion_dossier_contract.py
python3 -m pytest -q tests/test_captured_multi_leaf_promotion_contract.py
python3 -m pytest -q tests/test_msp085_live_completion.py
python3 -m pytest -q tests/test_msp085_final_18_leaf_completion.py

echo "==> check Modbus M1/M2 companion contract"
python3 -m pytest -q \
  tests/test_modbus_companion_contract.py \
  tests/test_modbus_trusted_revision.py \
  tests/test_modbus_v1_mcp_contract.py \
  tests/test_modbus_v1_addon_runtime_contract.py \
  tests/test_modbus_v1_live_qualification_contract.py \
  tests/test_fronius_m4_05_live_evidence.py \
  tests/test_fronius_m4_05_0651_go.py \
  tests/test_fronius_flavor_v1_2_walk_evidence.py \
  tests/test_fronius_m5_continuous_acquisition.py \
  tests/test_modbus_vendor_evidence_v1.py \
  tests/test_canonical_pv_semantics_v1.py \
  tests/test_public_graphql_m2m_v1.py
python3 scripts/validate_canonical_pv_v1.py \
  --document docs/platform/fixtures/canonical-pv/v1/golden-three-phase.json \
  --manifest docs/platform/manifests/canonical-pv-v1.json \
  --schema docs/platform/schemas/canonical-pv-observation-v1.schema.json \
  --source-registry docs/platform/fixtures/canonical-pv/v1/source-registry-bindings.json \
  --source-registry-schema docs/platform/schemas/canonical-pv-source-registry-bindings-v1.schema.json
python3 scripts/validate_public_graphql_m2m_v1.py \
  --manifest docs/platform/manifests/public-graphql-m2m-v1.json \
  --canonical-manifest docs/platform/manifests/canonical-pv-v1.json \
  --cases docs/platform/fixtures/public-graphql-m2m/v1/cases.json
python3 scripts/validate_canonical_pv_v1.py \
  --document docs/platform/fixtures/canonical-pv/v1/golden-mixed-retention.json \
  --manifest docs/platform/manifests/canonical-pv-v1.json \
  --schema docs/platform/schemas/canonical-pv-observation-v1.schema.json \
  --source-registry docs/platform/fixtures/canonical-pv/v1/source-registry-bindings.json \
  --source-registry-schema docs/platform/schemas/canonical-pv-source-registry-bindings-v1.schema.json
python3 -m pytest -q tests/test_eebus_operator_admin_contract.py
python3 -m pytest -q tests/test_driver_runtime_manager_v1.py
python3 scripts/check_runtime_driver_registration.py
python3 -m pytest -q tests/test_runtime_driver_registration.py
python3 scripts/check_bidirectional_registration.py
python3 -m pytest -q tests/test_bidirectional_registration.py
python3 scripts/check_runtime_control_contract.py
python3 -m pytest -q tests/test_runtime_control_contract.py
python3 -m pytest -q tests/test_runtime_driver_registration_rendered.py
python3 -m pytest -q tests/test_fronius_sunspec_phase1_contract.py
python3 -m pytest -q tests/test_sunspec_model_chain_contract.py
python3 -m pytest -q tests/test_sunspec_fronius_flavor_contract.py
python3 -m pytest -q tests/test_sunspec_model_123_fronius_v3_contract.py
if [ -n "${MODBUS_PRIOR_ROOT:-}" ]; then
  python3 scripts/validate_modbus_companion.py \
    --root . \
    --prior-root "${MODBUS_PRIOR_ROOT}"
else
  python3 scripts/validate_modbus_companion.py --root .
fi

echo "==> check opaque runtime acquisition companion contract"
python3 -m pytest -q tests/test_opaque_runtime_acquisition_contract.py
if [ -n "${MODBUS_PRIOR_ROOT:-}" ]; then
  python3 scripts/validate_opaque_runtime_acquisition.py \
    --root . \
    --prior-root "${MODBUS_PRIOR_ROOT}"
else
  python3 scripts/validate_opaque_runtime_acquisition.py --root .
fi

set --
if [ -n "${PLATFORM_PRIOR_MANIFEST:-}" ]; then
  set -- --prior-manifest "${PLATFORM_PRIOR_MANIFEST}"
fi
for required_var in PLATFORM_M625_DOCS_EEBUS_ROOT PLATFORM_M625_EXECUTION_PLANS_ROOT; do
  if [ -z "${!required_var:-}" ]; then
    echo "${required_var} is required for fail-closed M6.25 provenance validation." >&2
    exit 2
  fi
done
set -- "$@" \
  --m625-docs-eebus-root "${PLATFORM_M625_DOCS_EEBUS_ROOT}" \
  --m625-execution-plans-root "${PLATFORM_M625_EXECUTION_PLANS_ROOT}"
python3 scripts/validate_platform_contracts.py \
  --mode repository \
  --docs-ebus-root . \
  --docs-ebus-repository "${platform_docs_ebus_repository}" \
  --enforce-through MSP-DOCS-CLEAN \
  --toolchain-mode "${platform_toolchain_mode}" \
  "$@"

combined_ref_values=(
  "${PLATFORM_DOCS_EEBUS_ROOT:-}"
  "${PLATFORM_EEBUSREG_ROOT:-}"
  "${PLATFORM_DOCS_EBUS_REF:-}"
  "${PLATFORM_DOCS_EEBUS_REF:-}"
  "${PLATFORM_EEBUSREG_REF:-}"
  "${PLATFORM_PRIOR_MANIFEST:-}"
)
combined_ref_requested=false
for value in \
  "${PLATFORM_DOCS_EEBUS_ROOT:-}" \
  "${PLATFORM_EEBUSREG_ROOT:-}" \
  "${PLATFORM_DOCS_EBUS_REF:-}" \
  "${PLATFORM_DOCS_EEBUS_REF:-}" \
  "${PLATFORM_EEBUSREG_REF:-}"; do
  if [ -n "${value}" ]; then
    combined_ref_requested=true
  fi
done
if [ "${combined_ref_requested}" = true ]; then
  for value in "${combined_ref_values[@]}"; do
    test -n "${value}"
  done
  python3 scripts/validate_platform_combined_ref.py \
    --docs-ebus-root . \
    --docs-eebus-root "${PLATFORM_DOCS_EEBUS_ROOT}" \
    --eebusreg-root "${PLATFORM_EEBUSREG_ROOT}" \
    --m625-docs-eebus-root "${PLATFORM_M625_DOCS_EEBUS_ROOT}" \
    --m625-execution-plans-root "${PLATFORM_M625_EXECUTION_PLANS_ROOT}" \
    --docs-ebus-ref "${PLATFORM_DOCS_EBUS_REF}" \
    --docs-eebus-ref "${PLATFORM_DOCS_EEBUS_REF}" \
    --eebusreg-ref "${PLATFORM_EEBUSREG_REF}" \
    --prior-manifest "${PLATFORM_PRIOR_MANIFEST}" \
    --enforce-through MSP-DOCS-CLEAN \
    --toolchain-mode "${platform_toolchain_mode}"
fi

echo "==> check eBUS address-table taxonomy + frame-type contract hash (Phase C M-C0)"
bash scripts/check_address_table_taxonomy_hash.sh

echo "==> check runtime_state.json schema (runtime-state-w19-26 M0_DOC_GATE)"
bash scripts/check_runtime_state_schema.sh

echo "==> check deployment source-address wording"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import sys

path = pathlib.Path("deployment/full-stack.md")
text = path.read_text(encoding="utf-8")
lower = text.lower()

forbidden = [
    "gentle-join",
    "gentle join",
    "enables **gentle-join**",
    "asks the proxy to select a free initiator",
    "reuses the persisted source address",
    "promote source_addr.last",
]
required = [
    "gateway default source-selection policy",
    "selects and validates an admitted source",
    "rollback/migration input only",
    "must not be promoted into active source authority",
]

failed = False
for phrase in forbidden:
    if phrase in lower:
        print(f"{path}: legacy source-address wording remains: {phrase}", file=sys.stderr)
        failed = True

for phrase in required:
    if phrase not in lower:
        print(f"{path}: required source-address wording missing: {phrase}", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Deployment source-address wording gate passed.")
PY

echo "==> check NM 07FE/07FF service names"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import sys

checks = {
    "architecture/nm-model.md": [
        "`07 FE` | Inquiry of Existence",
        "`07 FF` | Sign of Life",
        "`07 FE` is Inquiry of Existence. `07 FF` is Sign of Life.",
    ],
    "architecture/nm-discovery.md": [
        "### 07 FF (Sign of Life Broadcast) -- Not Discovery",
    ],
    "architecture/nm-participant-policy.md": [
        "### 07 FF (Sign of Life) -- Optional-Later",
        "`07 FF` (Sign of Life) broadcasts originated by Helianthus",
    ],
}

for file_path, required_fragments in checks.items():
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for fragment in required_fragments:
        if fragment not in text:
            print(f"{file_path}: missing required fragment: {fragment}", file=sys.stderr)
            sys.exit(1)
    forbidden = [
        "07 FF (QueryExistence",
        "`07 FF` | QueryExistence",
        "`07 FF` QueryExistence",
        "`07 FF` (QueryExistence)",
    ]
    for fragment in forbidden:
        if fragment in text:
            print(f"{file_path}: stale 07FF QueryExistence text: {fragment}", file=sys.stderr)
            sys.exit(1)

print("NM 07FE/07FF service name gate passed.")
PY
