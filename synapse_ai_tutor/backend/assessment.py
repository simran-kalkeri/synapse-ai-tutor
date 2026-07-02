"""
Assessment Engine for Synapse AI Tutor.
Redesigned to support 15-question assessments (5 Easy / 5 Intermediate / 5 Hard),
weighted scoring (1/2/3 pts), and multi-topic independent scoring.
"""

import json
import random
import os

# Topic keywords for categorization
TOPIC_KEYWORDS = {
    "Neural Networks": [
        "neural network", "perceptron", "activation function", "backpropagation",
        "feedforward", "deep learning", "hidden layer", "weight", "bias",
        "gradient descent", "neuron", "multilayer", "deep neural", "ann",
        "artificial neural", "network architecture", "fully connected"
    ],
    "CNNs": [
        "cnn", "convolutional", "convolution", "pooling", "feature map",
        "kernel", "filter", "stride", "padding", "image classification",
        "object detection", "resnet", "vgg", "alexnet", "image recognition",
        "spatial", "feature extraction"
    ],
    "RNNs": [
        "rnn", "recurrent", "lstm", "gru", "sequence model", "time series",
        "hidden state", "vanishing gradient", "bidirectional", "seq2seq",
        "sequence to sequence", "temporal", "sequential data", "memory cell"
    ],
    "Transformers": [
        "transformer", "attention mechanism", "self-attention", "multi-head attention",
        "positional encoding", "encoder-decoder", "bert", "attention is all you need",
        "scaled dot-product", "cross-attention", "attention score", "query key value"
    ],
    "LLMs": [
        "large language model", "llm", "gpt", "language model", "token",
        "tokenization", "context window", "inference", "pre-training",
        "foundation model", "scaling law", "emergent", "few-shot",
        "zero-shot", "chain of thought", "reasoning"
    ],
    "Prompt Engineering": [
        "prompt engineering", "prompt", "few-shot prompt", "chain of thought",
        "system prompt", "prompt template", "instruction tuning",
        "prompt design", "in-context learning", "prompt optimization",
        "zero-shot", "prompt injection", "jailbreak"
    ],
    "Generative AI Fundamentals": [
        "generative ai", "generative model", "generation", "creative ai",
        "text generation", "image generation", "content generation",
        "synthetic data", "generative", "ai generated", "artificial intelligence",
        "responsible ai", "ai ethics", "ai safety", "agentic ai", "agent"
    ],
    "GANs": [
        "gan", "generative adversarial", "discriminator", "generator",
        "adversarial training", "mode collapse", "wasserstein", "stylegan",
        "dcgan", "conditional gan", "image synthesis", "adversarial network",
        "fake image", "deepfake"
    ],
    "Diffusion Models": [
        "diffusion model", "denoising", "noise schedule", "stable diffusion",
        "ddpm", "score matching", "latent diffusion", "diffusion process",
        "reverse process", "dall-e", "midjourney", "image diffusion",
        "noise prediction", "sampling", "probability", "stochastic"
    ],
    "Fine-Tuning and RAG": [
        "fine-tuning", "fine tuning", "rag", "retrieval augmented",
        "lora", "qlora", "adapter", "transfer learning", "domain adaptation",
        "retrieval", "vector database", "embedding", "knowledge base",
        "context retrieval", "document retrieval", "chunking"
    ]
}

# Difficulty weights: Easy=1, Intermediate=2, Hard=3
DIFFICULTY_WEIGHTS = {"easy": 1, "intermediate": 2, "hard": 3}

# Per-topic max score: 5*1 + 5*2 + 5*3 = 30
MAX_SCORE_PER_TOPIC = 30

# Level thresholds (raw score out of 30)
def get_level_from_raw(score: int) -> str:
    if score <= 12:
        return "Beginner"
    elif score <= 22:
        return "Intermediate"
    else:
        return "Advanced"


def load_dataset(filepath: str = None) -> list:
    """Load the JSONL dataset from file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "manus-dataset.jsonl")

    questions = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return questions


def categorize_questions(questions: list) -> dict:
    """
    Categorize questions into topics based on keyword matching.
    Returns {topic: [question_dicts]}
    """
    topic_banks = {topic: [] for topic in TOPIC_KEYWORDS}

    for q in questions:
        instruction = q.get("instruction", "").lower()
        response = q.get("response", "").lower()
        combined = instruction + " " + response

        best_topic = None
        best_score = 0

        for topic, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in combined)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic and best_score > 0:
            topic_banks[best_topic].append(q)

    return topic_banks


def assign_difficulty(q: dict, idx: int, total: int) -> str:
    """
    Heuristically assign difficulty based on question position and content length.
    First third = easy, middle = intermediate, last third = hard.
    """
    response_len = len(q.get("response", ""))
    instruction_len = len(q.get("instruction", ""))

    # Short questions with short answers = easy
    # Long complex instructions with long responses = hard
    combined_len = instruction_len + response_len
    if combined_len < 300:
        return "easy"
    elif combined_len < 700:
        return "intermediate"
    else:
        return "hard"


def generate_mcq_from_question(question: dict, topic: str, difficulty: str = "intermediate") -> dict:
    """
    Generate a multiple choice question from a dataset entry.
    """
    instruction = question.get("instruction", "")
    response = question.get("response", "")

    sentences = [s.strip() for s in response.split('.') if len(s.strip()) > 20]
    if not sentences:
        sentences = [response[:200]]

    correct_answer = sentences[0].strip() + "."

    distractors = [
        f"This concept is not relevant to {topic} and has no practical applications.",
        f"It is a deprecated approach that has been replaced by newer methodologies.",
        f"This only applies to supervised learning and cannot be used in other contexts.",
        f"It requires quantum computing resources and is not feasible with current hardware.",
        f"This technique was proven incorrect in recent peer-reviewed research.",
        f"It is exclusively used in computer vision and has no NLP applications.",
    ]

    random.shuffle(distractors)
    selected_distractors = distractors[:3]

    options = selected_distractors + [correct_answer]
    random.shuffle(options)

    correct_index = options.index(correct_answer)

    return {
        "question": instruction,
        "options": options,
        "correct_index": correct_index,
        "correct_answer": correct_answer,
        "topic": topic,
        "difficulty": difficulty,
        "points": DIFFICULTY_WEIGHTS[difficulty]
    }


def select_assessment_questions(topic_banks: dict, topic: str) -> list:
    """
    Select 15 questions for a topic assessment:
    5 Easy + 5 Intermediate + 5 Hard.
    Each difficulty tier is drawn from the dataset (or fallback).
    Returns a flat list of 15 MCQ dicts in order: easy, intermediate, hard.
    """
    available = topic_banks.get(topic, [])

    if len(available) == 0:
        return _generate_fallback_questions(topic)

    # Sort by difficulty heuristic
    easy_pool = []
    inter_pool = []
    hard_pool = []

    for i, q in enumerate(available):
        diff = assign_difficulty(q, i, len(available))
        if diff == "easy":
            easy_pool.append(q)
        elif diff == "intermediate":
            inter_pool.append(q)
        else:
            hard_pool.append(q)

    # Ensure we have enough — pull from others if needed
    all_pool = list(available)
    random.shuffle(all_pool)

    def fill_pool(pool, needed):
        while len(pool) < needed:
            pool.append(all_pool[len(pool) % len(all_pool)])
        return pool

    easy_pool = fill_pool(easy_pool, 5)
    inter_pool = fill_pool(inter_pool, 5)
    hard_pool = fill_pool(hard_pool, 5)

    selected_easy = random.sample(easy_pool, 5)
    selected_inter = random.sample(inter_pool, 5)
    selected_hard = random.sample(hard_pool, 5)

    mcqs = []
    for q in selected_easy:
        mcqs.append(generate_mcq_from_question(q, topic, "easy"))
    for q in selected_inter:
        mcqs.append(generate_mcq_from_question(q, topic, "intermediate"))
    for q in selected_hard:
        mcqs.append(generate_mcq_from_question(q, topic, "hard"))

    return mcqs  # Length = 15


def _generate_fallback_questions(topic: str) -> list:
    """Generate 15 fallback questions (5 easy, 5 intermediate, 5 hard)."""
    def make_q(q_text, correct, distractors, difficulty):
        options = distractors[:3] + [correct]
        random.shuffle(options)
        return {
            "question": q_text,
            "options": options,
            "correct_index": options.index(correct),
            "correct_answer": correct,
            "topic": topic,
            "difficulty": difficulty,
            "points": DIFFICULTY_WEIGHTS[difficulty]
        }

    easy = [
        make_q(f"What is {topic}?",
               f"{topic} is a foundational concept in modern AI and machine learning.",
               ["A database management tool.", "A type of network protocol.", "An operating system component."],
               "easy"),
        make_q(f"Which domain does {topic} primarily belong to?",
               "Artificial Intelligence and Machine Learning.",
               ["Embedded systems.", "Network engineering.", "Mechanical engineering."],
               "easy"),
        make_q(f"What is the main output of {topic}?",
               "Learned representations or predictions based on training data.",
               ["Raw bytes of data.", "Compiled binary code.", "Network packets."],
               "easy"),
        make_q(f"Is {topic} supervised or unsupervised by default?",
               "It depends on the specific variant and application context.",
               ["Always unsupervised.", "Always supervised.", "It requires reinforcement only."],
               "easy"),
        make_q(f"What type of data does {topic} typically work with?",
               "Structured or unstructured data depending on the architecture.",
               ["Only images.", "Only audio signals.", "Only tabular CSV data."],
               "easy"),
    ]

    inter = [
        make_q(f"What is a key challenge when training {topic} models?",
               "Balancing model complexity with generalization to avoid overfitting.",
               ["Lack of electricity.", "Too many CPUs.", "Insufficient storage for source code."],
               "intermediate"),
        make_q(f"How does {topic} handle high-dimensional data?",
               "By learning compressed representations that capture essential features.",
               ["By ignoring irrelevant dimensions entirely.", "By converting everything to 1D.", "By using lookup tables."],
               "intermediate"),
        make_q(f"What evaluation metric is commonly used for {topic}?",
               "It varies by task — accuracy, F1, BLEU, or perplexity are common.",
               ["Only RMSE is valid.", "Only accuracy can be used.", "Metrics are not needed."],
               "intermediate"),
        make_q(f"What role does the loss function play in {topic}?",
               "It quantifies the error between predictions and ground truth, guiding optimization.",
               ["It stores model weights permanently.", "It manages GPU memory.", "It defines the UI layout."],
               "intermediate"),
        make_q(f"What is transfer learning in the context of {topic}?",
               "Reusing pre-trained model weights on a new related task to reduce training time.",
               ["Training from scratch every time.", "Transferring data between servers.", "Sharing models over the internet."],
               "intermediate"),
    ]

    hard = [
        make_q(f"What are the theoretical limitations of {topic}?",
               "Computational complexity, data requirements, and interpretability constraints.",
               ["It can only run on Windows.", "It requires quantum hardware.", "No limitations exist."],
               "hard"),
        make_q(f"How would you optimize {topic} for low-latency inference?",
               "Through quantization, pruning, distillation, and efficient serving infrastructure.",
               ["By adding more layers.", "By using larger batch sizes only.", "By switching to a different programming language."],
               "hard"),
        make_q(f"What is the relationship between {topic} and attention mechanisms?",
               "Attention allows selective focus on relevant input parts, critical in modern architectures.",
               ["They are completely unrelated.", "Attention replaces all other components.", "Attention is only used in image models."],
               "hard"),
        make_q(f"How does {topic} scale with dataset size?",
               "Performance generally improves with more data but follows diminishing returns and requires careful regularization.",
               ["More data always hurts performance.", "Dataset size has no effect.", "It only works with small datasets."],
               "hard"),
        make_q(f"What recent research directions extend {topic}?",
               "Sparse architectures, mixture-of-experts, efficient attention, and multimodal extensions.",
               ["Going back to rule-based systems.", "Removing all non-linearity.", "Using only linear regression."],
               "hard"),
    ]

    return easy + inter + hard


def calculate_score(answers: list, questions: list) -> dict:
    """
    Calculate weighted assessment score for 15-question format.

    Points: Easy=1, Intermediate=2, Hard=3
    Max score = 30

    Returns:
        dict with score (raw), max_score, level, correct, total,
              percentage, per_difficulty breakdown
    """
    if not questions:
        return {
            "score": 0, "max_score": MAX_SCORE_PER_TOPIC,
            "level": "Beginner", "correct": 0, "total": 0,
            "percentage": 0, "per_difficulty": {}
        }

    score = 0
    correct = 0
    total = len(questions)

    per_difficulty = {"easy": {"correct": 0, "total": 0}, "intermediate": {"correct": 0, "total": 0}, "hard": {"correct": 0, "total": 0}}

    for i, q in enumerate(questions):
        diff = q.get("difficulty", "intermediate")
        pts = q.get("points", DIFFICULTY_WEIGHTS.get(diff, 1))
        per_difficulty.setdefault(diff, {"correct": 0, "total": 0})
        per_difficulty[diff]["total"] += 1

        if i < len(answers) and answers[i] is not None and answers[i] == q["correct_index"]:
            score += pts
            correct += 1
            per_difficulty[diff]["correct"] += 1

    max_score = MAX_SCORE_PER_TOPIC
    level = get_level_from_raw(score)
    percentage = int((score / max_score) * 100)

    return {
        "score": score,
        "max_score": max_score,
        "level": level,
        "correct": correct,
        "total": total,
        "percentage": percentage,
        "per_difficulty": per_difficulty
    }


def get_level(score_percent: int) -> str:
    """Legacy helper: level from 0-100 percentage."""
    if score_percent <= 40:
        return "Beginner"
    elif score_percent <= 75:
        return "Intermediate"
    else:
        return "Advanced"
