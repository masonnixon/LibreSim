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
