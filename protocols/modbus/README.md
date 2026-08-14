# Modbus Protocol References

Files in this directory are implementation-neutral Modbus protocol references.
They are covered by [`protocols/LICENSE`](../LICENSE), CC0-1.0.

- [`modbus-phase-one-wire-v1.md`](./modbus-phase-one-wire-v1.md) defines the
  public wire contract used by the first Helianthus Modbus implementation.
- [`../sunspec/sunspec-model-chain-v1.md`](../sunspec/sunspec-model-chain-v1.md)
  defines the implementation-neutral SunSpec model-chain and capability
  contract consumed above Modbus transport.

Helianthus scheduling, abandonment, provenance, profile, and qualification
policy remains under `docs/platform/` and is not relicensed by this directory.
The [Fronius SunSpec phase-one evidence packet](../../docs/platform/fronius-sunspec-evidence-v1.md)
is an AGPL platform-policy artifact; it independently summarizes sources and
does not add vendor register tables to this CC0 protocol directory.
