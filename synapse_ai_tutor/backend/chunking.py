"""
PDF Processing and Chunking module for Synapse AI Tutor.
Uses PyMuPDF to extract text from PDF textbooks and creates
overlapping chunks for embedding generation.
"""

import os
import pickle
import fitz  # PyMuPDF


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
    """
    chunks = []
    
    for page_data in pages:
        text = page_data["text"]
        source = page_data["source"]
        page = page_data["page"]
        
        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "source": source,
                "page": page
            })
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
                    chunks.append({
                        "text": chunk_text.strip(),
                        "source": source,
                        "page": page
                    })
                
                start = end - chunk_overlap
                if start < 0:
                    start = 0
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
    
    print(f"[INFO] Found {len(pdf_files)} PDF books to process")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(books_dir, pdf_file)
        print(f"  [PROC] Processing: {pdf_file}...")
        
        pages = extract_text_from_pdf(pdf_path)
        chunks = create_chunks(pages)
        all_chunks.extend(chunks)
        
        print(f"    [OK] Extracted {len(pages)} pages -> {len(chunks)} chunks")
    
    print(f"\n[DONE] Total chunks created: {len(all_chunks)}")
    return all_chunks


def save_chunks(chunks: list, filepath: str = None):
    """Save chunks to a pickle file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chunks.pkl")
    
    with open(filepath, 'wb') as f:
        pickle.dump(chunks, f)
    print(f"[SAVE] Chunks saved to {filepath}")


def load_chunks(filepath: str = None) -> list:
    """Load chunks from a pickle file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chunks.pkl")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'rb') as f:
        chunks = pickle.load(f)
    print(f"[LOAD] Loaded {len(chunks)} chunks from cache")
    return chunks
