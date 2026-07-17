# Frequenz Microgrid Component Graph Library Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- Bumped PyO3 to 0.29 to pull in the fix for RUSTSEC out-of-bounds read advisory GHSA-36hh-v3qg-5jq4 (`nth`/`nth_back` on list/tuple iterators).

- Updated the `frequenz-microgrid-component-graph` Rust crate to v0.6.0. This changes some outputs that are visible from Python:

  - The formula fallback engine was rewritten. Formulas can now contain meter-subtraction and diamond terms. Exact formula strings can differ from the previous release, even for the same graph.

  - The consumer formula now measures the non-consumer components behind one internal meter as one group: it subtracts `COALESCE(#meter, component readings...)` instead of each component on its own. Note: if such a meter also carries a load that is not in the component graph, that load is now subtracted together with the group while the meter reading is used.

  - Graph validation failures now raise `InvalidGraphError` with a message that starts with `Graph validation failed:`, followed by one indented line per problem. The old format was `InvalidGraph: <description>`. Note: some errors found while building the graph, for example a missing grid component, still use the old format. Code that matches on the message text of validation failures must be updated.

- `prefer_meters_in_component_formulas` now defaults to `False`: per-category formulas use the component reading as the primary source and the meter as the fallback. Set it to `True` to restore the old meter-first order. This changes only the order of the sources; the new fallback terms from v0.6.0 are used either way.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
