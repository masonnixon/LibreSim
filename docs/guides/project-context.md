# Project Context

LibreSim is a React/TypeScript frontend and FastAPI/Python backend for visual
block-diagram simulation. Development services use frontend port 4200 and
backend port 9000; Docker Compose is the supported reproducible environment.

The backend simulation kernel follows the block lifecycle `init()`,
`update()`, `rpt()`, and `propagateStates()`, with Euler, RK2, RK4, and Merson
integration methods. The frontend uses React Flow and Zustand.

Quality gates are configured in the backend and frontend manifests and are
run in CI: Ruff, mypy, Bandit, pytest with coverage, ESLint, TypeScript, and
secret detection. The canonical commands and coverage policy are maintained
in [`testing.md`](testing.md) and [`software-quality.md`](software-quality.md).

The repository uses the LibreSim Source Available Commercial License; the
authoritative terms remain in the root [`LICENSE`](../../LICENSE).

## Durable design decisions

These conventions were retained from the former `.claude/context.md` session
record before it was removed:

- OSK's public camelCase methods, such as `getOutput` and `setInput`, are
  intentional because they follow the Simulink/MATLAB-inspired API vocabulary.
- Standard engineering symbols such as `Kp`, `Ki`, `Kd`, `A`, `B`, `C`, and
  `D` retain their conventional capitalization even when a general naming rule
  would prefer lowercase identifiers.
- `Block.state()` remains the base-class method name. Subclass state storage
  uses `_x_state` where necessary to avoid shadowing that method.
- Pydantic models use aliases and `populate_by_name=True` to preserve the JSON
  contract shared with the frontend while allowing Python-facing field names.

The deleted context also contained dated implementation diaries. Their durable
outcomes are represented by the current source, tests, completed plans, and
audit records rather than being copied into this maintained guide.
