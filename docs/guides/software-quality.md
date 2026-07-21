# Software Quality Guide

This guide documents LibreSim's static-analysis, security, pre-commit, and CI
quality gates. Test execution and coverage policy are maintained separately in
the [testing guide](testing.md).

## Quality gates

| Tool | Scope | Configuration | Required stage |
|---|---|---|---|
| Ruff | Backend linting and formatting | `backend/pyproject.toml` | Pre-commit and CI |
| mypy | Backend static typing | `backend/pyproject.toml` | CI |
| Bandit | Backend security scanning | `backend/pyproject.toml` | Pre-commit and CI |
| ESLint | Frontend linting | `frontend/.eslintrc.cjs` | Pre-commit and CI |
| TypeScript | Frontend static typing | `frontend/tsconfig.json` | Pre-commit and CI |
| detect-secrets | Repository secret scanning | `.secrets.baseline` | Pre-commit |

The backend and frontend test suites enforce permanent 100% coverage gates.
See [testing.md](testing.md) for their commands and current measurements.

## Canonical commands

Run project quality commands from the repository root in Docker. When the
sandbox socket exists, every Docker invocation uses the explicit host shown
below.

```bash
# Backend lint
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  sh -c "pip install -q -e '.[dev]' && ruff check src/ tests/"

# Backend format check
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  sh -c "pip install -q -e '.[dev]' && ruff format --check src/ tests/"

# Backend type check
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  sh -c "pip install -q -e '.[dev]' && mypy src/ --config-file=pyproject.toml"

# Backend security scan
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  sh -c "pip install -q -e '.[dev]' && bandit -c pyproject.toml -r src/"

# Frontend lint
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend \
  npm run lint

# Frontend type check
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend \
  npm run typecheck
```

Ruff's configured rule families include Pyflakes/pycodestyle errors, import
sorting, bugbear checks, Python-upgrade checks, simplification, naming, and
warnings. mypy checks untyped function bodies and uses the Pydantic plugin;
module-specific compatibility overrides are documented in
`backend/pyproject.toml`. Bandit excludes test-only paths through its project
configuration.

## Pre-commit behavior

`.pre-commit-config.yaml` currently runs Ruff, Ruff formatting, Bandit,
repository hygiene checks, and detect-secrets. Frontend ESLint and TypeScript
hooks call the running frontend container. The backend pytest hook is a
pre-push hook. mypy runs in GitHub Actions and GitLab CI rather than as an
active pre-commit hook.

Pre-commit itself is a host Git integration, so installing or invoking it is
the sole exception to the Docker-only project-command rule:

```bash
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files
```

Do not treat a skipped container-backed hook as a successful quality run; use
the canonical Docker commands above before merging.

## Continuous integration

`.github/workflows/ci.yml` and `.gitlab-ci.yml` both require backend Ruff,
mypy, Bandit, pytest coverage, code-generation validation, frontend ESLint,
TypeScript, and Vitest coverage. The workflows install C/C++ and Rust
toolchains before code-generation validation and publish the canonical report
at `docs/reports/codegen-validation-report.md`.

When adding or changing a quality rule:

1. Change the owning configuration file.
2. Run the relevant canonical Docker command.
3. Update both CI pipelines if the command or artifact contract changes.
4. Update this guide only when the workflow or responsibility changes.

Never lower a quality or coverage threshold merely to make a failing gate
pass. Fix the violation or document an intentional, narrowly scoped exception.
