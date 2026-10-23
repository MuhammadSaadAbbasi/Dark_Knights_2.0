# API Contract v1

Base URL local: `http://127.0.0.1:8000`

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

## Admin endpoints planned (protect before production)
- `GET /api/admin/reports?status=NEW&severity=high`
- `GET /api/admin/reports/{report_id}`
- `PATCH /api/admin/reports/{report_id}` — category/severity/status correction
- `POST /api/admin/reports/{report_id}/merge` — confirm a duplicate relationship

The starter intentionally does not expose admin mutation endpoints until authentication and authorization are implemented.

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
