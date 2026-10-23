# CivicPulse website frontend

This folder contains two independent React/Vite website clients. Both use the
same FastAPI backend:

- `userpanel/` — public citizen report submission and lookup.
- `adminpanel/` — authenticated admin queue and review workflow.

Each client uses a small MVVM structure:

```text
src/
  model/       API types and data access
  viewmodel/   state and asynchronous UI actions
  view/        React components and styles
```

Run each panel from its own directory:

```powershell
cd apps\frontend\userpanel
npm install
npm run dev

cd apps\frontend\adminpanel
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in a local `.env` when the API is not at
`http://127.0.0.1:8000`.
