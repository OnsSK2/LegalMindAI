# LegalMind AI

> RAG-powered legal Q&A assistant for EU & French law.
> Production-ready · Modular · Deployed on GCP

## What it does
Ask questions about EU legislation, French legal texts, and GDPR
in plain language. LegalMind AI retrieves the relevant legal clauses
and generates a structured answer with source references.

## Tech stack
| Layer       | Tool                              |
|-------------|-----------------------------------|
| API         | FastAPI + Cloud Run               |
| Embeddings  | Vertex AI textembedding-gecko@003 |
| Vector DB   | ChromaDB (dev) / Vertex AI (prod) |
| LLM         | Vertex AI Gemini Pro              |
| Storage     | Google Cloud Storage              |
| Secrets     | GCP Secret Manager                |
| Orchestration | LangChain                       |

## Run locally

Requires **Python 3.14** (matches the Dockerfile base image).

### With Docker — recommended, starts API + ChromaDB
```bash
cp .env.example .env        # fill in GEMINI_API_KEY and GCP_PROJECT_ID
docker compose up --build
curl http://localhost:8080/health
```

### Without Docker — API only
```bash
uv venv .venv --python 3.14        # or: py -3.14 -m venv .venv
.venv\Scripts\activate             # Windows; source .venv/bin/activate on Unix
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Note: `.env` ships `CHROMA_HOST=chroma`, which is the compose service name.
Running the API outside compose against a containerised ChromaDB requires
`CHROMA_HOST=localhost`.

## Project structure
See the /services folder — one service per RAG stage.

## Status
- [x] Phase 1: Environment setup
- [ ] Phase 2: Data ingestion
- [ ] Phase 3: RAG pipeline
- [ ] Phase 4: Deploy to GCP
