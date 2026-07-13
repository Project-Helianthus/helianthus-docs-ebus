# helianthus-docs-ebus — local validation targets
#
# Usage:
#   make validate-schemas      # runtime-state JSON Schema gate (M0_DOC_GATE)
#   make ci-local              # full local CI suite (ci_local.sh)
#
# Plans referenced:
#   - runtime-state-w19-26.locked (validate-schemas: AD05/AD22 acceptance)

PLATFORM_TOOLCHAIN_MODE ?= supported

.PHONY: validate-schemas validate-platform-contracts validate-platform-combined-ref validate-platform-expiry ci-local help

help:
	@echo "Available targets:"
	@echo "  validate-schemas    Validate runtime-state JSON Schema vs example + negative fixtures (M0_DOC_GATE)"
	@echo "  validate-platform-contracts  Validate cross-runtime ownership contracts"
	@echo "  validate-platform-combined-ref  Validate exact supplied cross-repository refs"
	@echo "  validate-platform-expiry     Validate manifest expiry at EVALUATED_AT from EVALUATION_SOURCE"
	@echo "  ci-local            Run full local CI suite (scripts/ci_local.sh)"

validate-schemas:
	@bash scripts/check_runtime_state_schema.sh

validate-platform-contracts:
	@python3 -m pytest -q tests/test_platform_contracts.py
	@python3 scripts/validate_platform_contracts.py --mode repository --docs-ebus-root . --enforce-through MSP-DOCS-CLEAN --toolchain-mode "$(PLATFORM_TOOLCHAIN_MODE)"

validate-platform-combined-ref:
	@test -n "$(DOCS_EEBUS_ROOT)" && test -n "$(EEBUSREG_ROOT)"
	@test -n "$(DOCS_EBUS_REF)" && test -n "$(DOCS_EEBUS_REF)" && test -n "$(EEBUSREG_REF)"
	@test -n "$(PRIOR_MANIFEST)" && test -n "$(ENFORCE_THROUGH)"
	@python3 scripts/validate_platform_combined_ref.py --docs-ebus-root . --docs-eebus-root "$(DOCS_EEBUS_ROOT)" --eebusreg-root "$(EEBUSREG_ROOT)" --docs-ebus-ref "$(DOCS_EBUS_REF)" --docs-eebus-ref "$(DOCS_EEBUS_REF)" --eebusreg-ref "$(EEBUSREG_REF)" --prior-manifest "$(PRIOR_MANIFEST)" --enforce-through "$(ENFORCE_THROUGH)" --toolchain-mode "$(PLATFORM_TOOLCHAIN_MODE)"

validate-platform-expiry:
	@test -n "$(EVALUATED_AT)" || (echo "EVALUATED_AT is required" >&2; exit 2)
	@test -n "$(EVALUATION_SOURCE)" || (echo "EVALUATION_SOURCE is required" >&2; exit 2)
	@python3 scripts/validate_platform_contracts.py --mode main-expiry --docs-ebus-root . --evaluated-at "$(EVALUATED_AT)" --evaluation-source "$(EVALUATION_SOURCE)" --enforce-through MSP-DOCS-CLEAN --toolchain-mode "$(PLATFORM_TOOLCHAIN_MODE)"

ci-local:
	@bash scripts/ci_local.sh
