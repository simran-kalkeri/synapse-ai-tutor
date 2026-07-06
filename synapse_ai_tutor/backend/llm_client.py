"""
LLM Client for Synapse AI Tutor.
Primary: Ollama (remote server at http://10.1.17.65:11434)
Fallback: Groq API (cloud, fast inference)
Enhanced with full adaptive prompting and graceful fallback mode.
"""

import os
import requests

# ── Configuration ────────────────────────────────────────────────────────────
# Groq (primary)
def _get_groq_key() -> str:
    """Get Groq API key from environment variable."""
    return os.getenv("GROQ_API_KEY", "")


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# LLM Router — auto-selects model based on query type
try:
    from ai.llm.router import get_model_for_query as _route_query  # type: ignore
    _ROUTER_AVAILABLE = True
except ImportError:
    _ROUTER_AVAILABLE = False
    _route_query = None  # type: ignore

# Ollama (fallback)
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").lower() in ("true", "1", "yes")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Timeouts
CONNECT_TIMEOUT = 5
GENERATE_TIMEOUT = 120


def get_ollama_base_url() -> str:
    """Get the Ollama base URL from environment variable."""
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def check_connection() -> bool:
    """Check if any LLM provider is reachable. Ollama first, then Groq."""
    # Try Ollama (primary)
    if OLLAMA_ENABLED:
        try:
            base_url = get_ollama_base_url()
            response = requests.get(f"{base_url}/api/tags", timeout=CONNECT_TIMEOUT)
            if response.status_code == 200:
                return True
        except Exception:
            pass

    # Try Groq (fallback)
    groq_key = _get_groq_key()
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            client.models.list()
            return True
        except Exception:
            pass

    return False


def get_available_models() -> list:
    """Get list of available models."""
    models = []
    # Ollama models (primary)
    if OLLAMA_ENABLED:
        try:
            base_url = get_ollama_base_url()
            response = requests.get(f"{base_url}/api/tags", timeout=CONNECT_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                models.extend([m["name"] for m in data.get("models", [])])
        except Exception:
            pass

    # Groq models (fallback)
    groq_key = _get_groq_key()
    if groq_key:
        models.append(GROQ_MODEL)

    return models


def _call_groq(prompt: str, system_prompt: str, temperature: float, max_tokens: int, model: str = None) -> str:
    """Call Groq API. Returns text or raises Exception."""
    from groq import Groq

    groq_key = _get_groq_key()
    if not groq_key:
        raise ConnectionError("Groq API key not configured")

    client = Groq(api_key=groq_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model or GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _call_ollama(prompt: str, system_prompt: str, temperature: float, max_tokens: int, model: str = None) -> str:
    """Call Ollama API. Returns text or raises Exception."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    base_url = get_ollama_base_url()
    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=GENERATE_TIMEOUT
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("message", {}).get("content", "No response generated.")
    else:
        raise ConnectionError(f"Ollama returned status {response.status_code}")


def _call_nvidia(prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
    """
    Call NVIDIA NIM API.
    Delegates to ai.llm.client._call_nvidia (openai SDK, settings-aware) when available.
    Falls back to raw requests implementation for environments without openai package.
    """
    # Prefer the canonical implementation from ai.llm.client
    try:
        from ai.llm.client import _call_nvidia as _nim  # type: ignore
        return _nim(prompt, system_prompt, temperature, max_tokens)
    except ImportError:
        pass  # openai package or config module missing — use raw requests fallback

    import os
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    if not nvidia_key:
        raise ConnectionError("NVIDIA_API_KEY not configured")
    nvidia_model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    nvidia_base  = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    headers = {
        "Authorization": f"Bearer {nvidia_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": nvidia_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(
        f"{nvidia_base}/chat/completions",
        json=payload,
        headers=headers,
        timeout=GENERATE_TIMEOUT,
    )
    if resp.status_code != 200:
        raise ConnectionError(f"NVIDIA NIM returned {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_response(
    prompt: str,
    system_prompt: str = None,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    provider: str = None,
) -> str:
    """
    Generate a response from the LLM.
    provider='nvidia' → NVIDIA NIM (Nemotron).
    provider='groq' or None → Ollama (primary) → Groq (fallback).

    Returns generated text or an error/fallback magic string.
    """
    # NVIDIA explicit route
    if provider == "nvidia":
        try:
            return _call_nvidia(prompt, system_prompt or "", temperature, max_tokens)
        except Exception as e:
            # Fall through to Groq if NVIDIA fails
            pass

    # Auto-select model via router when not explicitly specified
    resolved_model = model
    if resolved_model is None and _ROUTER_AVAILABLE and _route_query is not None:
        try:
            resolved_model, _query_type = _route_query(prompt)
        except Exception:
            resolved_model = None  # fall through to default model

    # Try Ollama first (primary provider)
    if OLLAMA_ENABLED:
        try:
            return _call_ollama(prompt, system_prompt or "", temperature, max_tokens, resolved_model)
        except requests.exceptions.ConnectionError:
            pass  # Fall through to Groq
        except requests.exceptions.Timeout:
            return "__LLM_TIMEOUT__"
        except Exception:
            pass  # Fall through to Groq

    # Try Groq as fallback
    groq_key = _get_groq_key()
    if groq_key:
        try:
            return _call_groq(prompt, system_prompt or "", temperature, max_tokens, resolved_model)
        except Exception:
            pass

    # No providers available
    return "__LLM_OFFLINE__"

def generate_response_streaming(
    prompt: str,
    system_prompt: str = None,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
):
    """
    Stream tokens from Ollama (primary) or Groq (fallback) as they arrive.
    Synchronous generator yielding individual token strings.
    """
    if OLLAMA_ENABLED:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model or DEFAULT_MODEL,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            base_url = get_ollama_base_url()
            resp = requests.post(f"{base_url}/api/chat", json=payload, stream=True, timeout=GENERATE_TIMEOUT)
            resp.raise_for_status()

            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    import json as _json
                    try:
                        data = _json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except _json.JSONDecodeError:
                        continue
            return
        except Exception:
            pass  # Fall through to Groq

    # Fallback: Groq streaming
    from groq import Groq
    groq_key = _get_groq_key()
    if not groq_key:
        yield "__LLM_OFFLINE__"
        return

    client = Groq(api_key=groq_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model=model or GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def generate_tutoring_response(
    topic: str,
    level: str,
    knowledge_gaps: list,
    retrieved_chunks: list,
    student_question: str,
    mastery: int = 0,
    model: str = None,
    provider: str = None,                    # 'groq' | 'nvidia' | None (auto)
    extra_system_instruction: str = None,    # explain-mode prefix (eli5, researcher, etc.)
    # Student Digital Twin — all optional, safe to omit
    weak_topics: list = None,
    strong_topics: list = None,
    recent_mistakes: list = None,
    recent_context: list = None,
) -> dict:
    """
    Generate a comprehensive adaptive tutoring response.

    Injects topic, level, mastery, knowledge gaps, and optional student
    memory (weak/strong topics, recent mistakes, conversation context)
    into the system prompt for personalised tutoring.

    Returns:
        dict with keys: explanation, analogy, example, practice_questions,
                        full_response, sources, llm_available, fallback_used
    """
    # Build context from retrieved chunks (always available)
    context_text = ""
    sources = []
    for i, chunk in enumerate(retrieved_chunks[:5], 1):
        context_text += f"\n--- Source {i}: {chunk['source']} (Page {chunk['page']}) ---\n"
        context_text += chunk['text'] + "\n"
        sources.append({
            "source": chunk['source'],
            "page": chunk['page'],
            "text": chunk['text'][:300]
        })

    # Level-adaptive system prompt
    level_instructions = _get_level_instructions(level)

    gaps_text = ""
    if knowledge_gaps:
        gaps_text = f"\nKnowledge Gaps to Address: {', '.join(knowledge_gaps[:6])}\n"

    mastery_text = f"\nCurrent Mastery: {mastery}%" if mastery > 0 else ""

    # Student Digital Twin personalisation (optional)
    twin_text = ""
    if weak_topics:
        twin_text += f"\nWeak Topics (reinforce these): {', '.join(weak_topics[:5])}"
    if strong_topics:
        twin_text += f"\nStrong Topics (already mastered): {', '.join(strong_topics[:5])}"
    if recent_mistakes:
        twin_text += f"\nRecent Mistakes (address proactively): {', '.join(recent_mistakes[:6])}"

    # Recent conversation context for continuity
    context_block = ""
    if recent_context:
        ctx_lines = []
        for msg in recent_context[-4:]:
            role = "Student" if msg.get("role") == "user" else "Tutor"
            ctx_lines.append(f"{role}: {msg.get('content', '')[:200]}")
        if ctx_lines:
            context_block = "\n=== Recent Conversation ===\n" + "\n".join(ctx_lines) + "\n"

    # Explain-mode tone block (prepended before everything else)
    mode_block = ""
    if extra_system_instruction:
        mode_block = f"=== Response Tone ===\n{extra_system_instruction}\n\n"

    system_prompt = f"""{mode_block}You are Synapse, an expert adaptive AI tutor.

=== Student Profile ===
Topic: {topic}
Level: {level}{mastery_text}{gaps_text}{twin_text}

=== Adaptive Teaching Rules ===
{level_instructions}
{context_block}
=== Reference Material (from textbooks) ===
{context_text if context_text else "No textbook content retrieved for this query."}

=== Response Structure ===
Your response MUST include these four sections with exact headers:

## Explanation
A clear, level-appropriate explanation of the concept.

## Analogy
A relatable real-world analogy that makes the concept intuitive.

## Worked Example
A concrete step-by-step example (include code or math where appropriate for the level).

## Practice Questions
2-3 practice questions the student can answer to test understanding.

Be thorough, encouraging, and fully adapted to {level} level."""

    raw = generate_response(
        prompt=student_question,
        system_prompt=system_prompt,
        model=model,
        provider=provider,
        temperature=0.7,
        max_tokens=3000
    )



    # ── Fallback Handling ────────────────────────────────────────────────────
    fallback_used = False
    llm_available = True

    if raw.startswith("__LLM_OFFLINE__") or raw.startswith("__LLM_TIMEOUT__") or raw.startswith("__LLM_ERROR__"):
        llm_available = False
        fallback_used = True
        raw = _build_fallback_response(topic, level, knowledge_gaps, retrieved_chunks, student_question, raw)

    result = _parse_tutoring_response(raw)
    result["raw_response"] = raw
    result["sources"] = sources
    result["llm_available"] = llm_available
    result["fallback_used"] = fallback_used

    return result


def _build_fallback_response(topic, level, knowledge_gaps, chunks, question, error_code):
    """
    Build a RAG-only fallback response when the LLM is unavailable.
    Uses retrieved textbook content to answer the question.
    """
    reason = {
        "__LLM_OFFLINE__": "The AI model server is currently offline.",
        "__LLM_TIMEOUT__": "The AI model server timed out.",
    }.get(error_code.split(":")[0].strip(), "The AI model encountered an error.")

    retrieved_text = ""
    if chunks:
        retrieved_text = "\n\n".join([
            f"From {c['source']} (Page {c['page']}):\n{c['text'][:400]}"
            for c in chunks[:3]
        ])
    else:
        retrieved_text = "No textbook content was retrieved for this query."

    gaps_text = ""
    if knowledge_gaps:
        gaps_text = f"\n\n**Areas to review:** {', '.join(knowledge_gaps[:4])}"

    return f"""## Explanation
**Note:** {reason} Showing textbook content instead.

**Question:** {question}

Here is relevant content retrieved from your textbooks on **{topic}**:

{retrieved_text}
{gaps_text}

## Analogy
*The AI tutor is temporarily offline. Please review the textbook excerpts above.*

## Worked Example
*Please refer to the source books listed in the Sources panel for worked examples.*

## Practice Questions
1. Based on the retrieved content above, can you summarize what you understood about {topic}?
2. What aspect of {topic} would you like to explore further once the AI tutor is back online?
3. Can you identify any connections between this content and what you already know about {topic}?"""


def _get_level_instructions(level: str) -> str:
    """Get teaching style instructions based on student level."""
    if level == "Beginner":
        return """- Use simple, everyday language with no assumed knowledge
- Explain every technical term when first introduced
- Use analogies and metaphors extensively
- Avoid or minimize mathematical notation; favor intuitive explanations
- Break concepts into very small, digestible steps
- Be encouraging and patient
- Use real-world examples that anyone can relate to"""

    elif level == "Intermediate":
        return """- Use technical language but explain advanced concepts
- Provide practical, hands-on examples with code snippets
- Include moderate mathematical notation where it helps understanding
- Connect concepts to real-world applications and industry use cases
- Reference best practices and common patterns
- Balance theory with practical implementation"""

    else:  # Advanced
        return """- Use formal technical terminology freely and precisely
- Include mathematical formulations, proofs, and derivations where relevant
- Discuss cutting-edge research and recent advancements
- Provide deep theoretical insights and analysis
- Discuss trade-offs, edge cases, and design decisions
- Reference academic papers and advanced resources when appropriate
- Engage in nuanced, research-level technical discussion"""


def _parse_tutoring_response(response: str) -> dict:
    """Parse the LLM response into structured sections."""
    result = {
        "explanation": "",
        "analogy": "",
        "example": "",
        "practice_questions": "",
        "full_response": response
    }

    section_markers = {
        "explanation": ["## Explanation", "## 📖 Explanation", "**Explanation**"],
        "analogy": ["## Analogy", "## 🔄 Analogy", "**Analogy**"],
        "example": ["## Worked Example", "## 💡 Worked Example", "**Worked Example**"],
        "practice_questions": ["## Practice Questions", "## ✏️ Practice Questions", "**Practice Questions**"]
    }

    # Find all section positions
    section_positions = {}
    for key, markers in section_markers.items():
        for marker in markers:
            if marker in response:
                pos = response.index(marker)
                section_positions[key] = (pos, len(marker))
                break

    # Extract each section content
    sorted_keys = sorted(section_positions, key=lambda k: section_positions[k][0])
    for i, key in enumerate(sorted_keys):
        start_pos, marker_len = section_positions[key]
        content_start = start_pos + marker_len
        if i + 1 < len(sorted_keys):
            next_key = sorted_keys[i + 1]
            content_end = section_positions[next_key][0]
        else:
            content_end = len(response)
        result[key] = response[content_start:content_end].strip()

    # If no sections parsed, put everything in explanation
    if not result["explanation"] and not result["analogy"]:
        result["explanation"] = response

    return result
