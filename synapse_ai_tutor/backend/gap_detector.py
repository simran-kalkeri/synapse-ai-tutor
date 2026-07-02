"""
Knowledge Gap Detection module for Synapse AI Tutor.
Identifies prerequisite concepts for each topic and
detects gaps based on student's mastery scores.
"""

# Prerequisite maps for each topic
PREREQUISITE_MAP = {
    "Neural Networks": {
        "prerequisites": [
            "Linear Algebra",
            "Calculus (Derivatives & Chain Rule)",
            "Probability & Statistics",
            "Python Programming",
            "Optimization (Gradient Descent)"
        ],
        "related_topics": ["CNNs", "RNNs"],
        "key_concepts": [
            "Perceptrons",
            "Activation Functions",
            "Backpropagation",
            "Loss Functions",
            "Weight Initialization"
        ]
    },
    "CNNs": {
        "prerequisites": [
            "Neural Networks",
            "Linear Algebra",
            "Image Processing Basics",
            "Feature Extraction",
            "Optimization"
        ],
        "related_topics": ["Neural Networks"],
        "key_concepts": [
            "Convolution Operations",
            "Pooling Layers",
            "Feature Maps",
            "Stride and Padding",
            "Transfer Learning"
        ]
    },
    "RNNs": {
        "prerequisites": [
            "Neural Networks",
            "Sequence Modeling",
            "Backpropagation Through Time",
            "Linear Algebra",
            "Optimization"
        ],
        "related_topics": ["Neural Networks", "Transformers"],
        "key_concepts": [
            "Hidden States",
            "LSTM Gates",
            "GRU Architecture",
            "Vanishing Gradients",
            "Sequence-to-Sequence"
        ]
    },
    "Transformers": {
        "prerequisites": [
            "Vectors & Embeddings",
            "Sequence Modeling",
            "Attention Mechanisms",
            "Neural Networks",
            "Matrix Multiplication"
        ],
        "related_topics": ["RNNs", "LLMs"],
        "key_concepts": [
            "Self-Attention",
            "Multi-Head Attention",
            "Positional Encoding",
            "Encoder-Decoder Architecture",
            "Layer Normalization"
        ]
    },
    "LLMs": {
        "prerequisites": [
            "Transformers",
            "Attention Mechanisms",
            "Tokenization",
            "Neural Networks",
            "Probability Distributions"
        ],
        "related_topics": ["Transformers", "Fine-Tuning and RAG"],
        "key_concepts": [
            "Pre-training",
            "Context Windows",
            "Token Prediction",
            "Scaling Laws",
            "Emergent Abilities"
        ]
    },
    "Prompt Engineering": {
        "prerequisites": [
            "LLMs",
            "Natural Language Understanding",
            "Tokenization",
            "Context Windows",
            "API Usage"
        ],
        "related_topics": ["LLMs", "Generative AI Fundamentals"],
        "key_concepts": [
            "System Prompts",
            "Few-Shot Learning",
            "Chain-of-Thought",
            "Prompt Templates",
            "Output Formatting"
        ]
    },
    "Generative AI Fundamentals": {
        "prerequisites": [
            "Neural Networks",
            "Probability & Statistics",
            "Deep Learning Basics",
            "Python Programming",
            "Loss Functions"
        ],
        "related_topics": ["GANs", "Diffusion Models", "LLMs"],
        "key_concepts": [
            "Generative vs Discriminative",
            "Latent Space",
            "Sampling Methods",
            "Evaluation Metrics",
            "Ethical Considerations"
        ]
    },
    "GANs": {
        "prerequisites": [
            "Neural Networks",
            "Optimization",
            "Loss Functions",
            "Probability Distributions",
            "Backpropagation"
        ],
        "related_topics": ["Neural Networks", "Generative AI Fundamentals"],
        "key_concepts": [
            "Generator Network",
            "Discriminator Network",
            "Adversarial Training",
            "Mode Collapse",
            "Wasserstein Distance"
        ]
    },
    "Diffusion Models": {
        "prerequisites": [
            "Probability & Statistics",
            "Noise Processes",
            "Generative Modeling",
            "Neural Networks",
            "Optimization"
        ],
        "related_topics": ["GANs", "Generative AI Fundamentals"],
        "key_concepts": [
            "Forward Diffusion",
            "Reverse Process",
            "Denoising",
            "Score Matching",
            "Latent Diffusion"
        ]
    },
    "Fine-Tuning and RAG": {
        "prerequisites": [
            "Embeddings",
            "Vector Databases",
            "LLMs",
            "Transfer Learning",
            "Data Preprocessing"
        ],
        "related_topics": ["LLMs", "Transformers"],
        "key_concepts": [
            "LoRA / QLoRA",
            "Retrieval Pipeline",
            "Chunk Strategies",
            "Embedding Models",
            "Context Augmentation"
        ]
    }
}


def get_prerequisites(topic: str) -> list:
    """
    Get prerequisite concepts for a given topic.
    
    Args:
        topic: The topic name
        
    Returns:
        List of prerequisite concept strings
    """
    topic_data = PREREQUISITE_MAP.get(topic, {})
    return topic_data.get("prerequisites", [])


def get_key_concepts(topic: str) -> list:
    """
    Get key concepts for a given topic.
    
    Args:
        topic: The topic name
        
    Returns:
        List of key concept strings
    """
    topic_data = PREREQUISITE_MAP.get(topic, {})
    return topic_data.get("key_concepts", [])


def get_related_topics(topic: str) -> list:
    """
    Get related topics that share prerequisites.
    
    Args:
        topic: The topic name
        
    Returns:
        List of related topic strings
    """
    topic_data = PREREQUISITE_MAP.get(topic, {})
    return topic_data.get("related_topics", [])


def detect_knowledge_gaps(topic: str, mastery_scores: dict) -> dict:
    """
    Detect knowledge gaps based on the student's mastery scores
    and the topic's prerequisites.
    
    Args:
        topic: The selected topic
        mastery_scores: Dictionary of {topic: {"mastery": score, "level": level}}
        
    Returns:
        Dictionary with gaps, strengths, and recommendations
    """
    prerequisites = get_prerequisites(topic)
    related = get_related_topics(topic)
    key_concepts = get_key_concepts(topic)
    
    gaps = []
    strengths = []
    weak_related = []
    
    # Check related topics mastery
    for rel_topic in related:
        if rel_topic in mastery_scores:
            score = mastery_scores[rel_topic].get("mastery", 0)
            if score < 50:
                weak_related.append(rel_topic)
                # Add prerequisites of the weak related topic as gaps
                rel_prereqs = get_prerequisites(rel_topic)
                for prereq in rel_prereqs[:2]:  # Top 2 prerequisites
                    if prereq not in gaps:
                        gaps.append(prereq)
            elif score >= 75:
                strengths.append(rel_topic)
        else:
            # Not assessed yet — potential gap
            weak_related.append(rel_topic)
    
    # If the student hasn't taken the current topic's assessment
    # or scored low, flag prerequisite concepts as gaps
    current_score = mastery_scores.get(topic, {}).get("mastery", 0)
    
    if current_score < 50:
        # Add prerequisite concepts as potential gaps
        for prereq in prerequisites:
            if prereq not in gaps:
                gaps.append(prereq)
    elif current_score < 75:
        # Add some prerequisites as mild gaps
        for prereq in prerequisites[:3]:
            if prereq not in gaps:
                gaps.append(prereq)
    
    # Determine overall gap severity
    if len(gaps) >= 4:
        severity = "high"
        recommendation = f"Consider reviewing foundational concepts before diving deep into {topic}."
    elif len(gaps) >= 2:
        severity = "medium"
        recommendation = f"You have some gaps in prerequisites for {topic}. Focus on strengthening these areas."
    else:
        severity = "low"
        recommendation = f"You're well-prepared for {topic}! Keep building on your strengths."
    
    return {
        "topic": topic,
        "gaps": gaps,
        "strengths": strengths,
        "weak_related_topics": weak_related,
        "key_concepts": key_concepts,
        "severity": severity,
        "recommendation": recommendation
    }
