# Master prompt for a coding agent

Act as a senior software architect and full-stack engineer. Build **CivicPulse AI** in this existing monorepo. Read `README.md`, `docs/ARCHITECTURE.md`, and `docs/API_CONTRACT.md` first and preserve their contracts.

## Product
A citizen uploads a photo and types where the hazard is. Supported MVP categories:
1. open manhole / uncovered drain
2. pothole / damaged road
3. exposed electrical wire
4. waterlogging / flooded road
5. other
6. unknown / cannot classify

The AI should inspect visible evidence and return a structured preliminary category, severity suggestion, rationale, uncertainty, and `needs_human_review`. A photo cannot prove a wire is live, exact pothole/water depth, or accident cause. Do not state authorities were notified unless a real integration confirms it. High-risk cases require human verification.

## Applications
- Android citizen app: Kotlin + Jetpack Compose, developed in Android Studio.
- Web app/admin dashboard: React + TypeScript + Vite.
- Shared backend: Python + FastAPI + Pydantic.
- Database: SQLite for local MVP; keep data-access code modular so PostgreSQL can replace it.
- AI: create a provider adapter. Implement one real vision API only after confirming its current model ID, SDK, structured output support, pricing/access and required environment variables. Keep a mock provider for tests and local development.

## Required engineering behaviour
1. Inspect existing files before editing; do not overwrite unrelated work.
2. Follow `docs/API_CONTRACT.md` and update it if a change is necessary.
3. Keep AI keys server-side in environment variables; never put secrets in Android or web client.
4. Validate image MIME/signature, size and schema. Handle timeout, malformed output, unknown category and API failure.
5. Save the report before/independently of AI completion; failed AI must not delete the report.
6. Separate AI-suggested fields from admin-verified fields.
7. Admin actions must be authenticated and authorized before public deployment. Do not present the unauthenticated demo endpoints as production-ready.
8. Add unit tests for validation, severity policy and AI fallback. Add API tests for report creation and failure handling.
9. Use accessible UI: labels, visible focus, responsive layout, clear loading/errors, text severity labels (not colour alone), and plain language.
10. Avoid scope creep. Prioritize the end-to-end MVP over maps, complex analytics, notifications or model training.

## Work plan
Phase A: inspect repo and summarize planned edits.
Phase B: complete backend persistence (SQLite), validation, AI adapter, severity policy and tests.
Phase C: complete web citizen submission flow and admin report queue/detail/review.
Phase D: provide Kotlin/Compose screen and API client integration, preserving the team's Android project if present.
Phase E: run tests/builds available in the environment, fix errors, and update README with exact commands.

## Completion report
At the end, list files changed, setup/run commands, environment variables, tests actually run and their results, remaining limitations, and what must be done before public deployment. Never claim a test or integration works unless you ran it successfully.
