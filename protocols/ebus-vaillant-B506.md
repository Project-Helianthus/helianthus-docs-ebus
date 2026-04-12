# Vaillant B506 I/O Test

`PB=0xB5`, `SB=0x06`.

## Status

`B506` is modeled in john30 TypeSpec as an installer-auth write family for I/O
or actuator tests. It is not safe for blind probing on production heating
systems.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

Known configured rows use:

```text
Start/select test:
  02 value

Stop test:
  01
```

The `value` byte is target/profile-specific.

## Known Selectors

| Request payload | Name | Response shape | Evidence | Falsification test |
|---|---|---|---|---|
| `01` | stop I/O test | ACK/status | `LOCAL_TYPESPEC` | On isolated hardware, start a documented test and show `B506 01` does not stop it after ACK. |
| `02 <value>` | select/start I/O test | ACK/status plus physical side effect | `LOCAL_TYPESPEC` | On isolated hardware, send a documented value and show no actuator/log/test-mode effect. |

## Safety Rule

Only run `B506` against a controlled test fixture or an installation explicitly
prepared for actuator testing. A reasonable safe sequence is:

```text
1. Send stop:        B5 06 01
2. Send one test:    B5 06 02 <documented_value>
3. Observe locally.
4. Send stop again:  B5 06 01
```

Do not use this sequence on production hardware unless the operator has
explicitly accepted the risk.

## Unknowns

- Complete actuator enum per target class.
- Whether non-HMU, solar, or mixer modules share any selector values.
- Whether some devices require a separate service/installer unlock before ACK.

## References

- Public TypeSpec: [iotesthp_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/iotesthp_inc.tsp)
- Public TypeSpec: [iotestbsol_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/iotestbsol_inc.tsp)
- Public TypeSpec: [iotestbmc_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/iotestbmc_inc.tsp)
