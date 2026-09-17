# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Chicago zoning-data analysis: producing a chart showing the percentage of land
zoned for each use, broken down by ward.

## Code principles

Follow SOLID principles when writing or refactoring code:

- **Single Responsibility** — each module/function/class should have one reason to change.
  Keep data loading, transformation, and charting logic in separate units.
- **Open/Closed** — write code that can be extended (e.g. new zoning categories, new wards)
  without modifying existing working logic.
- **Liskov Substitution** — if you introduce class hierarchies or shared interfaces,
  subtypes must be usable anywhere the base type is expected, without surprising behavior.
- **Interface Segregation** — prefer small, focused interfaces/function signatures over
  large ones that force callers to depend on things they don't use.
- **Dependency Inversion** — depend on abstractions (e.g. a data-source interface), not
  concrete implementations, so the data source (CSV, API, database) can be swapped without
  rewriting analysis or charting code.

Apply these pragmatically — this is a small data project, not enterprise software. Don't
over-engineer with abstractions the project doesn't need yet; the goal is clean, testable,
maintainable code, not maximal indirection.

## General conventions

- Keep data-processing code and visualization code decoupled so the underlying data source
  can change without touching the chart logic.
- Prefer clear, well-named functions over comments explaining what code does.
- Write small, testable functions for data transformations (e.g. computing zoning
  percentages per ward) so they can be verified independently of the chart output.
- When adding a chart, use the `dataviz` skill guidance for styling and accessibility.

## Documentation style

Be terse. No flowery language — plain, direct sentences. State facts, not narrative.
Applies to README, code comments, and docstrings.
