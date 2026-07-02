"""
RAG (Retrieval-Augmented Generation) Pipeline for Synapse AI Tutor.
Orchestrates the full RAG pipeline: chunking, embedding, indexing, and retrieval.
Implements smart caching to avoid regenerating embeddings.

Extended with GraphRAG support: graph_rag_search() uses knowledge-graph
query expansion before FAISS retrieval.
"""

import os
from backend.chunking import process_all_books, save_chunks, load_chunks
from backend.embeddings import (
    generate_embeddings, build_faiss_index,
    save_faiss_index, load_faiss_index
)
from backend.retriever import retrieve, retrieve_for_topic


class RAGPipeline:
    """
    Complete RAG pipeline that manages the knowledge corpus,
    embeddings, FAISS index, and retrieval.

    Provides:
        search()            -- standard FAISS retrieval
        search_for_topic()  -- topic-anchored FAISS retrieval
        graph_rag_search()  -- GraphRAG (graph expansion + FAISS + reranking)
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            data_dir: Path to the data directory
        """
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        self.data_dir = data_dir
        self.books_dir = os.path.join(data_dir, "books")
        self.chunks_path = os.path.join(data_dir, "chunks.pkl")
        self.index_path = os.path.join(data_dir, "faiss_index.bin")
        
        self.chunks = None
        self.index = None
        self.is_ready = False
    
    def initialize(self) -> bool:
        """
        Initialize the RAG pipeline.
        Loads cached data if available, otherwise processes books from scratch.
        
        Returns:
            True if initialization was successful
        """
        # Check if cached data exists
        if os.path.exists(self.chunks_path) and os.path.exists(self.index_path):
            print("[CACHE] Found cached chunks and FAISS index - loading directly...")
            self.chunks = load_chunks(self.chunks_path)
            self.index = load_faiss_index(self.index_path)
            
            if self.chunks is not None and self.index is not None:
                self.is_ready = True
                print(f"[OK] RAG Pipeline ready! ({len(self.chunks)} chunks, {self.index.ntotal} vectors)")
                return True
        
        # Process books from scratch
        print("[BUILD] Building RAG pipeline from scratch...")
        return self._build_from_scratch()
    
    def _build_from_scratch(self) -> bool:
        """Build the complete pipeline from PDF books."""
        try:
            # Step 1: Process PDFs and create chunks
            print("\n[STEP 1/3] Processing PDF books...")
            self.chunks = process_all_books(self.books_dir)
            
            if not self.chunks:
                print("[ERROR] No chunks created from books!")
                return False
            
            # Save chunks
            save_chunks(self.chunks, self.chunks_path)
            
            # Step 2: Generate embeddings
            print("\n[STEP 2/3] Generating embeddings...")
            embeddings = generate_embeddings(self.chunks)
            
            # Step 3: Build FAISS index
            print("\n[STEP 3/3] Building FAISS index...")
            self.index = build_faiss_index(embeddings)
            
            # Save FAISS index
            save_faiss_index(self.index, self.index_path)
            
            self.is_ready = True
            print(f"\n[OK] RAG Pipeline built successfully!")
            print(f"   {len(self.chunks)} chunks | {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error building RAG pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, k: int = 5) -> list:
        """
        Search for relevant content.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of relevant chunk dictionaries
        """
        if not self.is_ready:
            return []
        return retrieve(query, self.index, self.chunks, k)
    
    def search_for_topic(self, topic: str, question: str, k: int = 5) -> list:
        """
        Search for content relevant to a topic and question.
        
        Args:
            topic: The selected topic
            question: The student's question
            k: Number of results
            
        Returns:
            List of relevant chunk dictionaries
        """
        if not self.is_ready:
            return []
        return retrieve_for_topic(topic, question, self.index, self.chunks, k)

    def graph_rag_search(self, question: str, topic: str, k: int = 6) -> dict:
        """
        Graph-augmented retrieval pipeline.

        Steps:
          1. Expand the query using the knowledge graph (concept neighbours).
          2. Run FAISS retrieval on the expanded query.
          3. Rerank results by concept overlap.

        Args:
            question: The student's raw question.
            topic:    Currently selected topic.
            k:        Number of final chunks to return.

        Returns:
            {
                "chunks":             list[dict],
                "expanded_query":     str,
                "matched_concepts":   list[str],
                "neighbour_concepts": list[str],
                "retrieval_method":   "GraphRAG",
                "graph_stats":        dict,
            }
        """
        if not self.is_ready:
            return {
                "chunks":             [],
                "expanded_query":     question,
                "matched_concepts":   [],
                "neighbour_concepts": [],
                "retrieval_method":   "GraphRAG (index not ready)",
                "graph_stats":        {},
            }

        from backend.graph_rag import graph_rag_retrieve
        return graph_rag_retrieve(
            question=question,
            topic=topic,
            index=self.index,
            chunks=self.chunks,
            k=k,
        )
    
    def get_status(self) -> dict:
        """Get the current status of the RAG pipeline."""
        return {
            "is_ready": self.is_ready,
            "num_chunks": len(self.chunks) if self.chunks else 0,
            "num_vectors": self.index.ntotal if self.index else 0,
            "chunks_cached": os.path.exists(self.chunks_path),
            "index_cached": os.path.exists(self.index_path)
        }
