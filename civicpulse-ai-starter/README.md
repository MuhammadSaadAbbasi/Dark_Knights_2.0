# CivicPulse AI — starter repository

CivicPulse AI lets a citizen submit a hazard photo and a location description through the website. A shared Python API stores the report and asks a vision-capable AI provider for a **suggested** category and preliminary severity. Admins verify or correct the result through the same website.

## Stack
- Web user/admin: React + TypeScript + Vite
- Backend: Python + FastAPI + Pydantic
- MVP database: SQLite
- AI: provider adapter placeholder; choose Gemini or OpenAI after testing availability, price and sample-image performance

## Monorepo layout
- `apps/web/` — original combined React starter
- `apps/frontend/userpanel/` — public citizen website, organized with MVVM
- `apps/frontend/adminpanel/` — authenticated admin website, organized with MVVM
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

The API uses SQLite persistence and a **mock AI assessment** by default so the end-to-end flow can run without an API key. A Gemini adapter is included but must be enabled only after confirming that the configured model is available to your Google project. Reports remain available after an API restart. Never commit real keys.

To enable Gemini locally, set `AI_PROVIDER=gemini`, add your key to `services/api/.env`, and set `GEMINI_MODEL` to the exact model ID available in your Google AI project. The checked-in placeholder is `gemini-3.5-flash`; availability of that model ID is not verified by this repository. The adapter reads `services/api/.env` when the process environment does not already provide these values, so restart Uvicorn after changing the file.

The first admin account is bootstrapped from `ADMIN_USERNAME` and `ADMIN_PASSWORD` on first startup. The password is stored as a salted PBKDF2 hash. The website logs in through `POST /api/auth/login` and sends the returned short-lived JWT as a Bearer token. Set a random `JWT_SECRET` with at least 32 characters. Admin review changes are recorded in an audit history. AI calls use the configured timeout and retry limits.

Website users can register and sign in through `POST /api/auth/register` and
`POST /api/auth/login`. Registration collects an email address and home
area/neighborhood. Their reports are stored with ownership information, so users
can only look up their own reports.

For a controlled hackathon evaluation, set `DEMO_LOGIN_ENABLED=true` in
`services/api/.env`. The User and Admin panels then show direct demo-login
buttons. Keep this setting false in production; the demo route is disabled by
default.

Run backend tests from `services/api`:
```bash
pytest
```

## Run user website
```bash
cd apps/frontend/userpanel
npm install
npm run dev
```
The user website submits reports and looks them up through the shared API. Configure `VITE_API_BASE_URL` for deployment.

## Run admin website
```bash
cd apps/frontend/adminpanel
npm install
npm run dev
```
The admin website signs in through `POST /api/auth/login`, then uses the JWT for queue and review requests. Its MVVM layers are under `src/model`, `src/viewmodel`, and `src/view`.

## Team workflow
1. Agree on API contract in `docs/API_CONTRACT.md` before coding in parallel.
2. Create GitHub issues for `web-user`, `web-admin`, `api-ai`, and `testing-deploy`.
3. Use branches: `feature/web-user`, `feature/web-admin`, `feature/api-ai`.
4. Merge small pull requests into `main`; don't edit another teammate's files without coordination.
5. Keep `.env` out of Git. Commit `.env.example` only.
6. Test image upload, unknown/unclear images, AI failure, and admin review before demo.

## MVP safety rules
- AI result is a suggestion, not a verified safety determination.
- Never claim a wire is live based only on a photo.
- Never claim an authority was notified unless a real integration confirms it.
- Unknown/ambiguous images go to manual review.
- Keep uploaded images private and validate file size/type in production.
