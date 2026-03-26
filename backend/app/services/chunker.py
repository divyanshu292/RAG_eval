from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def chunk_text(text: str, source_filename: str = "") -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
    )
    splits = splitter.split_text(text)
    chunks = []
    for i, chunk_text in enumerate(splits):
        chunks.append(
            {
                "text": chunk_text,
                "chunk_index": i,
                "metadata": {
                    "page_number": None,
                    "source_filename": source_filename,
                },
            }
        )
    return chunks
