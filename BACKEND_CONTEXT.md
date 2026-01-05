# Backend Context (Django)

This document is the canonical reference for frontend-backend integration during development.

## TAG=[MILESTONE:R1_RELEASE]
Backend APIs are ready for UI development for:
- Auth (register/activate/login/refresh/reset)
- Profile + roles
- User directory + role management
- In-app notifications (email + in-app)
- Feedback system
- BOM / purchase request workflows (templates, signoff, procurement approvals, receiving, audit events)
- Catalog items (dynamic per-user list)
- Purchase Orders
- Assets auto-conversion and management
- Partner transfers
- Bills upload/download
- Search history

## Project Layout
- Backend code: `backend/`
- Django settings: `backend/procurement_tool/settings.py`
- Apps:
  - `backend/accounts/` (custom user auth + activation + reset)
  - `backend/profiles/` (user profile)
  - `backend/notifications/` (in-app notifications)
  - `backend/boms/` (BOM / purchase request workflows)
  - `backend/catalog/` (dynamic item catalog)
  - `backend/purchase_orders/` (purchase orders)
  - `backend/attachments/` (file uploads)
  - `backend/searches/` (search history)
  - `backend/assets/` (assets)
  - `backend/transfers/` (partner transfers)
  - `backend/bills/` (bills workflow)
  - `backend/core/` (health + Microsoft Graph mailer + misc)

## Local Dev
- Run backend: `python backend/manage.py runserver 0.0.0.0:8000`
- API base URL (frontend should use): `http://localhost:8000/api`
- Health: `GET http://localhost:8000/api/health/` -> `{ "status": "ok" }`

## Environment (.env)
Create `backend/.env` (copy from `backend/.env.example`).

Key vars:
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DB_ENGINE` = `sqlite` or `postgres`
- `CORS_ALLOWED_ORIGINS` (if frontend is served from `http://localhost:4200`)
- `BACKEND_BASE_URL` (used to build fallback links in emails)
- `FRONTEND_BASE_URL` (preferred for activation/reset links)
- `NOTIFICATIONS_SEND_EMAIL=1` (optional; mirrors in-app notifications to email via Graph)
  - Per-user toggle: `notifications_email_enabled` must be `true` on the profile
- `PO_NUMBER_PREFIX`, `PO_NUMBER_PADDING` (purchase order number format)
- `MEDIA_ROOT`, `MEDIA_URL` (file uploads; defaults to `backend/media`)
- `API_RATE_USER`, `API_RATE_ANON` (request throttling)
- `API_DEBUG_ERRORS=1` (include exception details in API error responses; default on in debug)
- Microsoft Graph:
  - `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_SENDER`
  - optional tuning: `GRAPH_TIMEOUT_SECONDS`, `GRAPH_MAX_RETRIES`, `GRAPH_RETRY_BACKOFF_SECONDS`

Dev-only toggles (default to enabled when `DJANGO_DEBUG=1`):
- `ALLOW_NON_TLD_EMAILS` (allows emails like `name@company`)
- `ALLOW_NUMERIC_PASSWORDS` (allows passwords like `12345678`)

## Auth Model
Custom user model: `accounts.User`
- Login identifier: `email`
- Activation gate: `is_active` must be `true` to log in
- Email matching: login is case-insensitive (`email__iexact`)
- Role signal: `roles` is returned on user payloads (computed from profile roles + superuser status)

## Auth Endpoints (JWT)
All endpoints are under `/api/`.

### Register
- `POST /api/auth/register/`
- Body:
  - `email` (string)
  - `password` (string)
  - optional: `first_name`, `last_name`
- Responses:
  - `201` (success): `{ user: {...}, detail: "...", mail_sent: true|false }`
  - `400` (validation): `{ field: ["..."] }`

Notes:
- On success, backend attempts to send an activation email.
- Email failures do **not** block registration; `mail_sent=false` indicates delivery failed.
- When `DJANGO_DEBUG=1` and Graph fails, response includes:
  - `activation_link` and `mail_error` (to unblock local frontend testing)

### Activate account
- `GET /api/auth/activate/?uid=...&token=...`
- `POST /api/auth/activate/` with `{ uid, token }`

### Login (JWT)
- `POST /api/auth/login/`
- Body: `{ email, password }`
- Response `200`: `{ access, refresh, user }`
- If `is_active=false`: `400` with `detail: "Account is not activated."`

### Refresh access token
- `POST /api/auth/token/refresh/`
- Body: `{ refresh }`
- Response `200`: `{ access }`

### Current user
- `GET /api/auth/me/` (Authorization: `Bearer <access>`)

## Users (Directory)
Requires Authorization: `Bearer <access>`.
- `GET /api/users/` (list users for assignee/approver selection; includes `roles`)

## Admin (Role Management)
Requires Authorization: `Bearer <access>` and `admin` role.
- `PATCH /api/admin/users/:id/`
  - fields: `roles` (array of strings), `is_active` (bool)
  - allowed roles: `approver`, `procurement`, `admin` (`employee` is implicit)

### Password reset
- `POST /api/auth/password-reset/` with `{ email }`
  - Always returns `200` to avoid leaking user existence.
  - When `DJANGO_DEBUG=1` and Graph fails, response may include `reset_link` + `mail_error`.
- `GET /api/auth/password-reset/confirm/?uid=...&token=...` (validates link)
- `POST /api/auth/password-reset/confirm/` with `{ uid, token, new_password }`

## Profile Endpoints
Requires Authorization: `Bearer <access>`.
- `GET /api/profile/`
- `PATCH /api/profile/`
  - fields: `display_name`, `phone_number`, `job_title`, `avatar_url`, `notifications_email_enabled`
  - read-only: `roles` (set via admin)

## Notifications (In-app)
Requires Authorization: `Bearer <access>`.
- `GET /api/notifications/` (list mine)
- `GET /api/notifications/:id/` (retrieve mine)
- `POST /api/notifications/:id/mark-read/`
- `POST /api/notifications/mark-all-read/`
- `GET /api/notifications/unread-count/`

Filters for `GET /api/notifications/`:
- `unread=1` or `read=1`
- `level=INFO,SUCCESS,WARNING,ERROR`
- `created_from`, `created_to` (ISO date/datetime)

## Feedback
Requires Authorization: `Bearer <access>`.
- `POST /api/feedback/` (create)
- `GET /api/feedback/` (admin sees all; others see their own)
- `PATCH /api/feedback/:id/` (admin only; update `status`, `admin_note`)

Create fields:
- `category`: `BUG`, `FEATURE`, `UX`, `OTHER`
- `message` (required)
- `page_url` (optional)
- `rating` (optional, 1-5)
- `metadata` (optional JSON)

## BOM / Purchase Requests (REST)
Requires Authorization: `Bearer <access>`.

### Templates
- `GET /api/bom-templates/` (global + mine)
- `POST /api/bom-templates/` (creates mine)
- `PATCH /api/bom-templates/:id/` (only owner or admin; if template is global, backend clones it for the user and returns the new template)
- Seed global templates: `python backend/manage.py seed_bom_templates`
Schema extras for UI:
- `schema.sample_bom` (sample BOM data)
- `schema.sample_items` (list of sample items, with base fields + `data` for schema fields)

### BOMs (Purchase Requests)
- `GET /api/boms/` (admin/procurement see all; others see own + collaborating)
- `POST /api/boms/` (creates DRAFT)
- Draft capacity: controlled by `BOM_MAX_DRAFTS_PER_USER` (default 15, `0` = unlimited)
- `PATCH /api/boms/:id/` (only when DRAFT/NEEDS_CHANGES; owner/collaborator/admin)
- `POST /api/boms/:id/items/` (add item)
- `POST /api/boms/:id/request-signoff/` (assign signoff for some/all items)
- `POST /api/boms/:id/request-procurement-approval/` (creates approval request; all must approve)
- `POST /api/boms/:id/cancel/` (cancels pending signoff/approval, resets to DRAFT; only BOM owner or procurement)
- `GET /api/boms/:id/export/?format=pdf|csv|json` (download BOM + items)
  - PDF export requires `fpdf2` to be installed (added to `backend/requirements.txt`).

Filters for `GET /api/boms/`:
- `status=DRAFT,APPROVED,...` (comma-separated)
- `search` or `q` (title/project)
- `project`, `owner_id`, `template_id`
- `created_from`, `created_to`, `updated_from`, `updated_to`
Workflow permissions hardening:
- BOM owners and collaborators can request signoff and procurement approval.
- Procurement approvals must be assigned to users with `approver` role.
- Procurement actions require `procurement` role (admin does not bypass unless explicitly assigned).

### BOM Collaborators (Workspace)
Collaborators can view and edit the BOM while it is in `DRAFT` or `NEEDS_CHANGES`. Collaborators and owners can request signoff or procurement approval.
- `GET /api/boms/:id/collaborators/`
- `POST /api/boms/:id/collaborators/` with `{ user_id }`
- `DELETE /api/boms/:id/collaborators/:user_id/` (owner/procurement/admin; or collaborator can remove themselves)

Filters for `GET /api/boms/`:
- `status=DRAFT,APPROVED,...` (comma-separated)
- `search` or `q` (title/project)
- `project`, `owner_id`, `template_id`
- `created_from`, `created_to`, `updated_from`, `updated_to`

### Signoff Inbox (Items)
- `GET /api/bom-items/` (owner sees own; assignee sees assigned)
- `POST /api/bom-items/:id/signoff/` (assignee/admin decides APPROVED/NEEDS_CHANGES)

Filters for `GET /api/bom-items/`:
- `bom_id`, `assignee_id`, `signoff_status`, `search`

### Procurement Approval Inbox
- `GET /api/procurement-approvals/` (admin sees all; others see assigned)
- `POST /api/procurement-approvals/:id/decide/` (APPROVED/NEEDS_CHANGES; all must approve)

Notifications:
- When a BOM is fully approved, the BOM owner and all users with the `procurement` role receive an in-app notification (email optional).

Filters for `GET /api/procurement-approvals/`:
- `status`, `bom_id`, `request_id`

### Procurement Actions
- `POST /api/procurement-actions/:bom_id/mark-ordered/` (procurement role only)
- `POST /api/procurement-actions/:bom_id/receive/` (procurement role only; supports partial receipts)

### Pagination
List endpoints use standard pagination (`count`, `next`, `previous`, `results`):
- `GET /api/boms/`, `GET /api/bom-items/`, `GET /api/procurement-approvals/`
- `GET /api/bom-events/`, `GET /api/notifications/`, `GET /api/bom-templates/`
Query params:
- `page` (1-based)
- `page_size` (default 25, max 200)

### Audit Log
- `GET /api/bom-events/` (admin/procurement see all; others filtered to own)

Filters for `GET /api/bom-events/`:
- `bom_id`, `actor_id`, `event_type`
- `created_from`, `created_to`
- `order=created_at` or `order=-created_at`

## Catalog Items
Requires Authorization: `Bearer <access>`.
- `GET /api/catalog-items/` (list; admin/procurement see all, others see own)
- `POST /api/catalog-items/` (create)
- `PATCH /api/catalog-items/:id/` (update)
- `DELETE /api/catalog-items/:id/` (delete)

Filters for `GET /api/catalog-items/`:
- `search` or `q` (name/vendor/category)
- `category`, `vendor`

## Purchase Orders
Requires Authorization: `Bearer <access>`.
- `GET /api/purchase-orders/` (procurement/admin see all; others see own or BOM-linked)
- `POST /api/purchase-orders/` (procurement only; generates `po_number` if blank)
- `PATCH /api/purchase-orders/:id/` (procurement only)
- `POST /api/purchase-orders/:id/items/` (procurement only; add line)
- `POST /api/purchase-orders/:id/mark-sent/` (procurement only)
- `POST /api/purchase-orders/:id/cancel/` (procurement only)
- `POST /api/purchase-orders/:id/receive/` (procurement only; partial receipts)

Filters for `GET /api/purchase-orders/`:
- `status`, `bom_id`, `vendor`, `category`, `search` (po_number/vendor)
- `created_from`, `created_to`, `updated_from`, `updated_to`

## Attachments (Bills/Invoices)
Requires Authorization: `Bearer <access>`.
- `GET /api/attachments/`
- `POST /api/attachments/` (multipart; fields: `file`, optional `bom`, `purchase_order`, `bill`)
- `DELETE /api/attachments/:id/`

Filters for `GET /api/attachments/`:
- `bom_id`, `purchase_order_id`, `bill_id`

## Search History
Requires Authorization: `Bearer <access>`.
- `GET /api/search/history/` (list)
- `POST /api/search/history/` (log query + filters)

## Assets
Requires Authorization: `Bearer <access>`.
- `GET /api/assets/` (procurement/admin see all; others see assets from their BOMs)
- `PATCH /api/assets/:id/` (procurement/admin)

Filters for `GET /api/assets/`:
- `status`, `bom_id`, `purchase_order_id`, `category`, `vendor`, `search`

Auto-conversion:
- Fully received BOM/PO items create assets automatically.

## Partner Transfers
Requires Authorization: `Bearer <access>`.
- `GET /api/partners/` (list)
- `GET /api/transfers/` (list transfers)
- `POST /api/transfers/` (procurement/admin only)
- `PATCH /api/transfers/:id/` (procurement/admin only)
- `POST /api/transfers/:id/items/` (add asset line)
- `POST /api/transfers/:id/submit/`
- `POST /api/transfers/:id/approve/` (approver/admin)
- `POST /api/transfers/:id/complete/` (procurement/admin)
- `POST /api/transfers/:id/cancel/` (procurement/admin)

## Bills
Requires Authorization: `Bearer <access>`.
- `GET /api/bills/`
- `POST /api/bills/`
- `PATCH /api/bills/:id/` (creator/procurement/admin)
- `DELETE /api/bills/:id/`

Filters for `GET /api/bills/`:
- `status`, `vendor`, `bom_id`, `purchase_order_id`
- `created_from`, `created_to`

## CORS
If the frontend runs at `http://localhost:4200` and calls the API at `http://localhost:8000`, set:
- `CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200`

## Microsoft Graph (Validation)
Before relying on register/reset flows, test Graph configuration:
- `python backend/manage.py test_graph_email --to you@domain.com`

Common failure:
- `HTTP 401: invalid_client (AADSTS7000215)` means `GRAPH_CLIENT_SECRET` is wrong. In Azure App Registration, copy the *client secret Value* (not the Secret ID), update `backend/.env`, and restart the backend.
  - If your secret contains `#`, wrap it in quotes in `.env` or it will be truncated by dotenv.
  - If you previously exported env vars in your shell/system, the backend now forces `backend/.env` to override them.
- `HTTP 403: ErrorAccessDenied` means the app lacks Graph Mail.Send permission or admin consent, or `GRAPH_SENDER` is not a valid mailbox in the tenant.

## Email Links (Frontend Routes)
When `FRONTEND_BASE_URL` is set, the backend generates:
- Activation: `${FRONTEND_BASE_URL}/activate?uid=...&token=...`
- Reset confirm: `${FRONTEND_BASE_URL}/reset-password/confirm?uid=...&token=...`

## Known Runtime Quirk
If you run the backend on a Python version where Django admin crashes with:
`AttributeError: 'super' object has no attribute 'dicts'`,
we apply a safe runtime patch in `backend/core/apps.py` to keep admin rendering working.
