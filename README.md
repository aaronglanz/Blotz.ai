## Property App (Nestly) — working frontend + backend

### What’s here
- **backend**: FastAPI + Postgres (SQLAlchemy) + Redis + Celery worker
- **frontend**: Vite + React + React Query, proxies `/api` to the backend in dev

### Prereqs
- **Docker Desktop** (recommended) for Postgres + Redis
- **Node 20+** for the frontend
- **Python 3.12+** for the backend (if not using the backend container)

### Quickstart (recommended: everything via Docker)
1. Create your env file:

```bash
cp .env.example .env
```

2. Put real values into `.env` (at least `ANTHROPIC_API_KEY` / `GOOGLE_PLACES_API_KEY` if you want those features).

3. Start everything:

```bash
docker compose up --build
```

4. Open the app:
- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/health`

### Local dev (no Docker for app code)
You can still use Docker just for Postgres/Redis:

```bash
docker compose up -d db redis
```

Then run backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Then run worker (separate terminal, same venv):

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks worker --loglevel=info
```

Then run frontend:

```bash
cd frontend
npm install
npm run dev
```

### Notes
- **Do not commit `.env`**. It’s already ignored by `.gitignore`.
- If you ever accidentally pasted real API keys into `.env`, **rotate them immediately** in their respective dashboards.

