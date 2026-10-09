# Modbus Protocol References

This AGPL-3.0 page indexes Helianthus acquisition and qualification contracts.
Implementation-neutral wire references remain separately under CC0-1.0 in
[the protocol directory](../protocols/modbus/README.md).

- [`modbus-phase-one-wire-v1.md`](../protocols/modbus/modbus-phase-one-wire-v1.md) defines the
  public wire contract used by the first Helianthus Modbus implementation.
- [`../sunspec/sunspec-model-chain-v1.md`](protocol-routing-vendor-sunspec-model-chain-v1.md)
  defines the Helianthus SunSpec model-chain and capability
  contract consumed above Modbus transport.
- [`../sunspec/fronius-observed-flavor-v1.md`](protocol-routing-vendor-fronius-observed-flavor-v1.md)
  defines the exact observed Fronius flavor layered above a successfully
  admitted standard capability.
- [`growatt-candidate-evidence-v1.md`](protocol-routing-vendor-growatt-candidate-evidence-v1.md)
  records a proprietary Growatt Modbus candidate without claiming SunSpec or
  profile admission.
- [`huawei-gateway-candidate-evidence-v1.md`](protocol-routing-vendor-huawei-candidate-evidence-v1.md)
  separates SmartLogger, S-Dongle, and EMMA as independent first-class
  evidence candidates with fail-closed overlap rules.

Helianthus scheduling, abandonment, provenance, profile, and qualification
policy remains under `docs/platform/` and is not relicensed by this directory.
The [Fronius SunSpec phase-one evidence packet](../docs/platform/fronius-sunspec-evidence-v1.md)
is an AGPL platform-policy artifact; it independently summarizes sources and
does not relicense the separate CC0 wire references.
