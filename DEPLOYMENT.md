# Deployment (Release-based)

This project deploys on GitHub **Release published** events via `.github/workflows/release-deploy.yml`.

## Prereqs on the Droplet
- Docker + Docker Compose v2 (`docker compose`).
- A working `.env.prod` in `/home/ubuntu/procura_backend`.
- The repo files present at `/home/ubuntu/procura_backend` (including `docker-compose.prod.yml`).

## Required GitHub Secrets
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `PROD_SERVER_IP`
- `PROD_SERVER_SSH_USER`
- `PROD_SERVER_SSH_KEY`
- `PROD_SERVER_SSH_PORT` (optional, default 22)
- `PROD_SERVER_SSH_PASSPHRASE` (optional)

## Production Compose
`docker-compose.prod.yml` expects:
- `DOCKERHUB_USERNAME` (set by the workflow)
- `IMAGE_TAG` (release tag set by the workflow)
- Database vars in `.env.prod`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, plus `POSTGRES_HOST=db`.
 - Web service is exposed on host port `8001` (container port `8000`).
 - Web container runs WSGI via `gunicorn` with SSE support (single-instance, in-memory channel layer).

## Release Flow
1. Create a GitHub Release.
2. Workflow builds and pushes:
   - `DOCKERHUB_USERNAME/procura-backend:<release-tag>`
   - `DOCKERHUB_USERNAME/procura-backend:latest`
3. Deployment runs on the droplet:
   - pulls the new image
   - runs migrations + collectstatic
   - starts the `web` service and runs migrations/collectstatic via `exec`
   - health checks `/api/health/`
   - rolls back if health check fails
