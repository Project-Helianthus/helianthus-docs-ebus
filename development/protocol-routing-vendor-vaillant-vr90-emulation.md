# VR90 emulation policy

This AGPL application policy uses the separate [CC0 VR90 wire reference](../protocols/vaillant/ebus-vaillant-vr90-emulation.md).

## Emulation Jitter

To avoid the VRC700 detecting a perfectly stable synthetic temperature, the emulator applies slow-drift jitter:

- **Random walk:** ±1 D2C tick (0.0625°C) per poll cycle
- **Bounded:** total drift clamped to ±0.5°C from source temperature
- **D2C-quantized:** final value is always an exact D2C tick (`math.Round(temp * 16) / 16`)

This produces naturalistic temperature fluctuation that matches real sensor noise characteristics.
