# Codex project instructions

## Docker

The Codex sandbox exposes the Docker daemon at `/run/docker.sock`, while the
Docker client defaults to `/var/run/docker.sock`. Prefix every `docker` and
`docker compose` invocation with `DOCKER_HOST=unix:///run/docker.sock`.

Example:

```bash
DOCKER_HOST=unix:///run/docker.sock docker compose up --build
```
