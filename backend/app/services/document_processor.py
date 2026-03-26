import io
import tempfile

import pdfplumber
from docx import Document


def extract_text(file_bytes: bytes, file_type: str) -> str:
    if file_type == "pdf":
        return _extract_pdf(file_bytes)
    elif file_type == "docx":
        return _extract_docx(file_bytes)
    elif file_type == "txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_bytes: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _extract_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
