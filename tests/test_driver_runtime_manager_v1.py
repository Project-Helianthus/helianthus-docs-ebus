from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "platform" / "driver-runtime-manager-v1.md"
API = ROOT / "api" / "driver-runtime-v1.md"
PORTAL = ROOT / "api" / "portal.md"
MODBUS_ADDON = ROOT / "api" / "modbus-v1-addon-runtime.md"
PLATFORM_INDEX = ROOT / "docs" / "platform" / "README.md"
LIFECYCLE = ROOT / "architecture" / "runtime-driver-lifecycle.md"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_historical_driver_snapshot_v1_vocabulary() -> None:
    text = _normalized(API)
    for required in (
        "DriverSnapshotV1",
        "`ebus.primary`",
        "`modbus.tcp.default`",
        "`eebus.primary`",
        "`RUNNING`, `STOPPED`",
        "`DISABLED`, `STOPPED`, `STARTING`, `RUNNING`, `DEGRADED`, `BACKOFF`, `STOPPING`, `FAILED`",
        "`reason`",
        "`retry`",
        "`generation`",
        "`desired_revision`",
        "`revision`",
        "`attempt`",
        "`capabilities`",
        "`effective_capabilities`",
        "`safety_quarantined`",
    ):
        assert required in text


def test_snapshot_invariants_are_explicit() -> None:
    text = _normalized(API)
    for required in (
        "desired state is operator intent",
        "observed state is runtime fact",
        "monotonically increases",
        "generation changes only when a new driver instance is admitted",
        "revision changes on every externally visible snapshot mutation",
        "attempt is scoped to one generation",
        "reason is a closed categorical value",
        "endpoint, credential, raw transport error, or protocol payload",
        "capabilities are immutable for one generation",
    ):
        assert required in text


def test_effective_capability_withdrawal_is_atomic_with_stop() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "effective capabilities are the currently admitted subset",
        "subset of `capabilities`",
        "empty in `DISABLED`, `STOPPED`, `STARTING`, `BACKOFF`, `STOPPING`, and `FAILED`",
        "same per-driver admission lock",
        "withdraws all effective capabilities before publishing `STOPPING`",
        "no provider invocation can be admitted after withdrawal",
    ):
        assert required in api
    for required in (
        "atomic effective-capability withdrawal",
        "blocked before provider invocation",
        "stop/restart withdrawal race",
    ):
        assert required in architecture


def test_unproven_close_enters_process_epoch_safety_quarantine() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        '"safety_quarantined": true',
        "`CLOSE_UNCONFIRMED`",
        "refused with `FAILED_PRECONDITION` at the lifecycle refusal-table quarantine row",
        "START with the current revision and desired RUNNING is a no-op and is not a recovery path",
        "observed state is `FAILED`",
        "effective capabilities are empty",
        "manual start and restart",
        "automatic retry",
        "provider construction",
        "until process restart",
    ):
        assert required in api
    for required in (
        "ordinary recoverable `FAILED`",
        "does not set `safety_quarantined`",
        "unproven-close safety quarantine",
        "cannot be cleared by an API operation",
    ):
        assert required in architecture


def test_active_callback_timeout_never_closes_beneath_raw_transport() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "two separately bounded phases",
        "second phase is permitted only when the first phase reaches zero active callbacks",
        "`STOP_TIMEOUT` is possible only when drain expiry leaves zero active callbacks",
        "An active-callback drain expiry bypasses the second phase entirely",
        "emits no `CloseRequest`",
        "immediately enters `CLOSE_UNCONFIRMED` safety quarantine",
        "actively executing admitted lease callback",
        "must not close beneath `RawTransport`",
        "blocks replacement",
        "abandoned non-invoking lease",
        "a proven `STOP_TIMEOUT` outcome",
        "outcome is restartable",
    ):
        assert required in api
        assert required in architecture


def test_historical_operation_concurrency_readback_and_diagnostics() -> None:
    text = _normalized(API)
    for required in (
        "`drivers.v1.list`",
        "`drivers.v1.start`",
        "`drivers.v1.stop`",
        "`drivers.v1.restart`",
        "Expected-revision comparison precedes the same-desired no-op test",
        "one current typed slot and at most one reserved successor",
        "A lost response is resolved through list/get readback",
        "No operation ID, request ID, disposition, completion field or receipt is returned",
        "Superseded: the former `DriverOperationV1` response",
        "echoes the snapshot's `desired_revision`, never the view `revision`",
        "a START during STOPPING takes the reserved slot as a typed replacement",
        "never contains an endpoint, credential, raw error, or protocol payload",
    ):
        assert required in text


def test_nonfatal_process_and_driver_readiness_boundary() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "Process readiness is not driver readiness",
        "protocol-local startup failure never terminates the shared gateway",
        "HTTP, MCP, GraphQL, and the operator surface remain available",
        "stable unavailable provider",
        "`FAILED` or `BACKOFF`",
        "At least one failed driver does not make process readiness fail",
        "global-fatal boundary",
    ):
        assert required in text


def test_retry_stop_restart_and_runtime_override_semantics() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "bounded exponential backoff",
        "retry budget",
        "`STARTING -> RUNNING`",
        "`STARTING -> BACKOFF`",
        "`BACKOFF -> STARTING`",
        "`STOPPING -> STOPPED`",
        "drain deadline",
        "adapter-owned close worker",
        "restart is one serialized stop-then-start operation",
        "Superseded by the D3 amendment: durable desired state",
        "survives a gateway process restart",
        "configured-disabled driver is not startable",
        "`FAILED_PRECONDITION` under the disabled-by-configuration row (order 4)",
        "does not rewrite add-on options",
    ):
        assert required in text


def test_transport_close_channels_have_explicit_owner_and_fresh_proof_budget() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "`DriverRuntime` is the sole sender to `CloseRequest`",
        "adapter owns the `CloseRequest` receiver and close worker",
        "adapter closes `Closed` only after its resources and adapter-owned closer retire",
        "never invokes an arbitrary manager callback or starts a manager cleanup goroutine",
        "closed or invalid `CloseRequest` is a lifecycle ownership violation",
        "adapter-owned close worker",
    ):
        assert required in api
    for required in (
        "two separately bounded phases",
        "fresh close-request/proof budget",
        "drain budget plus a fresh close/proof budget",
        "`STOP_TIMEOUT` only after adapter-proven closure",
        "absent adapter closure proof enters safety quarantine",
    ):
        assert required in architecture
    forbidden = "forced" + " local " + "tear" + "down"
    for path in (API, ARCHITECTURE):
        assert forbidden not in path.read_text(encoding="utf-8").lower()


def test_addon_validation_and_fatal_boundary_are_closed() -> None:
    architecture = _normalized(ARCHITECTURE)
    addon = _normalized(MODBUS_ADDON)
    for required in (
        "validates each enabled driver's own configuration independently",
        "invalid driver-local configuration disables only that driver",
        "global process inputs",
        "packaged binary integrity",
        "unreadable global configuration document",
        "global-fatal",
    ):
        assert required in architecture
    for required in (
        "DriverManager V1 successor",
        "driver-local Modbus validation failure",
        "must not prevent the gateway process from starting",
    ):
        assert required in addon


def test_rollout_is_mcp_first_and_one_release_acceptance_is_explicit() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "MCP prototype",
        "Status parity",
        "Portal rollout",
        "Home Assistant rollout",
        "one consolidated add-on release",
        "one multi-architecture build",
        "one CI/CD publication",
        "all three driver IDs",
        "startup failure injection",
        "process remains ready",
    ):
        assert required in text


def test_consumers_follow_g5_instead_of_the_historical_api() -> None:
    portal = _normalized(PORTAL)
    platform = _normalized(PLATFORM_INDEX)
    addon = _normalized(MODBUS_ADDON)
    lifecycle = _normalized(LIFECYCLE)
    for text, g5_link in (
        (portal, "./mcp.md#g5-runtime-lifecycle-mcp-contract-d4"),
        (platform, "../../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4"),
        (addon, "./mcp.md#g5-runtime-lifecycle-mcp-contract-d4"),
        (lifecycle, "../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4"),
    ):
        assert g5_link in text
    for required in (
        "consumer, not lifecycle authority",
        "future GraphQL parity must preserve the G5 closed driver projection and registered-driver catalog",
        "first MCP slice adds no Portal routes or controls",
        "requires no placeholder entries for unregistered drivers",
        "historical `DriverSnapshotV1` proposal is not a consumer implementation target",
    ):
        assert required in portal
    for required in (
        "[`driver-runtime-manager-v1.md`](./driver-runtime-manager-v1.md)",
        "authoritative first external list/get/start/stop/restart surface",
        "closed driver projection, and registered-driver catalog",
        "superseded historical material, not an implementation or acceptance target",
    ):
        assert required in platform
    for required in (
        "../architecture/runtime-driver-lifecycle.md",
        "../docs/platform/driver-runtime-manager-v1.md",
        "categorical unavailable status for a registered Modbus driver",
        "G5 lists only registered drivers using its closed wire projection",
        "does not require a Modbus placeholder or the historical snapshot fields",
    ):
        assert required in addon
    assert "historical `DriverSnapshotV1` proposal's `effective_capabilities`" in lifecycle
    assert "closed driver projection without capability fields" in lifecycle
    assert "snapshot is not an implementation or acceptance target" in lifecycle
    assert "field in the [driver API]" not in lifecycle
    assert "renders gateway-owned `DriverSnapshotV1`" not in portal
    assert "MCP-first `DriverSnapshotV1`" not in platform
    assert "successor is frozen in [`driver-runtime-v1.md`]" not in addon


def test_public_mcp_authority_supersedes_historical_inventory() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "superseded historical material in its entirety",
        "It is not an implementation or acceptance target",
        "Validators retaining examples below check historical consistency only",
        "./mcp.md#g5-runtime-lifecycle-mcp-contract-d4",
    ):
        assert required in api
    for required in (
        "../../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4",
        "`helianthus.runtime.list` can return a coherent snapshot",
        "`helianthus.runtime.{list,get,start,stop,restart}`",
        "historical `drivers.v1.*` tools are not delivery requirements",
        "There is no lifecycle GraphQL API, resolver, mutation or subscription.",
    ):
        assert required in architecture
    assert "implement and stabilize `drivers.v1.list`" not in architecture


def test_restart_acceptance_requires_revision_conflict_and_fresh_replacement() -> None:
    text = _normalized(ARCHITECTURE).split("## One-release Acceptance", 1)[1]
    for required in (
        "each accepted `RESTART` advances desired revision",
        "on successful replacement, increments generation exactly once",
        "retrying the old expected revision returns `REVISION_CONFLICT`",
        "a valid fresh-revision `RESTART` after settlement requests another replacement and is never deduplicated",
        "they allocate no revision or work and do not reset retry budgets or quarantine",
    ):
        assert required in text
