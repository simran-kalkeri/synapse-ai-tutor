"""
Retrieval Pipeline for Synapse AI Tutor.
Combines embedding generation and FAISS search for
retrieving relevant content from the knowledge corpus.
"""

from backend.embeddings import embed_query


def retrieve(query: str, index, chunks: list, k: int = 5) -> list:
    """
    Retrieve the most relevant chunks for a given query.
    
    Args:
        query: The search query text
        index: FAISS index
        chunks: List of chunk dictionaries
        k: Number of results to return
        
    Returns:
        List of relevant chunk dictionaries with text, source, and page
    """
    if index is None or not chunks:
        return []
    
    # Generate query embedding
    query_embedding = embed_query(query)
    
    # Search FAISS index
    scores, indices = index.search(query_embedding, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks) and idx >= 0:
            chunk = chunks[idx].copy()
            chunk["relevance_score"] = float(scores[0][i])
            results.append(chunk)
    
    return results


def retrieve_for_topic(topic: str, student_question: str, index, chunks: list, k: int = 5) -> list:
    """
    Retrieve content relevant to both the topic and student's specific question.
    
    Args:
        topic: The selected topic
        student_question: The student's question
        index: FAISS index
        chunks: List of chunk dictionaries
        k: Number of results to return
        
    Returns:
        List of relevant chunk dictionaries
    """
    # Combine topic and question for better retrieval
    combined_query = f"{topic}: {student_question}"
    return retrieve(combined_query, index, chunks, k)
