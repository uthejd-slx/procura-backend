# Procurement Tool

Repo layout:
- Backend: `backend/` (Django + DRF)
- Frontend: `frontend/` (Angular + Material)

Developer references:
- Backend API contract: `BACKEND_CONTEXT.md`
- Project history: `CHANGELOG.md`

## Quick start (Docker)
1. Copy `backend/.env.example` to `backend/.env` and fill in values.
   - For docker-compose + Postgres, set `DJANGO_DB_ENGINE=postgres`.
2. Run: `docker compose up --build`
3. Frontend: `http://localhost:4200/`
4. Backend API base: `http://localhost:8000/api/`

## Backend endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/` (JWT)
- `POST /api/auth/token/refresh/` (JWT)
- `GET|POST /api/auth/activate/`
- `POST /api/auth/password-reset/`
- `GET|POST /api/auth/password-reset/confirm/`
- `GET /api/auth/me/`
- `GET /api/profile/`
- `PATCH /api/profile/`

## Microsoft Graph mail
Set `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, and `GRAPH_SENDER` in `backend/.env`. The Azure app registration typically needs Microsoft Graph `Mail.Send` (Application) permission and admin consent.
