# Yuno — Payment Observability System

A production-oriented observability platform for payment transactions that normalizes heterogeneous, messy event data using a hybrid of rules and AI.

This repository contains two main parts:

- back/: Backend services (FastAPI, normalization workers, integrations with Data Lake and AI components)
- front/: Frontend UI (React + TypeScript + Vite)
- docs/: Comprehensive architecture and onboarding documentation

Status: Active — Hackathon/POC-ready. See docs/ for full implementation details.

---

## Quick overview

Yuno ingests raw payment events from multiple sources (S3/Data Lake, direct producers, files), normalizes them via a mix of deterministic rules and LLM-assisted normalization (LangChain + OpenAI), and exposes APIs for queries, analytics and monitoring.

Key features

- Hybrid normalization (Rules + AI)
- Ingest from Data Lakes (JSON/JSONL/CSV/Parquet)
- FastAPI backend with documented OpenAPI UI
- React + Vite frontend for dashboards and investigation
- Tested components (example: DataLakeClient with tests)

---

## Contents

- back/ — backend service and workers
- front/ — frontend application (React + TypeScript + Vite)
- docs/ — full architecture, START_HERE and developer docs

---

## Quick start

Prerequisites

- Python 3.10+ (recommended)
- Node.js 18+ and npm/yarn for the frontend
- PostgreSQL (for production or local testing)
- An OpenAI-compatible key if using AI normalization

Backend (development)

1. Open a terminal and go to the backend folder:

   cd back

2. Install dependencies (use your preferred tool; the project contains pyproject/requirements):

   # Example using a virtual environment
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt  # or use poetry/pip-tools as the project requires

3. Setup environment variables:

   copy .env.example .env
   # Edit .env and set DB connection, DATALAKE_URL, OPENAI_API_KEY, etc.

4. Apply database migrations:

   alembic upgrade head

5. Run the API locally:

   uvicorn app.main:app --reload --port 8000

6. Open API docs:

   http://localhost:8000/docs

Frontend (development)

1. Open a terminal and go to the frontend folder:

   cd front

2. Install node dependencies and run dev server:

   npm install
   npm run dev

3. Visit the frontend (Vite will show the local URL, typically http://localhost:5173)

Frontend scripts (from front/package.json)

- npm run dev — start Vite dev server (HMR)
- npm run build — compile TypeScript and build static assets
- npm run preview — serve built assets locally

---

## Data Lake integration

The backend includes a DataLake client and polling worker for ingesting raw files from configured Data Lake endpoints. See back/docs and back/app/infraestructure/datalake for implementation details and examples.

Example usage (from docs/back):

- Configure DATALAKE_BASE_URL or DATA_LAKE_URI in .env
- Run the poller once for testing: python -m app.workers.data_lake_poller --once

---

## Project structure (summary)

back/
- app/ — FastAPI app, routers, services, domain models
- infraestructure/ — DB clients, data lake client, AI adapters
- tests/ — unit and integration tests
- docs/ — backend-specific docs

front/
- src/ — React + TypeScript application
- package.json — dev/build scripts (Vite)

docs/
- START_HERE.md, ARCHITECTURE.md, ROADMAP.md, DATA_LAKE_INTEGRATION.md and more — read these first

---

## Testing

- Backend: pytest (and pytest-asyncio for async tests)
- Frontend: recommended to use vitest / jest depending on project config

Run backend tests:

cd back
.\.venv\Scripts\activate
pytest -v

---

## Contributing

Please read docs/START_HERE.md and docs/ARCHITECTURE.md before starting work. Follow these basics:

- Create feature branches from main
- Keep changes small and focused
- Add/update tests for new logic
- Update docs in docs/ for architectural or behavioral changes

---

## Resources

- Backend API docs: http://localhost:8000/docs (after running backend)
- Developer docs: docs/ (read INDEX.md and START_HERE.md first)
- Frontend dev: cd front && npm run dev

---

## License

Specify a license here (e.g., MIT) or include a LICENSE file at the repo root.

---

If anything here is missing or you want the README tailored further (add badges, CI, deployment steps, or environment variables reference), say what to include and the README will be updated.