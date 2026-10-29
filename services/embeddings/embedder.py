# LegalMind AI — Embedding Service
import os
from pathlib import Path
from loguru import logger
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

VECTOR_DIR  = Path("data/vector_store")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL") or (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def get_embeddings():
    logger.info(f"   Loading embedding model: {EMBED_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def store_chunks(chunks: list, collection: str = "legalmind") -> Chroma:
    embeddings = get_embeddings()
    logger.info(f"   Embedding {len(chunks)} chunks → ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DIR),
        collection_name=collection,
    )
    logger.info(f"   Stored {len(chunks)} chunks in '{collection}'")
    return vectorstore


def load_vectorstore(collection: str = "legalmind") -> Chroma:
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings,
        collection_name=collection,
    )


def test_retrieval(vectorstore: Chroma):
    queries = [
        "What are the rights of data subjects?",
        "What is the right to erasure?",
        "What are the obligations of data controllers?",
    ]
    logger.info("\n🔍 Testing retrieval...")
    for query in queries:
        results = vectorstore.similarity_search_with_score(query, k=2)
        logger.info(f"\n   Q: {query}")
        for doc, score in results:
            logger.info(
                f"   Score: {score:.4f} | "
                f"{doc.metadata.get('source')} | "
                f"{doc.page_content[:80]}..."
            )
