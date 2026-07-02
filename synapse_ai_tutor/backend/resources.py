"""
Resource Recommendation module for Synapse AI Tutor.
Provides curated learning resources (videos, articles, documentation)
for each topic.
"""

RESOURCE_MAP = {
    "Neural Networks": {
        "videos": [
            {
                "title": "3Blue1Brown — Neural Networks Series",
                "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
                "description": "Beautiful visual explanations of neural networks from the ground up."
            },
            {
                "title": "Andrej Karpathy — Building Neural Nets from Scratch",
                "url": "https://www.youtube.com/watch?v=VMj-3S1tku0",
                "description": "Hands-on coding of neural networks with backpropagation."
            }
        ],
        "articles": [
            {
                "title": "A Visual & Interactive Guide to Neural Networks",
                "url": "https://jalammar.github.io/visual-interactive-guide-basics-neural-networks/",
                "description": "Interactive visualizations of how neural networks learn."
            },
            {
                "title": "Neural Networks and Deep Learning (Michael Nielsen)",
                "url": "http://neuralnetworksanddeeplearning.com/",
                "description": "Free online book covering the fundamentals."
            }
        ],
        "documentation": [
            {
                "title": "PyTorch Tutorials — Neural Networks",
                "url": "https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html",
                "description": "Official PyTorch tutorial on building neural networks."
            }
        ]
    },
    "CNNs": {
        "videos": [
            {
                "title": "Stanford CS231n — CNNs for Visual Recognition",
                "url": "https://www.youtube.com/playlist?list=PL3FW7Lu3i5JvHM8ljYj-zLfQRF3EO8sYv",
                "description": "Comprehensive lecture series on convolutional neural networks."
            }
        ],
        "articles": [
            {
                "title": "A Comprehensive Guide to CNNs",
                "url": "https://towardsdatascience.com/a-comprehensive-guide-to-convolutional-neural-networks-the-eli5-way-3bd2b1164a53",
                "description": "Beginner-friendly guide explaining CNN architecture."
            },
            {
                "title": "CS231n Course Notes — ConvNets",
                "url": "https://cs231n.github.io/convolutional-networks/",
                "description": "Detailed technical notes on CNN architectures."
            }
        ],
        "documentation": [
            {
                "title": "TensorFlow CNN Tutorial",
                "url": "https://www.tensorflow.org/tutorials/images/cnn",
                "description": "Step-by-step guide to building a CNN with TensorFlow."
            }
        ]
    },
    "RNNs": {
        "videos": [
            {
                "title": "MIT 6.S191 — Recurrent Neural Networks",
                "url": "https://www.youtube.com/watch?v=SEnXr6v2ifU",
                "description": "MIT lecture on sequence modeling with RNNs."
            }
        ],
        "articles": [
            {
                "title": "Understanding LSTM Networks (Chris Olah)",
                "url": "https://colah.github.io/posts/2015-08-Understanding-LSTMs/",
                "description": "Classic visual explanation of LSTM architecture."
            },
            {
                "title": "The Unreasonable Effectiveness of RNNs (Karpathy)",
                "url": "https://karpathy.github.io/2015/05/21/rnn-effectiveness/",
                "description": "Explores what RNNs can do with fascinating examples."
            }
        ],
        "documentation": [
            {
                "title": "PyTorch RNN Tutorial",
                "url": "https://pytorch.org/tutorials/intermediate/char_rnn_classification_tutorial.html",
                "description": "Character-level RNN classification with PyTorch."
            }
        ]
    },
    "Transformers": {
        "videos": [
            {
                "title": "Andrej Karpathy — Let's Build GPT from Scratch",
                "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY",
                "description": "Build a GPT model from scratch, explaining transformer architecture."
            },
            {
                "title": "3Blue1Brown — Attention in Transformers",
                "url": "https://www.youtube.com/watch?v=eMlx5fFNoYc",
                "description": "Visual explanation of the attention mechanism."
            }
        ],
        "articles": [
            {
                "title": "The Illustrated Transformer (Jay Alammar)",
                "url": "https://jalammar.github.io/illustrated-transformer/",
                "description": "Definitive visual guide to transformer architecture."
            },
            {
                "title": "Attention Is All You Need (Original Paper)",
                "url": "https://arxiv.org/abs/1706.03762",
                "description": "The landmark paper that introduced the transformer."
            }
        ],
        "documentation": [
            {
                "title": "HuggingFace Transformers Documentation",
                "url": "https://huggingface.co/docs/transformers",
                "description": "Comprehensive documentation for the Transformers library."
            }
        ]
    },
    "LLMs": {
        "videos": [
            {
                "title": "Andrej Karpathy — Intro to LLMs",
                "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g",
                "description": "1-hour overview of large language models."
            },
            {
                "title": "Stanford CS324 — Large Language Models",
                "url": "https://stanford-cs324.github.io/winter2022/",
                "description": "Stanford course on understanding and using LLMs."
            }
        ],
        "articles": [
            {
                "title": "A Survey of Large Language Models",
                "url": "https://arxiv.org/abs/2303.18223",
                "description": "Comprehensive survey paper on LLM landscape."
            }
        ],
        "documentation": [
            {
                "title": "HuggingFace LLM Documentation",
                "url": "https://huggingface.co/docs/transformers/llm_tutorial",
                "description": "Guide to using LLMs with the Transformers library."
            }
        ]
    },
    "Prompt Engineering": {
        "videos": [
            {
                "title": "DeepLearning.AI — ChatGPT Prompt Engineering",
                "url": "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/",
                "description": "Free course by Andrew Ng on prompt engineering."
            }
        ],
        "articles": [
            {
                "title": "Prompt Engineering Guide",
                "url": "https://www.promptingguide.ai/",
                "description": "Comprehensive guide to prompt engineering techniques."
            },
            {
                "title": "OpenAI Prompt Engineering Best Practices",
                "url": "https://platform.openai.com/docs/guides/prompt-engineering",
                "description": "Official OpenAI guide to writing effective prompts."
            }
        ],
        "documentation": [
            {
                "title": "LangChain Prompt Templates",
                "url": "https://python.langchain.com/docs/concepts/prompt_templates/",
                "description": "Building reusable prompt templates with LangChain."
            }
        ]
    },
    "Generative AI Fundamentals": {
        "videos": [
            {
                "title": "Google — Generative AI Learning Path",
                "url": "https://www.cloudskillsboost.google/paths/118",
                "description": "Google's comprehensive generative AI learning path."
            }
        ],
        "articles": [
            {
                "title": "What Is Generative AI? (NVIDIA)",
                "url": "https://www.nvidia.com/en-us/glossary/generative-ai/",
                "description": "Clear overview of generative AI concepts."
            },
            {
                "title": "Generative Models (OpenAI Blog)",
                "url": "https://openai.com/index/generative-models/",
                "description": "OpenAI's blog post on generative modeling."
            }
        ],
        "documentation": [
            {
                "title": "HuggingFace Generative AI Docs",
                "url": "https://huggingface.co/docs/transformers/generation_strategies",
                "description": "Documentation on text generation strategies."
            }
        ]
    },
    "GANs": {
        "videos": [
            {
                "title": "MIT 6.S191 — Deep Generative Models",
                "url": "https://www.youtube.com/watch?v=3G5hWM6jqPk",
                "description": "MIT lecture covering GANs and other generative models."
            }
        ],
        "articles": [
            {
                "title": "A Gentle Introduction to GANs",
                "url": "https://machinelearningmastery.com/what-are-generative-adversarial-networks-gans/",
                "description": "Beginner-friendly explanation of GAN concepts."
            },
            {
                "title": "GAN Lab — Interactive Visualization",
                "url": "https://poloclub.github.io/ganlab/",
                "description": "Interactively visualize how GANs learn."
            }
        ],
        "documentation": [
            {
                "title": "PyTorch DCGAN Tutorial",
                "url": "https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html",
                "description": "Build a DCGAN to generate face images."
            }
        ]
    },
    "Diffusion Models": {
        "videos": [
            {
                "title": "What are Diffusion Models? (Ari Seff)",
                "url": "https://www.youtube.com/watch?v=fbLgFrlTnGU",
                "description": "Clear visual explanation of diffusion models."
            }
        ],
        "articles": [
            {
                "title": "The Illustrated Stable Diffusion (Jay Alammar)",
                "url": "https://jalammar.github.io/illustrated-stable-diffusion/",
                "description": "Visual guide to understanding stable diffusion."
            },
            {
                "title": "Understanding Diffusion Models: A Unified Perspective",
                "url": "https://arxiv.org/abs/2208.11970",
                "description": "Comprehensive mathematical treatment of diffusion models."
            }
        ],
        "documentation": [
            {
                "title": "HuggingFace Diffusers Documentation",
                "url": "https://huggingface.co/docs/diffusers",
                "description": "Library for working with diffusion models."
            }
        ]
    },
    "Fine-Tuning and RAG": {
        "videos": [
            {
                "title": "DeepLearning.AI — Fine-Tuning LLMs",
                "url": "https://www.deeplearning.ai/short-courses/finetuning-large-language-models/",
                "description": "Free course on fine-tuning large language models."
            },
            {
                "title": "RAG from Scratch (LangChain)",
                "url": "https://www.youtube.com/watch?v=sVcwVQRHIc8",
                "description": "Building RAG systems from scratch."
            }
        ],
        "articles": [
            {
                "title": "RAG — Retrieval Augmented Generation Explained",
                "url": "https://www.promptingguide.ai/techniques/rag",
                "description": "Clear explanation of RAG architecture and use cases."
            },
            {
                "title": "LoRA: Low-Rank Adaptation (Paper)",
                "url": "https://arxiv.org/abs/2106.09685",
                "description": "The paper introducing parameter-efficient fine-tuning."
            }
        ],
        "documentation": [
            {
                "title": "HuggingFace PEFT Documentation",
                "url": "https://huggingface.co/docs/peft",
                "description": "Parameter-efficient fine-tuning library."
            },
            {
                "title": "LangChain RAG Documentation",
                "url": "https://python.langchain.com/docs/tutorials/rag/",
                "description": "Building RAG applications with LangChain."
            }
        ]
    }
}


def get_resources(topic: str) -> dict:
    """
    Get learning resources for a specific topic.
    
    Args:
        topic: The topic name
        
    Returns:
        Dictionary with videos, articles, and documentation lists
    """
    return RESOURCE_MAP.get(topic, {
        "videos": [],
        "articles": [],
        "documentation": []
    })


def get_resources_for_level(topic: str, level: str) -> dict:
    """
    Get resources filtered/prioritized by student level.
    
    Args:
        topic: The topic name
        level: Student level (Beginner/Intermediate/Advanced)
        
    Returns:
        Dictionary with prioritized resources
    """
    resources = get_resources(topic)
    
    # Add level-specific recommendations
    if level == "Beginner":
        priority_note = "📌 Start with the videos for visual understanding, then read the articles."
    elif level == "Intermediate":
        priority_note = "📌 Dive into the articles and documentation, use videos for reinforcement."
    else:
        priority_note = "📌 Focus on documentation and research papers for advanced depth."
    
    return {
        **resources,
        "priority_note": priority_note,
        "level": level
    }
