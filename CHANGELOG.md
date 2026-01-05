# Changelog

All notable changes to this project will be documented in this file.

## Unreleased
### Added
- Seeded BOM templates now include `schema.sample_bom` and `schema.sample_items` with realistic sample data.
- Guided onboarding/tutorial overlay (auto-run on first login, manual trigger in user menu).
- BOM collaborators panel with add/remove + self-removal.
- BOM export downloads (PDF/CSV/JSON).
- Catalog item JSON data editor and BOM item prefill from catalog.
- Release-based GitHub Actions deployment workflow and production compose file.
- BOM collaboration support with collaborator management endpoints.
- BOM export endpoint for PDF/CSV/JSON downloads.
- Demo automation script (`frontend/scripts/demo-run.ts`) to seed data, capture UI screenshots, and generate `frontend/docs/USAGE_GUIDE.md`.
- Help guide page that renders the generated `frontend/docs/USAGE_GUIDE.md` inside the app.

### Changed
- Aligned UI to Release 1 scope: removed Teams/RFQ/Quotes/Reports dashboards and reorder hints from navigation and pages.
- Registration no longer fails if activation email sending fails; response includes `mail_sent=false`.
- Improved Graph mail test command with clearer error guidance for missing config and permission issues.
- Added a global API exception handler so frontend receives error details when `API_DEBUG_ERRORS=1`.
- Notifications bell badge now uses `/api/notifications/unread-count/`.
- Bills UI no longer exposes approval workflow actions (CRUD only).
- Attachments UI now supports BOM/PO/Bill only.
- Search page now covers history only.
- BOM template editing now allows global templates to be edited (saved as user-owned copies); delete is restricted to owner/admin.
- Template preview now uses sample data (`sample_bom`, `sample_items`) when provided.
- Editing a global BOM template now creates a user-owned copy instead of modifying the global template.
- Procurement-role users now receive a notification when a BOM is fully approved.
- BOM references in audit/procurement lists now link to the BOM detail page.
- Sidenav simplified with a "More" menu for secondary sections.
- Navigation and route access are now role-gated (approver/procurement/admin).
- Procurement-only actions are disabled unless the user has the `procurement` role (admins can still view).
- Tutorial steps are now role-aware and skip missing UI targets.
- Tutorial steps now resolve seeded demo records (BOM/PO/Transfer/Bill) when available.
- File upload inputs now use the dark theme styling (Choose file button + field).
- Help guide now includes a sticky table-of-contents sidebar for in-app navigation.
- BOM edit permissions now allow collaborators in `DRAFT`/`NEEDS_CHANGES`.
- BOM list includes a client-side "Shared with me" toggle.
- Help guide markdown loader now respects `APP_BASE_HREF` and falls back across `/assets/docs` and `/docs`.
- Help guide markdown now uses theme styling with responsive images/tables.
- Help guide markdown links now use the theme color.
- Help page header now has extra spacing above the guide panel.
- Help guide markdown styles now apply to rendered content (global encapsulation for the help page).
- Help page header layout now matches other pages with proper spacing and actions alignment.
- Refined notification badge sizing and positioning in the toolbar.
- Notification badge now uses the dark theme background and tighter positioning.
- Notification badge colors switched to dark + light text and positioned closer to the bell icon.
- Notification badge now anchors directly on the bell icon via a dedicated toolbar class.
- Notification badge now touches the bell corner and uses the dark-lime theme colors.
- Notification badge now overlaps the bell icon with tighter offsets.
- Adjusted notification badge inset to sit on the bell icon (not the button edge).
- Notification badge now anchors on the bell ring wrapper to touch the icon directly.
- Nudged notification badge closer to sit over the bell icon.
- Notification badge now anchors to the bell icon (not the ring) for true overlap.
- Notification badge now uses a custom overlay anchored to the bell icon for precise placement.
- Notification badge now offsets outward to sit on the bell icon top-right.
- Notification badge now uses the real unread count only (demo count removed).
- Added a dark border ring around the notifications icon.
- Usage guide signoff wording now reflects assignee access (any role).
- Production compose now exposes backend on host port 8001 to avoid conflicts.
- Deployment workflow now starts the web container and runs migrations/collectstatic via `docker compose exec` to avoid SSH timeouts.
### Added
- Feedback dialog with floating action button, user list, and admin status/admin_note updates.

## TAG=[MILESTONE:R1_RELEASE]
### Scope
- Release 1 backend scope aligned to the approved requirements (BOM workflow, procurement ordering, assets, transfers, bills upload/download, search history).

### Added
- Custom email-based auth + activation/reset via Microsoft Graph.
- Profile with roles and per-user notification email toggle.
- Feedback system (user submissions + admin review).
- BOM/Purchase Request workflows with signoff + procurement approvals.
- Procurement actions (mark ordered, receive items) on BOMs.
- Dynamic catalog items per user.
- Purchase Orders (vendor, items, receipts).
- Assets auto-created from fully received BOM/PO items.
- Partner transfers for assets.
- Bills module with upload/download support (via attachments).
- Search history logging.
- In-app notifications (email optional via Graph).

### Changed
- Workflow permissions hardened to enforce owner/role rules.
- Attachments now support linking to bills.
- BOM/PO items include optional `category`.
- Release 1 scope excludes teams, RFQ/quotes, reports, dashboards, and reorder hints (deferred).
- Release 1 UI includes the notifications unread badge and BOM list filters/pagination.
