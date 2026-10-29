"""
LegalMind AI — Ingestion Orchestrator
Runs the full pipeline:
PDF → Markdown → Chunks → Embeddings → ChromaDB
Documents loaded dynamically from data/documents.json
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from services.ingestion.ocr import convert_all_pdfs
from services.chunking.chunker import chunk_all
from services.embeddings.embedder import store_chunks, test_retrieval

load_dotenv()

DATA_RAW  = Path("data/raw")
DATA_PROC = Path("data/processed")
DOCS_CONFIG = Path("data/documents.json")


def load_document_registry() -> list:
    """
    Load document registry from JSON config.
    Falls back to auto-discovery if config missing.
    """
    if DOCS_CONFIG.exists():
        with open(DOCS_CONFIG, "r", encoding="utf-8") as f:
            docs = json.load(f)
        logger.info(f"   Loaded {len(docs)} documents from {DOCS_CONFIG}")
        return docs

    # Auto-discover PDFs in data/raw/
    logger.warning("   No documents.json found — auto-discovering PDFs...")
    docs = []
    for pdf in DATA_RAW.glob("*.pdf"):
        docs.append({
            "file":         pdf.name,
            "source":       pdf.stem.upper(),
            "full_name":    pdf.stem.replace("_", " ").title(),
            "jurisdiction": "Unknown",
            "domain":       "legal",
            "year":         0,
            "access_roles": ["admin", "lawyer"],
        })
        logger.info(f"   Auto-discovered: {pdf.name}")
    return docs


def save_report(n_docs, n_chunks, duration):
    DATA_PROC.mkdir(exist_ok=True)
    report = {
        "ingested_at":  datetime.utcnow().isoformat(),
        "documents":    n_docs,
        "total_chunks": n_chunks,
        "duration_sec": round(duration, 2),
    }
    report_path = DATA_PROC / "ingestion_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"   Report → {report_path}")


def main():
    start = time.time()
    logger.info("\n LegalMind AI — Ingestion Pipeline\n")

    # Step 1: Load document registry
    logger.info(" Step 1: Loading document registry...")
    documents = load_document_registry()
    if not documents:
        logger.error("No documents found.")
        sys.exit(1)

    # Step 2: PDF → Markdown
    logger.info("\n Step 2: Converting PDFs to Markdown...")
    markdown_texts = convert_all_pdfs(documents)
    if not markdown_texts:
        logger.error("No documents converted. Add PDFs to data/raw/")
        sys.exit(1)
    logger.info(f"   Converted: {list(markdown_texts.keys())}")

    # Step 3: Chunk
    logger.info("\n  Step 3: Legal-aware chunking...")
    chunks = chunk_all(markdown_texts, documents)

    # Step 4: Embed & store
    logger.info("\n Step 4: Embedding & storing in ChromaDB...")
    vectorstore = store_chunks(chunks)

    # Step 5: Test retrieval
    logger.info("\n Step 5: Testing retrieval...")
    test_retrieval(vectorstore)

    # Step 6: Save report
    duration = time.time() - start
    save_report(len(markdown_texts), len(chunks), duration)

    logger.info(f"\n Ingestion Complete!")
    logger.info(f"   Documents: {len(markdown_texts)}")
    logger.info(f"   Chunks:    {len(chunks)}")
    logger.info(f"   Time:      {duration:.1f}s")
    logger.info("\n   → Ready for Phase 3: RAG Pipeline 🎯\n")


if __name__ == "__main__":
    main()