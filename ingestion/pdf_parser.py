import re
import fitz
from typing import List
from langchain_core.documents import Document


def parse_mtg_rules_pdf(pdf_path: str) -> List[Document]:
    """
    Parses the MTG Comprehensive Rules PDF and returns a list of Document objects.
    Each document corresponds to a single rule or section header with metadata (rule_id, page, source).
    """
    doc = fitz.open(pdf_path)
    documents = []

    # Regex to detect start of a rule/section
    # Matches patterns like "100.1", "100.1a", "100.", "1."
    rule_start_regex = re.compile(
        r"^("
        r"\d{3}\.\d+[a-z]?\.?"  # e.g., 100.1, 100.1a, 100.1.
        r"|"
        r"\d{3}\."  # e.g., 100. (Section title)
        r"|"
        r"\d\."  # e.g., 1. (Chapter title)
        r")\s+(.*)$"
    )

    current_rule_id = "Intro"
    current_rule_text_lines = []
    current_rule_start_page = 0

    for page_num in range(len(doc)):
        page_text = doc[page_num].get_text("text")
        lines = page_text.split("\n")

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Check if this line starts a new rule
            match = rule_start_regex.match(line_stripped)
            if match:
                # Save the completed rule before starting the new one
                if current_rule_text_lines:
                    full_text = "\n".join(current_rule_text_lines)
                    documents.append(
                        Document(
                            page_content=full_text,
                            metadata={
                                "rule_id": current_rule_id,
                                "page": current_rule_start_page + 1,  # 1-indexed page
                                "source": pdf_path,
                            },
                        )
                    )

                # Start new rule
                current_rule_id = match.group(1).rstrip(".")
                current_rule_text_lines = [line_stripped]
                current_rule_start_page = page_num
            else:
                # Append to current rule
                if current_rule_text_lines:
                    current_rule_text_lines.append(line_stripped)
                else:
                    current_rule_text_lines = [line_stripped]
                    current_rule_start_page = page_num

    # Save the last rule
    if current_rule_text_lines:
        full_text = "\n".join(current_rule_text_lines)
        documents.append(
            Document(
                page_content=full_text,
                metadata={
                    "rule_id": current_rule_id,
                    "page": current_rule_start_page + 1,
                    "source": pdf_path,
                },
            )
        )

    return documents
