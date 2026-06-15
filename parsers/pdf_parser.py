"""
PDF text extraction using pdfplumber.
Extracts raw text from uploaded PDF resume files.
"""

import pdfplumber


def extract_text_from_pdf(file_path):
    """
    Extract all text content from a PDF file.
    Returns concatenated text from all pages.
    """
    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts).strip()
