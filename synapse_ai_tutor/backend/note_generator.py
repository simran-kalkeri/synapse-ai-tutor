"""
AI Knowledge Note Generator for Synapse AI Tutor.
Generates structured markdown notes for each concept using LLM + RAG.
Falls back to curated template content when LLM is offline.
Notes are stored as downloadable markdown files.
"""

import os
import json
from datetime import datetime
from backend.llm_client import generate_response

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NOTES_DIR = os.path.join(DATA_DIR, "notes")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")


# ── Note Generation ───────────────────────────────────────────────────────────

def generate_knowledge_note(topic: str, level: str, rag_pipeline=None) -> str:
    """
    Generate a structured knowledge note for a topic.

    Uses LLM via Groq API with optional RAG context.
    Falls back to template-based content when LLM is offline.

    Args:
        topic: The concept/topic name
        level: Student level (Beginner/Intermediate/Advanced)
        rag_pipeline: Optional RAG pipeline for context retrieval

    Returns:
        Markdown string with the full note content
    """
    # Try RAG retrieval for context
    context_text = ""
    if rag_pipeline and rag_pipeline.is_ready:
        try:
            chunks = rag_pipeline.search(f"explain {topic} definition examples", k=3)
            for chunk in chunks:
                context_text += f"\n{chunk['text'][:400]}\n"
        except Exception:
            pass

    system_prompt = f"""You are Synapse, an expert AI tutor creating a comprehensive knowledge note.

Student Level: {level}

{"Reference Material:" + context_text if context_text else ""}

Generate a structured knowledge note about the topic. Use this EXACT markdown structure:

# {topic}

## Definition
A clear, {level.lower()}-appropriate definition (2-3 sentences).

## Why It Matters
Explain why this concept is important in AI/ML (2-3 bullet points).

## Example
A concrete, practical example that demonstrates the concept.
Include a code snippet if relevant (Python preferred).

## Common Mistakes
List 3 common mistakes or misconceptions students have about this topic.

## Connected Concepts
List 4-5 related concepts with brief explanations of how they connect:
- **Concept Name** → How it relates

## Resources
List 3 recommended resources (books, papers, tutorials) for learning more.

## Summary
A concise 2-3 sentence summary wrapping up the key takeaways.

Make the content thorough, accurate, and adapted to {level} level.
Use clear formatting with markdown."""

    response = generate_response(
        prompt=f"Create a knowledge note about: {topic}",
        system_prompt=system_prompt,
        temperature=0.6,
        max_tokens=2500
    )

    # Check if LLM failed — use fallback template
    if response.startswith("__LLM_"):
        return get_note_template(topic, level)

    # Validate response has expected structure
    if f"# {topic}" not in response and "## Definition" not in response:
        # LLM returned something but not well-structured, prepend title
        response = f"# {topic}\n\n{response}"

    return response


def get_note_template(topic: str, level: str = "Beginner") -> str:
    """
    Return a pre-written template note for a topic.
    Used as fallback when LLM is offline.
    """
    templates = {
        "Embeddings": f"""# Embeddings

## Definition
Embeddings are dense vector representations of discrete objects (words, sentences, images) in a continuous vector space. They capture semantic meaning, allowing similar items to be positioned near each other in the vector space.

## Why It Matters
- **Foundation of modern NLP**: Every language model relies on embeddings to understand text
- **Enable similarity search**: Finding related content becomes a simple distance calculation
- **Bridge discrete and continuous**: Allow neural networks to process categorical data efficiently

## Example
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Convert text to embeddings
sentences = ["I love machine learning", "AI is fascinating"]
embeddings = model.encode(sentences)

# Each embedding is a 384-dimensional vector
print(embeddings.shape)  # (2, 384)
```

## Common Mistakes
1. **Confusing embeddings with one-hot encoding** — Embeddings are dense and learned; one-hot vectors are sparse and fixed
2. **Using the wrong embedding model** — Domain-specific tasks may need fine-tuned embedding models
3. **Ignoring dimensionality** — Higher dimensions capture more info but cost more compute

## Connected Concepts
- **Vector Databases** → Store and search embeddings efficiently at scale
- **Semantic Search** → Use embedding similarity to find relevant documents
- **Transformers** → Generate contextual embeddings that change based on surrounding text
- **RAG** → Uses embeddings to retrieve relevant knowledge for language models
- **Tokenization** → Text must be tokenized before being converted to embeddings

## Resources
- *Hands-On Large Language Models* — Chapter on Embeddings
- [Word2Vec Paper](https://arxiv.org/abs/1301.3781) — Original word embedding technique
- [Sentence-Transformers Documentation](https://www.sbert.net/) — Practical embedding library

## Summary
Embeddings transform discrete data into continuous vectors that capture semantic meaning. They are the foundation of similarity search, retrieval systems, and modern language models. Understanding embeddings is essential for working with any NLP or generative AI system.""",

        "Vector Databases": f"""# Vector Databases

## Definition
Vector databases are specialized database systems designed to store, index, and efficiently search high-dimensional vector embeddings. They enable fast similarity search across millions of vectors using algorithms like HNSW, IVF, and LSH.

## Why It Matters
- **Power RAG systems**: Retrieve relevant documents from massive knowledge bases in milliseconds
- **Scale AI applications**: Handle millions of embeddings that traditional databases can't efficiently search
- **Enable semantic search**: Find content by meaning, not just keyword matching

## Example
```python
import faiss
import numpy as np

# Create a FAISS index for 384-dimensional vectors
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Add vectors to the index
vectors = np.random.random((1000, dimension)).astype('float32')
index.add(vectors)

# Search for the 5 nearest neighbors
query = np.random.random((1, dimension)).astype('float32')
distances, indices = index.search(query, k=5)
print(f"Nearest neighbors: {{indices}}")
```

## Common Mistakes
1. **Choosing the wrong index type** — Flat indexes are exact but slow; approximate indexes trade accuracy for speed
2. **Not normalizing vectors** — Cosine similarity requires normalized vectors for correct results
3. **Ignoring index parameters** — Tuning nprobe, efSearch, etc. dramatically affects performance

## Connected Concepts
- **Embeddings** → The vectors that get stored in the database
- **Similarity Search** → The core operation vector databases optimize
- **RAG** → Uses vector databases to retrieve relevant context for LLMs
- **FAISS** → Facebook's library for efficient similarity search
- **Semantic Search** → Application of vector databases for meaning-based search

## Resources
- FAISS documentation and tutorials
- Pinecone, Weaviate, ChromaDB documentation
- *Hands-On Large Language Models* — Chapter on Vector Stores

## Summary
Vector databases are essential infrastructure for modern AI applications. They store embeddings and provide fast similarity search, enabling RAG systems, recommendation engines, and semantic search at scale.""",

        "Self-Attention": f"""# Self-Attention

## Definition
Self-attention is a mechanism that allows each element in a sequence to attend to (compute relevance scores with) every other element, including itself. It computes Query, Key, and Value vectors from the input to determine how much focus each position should place on other positions.

## Why It Matters
- **Enables parallel processing**: Unlike RNNs, self-attention processes all positions simultaneously
- **Captures long-range dependencies**: Any two positions can directly interact regardless of distance
- **Foundation of Transformers**: The core mechanism powering GPT, BERT, and all modern LLMs

## Example
```python
import torch
import torch.nn.functional as F

# Simplified self-attention
def self_attention(X, d_k):
    Q = X @ W_q  # Queries
    K = X @ W_k  # Keys
    V = X @ W_v  # Values

    # Scaled dot-product attention
    scores = (Q @ K.T) / (d_k ** 0.5)
    weights = F.softmax(scores, dim=-1)
    output = weights @ V
    return output
```

## Common Mistakes
1. **Forgetting the scaling factor** — Without dividing by √d_k, softmax saturates and gradients vanish
2. **Confusing self-attention with cross-attention** — Self-attention uses the same sequence for Q, K, V
3. **Ignoring computational cost** — Self-attention is O(n²) in sequence length

## Connected Concepts
- **Multi-Head Attention** → Running multiple self-attention in parallel for richer representations
- **Positional Encoding** → Adding position info since self-attention is permutation-invariant
- **Transformers** → Architecture built on self-attention layers
- **Query/Key/Value** → The three projections that enable attention computation
- **Attention Scores** → The weights determining how much each position attends to others

## Resources
- "Attention Is All You Need" (Vaswani et al., 2017)
- *Understanding Deep Learning* — Chapter on Attention
- Jay Alammar's "The Illustrated Transformer"

## Summary
Self-attention computes pairwise interactions between all positions in a sequence using Query-Key-Value projections. It enables parallel processing and long-range dependency capture, making it the foundation of the Transformer architecture that powers modern AI.""",

        "Neural Networks": f"""# Neural Networks

## Definition
Neural networks are computational models inspired by the human brain, consisting of interconnected layers of artificial neurons (nodes). Each neuron applies a weighted sum followed by a non-linear activation function, enabling the network to learn complex patterns from data.

## Why It Matters
- **Universal approximators**: Can theoretically learn any continuous function given enough capacity
- **Foundation of deep learning**: All modern AI architectures build upon neural network principles
- **Versatile**: Applied across vision, language, robotics, science, and beyond

## Example
```python
import torch.nn as nn

class SimpleNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = self.relu(self.layer1(x))
        return self.layer2(x)

model = SimpleNN(784, 128, 10)  # MNIST classifier
```

## Common Mistakes
1. **Poor weight initialization** — Using zeros or very large values prevents effective learning
2. **Ignoring overfitting** — Not using regularization (dropout, weight decay) on small datasets
3. **Wrong learning rate** — Too high causes divergence, too low causes extremely slow training

## Connected Concepts
- **Backpropagation** → Algorithm for computing gradients through the network
- **Activation Functions** → Non-linearities (ReLU, sigmoid, tanh) that enable complex learning
- **Loss Functions** → Measure prediction error to guide optimization
- **Gradient Descent** → Optimization algorithm that updates weights
- **Deep Learning** → Neural networks with many layers

## Resources
- *Understanding Deep Learning* by Simon J.D. Prince
- 3Blue1Brown's "Neural Networks" video series
- PyTorch official tutorials

## Summary
Neural networks are layered computational models that learn complex patterns through weighted connections and non-linear activations. They are the foundation of all deep learning and modern AI, trained via backpropagation and gradient descent.""",
    }

    # Return specific template if available
    if topic in templates:
        return templates[topic]

    # Generate a generic template for unknown topics
    return f"""# {topic}

## Definition
{topic} is a concept in the field of Generative AI and Machine Learning. It plays an important role in modern AI systems and applications.

## Why It Matters
- Core concept in understanding modern AI architectures
- Builds upon foundational machine learning principles
- Essential for practical AI development and research

## Example
Understanding {topic} requires hands-on practice with real implementations. Start by studying the theoretical foundations, then implement simple examples in Python.

## Common Mistakes
1. Rushing to advanced applications without understanding the fundamentals
2. Not connecting {topic} to its prerequisite concepts
3. Memorizing formulas without understanding intuition

## Connected Concepts
- Related to foundational AI and ML concepts
- Connects to modern generative AI architectures
- Builds upon mathematical and computational foundations

## Resources
- Relevant textbooks on AI and Machine Learning
- Online courses (Coursera, edX, fast.ai)
- Research papers on arXiv

## Summary
{topic} is an important concept in the AI/ML landscape. Building a strong understanding requires both theoretical study and practical implementation. Use the connected concepts above to build a comprehensive mental model."""


# ── Note Persistence (Markdown Files) ─────────────────────────────────────────

def save_note(username: str, topic: str, note_content: str) -> str:
    """
    Save a generated note as a markdown file.

    Args:
        username: Student username
        topic: Topic name
        note_content: Markdown content

    Returns:
        Absolute path to the saved file
    """
    user_dir = os.path.join(NOTES_DIR, _sanitize_filename(username))
    os.makedirs(user_dir, exist_ok=True)

    filename = f"{_sanitize_filename(topic)}.md"
    filepath = os.path.join(user_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(note_content)

    # Also update progress.json with metadata
    _update_note_metadata(username, topic, filepath)

    return filepath


def load_note(username: str, topic: str) -> str:
    """
    Load a saved note from markdown file.

    Returns:
        Markdown content string, or empty string if not found
    """
    user_dir = os.path.join(NOTES_DIR, _sanitize_filename(username))
    filename = f"{_sanitize_filename(topic)}.md"
    filepath = os.path.join(user_dir, filename)

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def get_note_filepath(username: str, topic: str) -> str:
    """Get the file path for a note (may not exist yet)."""
    user_dir = os.path.join(NOTES_DIR, _sanitize_filename(username))
    filename = f"{_sanitize_filename(topic)}.md"
    return os.path.join(user_dir, filename)


def get_all_notes(username: str) -> list:
    """
    Get all saved notes for a user.

    Returns:
        List of dicts: [{"topic": str, "filepath": str, "created_at": str, "content": str}]
    """
    user_dir = os.path.join(NOTES_DIR, _sanitize_filename(username))
    notes = []

    if not os.path.isdir(user_dir):
        return notes

    for filename in os.listdir(user_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(user_dir, filename)
            topic = filename.replace('.md', '').replace('_', ' ').title()

            # Try to get proper topic name from metadata
            metadata = _get_note_metadata(username)
            for t, meta in metadata.items():
                if _sanitize_filename(t) == filename.replace('.md', ''):
                    topic = t
                    break

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            created_at = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()

            notes.append({
                "topic": topic,
                "filepath": filepath,
                "created_at": created_at,
                "content": content,
                "summary": _extract_summary(content)
            })

    return sorted(notes, key=lambda x: x["created_at"], reverse=True)


def note_exists(username: str, topic: str) -> bool:
    """Check if a note already exists for this user/topic."""
    filepath = get_note_filepath(username, topic)
    return os.path.exists(filepath)


def delete_note(username: str, topic: str) -> bool:
    """Delete a note file."""
    filepath = get_note_filepath(username, topic)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """Convert a topic/username to a safe filename."""
    return name.lower().replace(' ', '_').replace('/', '_').replace('&', 'and').replace('(', '').replace(')', '')


def _extract_summary(content: str) -> str:
    """Extract the summary section from a note, or first ~100 chars."""
    if "## Summary" in content:
        parts = content.split("## Summary")
        if len(parts) > 1:
            summary = parts[1].strip()
            # Take first paragraph
            lines = [l.strip() for l in summary.split('\n') if l.strip()]
            if lines:
                return lines[0][:200]
    # Fallback: first meaningful line after title
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
    return lines[0][:200] if lines else "No summary available."


def _update_note_metadata(username: str, topic: str, filepath: str):
    """Update note metadata in progress.json."""
    data = _load_progress()
    if username not in data:
        data[username] = {}

    if "_notes_metadata" not in data[username]:
        data[username]["_notes_metadata"] = {}

    data[username]["_notes_metadata"][topic] = {
        "filepath": filepath,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    _save_progress(data)


def _get_note_metadata(username: str) -> dict:
    """Get note metadata from progress.json."""
    data = _load_progress()
    return data.get(username, {}).get("_notes_metadata", {})


def _load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_progress(data: dict):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
