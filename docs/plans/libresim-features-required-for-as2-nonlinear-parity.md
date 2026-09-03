---
title: LibreSim Generic Numerical and Hybrid-System Capability Proposal
tags:
  - libresim
  - numerical-methods
  - simulation
  - feature-proposal
status: proposal
owner: Mason Nixon
created: 2026-09-02
---

# LibreSim generic capability proposal

## Purpose

LibreSim should remain a general-purpose block-diagram simulation platform.
The requirements below are domain-independent. They enable users to compose
nonlinear, multibody, constrained, and hybrid dynamical systems from reusable
native blocks without embedding any particular robot, plant, or application in
LibreSim.

## 1. General matrix and vector operations

Provide consistent operations for arbitrary compatible shapes:

- matrix-matrix multiplication: `[m,k] × [k,n] -> [m,n]`;
- matrix-vector multiplication: `[m,n] × [n] -> [m]`;
- transpose: `[m,n] -> [n,m]`;
- vector concatenation, slicing, and indexed element access;
- block, diagonal, identity, and zero-matrix construction;
- explicit row/column orientation and shape metadata;
- deterministic broadcasting rules, or no broadcasting where ambiguous;
- actionable validation errors for incompatible dimensions.

Shape information must survive JSON parsing, compilation, nested subsystem
flattening, and runtime execution. Flattening order must be documented and
tested.

## 2. General linear-system solve primitive

Add a registered native block, such as `linear_solve`, for solving

\[
  A x = b
\]

where `A` is square and `b` is a vector or a matrix of right-hand sides.

Required behavior:

- Support arbitrary runtime dimension `N`, with a practical minimum of at
  least `N = 30`.
- Accept dense matrices and vector or matrix right-hand sides.
- Use a numerically stable method such as LU with partial pivoting or QR.
- Do not implement the operation as explicit matrix inversion.
- Support multiple right-hand sides without changing numerical semantics.
- Produce deterministic results for identical inputs and settings.
- Work through the normal JSON registry/compiler/adapter path.
- Expose method, pivoting, singularity tolerance, conditioning limit, and
  failure policy as documented parameters.

Failure behavior must be explicit:

- reject nonsquare matrices and dimension-mismatched right-hand sides;
- detect singular and numerically ill-conditioned systems;
- never return stale output from a previous step;
- never silently substitute a pseudoinverse unless explicitly selected;
- expose failure through a structured error or status output.

## 3. Solver diagnostics

Optionally expose success/failure status, residual norm `||A x-b||`, rank or
factorization status, condition estimate, pivot information, active dimension,
method identifier, and execution timing. Diagnostics must not alter numerical
outputs and must be connectable to scopes, logs, and supervisory logic.

## 4. Runtime-dimension and mode-aware data handling

Provide reusable mechanisms for selecting matrix rows/columns by index or mask,
masking vector elements, switching among fixed-shape alternatives, zeroing
inactive outputs, preserving declared maximum dimensions, and validating
dimension changes at event boundaries. The timing of a dimension or mode change
must be explicit: before the current update, after it, or at the next step.

## 5. Hybrid-system events and reset semantics

Support domain-neutral event conditions based on continuous signals, discrete
signals, or logical expressions; deterministic ordering for simultaneous events;
pre-event and post-event state access; reset maps for integrators, memory,
delays, solver caches, and discrete states; configurable hysteresis; and event
logs containing time, event identity, and reset result.

Document whether algebraic outputs are recomputed before or after reset maps
and how zero-duration repeated events are suppressed.

## 6. Algebraic-loop and constrained-system support

Provide explicit algebraic-loop detection during compilation and a documented
algebraic-loop or nonlinear residual solver with configurable iteration limit,
absolute/relative tolerances, relaxation, convergence status, residual, and
iteration count. Separate continuous integrator states from algebraic
variables. Nonlinear algebraic equations must not need to be disguised as a
`state_space` block.

## 7. Integration and solver-state lifecycle

Continuous and solver-backed blocks should share a clear lifecycle:

`initialize -> evaluate/update -> accept step -> optional reject/retry -> reset -> terminate`.

For Euler, RK4, Merson, and future adaptive methods, document input sampling
and derivative reevaluation. Cached factorizations and intermediates must be
invalidated when inputs or active modes change. Fixed-step execution must be
reproducible.

## 8. Structured signal contracts for subsystems

Nested subsystems should support explicit shape metadata on inports/outports,
consistent port numbering, boundary dimension validation before flattening,
recursive flattening that preserves shape and event semantics, stable flattened
names for scopes, and documented copy/reference behavior for mutable arrays.
JSON, the compiler, direct OSK execution, and GUI/runtime execution must agree.

## 9. Registry, serialization, and execution completeness

Every generic numerical block must support JSON construction, schema
validation, registry lookup, nested compilation, headless and normal runtime
execution, and lossless serialization/deserialization of parameters and
shapes. Unknown parameters, unsupported shapes, and unavailable methods should
fail early with actionable messages.

## 10. Required developer test matrix

Add generic tests for:

- scalar, 2×2, 3×3, and larger solves with known answers;
- random well-conditioned systems against a trusted reference;
- multiple right-hand sides;
- badly scaled, singular, and near-singular inputs;
- residual and conditioning diagnostics;
- matrix products, transpose, slicing, masking, concatenation, and shape
  validation;
- nested subsystem matrix/vector ports;
- event ordering, reset maps, repeated-event suppression, and cache
  invalidation;
- Euler and RK4 lifecycle semantics;
- deterministic reset and repeated execution;
- JSON round-trip, registry lookup, compilation, and headless execution;
- deliberate failures proving stale outputs and silent fallbacks do not occur.

At least one domain-neutral example must combine a nonlinear residual system, a
mode change, and a solve larger than 2×2, checking both numerical outputs and
diagnostics.

## 11. Performance and safety

Avoid unnecessary matrix copies where safe, make factorization reuse explicit,
expose timing for profiling, prevent unbounded allocations/iterations, and
document supported numeric dtypes and precision limits. Optimizations must not
weaken shape checks, residual checks, or failure reporting.

## 12. Acceptance criteria

A domain-neutral example must demonstrate:

1. a nonlinear state update;
2. runtime construction of a matrix and right-hand side from native signals;
3. a general solve with `N > 2`;
4. an event/mode change that changes the active equations;
5. deterministic reset and repeatability;
6. solution, residual, conditioning, and status outputs;
7. successful JSON compilation and headless execution;
8. deterministic failure for singular or dimension-invalid input.

No application-specific model, controller, or repository-side task should be
required for acceptance.

## Non-goals

Do not add application-specific equations or parameter sets, hidden registry
bypasses, linearized substitutes for nonlinear models, silent pseudoinverse or
stale-value fallbacks, or GUI-only behavior unavailable headlessly.
