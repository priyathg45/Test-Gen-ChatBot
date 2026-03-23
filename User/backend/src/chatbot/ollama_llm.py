"""Ollama local LLM for document QA and summaries.
Uses LangChain's ChatOllama when available; falls back to direct HTTP if needed.
Run Ollama locally (e.g. ollama run llama3.2) so the chatbot can use it for PDF/document answers.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_OLLAMA_AVAILABLE: Optional[bool] = None


def is_ollama_available(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is reachable."""
    global _OLLAMA_AVAILABLE
    if _OLLAMA_AVAILABLE is not None:
        return _OLLAMA_AVAILABLE
    try:
        import urllib.request
        req = urllib.request.Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                _OLLAMA_AVAILABLE = True
                return True
    except Exception as e:
        logger.debug("Ollama not available at %s: %s", base_url, e)
    _OLLAMA_AVAILABLE = False
    return False


def _build_prompt(system_prompt: str, messages: List[Dict[str, str]]) -> str:
    """Turn chat messages into a single user prompt for Ollama."""
    parts = []
    if system_prompt:
        parts.append(system_prompt.strip())
    for msg in messages:
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            parts.append(content)
        elif role == "assistant":
            parts.append(f"(Assistant previously said: {content})")
    return "\n\n".join(parts)


def generate_answer_with_ollama(
    system_prompt: str,
    messages: List[Dict[str, str]],
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2",
    max_tokens: int = 512,
    temperature: float = 0.3,
) -> str:
    """
    Generate an answer using Ollama (local LLM server).
    Prefer this for document QA when USE_OLLAMA_FOR_DOCUMENTS is True.
    """
    if not is_ollama_available(base_url):
        return ""

    try:
        from langchain_community.llms import Ollama
        llm = Ollama(
            base_url=base_url,
            model=model,
            temperature=temperature,
            num_predict=max_tokens,
        )
        prompt = _build_prompt(system_prompt, messages)
        response = llm.invoke(prompt)
        if response and isinstance(response, str):
            return response.strip()
        return ""
    except ImportError:
        # Fallback: direct HTTP to Ollama /api/generate
        try:
            import json
            import urllib.request
            prompt = _build_prompt(system_prompt, messages)
            body = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            req = urllib.request.Request(
                f"{base_url.rstrip('/')}/api/generate",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode())
                return (data.get("response") or "").strip()
        except Exception as e:
            logger.warning("Ollama HTTP fallback failed: %s", e)
            return ""
    except Exception as e:
        logger.warning("Ollama generate failed: %s", e)
        return ""
def stream_answer_with_ollama(
    system_prompt: str,
    messages: List[Dict[str, str]],
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2",
    max_tokens: int = 512,
    temperature: float = 0.3,
):
    """
    Stream an answer from Ollama (local LLM server).
    Yields chunks of text as they arrive.
    """
    if not is_ollama_available(base_url):
        yield "Error: Ollama server not reachable."
        return

    try:
        import json
        import urllib.request
        prompt = _build_prompt(system_prompt, messages)
        body = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp:
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    text = chunk.get("response", "")
                    if text:
                        yield text
                    if chunk.get("done"):
                        break
    except Exception as e:
        logger.warning("Ollama streaming failed: %s", e)
        yield f"Error during streaming: {str(e)}"
