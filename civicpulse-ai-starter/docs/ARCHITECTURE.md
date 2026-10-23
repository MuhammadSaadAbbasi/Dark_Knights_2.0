# Architecture overview

```text
Website user flow -----------\
                              --> FastAPI --> image validation --> AI provider adapter
Website admin flow ----------/       |                              |
                                     v                              v
                                SQLite/Postgres <-- validated assessment
                                     |
                                     v
                              Admin review queue
```

## Responsibility split
- Website user flow: select photo, location text, upload progress, show receipt/results.
- Website admin flow: report queue, report detail, review controls, counts.
- API: validation, storage, report lifecycle, severity policy, authorization, AI invocation.
- AI adapter: translate provider output into a validated `HazardAssessment`.
- Database: report record, assessment, review changes, audit events.

## Trust boundaries
The browser/mobile app and model output are untrusted. Validate file type/size, validate model schema, keep API secrets on the server, and require admin verification.
