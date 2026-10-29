# LegalMind AI — Chunking Service
import re
from loguru import logger
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.ingestion.text_processing import detect_language

CHUNK_CONFIGS = {
    "GDPR":            {"chunk_size": 800,  "chunk_overlap": 150},
    "FrenchCivilCode": {"chunk_size": 500,  "chunk_overlap": 80},
    "EU_AI_Act":       {"chunk_size": 1200, "chunk_overlap": 200},
    "EU_Charter":      {"chunk_size": 600,  "chunk_overlap": 100},
    "default":         {"chunk_size": 800,  "chunk_overlap": 150},
}

def chunk_markdown(md_text: str, metadata: dict, source: str = "default") -> list[Document]:
    config = CHUNK_CONFIGS.get(source, CHUNK_CONFIGS["default"])
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=["\n\nArticle ", "\n\nArt. ", "\n\n", "\n", ". ", " "]
    )
    chunks = splitter.create_documents([md_text], metadatas=[metadata])
    for i, chunk in enumerate(chunks):
        configured_language = metadata.get("language", "und")
        fallback_language = configured_language if configured_language != "auto" else "und"
        marked_languages = re.findall(
            r"<!--\s*language:\s*([a-z]{2,3})\s*-->",
            chunk.page_content,
            flags=re.IGNORECASE,
        )
        clean_content = re.sub(
            r"<!--\s*language:\s*[a-z]{2,3}\s*-->\s*\n?",
            "",
            chunk.page_content,
            flags=re.IGNORECASE,
        ).strip()
        detected_language = detect_language(clean_content, fallback_language)
        languages = list(dict.fromkeys([*marked_languages, detected_language]))
        chunk.page_content = clean_content
        chunk.metadata.update({
            "chunk_id":   i,
            "chunk_size": len(clean_content),
            "word_count": len(clean_content.split()),
            "language":   detected_language,
            "languages":  ",".join(language for language in languages if language != "und"),
        })
    logger.info(f"   {source}: {len(chunks)} chunks")
    return chunks

def chunk_all(markdown_texts: dict, documents_config: list) -> list[Document]:
    all_chunks = []
    config_map = {d["source"]: d for d in documents_config}
    for source, md_text in markdown_texts.items():
        doc_cfg = config_map.get(source, {})
        metadata = {
            "source":       source,
            "full_name":    doc_cfg.get("full_name", source),
            "jurisdiction": doc_cfg.get("jurisdiction", "Unknown"),
            "domain":       doc_cfg.get("domain", "legal"),
            "year":         doc_cfg.get("year", 0),
            "language":     doc_cfg.get("language", "und"),
            "access_roles": ",".join(doc_cfg.get("access_roles", ["admin"])),
        }
        chunks = chunk_markdown(md_text, metadata, source)
        all_chunks.extend(chunks)
    logger.info(f"   Total: {len(all_chunks)} chunks")
    return all_chunks
