# Frequenz Microgrid Component Graph Library Release Notes

## Upgrading

- The `microgrid` extra now requires `frequenz-client-microgrid >= 0.18.3` (was `>= 0.18.0`) so that the `SteamBoiler` component class is available.

## New Features

- `ComponentGraph` now accepts every component class shipped by `frequenz.client.microgrid.component`.  Battery and EV-charger subtypes (`LiIonBattery`, `NaIonBattery`, `AcEvCharger`, `DcEvCharger`, `HybridEvCharger`) are mapped to their cg-side subtype variant instead of collapsing to `Unspecified`.  Pass-through categories (`Converter`, `CryptoMiner`, `Electrolyzer`, `Hvac`, `Precharger`, `Relay`, `VoltageTransformer`), plus `SteamBoiler` and `UnrecognizedComponent`, are now mapped where they previously raised `ValueError("Unsupported component category: …")`.
