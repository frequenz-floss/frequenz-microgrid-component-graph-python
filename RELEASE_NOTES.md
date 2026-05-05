# Frequenz Microgrid Component Graph Library Release Notes

## Upgrading

- This release updates the `frequenz-microgrid-component-graph` rust crate version to 0.4.

- This release updates the `frequenz-microgrid-component-graph` rust crate version to 0.5.  `ComponentGraphConfig` is restructured to match: the six per-category `prefer_X_in_Y_formula` flags are replaced by a global `prefer_meters_in_component_formulas` plus per-formula overrides via the new `FormulaOverrides` class.  Also exposes the new `steam_boiler_formula` method, and renames `battery_coalesce_formula` / `pv_coalesce_formula` to `battery_ac_coalesce_formula` / `pv_ac_coalesce_formula`.

- `ComponentGraphConfig.__init__` is now declared as keyword-only in the type stubs (the runtime was already keyword-only, so positional calls were already failing at runtime).

- The per-category preference flags inverted polarity: where the old flags selected the *device*, the new override entries select the *meter*.  E.g. `ComponentGraphConfig(prefer_inverters_in_pv_formula=True)` becomes `ComponentGraphConfig(formula_overrides=FormulaOverrides(prefer_meters_in_pv_formula=False))`.
