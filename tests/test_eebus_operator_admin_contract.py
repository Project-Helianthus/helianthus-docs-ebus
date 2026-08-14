from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "eebus-operator-admin.md"
PORTAL = ROOT / "api" / "portal.md"
DECISIONS = ROOT / "architecture" / "decisions.md"
B524 = ROOT / "architecture" / "b524-structural-decisions.md"
B524_MAPPING = ROOT / "architecture" / "b524-semantic-mapping.md"
FSM_MAP = ROOT / "architecture" / "semantic-structure-fsm-map.md"
CONFIG_GATES = ROOT / "architecture" / "semantic-configuration-gates.md"
GRAPHQL = ROOT / "api" / "graphql.md"
MCP = ROOT / "api" / "mcp.md"
HA = ROOT / "development" / "ha-integration.md"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_shared_operator_boundary_has_no_eebus_specific_authentication() -> None:
    text = _normalized(CONTRACT)
    for required in (
        "canonical protocol-specific contract remains exclusively in",
        "post-m9-operator-pairing-browsers-v1.md",
        "post-m9-operator-admin-v1.md",
        "6f8154011c36f4811db473fea03db8544ab488bc",
        "Those documents alone own protocol routes",
        "`eebus.v1.*` remains the only eeBUS MCP namespace",
        "introduces no eeBUS-specific login, session, cookie, CSRF token, owner credential, Home Assistant credential, or eeBUS reauthentication",
        "Generic Portal and Home Assistant authentication remain out of scope",
        "Pairing actions remain functional in both Portal and Home Assistant",
        "gateway-owned typed API",
        "Portal and Home Assistant never read the trust store",
        "owner-only operator socket",
        "private keys, tokens, private PEM, trust-store bytes",
        "must not enter `ebus.v1`, GraphQL semantic fields, or the semantic registry",
    ):
        assert required in text
    for forbidden in (
        "owner-authenticated same-origin session",
        "CSRF-safe mutation admission",
        "Home Assistant uses a non-cookie, least-privilege credential",
        "Home Assistant receives no mutation grant",
        "Portal is the only mutation UX",
        "Home Assistant and public formatters receive no raw",
        "Home Assistant receives no raw or operator-only identity data",
        "Portal-only topology contract",
    ):
        assert forbidden not in text


def test_protocol_contract_is_linked_not_duplicated() -> None:
    text = _normalized(CONTRACT)
    for forbidden in (
        "/admin/eebus/v1/",
        "admin_boundary_unavailable",
        "`trusted`, `connected`, `discovered`, and `candidate`",
        "40-character lowercase certificate short identifier",
        "device/entity/feature/use-case tree",
        "snapshot hash",
        "one device, eleven entities, twenty features",
    ):
        assert forbidden not in text
    for required in (
        "authorized inspection of lossless protocol-native data",
        "canonical protocol documents own all tree shape",
        "Both Portal and Home Assistant host operator views may receive bounded raw SPINE and complete comparison identity through the gateway typed boundary",
        "Public and shareable formatters receive no raw or operator-only identity data",
    ):
        assert required in text


def test_fm5_structural_mode_survives_transient_acquisition() -> None:
    text = _normalized(CONTRACT)
    for required in (
        "`INTERPRETED`, `GPIO_ONLY`, and `ABSENT`",
        "`fm5_semantic_degraded_reason`",
        "`CONTROLLER_UNREACHABLE`",
        "`CONFIGURATION_UNAVAILABLE`",
        "`CONFIGURATION_NOT_INTERPRETABLE`",
        "`SOLAR_ACQUISITION_FAILED`",
        "`CYLINDER_ACQUISITION_FAILED`",
        "Structural FM5 mode is independent from transient acquisition health",
        "known coherent `INTERPRETED` baseline remains `INTERPRETED`",
        "same corpus before and after eeBUS activation",
        "transient acquisition failure never commits `GPIO_ONLY`",
        "`GPIO_ONLY` requires fresh, coherent structural evidence",
        "exactly `CONFIGURATION_NOT_INTERPRETABLE`",
        "does not refresh, zero, or withdraw retained solar or cylinder values",
        "fresh attempted-acquisition timestamps and source identity",
    ):
        assert required in text
    assert "`CONTROLLER_UNREACHABLE` when only retained evidence remains" not in text


def test_version_has_one_runtime_build_source_and_portal_links_contract() -> None:
    contract = _normalized(CONTRACT)
    portal = _normalized(PORTAL)
    decisions = _normalized(DECISIONS)
    for required in (
        "single injected build-time release version",
        "runtime health, Portal health, and add-on package metadata",
        "hard-coded fallback release number is forbidden",
        "startup fails closed for a release artifact whose injected version is empty or mismatched",
    ):
        assert required in contract
    assert "[`eebus-operator-admin.md`](./eebus-operator-admin.md)" in portal
    assert '"fm5_semantic_degraded_reason": null' in portal
    assert '"fm5_semantic_evidence_revision": "opaque-acquisition-revision"' in portal
    assert "ADR-028: Post-M9 operator boundary, FM5 degradation, and version authority" in decisions


def test_existing_fm5_authority_uses_the_provider_verdict() -> None:
    text = _normalized(B524)
    for required in (
        "one mode/reason/revision verdict",
        "structural mode and acquisition health are independent",
        "previous coherent `INTERPRETED` mode remains unchanged",
        "`GPIO_ONLY` only from fresh coherent `CONFIGURATION_NOT_INTERPRETABLE` evidence",
        "device-registry identity mutations advance a monotonic observation generation",
        "final registry-generation comparison and semantic verdict commit execute in one registry read critical section",
        "writer linearizes either before both operations or after both operations",
        "does not commit a structural verdict from a detached registry snapshot",
        "`fm5SemanticDegradedReason`",
        "`fm5SemanticEvidenceRevision`",
        "retains the last coherent solar snapshot without updating it",
        "retains the last coherent instance set without updating it",
        "Fresh coherent `ABSENT` or `GPIO_ONLY / CONFIGURATION_NOT_INTERPRETABLE` withdraws the family",
        "requires a decodable `temperatureC` to create or update an instance",
        "an already coherent instance may be retained unchanged",
        "does not refresh its values",
    ):
        assert required in text
    mapping = _normalized(B524_MAPPING)
    for required in (
        "A transient acquisition degradation retains only the last coherent snapshot",
        "it is not a new live sample",
        "does not update or zero it",
        "does not change the last coherent structural mode",
    ):
        assert required in mapping
    fsm_map = _normalized(FSM_MAP)
    gates = _normalized(CONFIG_GATES)
    for text in (fsm_map, gates):
        for required in (
            "transient acquisition reason retains the last coherent",
            "fresh coherent `ABSENT` or `GPIO_ONLY / CONFIGURATION_NOT_INTERPRETABLE` withdraws",
            "without updating or zeroing it",
        ):
            assert required in text
    assert "only instances with live temperature evidence are published" not in gates


def test_mcp_graphql_and_ha_expose_one_fm5_verdict() -> None:
    mcp = _normalized(MCP)
    graphql = _normalized(GRAPHQL)
    ha = _normalized(HA)
    for required in (
        "`ebus.v1.semantic.fm5_interpretation.get`",
        "`mode`, `degraded_reason`, and `evidence_revision`",
        "no v2 tool or legacy alias is introduced",
        "not part of the implemented surface above until the gateway implementation PR merges",
    ):
        assert required in mcp
    implemented_mcp = MCP.read_text(encoding="utf-8").split(
        "## Semantic Payload Notes", maxsplit=1
    )[0]
    assert "ebus.v1.semantic.fm5_interpretation.get" not in implemented_mcp
    for required in (
        "Status:** Pending gateway implementation",
        "fm5Interpretation: Fm5Interpretation",
        "nullable until the first coherent structural classification",
        "must not synthesize `GPIO_ONLY` or `ABSENT`",
        "degradedReason: Fm5SemanticDegradedReason",
        "evidenceRevision: String!",
        "Existing `fm5SemanticMode` remains stable",
    ):
        assert required in graphql
    for required in (
        "gateway-owned eeBUS operator projection",
        "native pairing flow without an eeBUS-specific credential or reauthentication step",
        "pending GraphQL contract",
        "target contract, not current integration availability",
        "fm5Interpretation { mode degradedReason evidenceRevision }",
        "does not derive a reason",
        "treats a null verdict as acquisition unavailable",
        "`GPIO_ONLY` with any reason other than `CONFIGURATION_NOT_INTERPRETABLE` is an invalid response",
    ):
        assert required in ha
    assert "fm5Interpretation: Fm5Interpretation!" not in graphql


def test_portal_and_mcp_keep_pairing_and_cold_start_fail_closed() -> None:
    portal = _normalized(PORTAL)
    mcp = _normalized(MCP)
    for required in (
        "Home Assistant uses the same gateway-owned pairing boundary",
        "Portal and Home Assistant pairing remain functional",
        "omits all three FM5 verdict fields until the first coherent structural classification",
    ):
        assert required in portal
    assert "not pairing authority" not in portal
    for required in (
        "returns `null` until the first coherent structural classification",
        "never fabricates `GPIO_ONLY` or `ABSENT` during bootstrap",
    ):
        assert required in mcp


def test_target_portal_fields_do_not_claim_current_availability() -> None:
    contract = _normalized(CONTRACT)
    portal = _normalized(PORTAL)
    assert "These additive surfaces are pending" in contract
    assert "post-M9 target field, pending gateway implementation" in portal
    assert "not claims about current runtime availability" in portal
