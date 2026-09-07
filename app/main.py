from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI(title="LegalMind AI")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "LegalMind AI",
        "env": os.getenv("APP_ENV", "development")
    }

@app.post("/query")
def query(q: str):
    return {
        "answer": "RAG pipeline coming in Step 5",
        "query": q
    }