# Print Lifecycle Hooks

Run your own steps at the start/end/cancel of a print without editing the core macros. Define a macro
whose name starts with `_PRINT_START_`, `_PRINT_END_`, or `_CANCEL_PRINT_` and it is picked up and
run automatically as part of `PRINT_START`, `PRINT_END`, or `CANCEL_PRINT`.

```ini
[gcode_macro _PRINT_START_10_message]
gcode:
    M117 Starting up
```

## Ordering (read this)

Hooks run in **sorted name order**, so **prefix them with a number** to control sequencing:
`_PRINT_START_10_...` runs before `_PRINT_START_20_...`.

> **Danger.** The order is only as reliable as the names. If two hooks must run in a specific order
> and you do not number them, one can run before the other expects it to. Always number hooks that
> have dependencies. This is the deliberate, documented sharp edge of a discover-and-run system.

## Caveats

- **Experimental, not yet verified on a physical printer.**
- It overrides `PRINT_START`/`PRINT_END`/`CANCEL_PRINT` via `rename_existing`, so it can **conflict
  with other plugins that override the same macros**. Install it alone among macro-overriders.
- Assumes your config defines `PRINT_START`/`PRINT_END`/`CANCEL_PRINT` by those names.
