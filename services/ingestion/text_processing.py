"""Language detection and cleanup for extracted legal document text."""

import re
from langdetect import DetectorFactory, detect_langs, LangDetectException

DetectorFactory.seed = 0


def detect_language(text: str, fallback: str = "und") -> str:
    """Return an ISO 639-1 language code for a sufficiently long text sample."""
    text = re.sub(r"<!--\s*language:\s*[a-z]{2,3}\s*-->", " ", text, flags=re.IGNORECASE)
    sample = re.sub(r"[#*`|<>]", " ", text).strip()
    if len(sample) < 50:
        return fallback
    try:
        candidates = detect_langs(sample)
    except LangDetectException:
        return fallback
    if not candidates or candidates[0].prob < 0.60:
        return fallback
    return candidates[0].lang


def annotate_markdown_languages(text: str) -> str:
    """Add language markers at language transitions without removing content."""
    text = re.sub(
        r"(?m)^<!--\s*language:\s*[a-z]{2,3}\s*-->\s*\n?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    blocks = re.split(r"(\n\s*\n)", text)
    current_language = None
    output = []
    for block in blocks:
        if not block or re.fullmatch(r"\n\s*\n", block):
            output.append(block)
            continue

        detected = detect_language(block)
        if detected != "und" and detected != current_language:
            output.append(f"<!-- language: {detected} -->\n")
            current_language = detected
        output.append(block)
    return "".join(output)


def process_document_text(text: str, document: dict) -> str:
    """Clean page extraction noise without dropping or translating languages."""
    official_journal_cleanup = document.get("page_layout") == "official_journal"

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()

        # Remove only known page furniture for documents with this layout.
        if official_journal_cleanup and (
            stripped == "Official Journal of the European Communities"
            or stripped == "18.12.2000"
            or re.fullmatch(r"C\s*364/\d+", stripped)
            or re.fullmatch(r"<mark>\s*[A-Z]{2}\s*</mark>", stripped, re.IGNORECASE)
        ):
            continue

        # Repair common OCR artifacts around list markers without altering text.
        line = re.sub(r"^(\s*[-*])\s*[�•·]\s*", r"\1 ", line)
        cleaned_lines.append(line.rstrip())

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Give every legal article a consistent heading, including those extracted
    # as plain text rather than Markdown headings.
    text = re.sub(
        r"(?m)^\s*(?:#+\s*)?Article\s+(\d+[a-z]?)\s*$",
        r"## Article \1",
        text,
        flags=re.IGNORECASE,
    )
    text = text.strip()
    return annotate_markdown_languages(text)
