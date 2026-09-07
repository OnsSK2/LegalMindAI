# LegalMind AI

> RAG-powered legal Q&A assistant for EU & French law.
> Modular · Runs entirely on free tools

## What it does
Ask questions about EU legislation, French legal texts, and GDPR
in plain language. LegalMind AI retrieves the relevant legal clauses
and generates a structured answer with source references.

## Tech stack
Everything below is free — no GCP billing account, no paid API tier.

| Layer         | Tool                                              |
|---------------|----------------------------------------------------|
| API           | FastAPI + Uvicorn                                  |
| Embeddings    | sentence-transformers (`all-MiniLM-L6-v2`), local  |
| Vector DB     | ChromaDB, local / self-hosted                      |
| LLM           | Gemini via Google AI Studio free-tier API key       |
| Storage       | Local filesystem (`./data`)                        |
| Secrets       | `.env` file (gitignored)                           |
| Orchestration | LangChain                                          |

Google AI Studio's free tier (`GEMINI_API_KEY` in `.env`) is a different
product from Vertex AI — it needs only a Google account, no billing setup,
and no credit card. Get a key at https://aistudio.google.com/apikey.

Cloud deployment (Cloud Run, GCS, Secret Manager) is a possible *later*
step once the RAG pipeline works, not a requirement to run this project.

## Run locally

Requires **Python 3.14** (matches the Dockerfile base image).

### With Docker — recommended, starts API + ChromaDB
```bash
cp .env.example .env        # fill in GEMINI_API_KEY (free — see Tech stack above)
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
- [ ] Phase 4: Deploy (optional, later — free tiers exist for Cloud Run)
