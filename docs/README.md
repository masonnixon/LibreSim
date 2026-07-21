# LibreSim Documentation

This directory is the canonical home for durable LibreSim documentation.

## Contents

- [`guides/`](guides/) — maintained developer, format, operations, testing,
  and software-quality guidance.
- [`plans/`](plans/) — active work plans; completed plans live in
  [`plans/completed/`](plans/completed/).
- [`audits/`](audits/) — dated audit records and remediation checkpoints.
- [`reports/`](reports/) — current generated reports; historical reports live
  in [`reports/archive/`](reports/archive/).
- [`assets/`](assets/) — durable supporting assets when an asset is required.

## Documentation lifecycle

New work starts as an active plan. When acceptance evidence is complete, move
the plan to `plans/completed/`. Generated validation output belongs in
`reports/`; dated snapshots and superseded reports belong in
`reports/archive/`. Audits retain their date and status in `audits/`.

A document is eligible for purge only when it is generated, machine-specific,
an unreferenced duplicate, or has had all unique information merged into its
authoritative replacement. Before purging, search code, CI, and Markdown
references and record the disposition in the consolidation plan.

## Project context

The maintained runtime and quality conventions extracted from the former
Claude session context are documented in [`guides/project-context.md`](guides/project-context.md).
