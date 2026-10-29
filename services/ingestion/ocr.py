# LegalMind AI — PDF to Markdown Converter
# Uses pymupdf native extraction + targeted per-page OCR fallback
# for pages whose PDF font mapping is broken (e.g. the year-2000 EU Charter).

import os
import re
from pathlib import Path

from loguru import logger
import pymupdf
import pytesseract
from pdf2image import convert_from_path

from services.ingestion.text_processing import process_document_text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_RAW  = Path("data/raw")
DATA_PROC = Path("data/processed")

# Tesseract paths (loaded from .env)
if os.getenv("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
if os.getenv("TESSDATA_PREFIX"):
    os.environ["TESSDATA_PREFIX"] = os.getenv("TESSDATA_PREFIX")

# Signature of the broken French font in the EU Charter PDF:
#   européen  → europØen
#   ci-après  → ci-aprŁs
# We only OCR pages that contain these markers, not the whole document.
BROKEN_LANG_SIGNATURE = re.compile(r"[ØŁ]")

# Languages passed to Tesseract for the fallback pages
OCR_LANGUAGES = "fra+eng+deu+spa+ita+nld+por+dan+swe+fin+ell"


# ---------------------------------------------------------------------------
# Page-level helpers
# ---------------------------------------------------------------------------
def _page_needs_ocr(text: str) -> bool:
    """Return True if the page shows the broken-French-font signature."""
    return bool(BROKEN_LANG_SIGNATURE.search(text))


def _ocr_single_page(pdf_path: Path, page_index: int) -> str:
    """
    OCR a single page (0-indexed) of a PDF.
    Used only for pages whose text layer has a broken font mapping.
    """
    try:
        images = convert_from_path(
            str(pdf_path),
            dpi=300,
            first_page=page_index + 1,
            last_page=page_index + 1,
        )
        if not images:
            return ""
        return pytesseract.image_to_string(images[0], lang=OCR_LANGUAGES)
    except Exception as e:
        logger.warning(f"   ⚠️ OCR failed on page {page_index + 1} of {pdf_path.name}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------
def _pymupdf_to_markdown(pdf_path: Path) -> str:
    """
    Extract text page by page with pymupdf.
    For any page whose font mapping is broken, run Tesseract on that page only.
    """
    doc = pymupdf.open(str(pdf_path))
    pages_out = []

    for i, page in enumerate(doc):
        text = page.get_text("text")

        if _page_needs_ocr(text):
            logger.info(f"   Page {i + 1}: broken font detected → OCR")
            text = _ocr_single_page(pdf_path, i)

        if text.strip():
            pages_out.append(f"<!-- page: {i + 1} -->\n\n{text.strip()}")

    doc.close()
    return "\n\n".join(pages_out)


def _clean_markdown(text: str) -> str:
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"Ar\s+ticle", "Article", text)
    text = re.sub(r"\n#+\s*(Article\s+\d+)", r"\n\n## \1", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def pdf_to_markdown(pdf_path: Path, out_path: Path, document: dict | None = None) -> str:
    logger.info(f"   Converting {pdf_path.name} → markdown...")

    md_text = _pymupdf_to_markdown(pdf_path)
    md_text = _clean_markdown(md_text)
    md_text = process_document_text(md_text, document or {})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_text, encoding="utf-8")
    logger.info(f"   ✅ Saved: {out_path.name} ({len(md_text) // 1024} KB)")
    return md_text


def convert_all_pdfs(documents: list) -> dict:
    results = {}
    for doc in documents:
        pdf_path = DATA_RAW / doc["file"]
        if not pdf_path.exists():
            logger.warning(f"   ⚠️  Skipping {doc['file']} — not found")
            continue

        out_path = DATA_PROC / doc["file"].replace(".pdf", ".md")

        if out_path.exists():
            logger.info(f"   ♻️  Using cached: {out_path.name}")
            md_text = out_path.read_text(encoding="utf-8")
            md_text = process_document_text(md_text, doc)
            out_path.write_text(md_text, encoding="utf-8")
            results[doc["source"]] = md_text
            continue

        md_text = pdf_to_markdown(pdf_path, out_path, doc)
        results[doc["source"]] = md_text

    return results