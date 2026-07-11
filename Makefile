# helianthus-docs-ebus — local validation targets
#
# Usage:
#   make validate-schemas      # runtime-state JSON Schema gate (M0_DOC_GATE)
#   make ci-local              # full local CI suite (ci_local.sh)
#
# Plans referenced:
#   - runtime-state-w19-26.locked (validate-schemas: AD05/AD22 acceptance)

.PHONY: validate-schemas validate-platform-contracts validate-platform-expiry ci-local help

help:
	@echo "Available targets:"
	@echo "  validate-schemas    Validate runtime-state JSON Schema vs example + negative fixtures (M0_DOC_GATE)"
	@echo "  validate-platform-contracts  Validate cross-runtime ownership contracts"
	@echo "  validate-platform-expiry     Validate manifest expiry at EVALUATED_AT from EVALUATION_SOURCE"
	@echo "  ci-local            Run full local CI suite (scripts/ci_local.sh)"

validate-schemas:
	@bash scripts/check_runtime_state_schema.sh

validate-platform-contracts:
	@python3 -m pytest -q tests/test_platform_contracts.py
	@python3 scripts/validate_platform_contracts.py --mode repository --docs-ebus-root . --pinned-tool python=3.12.10 --pinned-tool pyyaml=6.0.2

validate-platform-expiry:
	@test -n "$(EVALUATED_AT)" || (echo "EVALUATED_AT is required" >&2; exit 2)
	@test -n "$(EVALUATION_SOURCE)" || (echo "EVALUATION_SOURCE is required" >&2; exit 2)
	@python3 scripts/validate_platform_contracts.py --mode main-expiry --docs-ebus-root . --evaluated-at "$(EVALUATED_AT)" --evaluation-source "$(EVALUATION_SOURCE)" --pinned-tool python=3.12.10 --pinned-tool pyyaml=6.0.2

ci-local:
	@bash scripts/ci_local.sh
