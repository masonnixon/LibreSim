# LibreSim Documentation

This directory is the canonical home for durable LibreSim documentation.

## Guides

- [Adding new plot types](guides/adding-new-plot-types.md)
- [Blockset development](guides/blockset-development-guide.md)
- [LibreSim Coder](guides/libresim-coder.md)
- [MDL format reference](guides/mdl-format-reference.md)
- [Project context and design decisions](guides/project-context.md)
- [Running headless](guides/running-headless.md)
- [Software quality](guides/software-quality.md)
- [Testing](guides/testing.md)

## Plans

Active plans:

- [Documentation consolidation and purge](plans/documentation-consolidation-and-purge.md)
- [Documentation inventory manifest](plans/documentation-inventory-manifest.md)
- [Refactoring recommendations](plans/refactoring-recommendations.md)
- [Simulation-state compatibility facade deprecation](plans/sim-state-compatibility-facade-deprecation.md)

Completed plans:

- [Control-analysis visualization design](plans/completed/control-analysis-visualization-design.md)
- [100% coverage](plans/completed/coverage-100.md)
- [Fable audit completion](plans/completed/fable-audit-completion.md)
- [FAC-9 simulation-context concurrency](plans/completed/fac-9-sim-context-concurrency.md)
- [Simulation-correctness remediation](plans/completed/simulation-correctness-remediation.md)

## Audits and reports

- [Original Fable audit — 2026-07-07](audits/fable-2026-07-07.md)
- [Fable remediation checkpoint — 2026-07-10](audits/fable-remediation-checkpoint-2026-07-10.md)
- [Fable remediation final status — 2026-07-16](audits/fable-remediation-final-2026-07-16.md)
- [Current generated codegen validation report](reports/codegen-validation-report.md)
- [Archived codegen validation report — 2026-01-21](reports/archive/codegen-validation-2026-01-21.md)
- [Archived cross-language consistency report — 2026-01-21](reports/archive/codegen-cross-language-consistency-2026-01-21.md)
- [Documentation assets policy](assets/README.md)

## Documentation lifecycle

New work starts as an active plan. When acceptance evidence is complete, move
the plan to `plans/completed/`. Generated validation output belongs in
`reports/`; dated snapshots and superseded reports belong in
`reports/archive/`. Audits retain their date and status in `audits/`.

A document is eligible for purge only when it is generated, machine-specific,
an unreferenced duplicate, or has had all unique information merged into its
authoritative replacement. Before purging, search code, CI, and Markdown
references and record the disposition in the consolidation plan.

## Intentional root-level documents

The repository [README](../README.md), [license](../LICENSE), and
[agent instructions](../AGENTS.md) stay at the repository root by convention.
The [examples README](../examples/README.md) stays with the examples because
the backend serves that exact path.

## Project context

The maintained runtime and quality conventions extracted from the former
Claude session context are documented in [`guides/project-context.md`](guides/project-context.md).
