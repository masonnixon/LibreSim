# Sim/State Compatibility Facade Deprecation

> **Status:** proposed; separate maintainer approval required
> **Recorded by:** FAC-9 Phase 7
> **Depends on:** completed FAC-9 instance-scoped simulation state

## Purpose

FAC-9 retained class-level `State.*` and `Sim.*` access as a compatibility bridge for
older direct-OSK callers and custom blocks. Runtime correctness no longer depends on
those class attributes: built-in blocks, adapters, runners, and native simulations use
their explicitly owned `SimContext`.

Removing the bridge is intentionally outside FAC-9. It can break third-party blocks and
scripts even though it does not change built-in numerical behavior, so implementation
requires a separate maintainer decision and deprecation window.

## Proposed migration

1. Inventory external/custom block guidance and any remaining repository call sites.
2. Document replacements: `block.context`, `state.context`, explicit `SimContext`, and
   instance fields on native `Sim`.
3. Add one release cycle of actionable deprecation warnings for class-level reads and
   writes without warning from internally activated compatibility boundaries.
4. Remove `_StateFacade`, `_SimFacade`, the sequential legacy-context pairing, and their
   default mutable fallback state.
5. Retain explicit context activation only where it is useful for scoped custom-block
   compatibility, or remove it as a separately reviewed sub-decision.

## Acceptance gate

- no production or built-in block uses mutable class-level `State.*` or `Sim.*` state;
- direct adapter, runner, and native `Sim` isolation/convergence suites remain green;
- custom-block migration examples cover timing, sampling, termination, and integrators;
- release notes identify the breaking change and supported replacement API; and
- the complete backend, numerical, frontend, and generated-code matrices remain green.

Do not begin this plan merely as cleanup during another feature. Obtain explicit
approval and record the intended release/deprecation timeline first.
