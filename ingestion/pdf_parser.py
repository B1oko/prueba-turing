import logging
import re

import fitz
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_RULE_START_RE = re.compile(
    r"^("
    r"\d{3}\.\d+[a-z]?\.?"  # e.g. 100.1, 100.1a
    r"|"
    r"\d{3}\."  # e.g. 100. (section title)
    r"|"
    r"\d\."  # e.g. 1. (chapter title)
    r")\s+(.*)$"
)


def parse_mtg_rules_pdf(pdf_path: str) -> list[Document]:
    logger.info("Opening PDF file: '%s'", pdf_path)
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logger.info("PDF opened successfully. Total pages: %d", total_pages)

    documents = []
    current_rule_id = "Intro"
    current_rule_text_lines: list[str] = []
    current_rule_start_page = 0

    for page_num in range(total_pages):
        if (page_num + 1) % 100 == 0 or page_num == 0 or page_num == total_pages - 1:
            logger.info("Parsing page %d/%d...", page_num + 1, total_pages)
        lines = doc[page_num].get_text("text").split("\n")

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            match = _RULE_START_RE.match(line_stripped)
            if match:
                if current_rule_text_lines:
                    documents.append(
                        Document(
                            page_content="\n".join(current_rule_text_lines),
                            metadata={
                                "rule_id": current_rule_id,
                                "page": current_rule_start_page + 1,
                                "source": pdf_path,
                            },
                        )
                    )
                current_rule_id = match.group(1).rstrip(".")
                current_rule_text_lines = [line_stripped]
                current_rule_start_page = page_num
            else:
                if current_rule_text_lines:
                    current_rule_text_lines.append(line_stripped)
                else:
                    current_rule_text_lines = [line_stripped]
                    current_rule_start_page = page_num

    if current_rule_text_lines:
        documents.append(
            Document(
                page_content="\n".join(current_rule_text_lines),
                metadata={
                    "rule_id": current_rule_id,
                    "page": current_rule_start_page + 1,
                    "source": pdf_path,
                },
            )
        )

    logger.info("Parsing complete. Extracted %d rule documents.", len(documents))
    return documents
