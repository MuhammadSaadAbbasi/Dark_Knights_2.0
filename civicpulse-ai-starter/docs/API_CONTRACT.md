# API Contract v1

Base URL local: `http://127.0.0.1:8000`

## `POST /api/auth/login`
Accepts:
```json
{
  "username": "admin",
  "password": "your-password"
}
```

Returns a short-lived signed bearer token:
```json
{
  "access_token": "JWT",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

Admin website requests send the token in:
```text
Authorization: Bearer <access_token>
```

## `POST /api/auth/register`
Creates a normal website user account and returns the same token response.
Usernames may contain letters, numbers, `.`, `_`, and `-`. Passwords must be at
least eight characters. Registration also requires `email` and `location`; the
location is the user's home area or neighborhood and is separate from a report
location.

```json
{
  "username": "new-citizen",
  "password": "at-least-8-characters",
  "email": "citizen@example.com",
  "location": "Central District"
}
```

## `POST /api/auth/demo-login`
Returns a normal JWT session for the requested `user` or `admin` demo role.
This route is available only when `DEMO_LOGIN_ENABLED=true` and is intended
for a controlled hackathon evaluation environment. Keep it disabled in
production.

User report endpoints require the returned token:
- `POST /api/reports`
- `GET /api/reports/{report_id}`

Reports are associated with the authenticated user. A user cannot read another
user's report by ID.

## `POST /api/reports`
Content type: `multipart/form-data`
- `photo` (required): JPG, PNG, or WebP image
- `location_text` (required): human-readable road/area/landmark description
- `description` (optional): additional observed details

Returns `201 Created`:
```json
{
  "id": "uuid",
  "status": "NEW",
  "ai_status": "COMPLETE",
  "assessment": {
    "category": "open_manhole",
    "visible_evidence": ["An uncovered opening appears visible"],
    "suggested_severity": "high",
    "rationale": "The image appears to show an uncovered opening in a public area.",
    "uncertainty": "Depth and exact risk cannot be confirmed from one image.",
    "needs_human_review": true
  }
}
```

## `GET /api/reports/{report_id}`
Returns report ID, created time, location text, case status, AI status, and assessment. Production should use an unguessable reporter token or authenticated ownership; UUID alone should not be treated as authorization.

## Admin endpoints (protect before production)
- `GET /api/admin/reports?status=NEW&severity=high`
- `GET /api/admin/hotspots?limit=10` — real location aggregation for priority and critical reports
- `GET /api/admin/reports/{report_id}/image` — authenticated image evidence for the admin detail view
- `PATCH /api/admin/reports/{report_id}` — category/severity/status correction
- `DELETE /api/admin/reports/{report_id}` — permanently removes a report, its audit events, and stored image
- `GET /api/admin/reports/{report_id}/audit`
- `POST /api/admin/reports/{report_id}/merge` — confirm a duplicate relationship

Admin endpoints require a bearer token for a user with the `admin` role. The image endpoint streams the stored upload only after that authorization check; upload paths are never returned to the browser.

Admin report lists support bounded pagination:
```text
GET /api/admin/reports?page=1&page_size=20
```

Pagination metadata is returned in `X-Total-Count`, `X-Page`, and `X-Page-Size` headers.

AI provider execution uses a configurable timeout and at most two retries. Configure these with `AI_TIMEOUT_SECONDS` and `AI_RETRIES`.

Admin review keeps AI suggestions separate from verified values:
```json
{
  "verified_category": "pothole_road_damage",
  "verified_severity": "medium",
  "review_note": "Confirmed by admin review.",
  "reviewed_at": "2026-10-23T12:00:00+00:00"
}
```

## Category enum
`open_manhole`, `pothole_road_damage`, `exposed_electrical_wire`, `waterlogging`, `other`, `unknown`

## Severity enum
`critical`, `high`, `medium`, `low`, `uncertain`

## Status enum
`NEW`, `UNDER_REVIEW`, `VERIFIED`, `ASSIGNED`, `RESOLVED`, `REJECTED`

## Rules
- AI fields are preliminary suggestions.
- Never auto-merge duplicates or automatically dispatch a response.
- Unknown, low-quality, or unsupported images require human review.
