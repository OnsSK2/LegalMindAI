# LegalMind AI Architecture

## Overview

LegalMind AI is designed as a legal question-answering system. The target architecture routes user requests through an API to either a retrieval-augmented generation (RAG) pipeline or a set of tools, then returns an answer with supporting citations.



## Target architecture

```mermaid
flowchart TD
    User --> API["FastAPI<br/>JWT authentication + RBAC"]
    API --> Router{"LangGraph router"}

    Router -->|Answer| RAG["RAG pipeline<br/>ChromaDB + Ollama"]
    RAG --> DB[("ChromaDB")]
    DB --> LLM["Ollama / Gemini<br/>llama3.2 or Gemini Flash"]
    LLM --> Result(["Grounded answer + citations"])

    Router -->|Tools| MCP["MCP tools<br/>search · ingest"]
    MCP --> Docs[("data/processed/<br/>gdpr.md · civil.md")]
    Docs --> Result