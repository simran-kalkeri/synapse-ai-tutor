"""
PDF Processing and Chunking module for Synapse AI Tutor.
Uses PyMuPDF to extract text from PDF textbooks and creates
overlapping chunks for embedding generation.
"""

import json
import os
import fitz  # PyMuPDF

from config.logging_config import get_logger

logger = get_logger(__name__)



def extract_text_from_pdf(pdf_path: str) -> list:
    """
    Extract text from a PDF file using PyMuPDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries with text, source, and page number
    """
    doc = fitz.open(pdf_path)
    source_name = os.path.basename(pdf_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        if text.strip():
            pages.append({
                "text": text.strip(),
                "source": source_name,
                "page": page_num + 1  # 1-indexed
            })
    
    doc.close()
    return pages


def create_chunks(pages: list, chunk_size: int = 800, chunk_overlap: int = 150) -> list:
    """
    Create overlapping text chunks from extracted pages.

    Args:
        pages: List of page dictionaries from extract_text_from_pdf
        chunk_size: Maximum characters per chunk
        chunk_overlap: Number of overlapping characters between chunks

    Returns:
        List of chunk dictionaries with text, source, and page

    Raises:
        ValueError: If chunk_overlap >= chunk_size (infinite loop risk).
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
        )

    chunks = []

    for page_data in pages:
        text = page_data["text"]
        source = page_data["source"]
        page = page_data["page"]

        if len(text) <= chunk_size:
            chunks.append({"text": text, "source": source, "page": page})
        else:
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]

                # Try to break at a sentence boundary
                if end < len(text):
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    break_point = max(last_period, last_newline)
                    if break_point > chunk_size * 0.5:
                        chunk_text = chunk_text[:break_point + 1]
                        end = start + break_point + 1

                if chunk_text.strip():
                    chunks.append({"text": chunk_text.strip(), "source": source, "page": page})

                advance = end - chunk_overlap
                if advance <= start:
                    advance = start + 1  # Always advance at least one char (safety guard)
                start = advance

                if end >= len(text):
                    break

    return chunks



def process_all_books(books_dir: str = None) -> list:
    """
    Process all PDF books in the books directory.

    Args:
        books_dir: Path to the directory containing PDF books

    Returns:
        List of all chunks from all books
    """
    if books_dir is None:
        books_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "books")

    all_chunks = []
    pdf_files = [f for f in os.listdir(books_dir) if f.endswith('.pdf')]

    logger.info("books_found", count=len(pdf_files), books_dir=books_dir)

    for pdf_file in pdf_files:
        pdf_path = os.path.join(books_dir, pdf_file)
        logger.info("book_processing", filename=pdf_file)

        pages = extract_text_from_pdf(pdf_path)
        chunks = create_chunks(pages)
        all_chunks.extend(chunks)

        logger.info("book_processed", filename=pdf_file, pages=len(pages), chunks=len(chunks))

    logger.info("books_complete", total_chunks=len(all_chunks))
    return all_chunks


def save_chunks(chunks: list, filepath: str = None):
    """
    Save chunks to a JSON file (replaces old pickle format to prevent RCE).

    Args:
        chunks: List of chunk dicts.
        filepath: Destination path; defaults to ``data/chunks.json``.
    """
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "chunks.json"
        )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    logger.info("chunks_saved", filepath=filepath, count=len(chunks))


def load_chunks(filepath: str = None) -> list:
    """
    Load chunks from a JSON file.  Returns ``[]`` if the file does not exist.

    Legacy ``.pkl`` files are automatically migrated to JSON on first load.

    Args:
        filepath: Source path; defaults to ``data/chunks.json``.

    Returns:
        List of chunk dicts, or ``[]`` if the file is missing.
    """
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "chunks.json"
        )

    # Legacy migration: if JSON is missing but .pkl exists, migrate it once.
    if not os.path.exists(filepath):
        pkl_path = filepath.replace(".json", ".pkl")
        if os.path.exists(pkl_path):
            logger.warning(
                "chunks_pkl_migration",
                detail="Migrating chunks.pkl to chunks.json.",
            )
            try:
                import pickle  # noqa: PLC0415
                with open(pkl_path, "rb") as f:
                    chunks = pickle.load(f)
            except Exception:
                with open(pkl_path, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
            save_chunks(chunks, filepath)
            logger.info("chunks_migration_done", new_path=filepath)
            return chunks
        return []  # Fixed: was returning None, causing TypeError in callers

    with open(filepath, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    logger.info("chunks_loaded", filepath=filepath, count=len(chunks))
    return chunks
