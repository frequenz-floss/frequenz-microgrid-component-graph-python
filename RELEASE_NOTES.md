# Frequenz Microgrid Component Graph Library Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- The `microgrid` extra now needs `frequenz-client-microgrid >= 0.18.4`, up from `>= 0.18.3`. A component's operational mode is read from its `provides_telemetry()` and `accepts_control()` methods, and 0.18.3 has neither, so the feature below would do nothing there. If you pin the client yourself, move the pin to `>= 0.18.4, < 0.19`.

## New Features

- Formulas now take a component's operational mode into account. A component that provides no telemetry is not used as a measurement source. It is still used to classify the meter that measures it (e.g. as a PV meter or a CHP meter), so it can still be measured through that meter.

  The mode is read from the component's `provides_telemetry()` and `accepts_control()` methods. A component that does not have both methods, or does not specify both values, is treated as providing telemetry and is used exactly as before. A component built from the microgrid API carries the mode the API reports for it, so formulas can change for a site that has an inactive or control-only component.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
