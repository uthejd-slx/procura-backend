# Milestones

This project is developed in backend-first milestones. Each milestone is tagged so a context-service can detect what APIs are ready.

## Tag Format
- Use this exact pattern in docs/changelog: `TAG=[MILESTONE:<ID>]`
- Example: `TAG=[MILESTONE:R1_RELEASE]`

## Release 1

### TAG=[MILESTONE:R1_RELEASE]
- Auth (email/password) + activation/reset via Microsoft Graph
- Profile + roles
- User directory + admin role management APIs
- Notifications (in-app + email)
- Feedback system (user submissions + admin review)
- BOM/Purchase Request workflow (templates, items, signoff, approvals, receiving)
- Catalog items (dynamic per-user list)
- Purchase Orders
- Assets auto-conversion and management
- Partner transfers
- Bills upload/download
- Search history

## Deferred (Hold for later)
- Teams module
- RFQ/quote comparison
- Reporting/analytics
- Throttling/rate limits
- Reorder hints beyond basic search history
