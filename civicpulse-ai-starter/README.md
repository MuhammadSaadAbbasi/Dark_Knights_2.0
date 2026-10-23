# CivicPulse AI — starter repository

CivicPulse AI lets a citizen submit a hazard photo and a location description. A shared Python API stores the report and asks a vision-capable AI provider for a **suggested** category and preliminary severity. Admins verify or correct the result.

## Stack
- Android: Kotlin + Jetpack Compose (your team opens/builds this in Android Studio)
- Web/Admin: React + TypeScript + Vite
- Backend: Python + FastAPI + Pydantic
- MVP database: SQLite
- AI: provider adapter placeholder; choose Gemini or OpenAI after testing availability, price and sample-image performance

## Monorepo layout
- `apps/android/` — Android Studio project placeholder and API contract
- `apps/web/` — React + TypeScript admin/citizen web starter
- `services/api/` — FastAPI backend
- `docs/` — architecture and API contract
- `shared/` — shared JSON examples and category definitions

## Run backend
```bash
cd services/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows cmd; use cp on macOS/Linux
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

This starter uses a **mock AI assessment** so the end-to-end flow can run without an API key. Replace `app/ai/provider.py` with a real provider integration only after adding your API key to `.env`. Never commit real keys.

## Run web
```bash
cd apps/web
npm install
npm run dev
```
The web UI expects the API at `http://127.0.0.1:8000`. For deployment, configure `VITE_API_BASE_URL`.

## Android integration
Open/create the Android project in Android Studio under `apps/android/`. Follow `docs/API_CONTRACT.md`. Use Retrofit/OkHttp or Ktor client; send multipart form data with fields:
- `photo`: image file
- `location_text`: required location description
- `description`: optional extra context

Do not put AI-provider keys in Android code. The Android app calls your backend only.

## Team workflow
1. Agree on API contract in `docs/API_CONTRACT.md` before coding in parallel.
2. Create GitHub issues for `android`, `web-admin`, `api-ai`, and `testing-deploy`.
3. Use branches: `feature/android-report`, `feature/web-admin`, `feature/api-ai`.
4. Merge small pull requests into `main`; don't edit another teammate's files without coordination.
5. Keep `.env` out of Git. Commit `.env.example` only.
6. Test image upload, unknown/unclear images, AI failure, and admin review before demo.

## MVP safety rules
- AI result is a suggestion, not a verified safety determination.
- Never claim a wire is live based only on a photo.
- Never claim an authority was notified unless a real integration confirms it.
- Unknown/ambiguous images go to manual review.
- Keep uploaded images private and validate file size/type in production.
