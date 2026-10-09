# SunSpec Protocol References

This AGPL-3.0 page indexes Helianthus acquisition and qualification contracts.
Implementation-neutral wire references remain separately under CC0-1.0 in
[the protocol directory](../protocols/sunspec/README.md).

- [`sunspec-model-chain-v1.md`](protocol-routing-vendor-sunspec-model-chain-v1.md) defines the
  SunSpec model-chain, retention, and capability-admission contract.
- [`fronius-observed-flavor-v1.md`](protocol-routing-vendor-fronius-observed-flavor-v1.md) defines
  the first exact, evidence-bounded and read-only vendor flavor layered after
  capability admission.
- [`fronius-observed-flavor-v1-1.md`](protocol-routing-vendor-fronius-observed-flavor-v1-1.md)
  defines a separate exact successor for the observed chain that includes
  standard Model `123/L24`; it does not replace or widen V1.
- [`additional-model-evidence-v1.md`](protocol-routing-vendor-sunspec-additional-model-evidence-v1.md)
  records the FMV3-M7-01 manufacturer-neutral candidate sets and read-only
  admission boundary for later standard-model expansion.

The page is an independently authored contract. It does not redistribute
upstream specification text, model files, vendor manuals, or vendor register
tables. Helianthus scheduling, acquisition, vendor applicability, and runtime
activation policy remain under `docs/platform/` and are not relicensed by this
directory.
