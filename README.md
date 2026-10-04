# LegaliQ

LegaliQ has a FastAPI/RAG backend in this folder and a Next.js UI in the sibling
`LegaliQ-cm` folder. The UI sends chat requests to its same-origin
`/api/lawbridge` route, which forwards them to this backend.

## Start the backend

From this folder, create and activate a virtual environment, then install the
backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The backend uses the PDFs in `knowledge_base/` to build its searchable legal
index. Run ingestion when setting up a new index or after adding PDFs:

```powershell
python ingest.py
```

For Gemini-generated answers, set `GEMINI_API_KEY` in this folder's `.env` file.
Keep that key on the backend; do not put it in the frontend environment.

Start the API:

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Check that it is running at `http://127.0.0.1:8000/health`.

## Start the UI

In a second terminal:

```powershell
cd ..\LegaliQ-cm
pnpm install
pnpm dev
```

Open `http://localhost:3000`. The UI's API route defaults to
`http://127.0.0.1:8000/api/lawbridge`. To use a different backend URL, set
`LEGALIQ_API_URL` in the UI project's `.env.local` and restart the Next.js
server. The value must be the full chat endpoint URL.

The API accepts `question` and an optional `conversation` array, and returns an
`answer` with retrieved `sources`. The chat UI renders those sources below each
answer. `GET /health` is available for checking backend readiness.
