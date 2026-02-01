# Naming Conventions

This document describes naming patterns used in the current implementation.

## Packages

- Package names are lowercase and single-word (`protocol`, `transport`, `registry`, `schema`).
- Internal helpers live under `internal/` and are not exported outside their module.

## Data Types

- eBUS data types are represented with uppercase identifiers that reflect common eBUS terminology:
  `DATA1b`, `DATA2c`, `DATA2b`, `EXP`, `WORD`, `BCD`, `BITFIELD`.
- Replacement values are referred to explicitly as “replacement values” and are defined per type.

## Methods

- Vendor methods use snake_case strings (e.g., `get_status`, `set_target_temp`, `get_parameters`, `get_energy_stats`).
- Method names express intent rather than transport details.

## Schemas and Fields

- Schema field names are snake_case and describe semantic values (`flow_temp`, `target_temp`, `pump_status`).
- Conditional schemas are described by `target` and optional hardware version bounds.

## Protocol Constants

- eBUS addresses and command bytes are referenced in hex (e.g., `0xB5`, `0x04`).
- Control symbols are named by their protocol role (`SymbolAck`, `SymbolNack`, `SymbolEscape`, `SymbolSyn`).
