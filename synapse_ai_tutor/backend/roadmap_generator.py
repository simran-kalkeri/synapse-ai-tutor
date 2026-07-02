"""
Learning Roadmap Generator for Synapse AI Tutor.
Generates personalized learning paths based on topic, level, and knowledge gaps.
Uses the prerequisite graph from gap_detector.py.
"""

import json
import os
from datetime import datetime
from backend.gap_detector import PREREQUISITE_MAP, get_prerequisites, get_key_concepts

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "progress.json")


# ── Roadmap Generation ────────────────────────────────────────────────────────

def generate_roadmap(topic: str, level: str, gaps: list) -> list:
    """
    Generate a personalized learning roadmap for a topic.

    The roadmap orders prerequisites first, then gap-filling concepts,
    then the main topic, then advanced extensions.

    Args:
        topic: The selected topic (e.g., "Fine-Tuning and RAG")
        level: Student level ("Beginner", "Intermediate", "Advanced")
        gaps: List of detected knowledge gap strings

    Returns:
        List of roadmap step dicts:
        [
            {
                "name": str,
                "description": str,
                "status": "locked" | "current" | "complete",
                "order": int,
                "is_current": bool,
                "step_type": "prerequisite" | "gap" | "core" | "advanced"
            }
        ]
    """
    topic_data = PREREQUISITE_MAP.get(topic, {})
    prerequisites = topic_data.get("prerequisites", [])
    key_concepts = topic_data.get("key_concepts", [])
    related = topic_data.get("related_topics", [])

    roadmap = []
    seen = set()
    order = 0

    # Phase 1: Prerequisites (for Beginner/Intermediate)
    if level in ("Beginner", "Intermediate"):
        prereqs_to_add = prerequisites[:5] if level == "Beginner" else prerequisites[:3]
        for prereq in prereqs_to_add:
            if prereq not in seen:
                seen.add(prereq)
                roadmap.append({
                    "name": prereq,
                    "description": _get_step_description(prereq, "prerequisite"),
                    "status": "locked",
                    "order": order,
                    "is_current": False,
                    "step_type": "prerequisite"
                })
                order += 1

    # Phase 2: Knowledge gaps that aren't already in prerequisites
    for gap in gaps:
        if gap not in seen:
            seen.add(gap)
            roadmap.append({
                "name": gap,
                "description": _get_step_description(gap, "gap"),
                "status": "locked",
                "order": order,
                "is_current": False,
                "step_type": "gap"
            })
            order += 1

    # Phase 3: Key concepts of the topic itself
    if level == "Beginner":
        concepts_to_add = key_concepts[:3]
    elif level == "Intermediate":
        concepts_to_add = key_concepts[:4]
    else:
        concepts_to_add = key_concepts[:2]

    for concept in concepts_to_add:
        if concept not in seen:
            seen.add(concept)
            roadmap.append({
                "name": concept,
                "description": _get_step_description(concept, "core"),
                "status": "locked",
                "order": order,
                "is_current": False,
                "step_type": "core"
            })
            order += 1

    # Phase 4: The main topic itself
    if topic not in seen:
        seen.add(topic)
        roadmap.append({
            "name": topic,
            "description": _get_step_description(topic, "core"),
            "status": "locked",
            "order": order,
            "is_current": False,
            "step_type": "core"
        })
        order += 1

    # Phase 5: Advanced / related topics (for Intermediate/Advanced)
    if level in ("Intermediate", "Advanced"):
        for rel in related[:2]:
            if rel not in seen:
                seen.add(rel)
                roadmap.append({
                    "name": rel,
                    "description": _get_step_description(rel, "advanced"),
                    "status": "locked",
                    "order": order,
                    "is_current": False,
                    "step_type": "advanced"
                })
                order += 1

    # Mark the first step as current
    if roadmap:
        roadmap[0]["status"] = "current"
        roadmap[0]["is_current"] = True

    return roadmap


def _get_step_description(concept: str, step_type: str) -> str:
    """Generate a brief description for a roadmap step."""
    descriptions = {
        # Prerequisites
        "Linear Algebra": "Vectors, matrices, and operations fundamental to neural networks",
        "Calculus (Derivatives & Chain Rule)": "Derivatives and chain rule used in backpropagation",
        "Probability & Statistics": "Probability distributions, Bayes theorem, and statistical inference",
        "Python Programming": "Core Python skills for implementing ML models",
        "Optimization (Gradient Descent)": "Gradient-based optimization methods for training models",
        "Vectors & Embeddings": "Numerical representations of data in high-dimensional space",
        "Sequence Modeling": "Techniques for processing sequential and temporal data",
        "Attention Mechanisms": "Selective focus mechanisms in neural networks",
        "Matrix Multiplication": "Core linear algebra operation used in transformers",
        "Image Processing Basics": "Fundamental image manipulation and representation",
        "Feature Extraction": "Identifying and extracting meaningful patterns from data",
        "Backpropagation Through Time": "Training algorithm for recurrent neural networks",
        "Natural Language Understanding": "Comprehending and interpreting human language",
        "Tokenization": "Breaking text into tokens for model processing",
        "Context Windows": "Managing input length limits in language models",
        "API Usage": "Working with model APIs and endpoints",
        "Deep Learning Basics": "Foundations of deep neural network architectures",
        "Loss Functions": "Measuring prediction errors to guide model training",
        "Noise Processes": "Understanding noise in probabilistic models",
        "Generative Modeling": "Creating models that generate new data samples",
        "Optimization": "Methods for finding optimal model parameters",
        "Embeddings": "Dense vector representations of discrete entities",
        "Vector Databases": "Specialized databases for similarity search on embeddings",
        "Transfer Learning": "Reusing pre-trained models for new tasks",
        "Data Preprocessing": "Cleaning and preparing data for model training",
        "Probability Distributions": "Mathematical functions describing likelihoods",

        # Key concepts
        "Perceptrons": "The simplest neural network unit — a linear classifier",
        "Activation Functions": "Non-linear functions that enable complex pattern learning",
        "Backpropagation": "Algorithm for computing gradients through the network",
        "Weight Initialization": "Strategies for setting initial model parameters",
        "Convolution Operations": "Sliding window operations for feature detection",
        "Pooling Layers": "Downsampling operations to reduce spatial dimensions",
        "Feature Maps": "Output of convolutional filters representing detected features",
        "Stride and Padding": "Parameters controlling convolution output size",
        "Hidden States": "Internal memory representations in recurrent networks",
        "LSTM Gates": "Gating mechanisms in Long Short-Term Memory networks",
        "GRU Architecture": "Simplified gated recurrent unit design",
        "Vanishing Gradients": "The problem of gradients becoming too small during training",
        "Self-Attention": "Mechanism for relating different positions in a sequence",
        "Multi-Head Attention": "Parallel attention mechanisms for richer representations",
        "Positional Encoding": "Adding position information to transformer inputs",
        "Encoder-Decoder Architecture": "Two-part architecture for sequence-to-sequence tasks",
        "Layer Normalization": "Normalizing activations within a layer",
        "Pre-training": "Training on large datasets before task-specific fine-tuning",
        "Token Prediction": "Predicting the next token in a sequence",
        "Scaling Laws": "Relationships between model size, data, and performance",
        "Emergent Abilities": "Capabilities that appear at large model scales",
        "System Prompts": "Instructions that define model behavior and persona",
        "Few-Shot Learning": "Learning from very few examples provided in context",
        "Chain-of-Thought": "Step-by-step reasoning in language model outputs",
        "Prompt Templates": "Structured formats for constructing effective prompts",
        "Output Formatting": "Controlling the structure and format of model outputs",
        "Generative vs Discriminative": "Two fundamental approaches to modeling",
        "Latent Space": "Compressed representation space learned by models",
        "Sampling Methods": "Techniques for generating diverse outputs",
        "Evaluation Metrics": "Measuring the quality of generated content",
        "Ethical Considerations": "Responsible AI development and deployment",
        "Generator Network": "The network that creates synthetic data in GANs",
        "Discriminator Network": "The network that evaluates authenticity in GANs",
        "Adversarial Training": "Training two networks against each other",
        "Mode Collapse": "When a GAN generates limited variety of outputs",
        "Wasserstein Distance": "A metric for measuring distribution similarity",
        "Forward Diffusion": "Gradually adding noise to data",
        "Reverse Process": "Gradually removing noise to generate data",
        "Denoising": "Removing noise to recover clean data",
        "Score Matching": "Learning the gradient of data distribution",
        "Latent Diffusion": "Diffusion in a compressed latent space",
        "LoRA / QLoRA": "Parameter-efficient fine-tuning methods",
        "Retrieval Pipeline": "End-to-end system for finding relevant documents",
        "Chunk Strategies": "Methods for splitting documents into retrievable pieces",
        "Embedding Models": "Models that convert text to vector representations",
        "Context Augmentation": "Enriching model input with retrieved information",
        "Sequence-to-Sequence": "Models that map input sequences to output sequences",

        # Topics
        "Neural Networks": "Core building blocks of deep learning — layers, weights, and training",
        "CNNs": "Convolutional Neural Networks for image and spatial data processing",
        "RNNs": "Recurrent Neural Networks for sequential and temporal data",
        "Transformers": "Attention-based architecture powering modern AI models",
        "LLMs": "Large Language Models — GPT, BERT, and language understanding",
        "Prompt Engineering": "Techniques for effective communication with AI models",
        "Generative AI Fundamentals": "Core concepts of AI systems that create new content",
        "GANs": "Generative Adversarial Networks — generator vs discriminator training",
        "Diffusion Models": "Noise-based generative models — Stable Diffusion, DALL-E",
        "Fine-Tuning and RAG": "Adapting models and augmenting with external knowledge",
    }

    default_descriptions = {
        "prerequisite": f"Foundational concept needed before advancing further",
        "gap": f"Knowledge gap identified — strengthen this area",
        "core": f"Core concept in the learning path",
        "advanced": f"Advanced topic for deeper exploration",
    }

    return descriptions.get(concept, default_descriptions.get(step_type, f"Study {concept}"))


# ── Roadmap Persistence ───────────────────────────────────────────────────────

def save_roadmap(username: str, topic: str, roadmap: list):
    """Save a user's roadmap to progress.json."""
    data = _load_progress()
    if username not in data:
        data[username] = {}
    if topic not in data[username]:
        data[username][topic] = {}
    data[username][topic]["roadmap"] = roadmap
    data[username][topic]["roadmap_generated_at"] = datetime.now().isoformat()
    _save_progress(data)


def load_roadmap(username: str, topic: str) -> list:
    """Load a user's roadmap from progress.json."""
    data = _load_progress()
    user_data = data.get(username, {})
    topic_data = user_data.get(topic, {})
    return topic_data.get("roadmap", [])


def update_roadmap_step(username: str, topic: str, step_name: str, new_status: str):
    """
    Update the status of a roadmap step.
    Also advances 'current' marker to the next locked step.
    """
    data = _load_progress()
    roadmap = data.get(username, {}).get(topic, {}).get("roadmap", [])

    if not roadmap:
        return

    for step in roadmap:
        if step["name"] == step_name:
            step["status"] = new_status
            step["is_current"] = False

    # Find next locked step and mark as current
    if new_status == "complete":
        for step in roadmap:
            if step["status"] == "locked":
                step["status"] = "current"
                step["is_current"] = True
                break

    data[username][topic]["roadmap"] = roadmap
    _save_progress(data)


def get_roadmap_progress(username: str, topic: str) -> dict:
    """Get roadmap completion statistics."""
    roadmap = load_roadmap(username, topic)
    if not roadmap:
        return {"total": 0, "complete": 0, "current": 0, "locked": 0, "percentage": 0}

    complete = sum(1 for s in roadmap if s["status"] == "complete")
    current = sum(1 for s in roadmap if s["status"] == "current")
    locked = sum(1 for s in roadmap if s["status"] == "locked")

    return {
        "total": len(roadmap),
        "complete": complete,
        "current": current,
        "locked": locked,
        "percentage": int((complete / len(roadmap)) * 100) if roadmap else 0
    }


# ── Internal Helpers ──────────────────────────────────────────────────────────

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
